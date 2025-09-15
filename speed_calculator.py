import time
import numpy as np


class SpeedCalculator:
    """车辆速度计算器，基于连续帧的位置变化计算速度"""

    def __init__(self, speed_factor=0.036, max_history=30):
        # speed_factor用于将像素/秒转换为km/h (0.036是一个经验值，可根据实际场景调整)
        self.speed_factor = speed_factor
        self.max_history = max_history  # 最大轨迹历史记录数量
        self.track_history = {}  # 存储轨迹历史 {vehicle_id: [(center_x, center_y, timestamp), ...]}

    def _calculate_displacement(self, prev_pos, curr_pos):
        """计算两点之间的位移（欧氏距离）"""
        return np.sqrt((curr_pos[0] - prev_pos[0]) ** 2 + (curr_pos[1] - prev_pos[1]) ** 2)

    def update_position(self, vehicle_id, bbox):
        """
        更新车辆位置并计算速度
        参数:
            vehicle_id: 车辆唯一标识
            bbox: 边界框 (x1, y1, x2, y2)
        返回:
            当前计算的速度 (km/h)
        """
        # 计算边界框中心点
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        current_time = time.time()  # 使用当前时间戳

        # 初始化该车辆的轨迹记录
        if vehicle_id not in self.track_history:
            self.track_history[vehicle_id] = []

        # 添加当前位置和时间到轨迹历史
        self.track_history[vehicle_id].append((center_x, center_y, current_time))

        # 限制历史记录数量，防止内存占用过大
        if len(self.track_history[vehicle_id]) > self.max_history:
            self.track_history[vehicle_id].pop(0)

        # 至少需要两个点才能计算速度
        if len(self.track_history[vehicle_id]) < 2:
            return 0.0

        # 使用最近的几个点来计算平均速度，提高准确性
        # 取最近的5个点（如果有），否则取所有可用点
        num_points = min(5, len(self.track_history[vehicle_id]))
        recent_points = self.track_history[vehicle_id][-num_points:]

        total_distance = 0.0
        total_time = 0.0

        # 计算总位移和总时间
        for i in range(1, num_points):
            prev_x, prev_y, prev_time = recent_points[i - 1]
            curr_x, curr_y, curr_time = recent_points[i]

            distance = self._calculate_displacement((prev_x, prev_y), (curr_x, curr_y))
            time_diff = curr_time - prev_time

            total_distance += distance
            total_time += time_diff

        # 避免除以零
        if total_time <= 0:
            return 0.0

        # 计算平均速度 (像素/秒) 并转换为 km/h
        speed_pixel_per_sec = total_distance / total_time
        speed_kmh = speed_pixel_per_sec * self.speed_factor

        # 过滤异常值（速度不可能为负，也不会超过合理范围）
        if speed_kmh < 0 or speed_kmh > 200:  # 假设最大速度不超过200km/h
            return 0.0

        # 保留一位小数
        return round(speed_kmh, 1)

    def clear_old_tracks(self, max_age=5.0):
        """清理长时间没有更新的轨迹"""
        current_time = time.time()
        to_remove = []

        for vehicle_id, history in self.track_history.items():
            if not history:
                to_remove.append(vehicle_id)
                continue

            # 检查最后更新时间
            last_update_time = history[-1][2]
            if current_time - last_update_time > max_age:
                to_remove.append(vehicle_id)

        # 移除过期轨迹
        for vehicle_id in to_remove:
            del self.track_history[vehicle_id]
