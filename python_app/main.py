#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
子集和问题求解器 - 主程序
使用PyQt6构建GUI界面，调用Rust核心算法进行高性能计算
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, 
    QTableWidgetItem, QHeaderView, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMutex, QWaitCondition
from PyQt6.QtGui import QColor

# 导入UI和处理模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python_app.ui.main_window import Ui_MainWindow
from python_app.handlers.file_handler import FileHandler
from python_app.handlers.calc_handler import CalculationHandler

class SubsetSumApp(QMainWindow):
    """子集和问题求解器主应用"""
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # 初始化变量
        self.numbers = []
        self.indices = []  # 原始索引
        self.results = []
        self.filename = ""
        self.calculation_thread = None
        self.is_calculating = False
        
        # 初始化处理器
        self.file_handler = FileHandler()
        self.calc_handler = CalculationHandler()
        
        # 连接信号和槽
        self.connect_signals()
        
        # 初始化UI状态
        self.init_ui()
    
    def init_ui(self):
        """初始化UI状态"""
        # 设置默认值
        self.ui.txtPrecision.setText("0.0")
        self.ui.txtTarget.setText("0.0")
        
        # 设置算法选择下拉框
        self.ui.cmbAlgorithm.addItem("位运算枚举法 (n≤25)", "bit_enum")
        self.ui.cmbAlgorithm.addItem("Meet-in-the-Middle (25<n≤40)", "meet_middle")
        self.ui.cmbAlgorithm.addItem("动态规划算法 (整数问题)", "dp")
        self.ui.cmbAlgorithm.addItem("分支定界法 (n>40，单解)", "branch_bound")
        self.ui.cmbAlgorithm.addItem("自动选择最佳算法", "auto")
        self.ui.cmbAlgorithm.setCurrentIndex(4)  # 默认自动选择
        
        # 初始化按钮状态
        self.ui.btnCalculate.setEnabled(False)
        self.ui.btnStop.setEnabled(False)
        self.ui.btnPause.setEnabled(False)  # 初始时暂停按钮禁用
        self.ui.btnExport.setEnabled(False)
        
        # 设置表格属性
        self.ui.tblNumbers.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ui.tblResults.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 设置状态标签
        self.ui.lblStatus.setText("就绪")
    
    def connect_signals(self):
        """连接信号和槽"""
        self.ui.btnBrowse.clicked.connect(self.browse_file)
        self.ui.btnCalculate.clicked.connect(self.start_calculation)
        self.ui.btnStop.clicked.connect(self.stop_calculation)
        self.ui.btnPause.clicked.connect(self.toggle_pause_calculation)
        self.ui.btnExport.clicked.connect(self.export_results)
        
        # 算法选择变化时更新UI
        self.ui.cmbAlgorithm.currentIndexChanged.connect(self.update_ui_for_algorithm)
    
    def browse_file(self):
        """浏览并加载文件"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", 
            "文本文件 (*.txt);;Excel文件 (*.xlsx *.xls);;所有文件 (*)"
        )
        
        if filename:
            self.filename = filename
            self.ui.txtFilePath.setText(filename)
            try:
                self.numbers, self.indices = self.file_handler.load_data(filename)
                self.ui.btnCalculate.setEnabled(True)
                self.ui.lblStatus.setText(f"已加载 {len(self.numbers)} 个数字")
                self.display_input_data()
                
                # 根据数据规模自动选择算法
                self.suggest_algorithm()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法加载文件: {str(e)}")
    
    def suggest_algorithm(self):
        """根据数据规模建议算法"""
        n = len(self.numbers)
        if n <= 25:
            self.ui.cmbAlgorithm.setCurrentIndex(0)  # 位运算枚举
        elif n <= 40:
            self.ui.cmbAlgorithm.setCurrentIndex(1)  # Meet-in-the-Middle
        else:
            self.ui.cmbAlgorithm.setCurrentIndex(3)  # 分支定界
    
    def display_input_data(self):
        """显示导入的数据"""
        # 清空表格
        self.ui.tblNumbers.setRowCount(len(self.numbers))
        self.ui.tblNumbers.setColumnCount(2)
        self.ui.tblNumbers.setHorizontalHeaderLabels(['索引', '数值'])
        
        # 填充数据
        for i, (idx, num) in enumerate(zip(self.indices, self.numbers)):
            self.ui.tblNumbers.setItem(i, 0, QTableWidgetItem(str(idx)))
            self.ui.tblNumbers.setItem(i, 1, QTableWidgetItem(f"{num:.2f}"))
    
    def update_ui_for_algorithm(self):
        """根据选择的算法更新UI"""
        algorithm = self.ui.cmbAlgorithm.currentData()
        if algorithm == "branch_bound":
            # 分支定界法默认不计算所有解
            self.ui.chkFindAll.setChecked(False)
            self.ui.chkFindAll.setEnabled(False)
        else:
            self.ui.chkFindAll.setEnabled(True)
    
    def start_calculation(self):
        """开始计算"""
        if not self.numbers:
            QMessageBox.warning(self, "警告", "请先导入数据")
            return
        
        try:
            target = float(self.ui.txtTarget.text())
            precision = float(self.ui.txtPrecision.text())
            find_all = self.ui.chkFindAll.isChecked()
            algorithm = self.ui.cmbAlgorithm.currentData()
            
            # 更新UI状态
            self.ui.btnCalculate.setEnabled(False)
            self.ui.btnStop.setEnabled(True)
            self.ui.btnPause.setEnabled(True)  # 开始计算后启用暂停按钮
            self.ui.btnExport.setEnabled(False)
            self.ui.lblStatus.setText("计算中...")
            self.is_calculating = True
            
            # 创建并启动计算线程
            self.calculation_thread = CalculationThread(
                self.numbers, target, precision, find_all, algorithm
            )
            self.calculation_thread.result_ready.connect(self.handle_results)
            self.calculation_thread.progress_update.connect(self.update_progress)
            self.calculation_thread.error_occurred.connect(self.handle_error)
            self.calculation_thread.start()
            
        except ValueError as e:
            QMessageBox.critical(self, "错误", f"输入参数无效: {str(e)}")
    
    def stop_calculation(self):
        """停止计算"""
        if self.calculation_thread and self.is_calculating:
            self.calculation_thread.stop()
            self.is_calculating = False
            self.ui.btnCalculate.setEnabled(True)
            self.ui.btnStop.setEnabled(False)
            self.ui.btnPause.setEnabled(False)  # 停止计算后禁用暂停按钮
            self.ui.lblStatus.setText("计算已停止")
    
    def toggle_pause_calculation(self):
        """切换计算暂停状态"""
        if self.calculation_thread and self.is_calculating:
            if self.calculation_thread.is_paused():
                self.calculation_thread.resume()
                self.ui.btnPause.setText("暂停")
                self.ui.lblStatus.setText("计算中...")
            else:
                self.calculation_thread.pause()
                self.ui.btnPause.setText("继续")
                self.ui.lblStatus.setText("计算已暂停")
    
    def handle_results(self, results):
        """处理计算结果"""
        self.results = results
        self.is_calculating = False
        self.ui.btnCalculate.setEnabled(True)
        self.ui.btnStop.setEnabled(False)
        self.ui.btnPause.setEnabled(False)  # 计算完成后禁用暂停按钮
        self.ui.btnExport.setEnabled(True)
        
        # 显示结果
        self.display_results()
        
        # 更新状态
        self.ui.lblStatus.setText(f"计算完成，找到 {len(results)} 个解")
    
    def update_progress(self, progress):
        """更新进度"""
        self.ui.lblStatus.setText(f"计算中... {progress}%")
    
    def handle_error(self, error_msg):
        """处理错误"""
        self.is_calculating = False
        self.ui.btnCalculate.setEnabled(True)
        self.ui.btnStop.setEnabled(False)
        self.ui.btnPause.setEnabled(False)  # 出错后禁用暂停按钮
        self.ui.lblStatus.setText("计算出错")
        QMessageBox.critical(self, "错误", error_msg)
    
    def display_results(self):
        """显示计算结果"""
        if not self.results:
            self.ui.tblResults.setRowCount(0)
            return
        
        # 设置表格
        self.ui.tblResults.setRowCount(len(self.numbers))
        self.ui.tblResults.setColumnCount(2)
        self.ui.tblResults.setHorizontalHeaderLabels(['数值', '是否选中'])
        
        # 填充数据
        for i, (idx, num) in enumerate(zip(self.indices, self.numbers)):
            self.ui.tblResults.setItem(i, 0, QTableWidgetItem(f"{num:.2f}"))
            
            # 检查当前索引是否在任何解中
            is_selected = False
            for result in self.results:
                if idx in result:
                    is_selected = True
                    break
            
            item = QTableWidgetItem("是" if is_selected else "否")
            if is_selected:
                item.setBackground(QColor(255, 255, 0))  # 黄色背景
            
            self.ui.tblResults.setItem(i, 1, item)
    
    def export_results(self):
        """导出结果到Excel"""
        if not self.results:
            QMessageBox.warning(self, "警告", "没有可导出的结果")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存结果", "", 
            "Excel文件 (*.xlsx)"
        )
        
        if filename:
            try:
                # 获取目标值
                target = float(self.ui.txtTarget.text())
                
                self.file_handler.export_results(
                    filename, self.numbers, self.indices, self.results, target
                )
                QMessageBox.information(self, "成功", "结果已成功导出")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")


class CalculationThread(QThread):
    """计算线程"""
    result_ready = pyqtSignal(list)
    progress_update = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, numbers, target, precision, find_all, algorithm):
        super().__init__()
        self.numbers = numbers
        self.target = target
        self.precision = precision
        self.find_all = find_all
        self.algorithm = algorithm
        # 添加停止和暂停标志
        self._stop_requested = False
        self._paused = False
        self._pause_mutex = QMutex()
        self._pause_condition = QWaitCondition()
    
    def stop(self):
        """安全请求停止计算"""
        self._stop_requested = True
        # 恢复计算以便检查停止标志
        self.resume()
    
    def pause(self):
        """暂停计算"""
        self._pause_mutex.lock()
        self._paused = True
        self._pause_mutex.unlock()
    
    def resume(self):
        """恢复计算"""
        self._pause_mutex.lock()
        self._paused = False
        self._pause_condition.wakeAll()
        self._pause_mutex.unlock()
    
    def is_paused(self):
        """检查是否暂停状态"""
        self._pause_mutex.lock()
        paused = self._paused
        self._pause_mutex.unlock()
        return paused
    
    def _check_pause_and_stop(self):
        """检查是否需要暂停或停止
        返回True表示请求停止，返回False表示可以继续执行
        """
        # 首先检查是否请求停止
        if self._stop_requested:
            return True
        
        # 然后检查是否需要暂停
        self._pause_mutex.lock()
        try:
            if self._paused:
                # 等待恢复信号
                self._pause_condition.wait(self._pause_mutex)
                # 再次检查是否在等待期间被请求停止
                if self._stop_requested:
                    return True
        finally:
            self._pause_mutex.unlock()
        
        return False
    
    def run(self):
        try:
            # 检查是否在开始时就请求了停止
            if self._check_pause_and_stop():
                return
            
            # 发送进度更新
            self.progress_update.emit(10)
            
            # 使用计算处理器进行实际计算
            calc_handler = CalculationHandler()
            
            # 在调用Rust计算前检查暂停/停止
            if self._check_pause_and_stop():
                return
                
            results = calc_handler.calculate(
                self.numbers, 
                self.target, 
                self.precision, 
                self.find_all, 
                self.algorithm
            )
            
            # 计算完成后再次检查停止请求
            if self._stop_requested:
                return
                
            self.progress_update.emit(100)
            self.result_ready.emit(results)
        except Exception as e:
            self.error_occurred.emit(str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SubsetSumApp()
    window.show()
    sys.exit(app.exec())
