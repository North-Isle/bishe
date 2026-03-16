# 远程终端问诊系统

本项目是一个基于树莓派5的远程终端问诊系统，使用Python开发。系统采用服务器-客户端架构，实现了实时视频/音频传输、文字聊天、问诊记录存储等功能。

## 项目结构

```
├── server/            # 服务器端代码
│   ├── app.py         # 服务器主程序
│   ├── config.py      # 配置文件
│   ├── database.py    # 数据库操作
│   └── static/        # 静态文件
├── client/            # 客户端代码（树莓派端）
│   ├── app.py         # 客户端主程序
│   ├── config.py      # 配置文件
│   └── utils/         # 工具函数
├── requirements.txt   # 依赖包
└── README.md          # 项目说明
```

## 功能特性

- 实时视频/音频传输
- 文字聊天
- 问诊记录存储
- 简单易用的界面

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行服务器

```bash
cd server
python app.py
```

## 运行客户端（树莓派端）

```bash
cd client
python app.py
```

## 技术栈

- Python 3.7+
- Flask (服务器端)
- Socket/WebSockets (通信)
- OpenCV (视频处理)
- PyAudio (音频处理)
- SQLite (数据库)
- Tkinter (客户端界面)