# 🚗 智能车辆检测与分析系统 (Smart Vehicle Detection System)

本项目是一个基于 Python 和 YOLOv8 架构的实时车辆检测与多维数据分析系统。系统能够从视频流中精准检测车辆，提取车辆颜色、计算行驶速度，并将聚合后的结构化数据通过 TCP 协议实时分发给下游客户端。

## ✨ 核心特性 (Features)

* **⚡ 高性能目标检测**：基于 `YOLOv8` 纳米模型 (`yolov8n.pt` 及自定义 `WALDO30` 模型)，实现高帧率的实时车辆抓取。
* **🎨 多维特征提取**：不仅检测车辆位置，还通过独立模块同步识别车辆**颜色** (`color_detector`) 与**速度** (`speed_calculator`)。
* **🧩 模块化架构**：高度解耦的面向对象设计，检测、提取、聚合、通信各司其职，极易扩展与二次开发。
* **📡 实时数据流**：内置轻量级 TCP Server，支持将结构化的车辆分析结果（如 BBox、速度、颜色、ID）实时推送至外部客户端或大屏展示系统。

## 📂 项目结构 (Project Structure)

```text
├── models/                           # AI 模型权重目录
│   ├── WALDO30_yolov8n_640x640.pt    # 自定义训练的 YOLOv8 模型 (640x640)
│   └── yolov8n.pt                    # 官方基础 YOLOv8 纳米模型
├── main.py                           # 系统主入口，串联整体业务逻辑
├── model_loader.py                   # 模型加载器，负责初始化 YOLO 等模型
├── vehicle_detector.py               # 车辆检测核心逻辑 (BBox/类别提取)
├── color_detector.py                 # 颜色识别模块
├── speed_calculator.py               # 速度计算模块 (基于帧间位移/透视变换)
├── vehicle_data.py                   # 数据实体类 (Data Classes) 定义
├── vehicle_aggregator.py             # 数据聚合器，将检测、颜色、速度打包组合
└── tcp_server.py                     # TCP 通信模块，负责向下游推送 JSON/序列化数据
```

🛠️ 环境依赖 (Prerequisites)
Python 3.8+

ultralytics (YOLOv8 官方库)

opencv-python (OpenCV)

numpy

安装基础依赖：

```Bash
pip install ultralytics opencv-python numpy
```
🚀 运行指南 (Getting Started)
准备模型：确保 models/ 目录下已存在 .pt 权重文件。

启动系统：
运行主程序启动检测流与 TCP 服务：

```Bash
python main.py
```
接收数据：系统启动后，TCP Server 将开始监听。你可以编写简单的 TCP 客户端连接到对应端口（默认端口请查看 tcp_server.py 配置）来接收实时检测数据。

🤝 贡献与定制 (Customization)
如果需要替换检测模型，只需修改 model_loader.py 中的路径配置；如果需要对接不同的外部系统，可直接修改 tcp_server.py 的数据封装逻辑。
