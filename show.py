import sys
import json
import socket
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QFrame)
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRectF, QTimer

# 车辆类型与颜色映射
VEHICLE_TYPE_COLOR = {
    "car": QColor(0, 128, 255),  # 蓝色
    "motorcycle": QColor(0, 255, 128),  # 浅绿色
    "bus": QColor(255, 165, 0),  # 橙色
    "truck": QColor(255, 0, 128)  # 紫红色
}

# 干道场景参数
ROAD_WIDTH = 600
ROAD_HEIGHT = 400
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT
SIDEWALK_WIDTH = 50


class Vehicle:
    """虚拟车辆类，存储车辆状态"""

    def __init__(self, vehicle_id, vehicle_type, color, speed, bbox):
        self.id = vehicle_id
        self.type = vehicle_type
        self.color = color
        self.speed = speed
        self.bbox = bbox
        self.x = 0  # 虚拟场景X坐标
        self.y = 0  # 虚拟场景Y坐标
        self.lane = 0  # 车道号
        self.update_position()

    def update_position(self):
        """根据检测框更新虚拟位置（将视频坐标映射到虚拟场景）"""
        x1, y1, x2, y2 = self.bbox
        # 简单的坐标映射逻辑，可根据实际场景调整
        self.x = (x1 / 1280) * ROAD_WIDTH  # 假设原视频宽度1280
        self.y = (y1 / 720) * ROAD_HEIGHT  # 假设原视频高度720

        # 根据Y坐标分配车道
        self.lane = min(int(self.y / (ROAD_HEIGHT / LANE_COUNT)), LANE_COUNT - 1)

        # 根据速度调整X方向移动（模拟前进）
        self.x = (self.x + self.speed * 0.05) % (ROAD_WIDTH + 100)


class TCPClient(QThread):
    """TCP客户端线程，接收车辆数据"""
    data_received = pyqtSignal(list)  # 发送车辆数据列表信号

    def __init__(self, host='localhost', port=9999):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True
        self.socket = None

    def run(self):
        """线程运行函数，持续接收数据"""
        while self.running:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                print(f"已连接到服务器 {self.host}:{self.port}")

                while self.running:
                    data = self.socket.recv(4096).decode('utf-8')
                    if not data:
                        break

                    # 解析JSON数据
                    try:
                        vehicle_data = json.loads(data.strip())
                        self.data_received.emit(vehicle_data)
                    except json.JSONDecodeError as e:
                        print(f"数据解析错误: {e}")

            except Exception as e:
                print(f"连接错误: {e}，重试中...")
                self.socket.close()
                self.msleep(3000)  # 3秒后重试

        if self.socket:
            self.socket.close()

    def stop(self):
        """停止客户端"""
        self.running = False
        self.wait()


