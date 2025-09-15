import torch
from ultralytics import YOLO
import os

class ModelLoader:
    def __init__(self):
        """初始化模型加载器"""
        self.detection_model_path = "models/yolov8n.pt"
        self.classification_model_path = "models/WALDO30_yolov8n_640x640.pt"
        
        # 检查设备
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {self.device}")
    
    def load_detection_model(self):
        if not os.path.exists(self.detection_model_path):
            raise FileNotFoundError(f"检测模型文件不存在: {self.detection_model_path}")
        """加载车辆检测模型"""
        try:
            model = YOLO(self.detection_model_path)
            model.to(self.device)
            return model
        except Exception as e:
            print(f"检测模型加载失败: {e}")
            raise
    
    def load_classification_model(self):
        if not os.path.exists(self.classification_model_path):
            raise FileNotFoundError(f"分类模型文件不存在: {self.classification_model_path}")
        """加载车辆分类模型"""
        try:
            # 这里使用简化版本，实际应用中会加载更专业的分类模型
            model = YOLO(self.classification_model_path)
            model.to(self.device)
            return model
        except Exception as e:
            print(f"分类模型加载失败: {e}")
            raise
    
    def load_custom_model(self, model_path):
        """加载自定义模型"""
        try:
            model = YOLO(model_path)
            model.to(self.device)
            return model
        except Exception as e:
            print(f"自定义模型加载失败: {e}")
            raise
