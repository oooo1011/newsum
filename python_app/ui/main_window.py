#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
主窗口UI定义
使用PyQt6构建GUI界面
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, 
    QTableWidget, QCheckBox, QComboBox, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QGroupBox, QFileDialog, QMessageBox, QProgressBar,
    QSplitter, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon


class Ui_MainWindow(object):
    """主窗口UI定义类"""
    
    def setupUi(self, MainWindow):
        """设置UI组件"""
        # 设置窗口属性
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setWindowTitle("SubsetSum Solver - 子集和问题求解器")
        
        # 创建中央窗口部件
        self.centralwidget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.centralwidget)
        
        # 创建数据导入区域
        self.create_data_import_section()
        
        # 创建参数设置区域
        self.create_params_section()
        
        # 创建计算控制区域
        self.create_calculation_section()
        
        # 创建结果显示区域
        self.create_results_section()
        
        # 创建状态栏
        self.create_status_section()
    
    def create_data_import_section(self):
        """创建数据导入区域"""
        group_box = QGroupBox("数据导入")
        layout = QHBoxLayout()
        
        # 文件路径显示
        self.txtFilePath = QLineEdit()
        self.txtFilePath.setReadOnly(True)
        self.txtFilePath.setPlaceholderText("请选择数据文件...")
        
        # 浏览按钮
        self.btnBrowse = QPushButton("浏览...")
        self.btnBrowse.setFixedWidth(80)
        
        layout.addWidget(self.txtFilePath)
        layout.addWidget(self.btnBrowse)
        
        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)
        
        # 数据表格
        self.tblNumbers = QTableWidget()
        self.tblNumbers.setColumnCount(2)
        self.tblNumbers.setHorizontalHeaderLabels(['索引', '数值'])
        self.tblNumbers.setMinimumHeight(150)
        
        self.main_layout.addWidget(self.tblNumbers)
    
    def create_params_section(self):
        """创建参数设置区域"""
        group_box = QGroupBox("计算参数")
        layout = QGridLayout()
        
        # 目标和值
        layout.addWidget(QLabel("目标和值:"), 0, 0)
        self.txtTarget = QLineEdit()
        self.txtTarget.setPlaceholderText("输入目标和值...")
        layout.addWidget(self.txtTarget, 0, 1)
        
        # 计算精度
        layout.addWidget(QLabel("计算精度:"), 0, 2)
        self.txtPrecision = QLineEdit()
        self.txtPrecision.setPlaceholderText("输入计算精度...")
        layout.addWidget(self.txtPrecision, 0, 3)
        
        # 算法选择
        layout.addWidget(QLabel("算法选择:"), 1, 0)
        self.cmbAlgorithm = QComboBox()
        layout.addWidget(self.cmbAlgorithm, 1, 1, 1, 3)
        
        # 计算所有解选项
        self.chkFindAll = QCheckBox("计算所有可能解")
        layout.addWidget(self.chkFindAll, 2, 0, 1, 4)
        
        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)
    
    def create_calculation_section(self):
        """创建计算控制区域"""
        layout = QHBoxLayout()
        
        # 开始计算按钮
        self.btnCalculate = QPushButton("开始计算")
        self.btnCalculate.setMinimumHeight(40)
        font = QFont()
        font.setBold(True)
        self.btnCalculate.setFont(font)
        
        # 暂停/恢复计算按钮
        self.btnPause = QPushButton("暂停计算")
        self.btnPause.setMinimumHeight(40)
        
        # 停止计算按钮
        self.btnStop = QPushButton("停止计算")
        self.btnStop.setMinimumHeight(40)
        
        layout.addWidget(self.btnCalculate)
        layout.addWidget(self.btnPause)
        layout.addWidget(self.btnStop)
        
        self.main_layout.addLayout(layout)
    
    def create_results_section(self):
        """创建结果显示区域"""
        group_box = QGroupBox("计算结果")
        layout = QVBoxLayout()
        
        # 结果表格
        self.tblResults = QTableWidget()
        self.tblResults.setColumnCount(2)
        self.tblResults.setHorizontalHeaderLabels(['数值', '是否选中'])
        self.tblResults.setMinimumHeight(150)
        
        layout.addWidget(self.tblResults)
        
        # 导出按钮
        self.btnExport = QPushButton("导出结果")
        layout.addWidget(self.btnExport)
        
        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)
    
    def create_status_section(self):
        """创建状态栏"""
        layout = QHBoxLayout()
        
        # 状态标签
        layout.addWidget(QLabel("状态:"))
        self.lblStatus = QLabel("就绪")
        layout.addWidget(self.lblStatus)
        
        # 添加弹性空间
        layout.addStretch()
        
        self.main_layout.addLayout(layout)
