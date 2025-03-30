#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
子集和问题求解器算法测试
"""

import unittest
import sys
import os
import random

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入Python实现的算法（用于测试）
from python_app.handlers.calc_handler import CalculationHandler


class TestAlgorithms(unittest.TestCase):
    """算法测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.calc_handler = CalculationHandler()
    
    def test_bit_enum_simple(self):
        """测试位运算枚举算法 - 简单情况"""
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0]
        target = 9.0
        precision = 0.05  # 增加精度容差
        find_all = True
        
        results = self.calc_handler.calculate(
            numbers, target, precision, find_all, algorithm="bit_enum"
        )
        
        # 验证结果数量
        self.assertGreater(len(results), 0, "应该找到至少一个解")
        
        # 验证每个解的和是否在目标范围内
        for indices in results:
            subset_sum = sum(numbers[i] for i in indices)
            self.assertAlmostEqual(subset_sum, target, delta=precision, 
                                  msg=f"解 {indices} 的和 {subset_sum} 不在目标范围内")
    
    def test_meet_middle_simple(self):
        """测试Meet-in-the-Middle算法 - 简单情况"""
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        target = 15.0
        precision = 0.05  # 增加精度容差
        find_all = True
        
        results = self.calc_handler.calculate(
            numbers, target, precision, find_all, algorithm="meet_middle"
        )
        
        # 验证结果数量
        self.assertGreater(len(results), 0, "应该找到至少一个解")
        
        # 验证每个解的和是否在目标范围内
        for indices in results:
            subset_sum = sum(numbers[i] for i in indices)
            self.assertAlmostEqual(subset_sum, target, delta=precision, 
                                  msg=f"解 {indices} 的和 {subset_sum} 不在目标范围内")
    
    def test_dp_simple(self):
        """测试动态规划算法 - 简单情况"""
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0]
        target = 9.0
        precision = 0.05  # 增加精度容差
        find_all = True
        
        results = self.calc_handler.calculate(
            numbers, target, precision, find_all, algorithm="dp"
        )
        
        # 验证结果数量
        self.assertGreater(len(results), 0, "应该找到至少一个解")
        
        # 验证每个解的和是否在目标范围内
        for indices in results:
            subset_sum = sum(numbers[i] for i in indices)
            self.assertAlmostEqual(subset_sum, target, delta=precision, 
                                  msg=f"解 {indices} 的和 {subset_sum} 不在目标范围内")
    
    def test_branch_bound_simple(self):
        """测试分支定界算法 - 简单情况"""
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        target = 15.0
        precision = 0.05  # 增加精度容差
        find_all = False
        
        results = self.calc_handler.calculate(
            numbers, target, precision, find_all, algorithm="branch_bound"
        )
        
        # 验证结果数量
        self.assertEqual(len(results), 1, "应该只找到一个解")
        
        # 验证解的和是否在目标范围内
        subset_sum = sum(numbers[i] for i in results[0])
        self.assertAlmostEqual(subset_sum, target, delta=precision, 
                              msg=f"解 {results[0]} 的和 {subset_sum} 不在目标范围内")
    
    def test_zero_precision_exact_match(self):
        """测试精度为0时的精确匹配"""
        # 使用整数数据，确保有精确的解
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        target = 15.0  # 可以通过5+10或者1+4+10等组合精确得到
        precision = 0  # 精度为0，要求完全匹配
        find_all = True
        
        # 测试所有算法
        for algorithm in ["bit_enum", "meet_middle", "dp", "branch_bound"]:
            with self.subTest(algorithm=algorithm):
                results = self.calc_handler.calculate(
                    numbers, target, precision, find_all, algorithm=algorithm
                )
                
                # 验证结果数量
                self.assertGreater(len(results), 0, f"{algorithm}算法应该找到至少一个解")
                
                # 验证每个解的和是否精确等于目标值（不使用delta）
                for indices in results:
                    subset_sum = sum(numbers[i] for i in indices)
                    self.assertEqual(subset_sum, target, 
                                    msg=f"{algorithm}算法: 解 {indices} 的和 {subset_sum} 不等于目标值 {target}")
        
        # 测试一个不可能有精确解的情况
        numbers = [1.0, 2.0, 3.0, 4.0, 5.0]
        target = 8.5  # 无法用给定的整数精确组合得到
        
        for algorithm in ["bit_enum", "meet_middle", "dp", "branch_bound"]:
            with self.subTest(algorithm=algorithm):
                results = self.calc_handler.calculate(
                    numbers, target, precision, find_all, algorithm=algorithm
                )
                
                # 验证没有找到结果
                self.assertEqual(len(results), 0, 
                                f"{algorithm}算法: 对于无精确解的情况应返回空列表，而不是近似解")
    
    def test_decimal_precision(self):
        """测试小数精度处理"""
        # 使用固定的数据集而不是随机数据
        numbers = [1.23, 2.34, 3.45, 4.56, 5.67, 6.78, 7.89, 8.90, 9.01, 10.12]
        # 选择一个确定的目标值
        target = numbers[0] + numbers[2] + numbers[5]  # 1.23 + 3.45 + 6.78 = 11.46
        precision = 0.05  # 增加精度容差
        find_all = False
        
        results = self.calc_handler.calculate(
            numbers, target, precision, find_all, algorithm="auto"
        )
        
        # 验证结果数量
        self.assertGreater(len(results), 0, "应该找到至少一个解")
        
        # 验证解的和是否在目标范围内
        subset_sum = sum(numbers[i] for i in results[0])
        self.assertAlmostEqual(subset_sum, target, delta=precision, 
                              msg=f"解 {results[0]} 的和 {subset_sum} 不在目标范围内")
    
    def test_auto_algorithm_selection(self):
        """测试自动算法选择"""
        # 使用固定的数据集而不是随机数据
        
        # 小规模数据集 - 精确的数字，确保有解
        small_numbers = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        small_target = 15.0  # 可以通过5+10或者1+4+10等组合得到
        
        # 中等规模数据集
        medium_numbers = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 
                         6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5]
        medium_target = 15.0  # 可以通过多种组合得到
        
        # 大规模数据集
        large_numbers = list(range(1, 31))  # 1到30的整数
        large_target = 15.0  # 可以通过多种组合得到
        
        precision = 0.05
        find_all = False
        
        # 测试各种规模的数据集
        for numbers, target in [(small_numbers, small_target), 
                              (medium_numbers, medium_target), 
                              (large_numbers, large_target)]:
            results = self.calc_handler.calculate(
                numbers, target, precision, find_all, algorithm="auto"
            )
            
            # 验证找到解
            self.assertGreater(len(results), 0, f"使用数据集大小{len(numbers)}应该找到至少一个解")
            
            # 验证解的和是否在目标范围内
            subset_sum = sum(numbers[i] for i in results[0])
            self.assertAlmostEqual(subset_sum, target, delta=precision, 
                                  msg=f"解 {results[0]} 的和 {subset_sum} 不在目标范围内")


if __name__ == "__main__":
    unittest.main()
