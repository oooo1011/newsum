#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
子集和问题求解器 - 启动脚本
用于从项目根目录启动GUI应用程序
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入并运行应用程序
from python_app.main import SubsetSumApp
from PyQt6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubsetSumApp()
    window.show()
    sys.exit(app.exec())
