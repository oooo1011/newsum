#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
计算处理模块
负责调用Rust核心算法进行子集和计算
"""

import time
import logging
import sys
import os
import ctypes
from typing import List, Tuple, Optional
from cffi import FFI

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CalculationHandler:
    """计算处理类，负责调用Rust核心算法"""
    
    def __init__(self):
        """初始化计算处理器"""
        self.rust_module_loaded = False
        try:
            # 获取Rust库文件的完整路径
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            rust_lib_path = os.path.join(root_dir, 'rust_solver', 'target', 'release')
            
            # 检查Rust库文件是否存在
            if sys.platform == 'win32':
                dll_name = "rust_solver.dll"
            elif sys.platform == 'darwin':
                dll_name = "librust_solver.dylib"
            else:
                dll_name = "librust_solver.so"
                
            dll_path = os.path.join(rust_lib_path, dll_name)
            
            if os.path.exists(dll_path):
                logger.info("找到Rust库文件: %s", dll_path)
            else:
                logger.error("Rust库文件不存在: %s", dll_path)
                raise ImportError(f"Rust库文件不存在: {dll_path}")
            
            # 使用CFFI加载Rust库
            try:
                logger.info("尝试使用CFFI加载Rust库...")
                self.ffi = FFI()
                
                # 定义C ABI接口
                self.ffi.cdef("""
                    int rust_find_subset_sum(
                        const double* numbers_ptr,
                        unsigned int numbers_len,
                        double target,
                        double precision,
                        int find_all,
                        const unsigned char* algorithm_ptr,
                        unsigned int algorithm_len,
                        unsigned int** result_ptr,
                        unsigned int* result_rows,
                        unsigned int** result_cols
                    );
                    
                    int rust_free_result(
                        unsigned int* data_ptr,
                        unsigned int* cols_ptr
                    );
                    
                    unsigned int rust_get_num_cpus();
                    
                    int rust_set_thread_pool_size(unsigned int size);
                """)
                
                # 加载动态库
                self.rust_lib = self.ffi.dlopen(dll_path)
                logger.info("使用CFFI成功加载Rust库")
                
                # 标记模块已加载
                self.rust_module_loaded = True
                
            except Exception as e:
                logger.error("使用CFFI加载失败: %s", str(e))
        except Exception as e:
            logger.error("初始化Rust模块时出错: %s", str(e))
            self.rust_module_loaded = False
        
        logger.info("Rust模块加载状态: %s", self.rust_module_loaded)
    
    def calculate(self, numbers: List[float], target: float, precision: float, 
                 find_all: bool, algorithm: str = "auto") -> List[List[int]]:
        """
        计算满足子集和条件的所有可能组合
        
        参数:
            numbers: 数字列表
            target: 目标和
            precision: 精度（允许的误差范围）
            find_all: 是否查找所有解
            algorithm: 使用的算法，可选值：auto, bit_enum, meet_middle, dp, branch_bound
            
        返回:
            满足条件的索引列表的列表
        """
        start_time = time.time()
        logger.info("开始计算，数据大小: %d, 目标和: %.2f, 精度: %.2f, 查找所有解: %s, 算法: %s",
                   len(numbers), target, precision, find_all, algorithm)
        
        results = []
        try:
            if self.rust_module_loaded:
                # 调用Rust模块进行计算
                logger.info("使用Rust模块计算")
                results = self._rust_calculate(numbers, target, precision, find_all, algorithm)
            else:
                # 如果Rust模块未加载，使用Python实现
                logger.info("使用Python实现计算")
                results = self._python_fallback(numbers, target, precision, find_all, algorithm)
        except Exception as e:
            logger.error("计算过程中发生错误: %s", str(e))
            # 出错时使用Python实现作为后备
            logger.info("出错后使用Python实现计算")
            results = self._python_fallback(numbers, target, precision, find_all, algorithm)
        
        end_time = time.time()
        logger.info("计算完成，用时: %.2f秒，找到解的数量: %d", end_time - start_time, len(results))
        return results
    
    def _rust_calculate(self, numbers: List[float], target: float, precision: float, 
                       find_all: bool, algorithm: str) -> List[List[int]]:
        """使用Rust实现的子集和算法"""
        # 转换Python数据类型为C数据类型
        numbers_array = self.ffi.new("double[]", numbers)
        numbers_len = len(numbers)
        
        # 转换算法字符串
        algorithm_bytes = algorithm.encode('utf-8')
        algorithm_ptr = self.ffi.new("unsigned char[]", algorithm_bytes)
        algorithm_len = len(algorithm_bytes)
        
        # 创建指针，用于存储结果
        result_ptr_ptr = self.ffi.new("unsigned int**")
        result_rows_ptr = self.ffi.new("unsigned int*")
        result_cols_ptr_ptr = self.ffi.new("unsigned int**")
        
        # 调用Rust函数
        find_all_int = 1 if find_all else 0
        ret = self.rust_lib.rust_find_subset_sum(
            numbers_array, numbers_len,
            target, precision, find_all_int,
            algorithm_ptr, algorithm_len,
            result_ptr_ptr, result_rows_ptr, result_cols_ptr_ptr
        )
        
        if ret != 0:
            logger.error("Rust函数返回错误码: %d", ret)
            return []
        
        # 解析结果
        result_rows = result_rows_ptr[0]
        result_ptr = result_ptr_ptr[0]
        result_cols_ptr = result_cols_ptr_ptr[0]
        
        # 将C数组转换为Python列表
        results = []
        idx = 0
        for i in range(result_rows):
            cols = result_cols_ptr[i]
            row = []
            for j in range(cols):
                row.append(result_ptr[idx])
                idx += 1
            results.append(row)
        
        # 释放C分配的内存
        self.rust_lib.rust_free_result(result_ptr, result_cols_ptr)
        
        return results
    
    def _python_fallback(self, numbers, target, precision, find_all, algorithm):
        """Python实现的子集和算法（仅用于测试，性能较差）"""
        logger.warning("使用Python回退实现，性能将大幅降低")
        
        # 使用原始浮点数进行计算，不再转换为整数
        # 根据算法选择
        if algorithm == "bit_enum" or (algorithm == "auto" and len(numbers) <= 25):
            results = self._bit_enum_subset_sum(numbers, target, precision, find_all)
        elif algorithm == "meet_middle" or (algorithm == "auto" and len(numbers) <= 40):
            results = self._meet_middle_subset_sum(numbers, target, precision, find_all)
        elif algorithm == "dp":
            results = self._dp_subset_sum(numbers, target, precision, find_all)
        else:  # branch_bound或者auto并且数据规模大
            results = self._branch_bound_subset_sum(numbers, target, precision, find_all)
        
        return results
    
    def _bit_enum_subset_sum(self, numbers, target, precision, find_all):
        """位运算枚举算法（Python实现）"""
        logger.info("使用位运算枚举算法")
        
        # 将浮点数转换为整数（乘以100）以提高精度
        scale = 100.0
        int_numbers = [int(num * scale) for num in numbers]
        int_target = int(target * scale)
        int_precision = int(precision * scale)
        
        n = len(numbers)
        results = []
        
        # 对于较大的n，限制枚举范围
        max_enum = min(2**n, 2**30)
        
        for mask in range(max_enum):
            subset_sum = 0
            indices = []
            
            for i in range(n):
                if (mask & (1 << i)) != 0:
                    subset_sum += int_numbers[i]
                    indices.append(i)
            
            if abs(subset_sum - int_target) <= int_precision:
                results.append(indices)
                if not find_all:
                    break
        
        return results
    
    def _meet_middle_subset_sum(self, numbers, target, precision, find_all):
        """Meet-in-the-Middle算法（Python实现）"""
        logger.info("使用Meet-in-the-Middle算法")
        
        # 将浮点数转换为整数（乘以100）以提高精度
        scale = 100.0
        int_numbers = [int(num * scale) for num in numbers]
        int_target = int(target * scale)
        int_precision = int(precision * scale)
        
        n = len(numbers)
        mid = n // 2
        results = []
        
        # 计算前半部分所有可能的子集和
        first_half = []
        for mask in range(1 << mid):
            subset_sum = 0
            indices = []
            
            for i in range(mid):
                if (mask & (1 << i)) != 0:
                    subset_sum += int_numbers[i]
                    indices.append(i)
            
            first_half.append((subset_sum, indices))
        
        # 排序以便二分查找
        first_half.sort()
        
        # 计算后半部分并查找匹配
        for mask in range(1 << (n - mid)):
            subset_sum = 0
            indices = []
            
            for i in range(n - mid):
                if (mask & (1 << i)) != 0:
                    subset_sum += int_numbers[mid + i]
                    indices.append(mid + i)
            
            # 计算需要在前半部分查找的目标值
            target_sum = int_target - subset_sum
            lower_bound = target_sum - int_precision
            upper_bound = target_sum + int_precision
            
            # 二分查找满足条件的前半部分
            left = 0
            right = len(first_half)
            
            while left < right:
                m = (left + right) // 2
                if first_half[m][0] < lower_bound:
                    left = m + 1
                else:
                    right = m
            
            # 检查所有可能的匹配
            start_pos = left
            for i in range(start_pos, len(first_half)):
                if first_half[i][0] > upper_bound:
                    break
                
                combined_indices = first_half[i][1] + indices
                results.append(combined_indices)
                
                if not find_all:
                    return results
        
        return results
    
    def _dp_subset_sum(self, numbers, target, precision, find_all):
        """动态规划算法（Python实现）"""
        logger.info("使用动态规划算法")
        
        # 将浮点数转换为整数（乘以100）以提高精度
        scale = 100.0
        int_numbers = [int(num * scale) for num in numbers]
        int_target = int(target * scale)
        int_precision = int(precision * scale)
        
        n = len(numbers)
        target_range = range(int_target - int_precision, int_target + int_precision + 1)
        
        # 计算正数和负数的和，确定DP表的范围
        positive_sum = sum(x for x in int_numbers if x > 0)
        negative_sum = sum(x for x in int_numbers if x < 0)
        
        # 计算DP表需要的范围
        min_sum = negative_sum
        max_sum = positive_sum
        dp_size = max_sum - min_sum + 1
        offset = abs(min_sum)
        
        # 创建DP表和路径跟踪
        dp = [False] * dp_size
        paths = [[] for _ in range(dp_size)]
        
        # 初始状态：空集和为0
        dp[0 + offset] = True
        paths[0 + offset].append([])
        
        # 填充DP表
        for i in range(n):
            for j in range(max_sum, min_sum - 1, -1):
                prev_idx = j - int_numbers[i]
                
                # 检查前一个状态是否可达且在范围内
                if min_sum <= prev_idx <= max_sum and dp[prev_idx + offset]:
                    dp[j + offset] = True
                    
                    # 只在需要所有解或当前和在目标范围内时构建路径
                    if find_all or j in target_range:
                        for prev_path in paths[prev_idx + offset]:
                            new_path = prev_path.copy()
                            new_path.append(i)
                            paths[j + offset].append(new_path)
        
        # 收集结果
        results = []
        for t in target_range:
            if min_sum <= t <= max_sum:
                idx = t + offset
                if dp[idx]:
                    results.extend(paths[idx])
                    if not find_all and results:
                        break
        
        return results
    
    def _branch_bound_subset_sum(self, numbers, target, precision, find_all):
        """分支定界算法（Python实现）"""
        logger.info("使用分支定界算法")
        
        # 将浮点数转换为整数（乘以100）以提高精度
        scale = 100.0
        int_numbers = [int(num * scale) for num in numbers]
        int_target = int(target * scale)
        int_precision = int(precision * scale)
        
        n = len(numbers)
        results = []
        
        # 按绝对值降序排序，优先选择较大的数字
        items = [(abs(int_numbers[i]), i) for i in range(n)]
        items.sort(reverse=True)
        
        # 创建索引映射
        sorted_indices = [item[1] for item in items]
        sorted_numbers = [int_numbers[i] for i in sorted_indices]
        
        def backtrack(index, current_sum, path):
            # 检查当前和是否满足要求
            if abs(current_sum - int_target) <= int_precision:
                # 将排序后的索引映射回原始索引
                results.append([sorted_indices[i] for i in path])
                if not find_all:
                    return True
            
            # 剪枝：如果已找到解且不需要所有解，则提前返回
            if not find_all and results:
                return True
            
            # 剪枝：如果已经处理完所有元素，则返回
            if index == n:
                return False
            
            # 不选当前元素
            if backtrack(index + 1, current_sum, path):
                return True
            
            # 选择当前元素
            path.append(index)
            if backtrack(index + 1, current_sum + sorted_numbers[index], path):
                return True
            path.pop()
            
            return False
        
        backtrack(0, 0, [])
        return results
