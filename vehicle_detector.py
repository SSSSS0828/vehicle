import cv2
import numpy as np
from ultralytics import YOLO
from vehicle_aggregator import VehicleAggregator
from vehicle_data import VehicleData  # 统一使用vehicle_data中的类
import time


class VehicleDetector:
    def __init__(self, camera_matrix=None, speed_factor=0.036):
        # 加载YOLO模型
        try:
            self.detection_model = YOLO("models/yolov8n.pt")
            print("YOLO模型加载成功")
        except Exception as e:
            print(f"模型加载失败: {e}")
            raise

        # 初始化聚合器，传递速度因子
        self.aggregator = VehicleAggregator(speed_factor=speed_factor)
        # 统一车辆类别映射（与YOLO官方ID匹配）
        self.vehicle_classes = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
        self.conf_threshold = 0.5  # 置信度阈值

        # 车辆ID跟踪改进：使用字典存储检测框与ID的映射，提高连续性
        self.vehicle_ids = {}  # {检测框哈希值: vehicle_id}
        self.next_vehicle_id = 0  # 下一个可用ID
        self.debug = True

    def _get_vehicle_id(self, bbox):
        """
        根据边界框获取或分配车辆ID，提高跟踪连续性
        通过计算与历史检测框的相似度来匹配同一车辆
        """
        x1, y1, x2, y2 = bbox
        current_center = ((x1 + x2) / 2, (y1 + y2) / 2)
        min_distance = 50  # 最大匹配距离（像素）
        matched_id = None
        matched_bbox = None  # 用于记录匹配到的existing_bbox

        # 检查是否与现有车辆匹配
        for existing_bbox, vehicle_id in list(self.vehicle_ids.items()):
            ex_x1, ex_y1, ex_x2, ex_y2 = existing_bbox
            existing_center = ((ex_x1 + ex_x2) / 2, (ex_y1 + ex_y2) / 2)

            # 计算中心点距离
            distance = np.sqrt(
                (current_center[0] - existing_center[0]) ** 2 +
                (current_center[1] - existing_center[1]) ** 2
            )

            if distance < min_distance:
                matched_id = vehicle_id
                matched_bbox = existing_bbox  # 记录匹配的bbox
                break

        if matched_id is not None:
            # 更新边界框记录
            del self.vehicle_ids[matched_bbox]  # 使用记录的matched_bbox
            self.vehicle_ids[bbox] = matched_id
            return matched_id
        else:
            # 分配新ID
            new_id = self.next_vehicle_id
            self.vehicle_ids[bbox] = new_id
            self.next_vehicle_id += 1
            return new_id

    def process_frame(self, frame):
        """处理单帧并返回车辆数据列表"""
        vehicles = []
        detections = self.detect_vehicles(frame)
        if not detections.size:
            return vehicles

        # 清理旧的ID映射（超过一定数量时）
        if len(self.vehicle_ids) > 100:
            self.vehicle_ids = {k: v for k, v in list(self.vehicle_ids.items())[-50:]}

        for i, det in enumerate(detections):
            try:
                x1, y1, x2, y2, conf, class_id = det
                class_id = int(class_id)
                if class_id not in self.vehicle_classes:
                    continue

                vehicle_type = self.vehicle_classes[class_id]
                bbox = (float(x1), float(y1), float(x2), float(y2))

                # 使用改进的ID分配方法
                vehicle_id = self._get_vehicle_id(bbox)

                # 调用聚合器获取颜色和速度
                color, speed = self.aggregator.get_vehicle_features(frame, bbox, vehicle_id)

                vehicles.append(VehicleData(
                    id=vehicle_id,
                    bbox=bbox,
                    type=vehicle_type,
                    color=color,
                    speed=speed,
                    confidence=float(conf),
                    timestamp=time.time()  # 使用更精确的时间戳
                ))
            except Exception as e:
                print(f"处理检测结果出错: {e}")
                continue

        return vehicles

    def detect_vehicles(self, frame):
        """检测车辆并返回边界框数据"""
        try:
            results = self.detection_model(
                frame,
                conf=self.conf_threshold,
                classes=[2, 3, 5, 7],  # 只检测车辆类别
                verbose=False
            )
            if not results or not results[0].boxes:
                return np.array([])
            return results[0].boxes.data.cpu().numpy()  # 格式：[x1,y1,x2,y2,conf,class_id]
        except Exception as e:
            print(f"检测出错: {e}")
            return np.array([])
