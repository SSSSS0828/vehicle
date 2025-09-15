import cv2
import numpy as np
from color_detector import ColorDetector
from speed_calculator import SpeedCalculator  # 使用修复后的速度计算器

class VehicleAggregator:
    """聚合车辆颜色和速度信息"""
    def __init__(self, speed_factor=0.036):
        self.color_detector = ColorDetector()
        # 传递speed_factor参数，可根据实际场景调整
        self.speed_calculator = SpeedCalculator(speed_factor=speed_factor)
        self.track_history = self.speed_calculator.track_history  # 复用轨迹数据
        self.color_threshold = 50  # 颜色检测阈值

    def get_vehicle_features(self, frame, bbox, vehicle_id):
        """提取颜色和速度特征"""
        x1, y1, x2, y2 = map(int, bbox)
        h, w = frame.shape[:2]
        # 边界框越界处理
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        roi = frame[y1:y2, x1:x2]

        color = self.color_detector.detect_color(roi)  # 统一调用detect_color
        speed = self.speed_calculator.update_position(vehicle_id, bbox)
        return color, speed

    def clear_expired_tracks(self, max_age=5.0):
        """清理过期轨迹"""
        self.speed_calculator.clear_old_tracks(max_age=max_age)
