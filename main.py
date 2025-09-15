import cv2
import threading
import time
import signal
import sys
import numpy as np
from vehicle_detector import VehicleDetector
from tcp_server import VehicleTCPServer


class TrafficMonitoringSystem:
    """交通监控系统主类"""

    def __init__(self):
        # 系统配置
        self.config = {
            'camera_source': "111.mp4",  # 可以是视频文件路径或摄像头ID
            'server_host': '0.0.0.0',
            'server_port': 9999,
            'show_video': True,
            'run_server': False,
            'camera_matrix': np.array([[1000, 0, 320], [0, 1000, 240], [0, 0, 1]])
        }

        # 初始化组件
        self.detector = VehicleDetector(self.config['camera_matrix'])
        self.tcp_server = VehicleTCPServer(self.config['server_host'], self.config['server_port'])

        # 系统状态变量
        self.running = False
        self.frame = None
        self.detected_vehicles = []  # 存储检测到的车辆数据
        self.is_paused = False
        self.lock = threading.Lock()  # 线程同步锁

        # 注册信号处理（优雅退出）
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """处理系统信号，实现优雅退出"""
        print(f"接收到信号 {signum}，停止系统...")
        self.stop()
        sys.exit(0)

    def start(self):

        """启动系统"""
        self.running = True

        # 启动TCP服务器（如果配置开启）
        if self.config['run_server']:
            self.tcp_server.start()

        # 启动各个工作线程
        threading.Thread(target=self._camera_loop, daemon=True).start()
        threading.Thread(target=self._processing_loop, daemon=True).start()

        # 如果需要显示视频，启动显示线程
        if self.config['show_video']:
            threading.Thread(target=self._display_loop, daemon=True).start()

        print("系统启动成功")

        # 主循环
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def _camera_loop(self):
        """摄像头/视频读取线程"""
        cap = cv2.VideoCapture(self.config['camera_source'])
        # 设置分辨率
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not cap.isOpened():
            print("无法打开摄像头/视频")
            self.running = False
            return

        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("获取帧失败，重试...")
                cap.release()
                cap = cv2.VideoCapture(self.config['camera_source'])
                continue

            # 线程安全地更新当前帧
            with self.lock:
                self.frame = frame.copy()

            time.sleep(0.03)  # 控制帧率

        cap.release()

    def _processing_loop(self):
        """车辆检测处理线程"""
        while self.running:
            # 处理暂停状态
            while self.is_paused and self.running:
                time.sleep(0.1)

            current_frame = None
            # 线程安全地获取当前帧
            with self.lock:
                if self.frame is not None:
                    current_frame = self.frame.copy()

            if current_frame is not None:
                try:
                    # 检测车辆
                    vehicles = self.detector.process_frame(current_frame)
                    # 转换为字典列表
                    vehicle_dicts = [v.to_dict() for v in vehicles]

                    # 线程安全地更新检测结果
                    with self.lock:
                        self.detected_vehicles = vehicle_dicts

                    # 如果开启了服务器，发送数据
                    if self.config['run_server']:
                        self.tcp_server.send_data(vehicle_dicts)

                except Exception as e:
                    print(f"处理帧出错: {e}")

            time.sleep(0.05)

    def _display_loop(self):
        """视频显示线程"""
        # 尝试加载中文字体
        font = None
        font_candidates = [
            "C:/Windows/Fonts/simhei.ttf" if sys.platform.startswith('win') else
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc" if sys.platform.startswith('linux') else
            "/System/Library/Fonts/PingFang.ttc"
        ]

        for path in font_candidates:
            if cv2.os.path.exists(path):
                try:
                    font = cv2.freetype.createFreeType2()
                    font.loadFontData(path, 0)
                    break
                except:
                    continue

        if not font:
            print("警告：未加载中文字体，中文可能显示异常")

        while self.running:
            current_frame = None
            current_vehicles = []

            # 线程安全地获取数据
            with self.lock:
                if self.frame is not None:
                    current_frame = self.frame.copy()
                current_vehicles = self.detected_vehicles.copy()

            if current_frame is not None:
                # 绘制检测结果
                for vehicle in current_vehicles:
                    if 'bbox' not in vehicle:
                        continue

                    x1, y1, x2, y2 = map(int, vehicle['bbox'])
                    # 绘制边界框
                    cv2.rectangle(current_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # 绘制标签 - 调整字体粗细和大小
                    label = f"{vehicle['type']} {vehicle['color']} {vehicle['speed']}km/h"
                    if font:
                        # 线宽改为1（更细），字体高度调整为14（稍小）
                        font.putText(
                            current_frame,
                            label,
                            (x1, y1 - 10),
                            14,  # 字体高度（稍小一些）
                            (0, 0, 255),  # 颜色
                            1,  # 线宽（更细）
                            cv2.LINE_AA,  # 抗锯齿线条
                            bottomLeftOrigin=False  # 原点位置
                        )
                    else:
                        cv2.putText(
                            current_frame,
                            label,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,  # 字体大小
                            (0, 0, 255),
                            1  # 线宽（更细）
                        )

                # 显示图像
                cv2.imshow("交通监控系统", current_frame)

                # 处理按键
                key = cv2.waitKey(1)
                if key == ord('q'):  # 按q退出
                    self.stop()
                elif key == ord('p'):  # 按p暂停/继续
                    self.is_paused = not self.is_paused

        cv2.destroyAllWindows()

    def stop(self):
        """停止系统"""
        self.running = False
        self.tcp_server.stop()
        print("系统已停止")


if __name__ == "__main__":
    system = TrafficMonitoringSystem()
    system.start()
