class VehicleData:
    """存储车辆检测的所有相关数据"""
    def __init__(self, id, bbox, type, color, speed, confidence, timestamp):
        self.id = id                  # 车辆唯一标识
        self.bbox = bbox              # 边界框 (x1, y1, x2, y2)
        self.type = type              # 车辆类型 (car, motorcycle, bus, truck)
        self.color = color            # 车辆颜色
        self.speed = speed            # 车辆速度 (km/h)
        self.confidence = confidence  # 检测置信度
        self.timestamp = timestamp    # 时间戳

    def to_dict(self):
        """转换为字典格式，便于序列化"""
        return {
            'id': self.id,
            'bbox': self.bbox,
            'type': self.type,
            'color': self.color,
            'speed': self.speed,
            'confidence': self.confidence,
            'timestamp': self.timestamp
        }
