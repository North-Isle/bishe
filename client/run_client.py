#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派客户端启动脚本
使用 PyQt5 桌面应用程序界面
"""

import sys
import os

# 添加父目录到路径，以便导入 utils 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui_client import main

if __name__ == '__main__':
    main()
