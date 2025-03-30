use rayon::prelude::*;
use std::sync::{Arc, Mutex};

/// 使用位运算枚举算法查找子集和（直接实现，不依赖Python）
/// 
/// 适用于较小规模的数据集(n≤25)
/// 时间复杂度: O(2^n)
/// 
/// # 参数
/// * `numbers` - 整数数组
/// * `target` - 目标和值
/// * `precision` - 精度（绝对值）
/// * `find_all` - 是否查找所有解
pub fn find_subset_sum_bit_enum_raw(
    numbers: &[i64],
    target: i64,
    precision: i64,
    find_all: bool,
) -> Vec<Vec<usize>> {
    let results = Arc::new(Mutex::new(Vec::new()));
    let found = Arc::new(Mutex::new(false));
    let results_for_closure = results.clone();
    let found_for_closure = found.clone();
    
    // 获取CPU核心数，用于并行计算
    let n = numbers.len();
    let max_combinations = if n >= 30 { 1u64 << 30 } else { 1u64 << n };
    
    // 将任务分割成多个块，以便并行处理
    let num_cpus = num_cpus::get() as u64;
    let block_size = max_combinations / num_cpus + 1;
    
    // 并行处理每个块
    (0..num_cpus).into_par_iter().for_each(|cpu_id| {
        let start = cpu_id * block_size;
        let end = std::cmp::min(start + block_size, max_combinations);
        
        // 处理当前块中的所有组合
        for mask in start..end {
            // 如果只需要找到一个解且已经找到，则提前退出
            if !find_all && *found_for_closure.lock().unwrap() {
                break;
            }
            
            let mut subset_sum = 0;
            let mut indices = Vec::new();
            
            // 计算当前组合的和
            for i in 0..std::cmp::min(n, 64) {
                if (mask & (1 << i)) != 0 {
                    subset_sum += numbers[i];
                    indices.push(i);
                }
            }
            
            // 检查是否满足目标和（考虑精度）
            let is_match = if precision == 0 {
                subset_sum == target
            } else {
                (subset_sum - target).abs() <= precision
            };

            if is_match {
                let mut results_guard = results_for_closure.lock().unwrap();
                results_guard.push(indices);
                
                if !find_all {
                    let mut found_guard = found_for_closure.lock().unwrap();
                    *found_guard = true;
                    break;
                }
            }
        }
    });
    
    // 返回结果 - 修改此部分以避免try_unwrap导致的线程恐慌
    let final_results = {
        let guard = results.lock().unwrap();
        guard.clone()  // 直接克隆锁内的数据，而不是尝试unwrap Arc
    };
    
    // 如果只需要一个解且找到了多个，只返回第一个
    if !find_all && final_results.len() > 1 {
        return vec![final_results[0].clone()];
    }
    
    final_results
}

/*
/// 使用位运算枚举算法查找子集和
/// 
/// 适用于较小规模的数据集(n≤25)
/// 时间复杂度: O(2^n)
/// 
/// # 参数
/// * `numbers` - 整数数组
/// * `target` - 目标和值
/// * `precision` - 精度（绝对值）
/// * `find_all` - 是否查找所有解
pub fn find_subset_sum_bit_enum(
    py: Python,
    numbers: &[i64],
    target: i64,
    precision: i64,
    find_all: bool,
) -> Vec<Vec<usize>> {
    // 这里是原始实现，现在由于不再使用PyO3，所以注释掉
    find_subset_sum_bit_enum_raw(numbers, target, precision, find_all)
}
*/

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_bit_enum_simple() {
        let numbers = vec![1, 2, 3, 4, 5];
        let target = 9;
        let precision = 0;
        
        let results = find_subset_sum_bit_enum_raw(&numbers, target, precision, true);
        
        // 应该有两个解：[2,3,4] 和 [4,5]
        assert_eq!(results.len(), 2);
        
        // 验证结果
        let sums: Vec<i64> = results.iter()
            .map(|indices| indices.iter().map(|&i| numbers[i]).sum())
            .collect();
        
        for sum in sums {
            assert_eq!(sum, target);
        }
    }
}
