#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
子集和问题求解器IO测试
测试文件导入导出功能
"""

import unittest
import sys
import os
import tempfile
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入文件处理模块
from python_app.handlers.file_handler import FileHandler


class TestIO(unittest.TestCase):
    """IO测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.file_handler = FileHandler()
        self.temp_dir = tempfile.TemporaryDirectory()
    
    def tearDown(self):
        """测试后清理"""
        self.temp_dir.cleanup()
    
    def test_load_txt_file(self):
        """测试加载文本文件"""
        # 创建测试文本文件
        test_data = [1.23, 4.56, 7.89, 10.01, 20.02, 30.03, 40.04, 50.05, 60.06, 70.07]
        txt_path = os.path.join(self.temp_dir.name, "test_data.txt")
        
        with open(txt_path, 'w') as f:
            for num in test_data:
                f.write(f"{num}\n")
        
        # 测试加载
        numbers, indices = self.file_handler.load_data(txt_path)
        
        # 验证结果
        self.assertEqual(len(numbers), len(test_data), "加载的数据数量不匹配")
        for i, (expected, actual) in enumerate(zip(test_data, numbers)):
            self.assertAlmostEqual(expected, actual, places=2, msg=f"第{i}个数据不匹配")
        
        # 验证索引
        self.assertEqual(indices, list(range(len(test_data))), "索引不匹配")
    
    def test_load_excel_file(self):
        """测试加载Excel文件"""
        # 创建测试Excel文件
        test_data = [1.23, 4.56, 7.89, 10.01, 20.02, 30.03, 40.04, 50.05, 60.06, 70.07]
        excel_path = os.path.join(self.temp_dir.name, "test_data.xlsx")
        
        df = pd.DataFrame(test_data)
        df.to_excel(excel_path, header=False, index=False)
        
        # 测试加载
        numbers, indices = self.file_handler.load_data(excel_path)
        
        # 验证结果
        self.assertEqual(len(numbers), len(test_data), "加载的数据数量不匹配")
        for i, (expected, actual) in enumerate(zip(test_data, numbers)):
            self.assertAlmostEqual(expected, actual, places=2, msg=f"第{i}个数据不匹配")
        
        # 验证索引
        self.assertEqual(indices, list(range(len(test_data))), "索引不匹配")
    
    def test_export_results(self):
        """测试导出结果"""
        # 准备测试数据
        numbers = [1.23, 4.56, 7.89, 10.01, 20.02, 30.03, 40.04, 50.05, 60.06, 70.07]
        indices = list(range(len(numbers)))
        results = [[0, 2, 5], [1, 3, 7]]  # 两个解
        
        # 导出结果
        export_path = os.path.join(self.temp_dir.name, "test_results.xlsx")
        self.file_handler.export_results(export_path, numbers, indices, results)
        
        # 验证导出文件存在
        self.assertTrue(os.path.exists(export_path), "导出文件不存在")
        
        # 读取导出文件
        df = pd.read_excel(export_path)
        
        # 验证列数
        expected_columns = 4  # 数值列 + 2个解列 + 是否选中列
        self.assertEqual(len(df.columns), expected_columns, "导出文件列数不正确")
        
        # 验证行数
        self.assertEqual(len(df), len(numbers), "导出文件行数不正确")
        
        # 验证选中标记
        for i in range(len(numbers)):
            is_selected = 0
            for result in results:
                if i in result:
                    is_selected = 1
                    break
            
            self.assertEqual(df.iloc[i]['是否选中'], is_selected, f"第{i}行的选中状态不正确")
    
    def test_data_validation(self):
        """测试数据验证功能"""
        # 测试数据量过少
        with self.assertRaises(ValueError):
            self.file_handler._validate_data([1.0, 2.0])
        
        # 测试数据量过多
        too_many = [float(i) for i in range(201)]
        with self.assertRaises(ValueError):
            self.file_handler._validate_data(too_many)
        
        # 测试非数字数据
        with self.assertRaises(ValueError):
            self.file_handler._validate_data([1.0, "not_a_number", 3.0])
        
        # 测试小数位数过多
        with self.assertRaises(ValueError):
            self.file_handler._validate_data([1.0, 2.0, 3.456])


if __name__ == "__main__":
    unittest.main()
