import cv2
import numpy as np


class ColorDetector:
    """检测车辆的主要颜色"""

    def __init__(self):
        # 定义颜色HSV范围
        self.color_ranges = {
            'red': [(0, 120, 70), (10, 255, 255), (170, 120, 70), (180, 255, 255)],
            'blue': [(100, 150, 0), (140, 255, 255)],
            'green': [(40, 40, 40), (70, 255, 255)],
            'yellow': [(20, 100, 100), (30, 255, 255)],
            'white': [(0, 0, 200), (180, 30, 255)],
            'black': [(0, 0, 0), (180, 255, 30)]
        }

    def detect_color(self, roi):
        """从车辆ROI中检测主要颜色"""
        if roi.size == 0:
            return "unknown"

        # 转换为HSV色彩空间
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        color_counts = {}

        # 统计每种颜色的像素数量
        for color, ranges in self.color_ranges.items():
            mask = None
            # 处理红色这种跨0度的颜色范围
            if color == 'red':
                mask1 = cv2.inRange(hsv_roi, np.array(ranges[0]), np.array(ranges[1]))
                mask2 = cv2.inRange(hsv_roi, np.array(ranges[2]), np.array(ranges[3]))
                mask = mask1 + mask2
            else:
                mask = cv2.inRange(hsv_roi, np.array(ranges[0]), np.array(ranges[1]))

            color_counts[color] = cv2.countNonZero(mask)

        # 返回像素最多的颜色
        max_color = max(color_counts, key=color_counts.get)
        return max_color if color_counts[max_color] > 0 else "unknown"