class RoadScene(QWidget):
    """干道场景绘制组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vehicles = {}  # {id: Vehicle对象}
        self.setMinimumSize(ROAD_WIDTH + 2 * SIDEWALK_WIDTH, ROAD_HEIGHT)
        self.setStyleSheet("background-color: #f0f0f0;")

    def update_vehicles(self, vehicle_data_list):
        """更新车辆数据"""
        # 更新现有车辆或添加新车辆
        for data in vehicle_data_list:
            vehicle_id = data['id']
            if vehicle_id in self.vehicles:
                self.vehicles[vehicle_id].speed = data['speed']
                self.vehicles[vehicle_id].bbox = data['bbox']
                self.vehicles[vehicle_id].update_position()
            else:
                self.vehicles[vehicle_id] = Vehicle(
                    vehicle_id=data['id'],
                    vehicle_type=data['type'],
                    color=data['color'],
                    speed=data['speed'],
                    bbox=data['bbox']
                )

        # 移除长时间未更新的车辆（5秒）
        current_time = data.get('timestamp', 0) if vehicle_data_list else 0
        to_remove = []
        for vid, vehicle in self.vehicles.items():
            if current_time - data.get('timestamp', 0) > 5:
                to_remove.append(vid)
        for vid in to_remove:
            del self.vehicles[vid]

        self.update()  # 触发重绘

    def paintEvent(self, event):
        """绘制场景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制道路
        road_rect = QRectF(
            SIDEWALK_WIDTH, 0,
            ROAD_WIDTH, ROAD_HEIGHT
        )
        painter.fillRect(road_rect, QBrush(QColor(50, 50, 50)))

        # 绘制车道线
        pen = QPen(QColor(255, 255, 255), 2, Qt.DashLine)
        painter.setPen(pen)
        for i in range(1, LANE_COUNT):
            y = (ROAD_HEIGHT / LANE_COUNT) * i
            painter.drawLine(
                SIDEWALK_WIDTH, y,
                SIDEWALK_WIDTH + ROAD_WIDTH, y
            )

        # 绘制车辆
        for vehicle in self.vehicles.values():
            # 车辆尺寸根据类型调整
            if vehicle.type == "car":
                w, h = 40, 20
            elif vehicle.type == "motorcycle":
                w, h = 20, 10
            elif vehicle.type == "bus":
                w, h = 60, 25
            else:  # truck
                w, h = 50, 25

            # 车辆位置（基于车道调整）
            lane_y = (vehicle.lane * (ROAD_HEIGHT / LANE_COUNT)) + (ROAD_HEIGHT / (2 * LANE_COUNT))
            vehicle_rect = QRectF(
                SIDEWALK_WIDTH + vehicle.x - w / 2,
                lane_y - h / 2,
                w, h
            )

            # 绘制车辆
            painter.fillRect(vehicle_rect, QBrush(VEHICLE_TYPE_COLOR.get(vehicle.type, QColor(200, 200, 200))))
            painter.drawRect(vehicle_rect)

            # 绘制车辆ID和速度
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("SimHei", 8))
            painter.drawText(
                vehicle_rect.center().x() - 15,
                vehicle_rect.center().y() + 4,
                f"{vehicle.id} ({vehicle.speed}km/h)"
            )

        # 绘制人行道
        sidewalk_left = QRectF(0, 0, SIDEWALK_WIDTH, ROAD_HEIGHT)
        sidewalk_right = QRectF(
            SIDEWALK_WIDTH + ROAD_WIDTH, 0,
            SIDEWALK_WIDTH, ROAD_HEIGHT
        )
        painter.fillRect(sidewalk_left, QBrush(QColor(150, 150, 150)))
        painter.fillRect(sidewalk_right, QBrush(QColor(150, 150, 150)))


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("车辆干道虚拟演示系统")
        self.setGeometry(100, 100, 800, 500)

        # 创建中心组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 添加标题
        title_label = QLabel("车辆干道实时监控演示")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("SimHei", 14, QFont.Bold))
        main_layout.addWidget(title_label)

        # 添加道路场景
        self.road_scene = RoadScene()
        main_layout.addWidget(self.road_scene)

        # 添加状态信息
        status_layout = QHBoxLayout()
        self.status_label = QLabel("等待连接到服务器...")
        self.vehicle_count_label = QLabel("车辆数量: 0")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.vehicle_count_label)
        main_layout.addLayout(status_layout)

        # 启动TCP客户端
        self.tcp_client = TCPClient()
        self.tcp_client.data_received.connect(self.on_data_received)
        self.tcp_client.start()

        # 定时器更新状态
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)

    def on_data_received(self, vehicle_data):
        """处理接收到的车辆数据"""
        self.road_scene.update_vehicles(vehicle_data)

    def update_status(self):
        """更新状态信息"""
        vehicle_count = len(self.road_scene.vehicles)
        self.vehicle_count_label.setText(f"车辆数量: {vehicle_count}")
        if self.tcp_client.socket:
            self.status_label.setText(f"已连接到服务器 {self.tcp_client.host}:{self.tcp_client.port}")
        else:
            self.status_label.setText("正在尝试连接到服务器...")

    def closeEvent(self, event):
        """窗口关闭时停止线程"""
        self.tcp_client.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())