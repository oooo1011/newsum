use rayon::prelude::*;
use std::cmp::Ordering;
use std::sync::{Arc, Mutex};

/// 使用Meet-in-the-Middle算法查找子集和（直接实现，不依赖Python）
/// 
/// 适用于中等规模的数据集(25<n≤40)
/// 时间复杂度: O(2^(n/2) * log(2^(n/2)))
/// 
/// # 参数
/// * `numbers` - 整数数组
/// * `target` - 目标和值
/// * `precision` - 精度（绝对值）
/// * `find_all` - 是否查找所有解
pub fn find_subset_sum_meet_middle_raw(
    numbers: &[i64],
    target: i64,
    precision: i64,
    find_all: bool,
) -> Vec<Vec<usize>> {
    let results = Arc::new(Mutex::new(Vec::new()));
    let results_for_closure = results.clone();
    let found = Arc::new(Mutex::new(false));
    let found_for_closure = found.clone();
    
    let n = numbers.len();
    let mid = n / 2;
    
    // 计算前半部分所有可能的子集和
    let mut first_half = Vec::with_capacity(1 << mid);
    for mask in 0..(1 << mid) {
        let mut sum = 0;
        let mut indices = Vec::new();
        for i in 0..mid {
            if (mask & (1 << i)) != 0 {
                sum += numbers[i];
                indices.push(i);
            }
        }
        first_half.push((sum, indices));
    }
    
    // 排序以便二分查找
    first_half.sort_by(|a, b| a.0.cmp(&b.0));
    
    // 并行计算后半部分
    let second_half_len = n - mid;
    let max_second_half = 1 << second_half_len;
    
    // 将后半部分分成多个块并行处理
    let num_cpus = num_cpus::get() as u64;
    let block_size = (max_second_half as u64 / num_cpus) + 1;
    
    (0..num_cpus).into_par_iter().for_each(|cpu_id| {
        let start = cpu_id * block_size;
        let end = std::cmp::min(start + block_size, max_second_half as u64);
        
        for mask in start..end {
            // 如果只需要找到一个解且已经找到，则提前退出
            if !find_all && *found_for_closure.lock().unwrap() {
                break;
            }
            
            let mut sum = 0;
            let mut indices = Vec::new();
            for i in 0..second_half_len {
                if (mask & (1 << i)) != 0 {
                    sum += numbers[mid + i];
                    indices.push(mid + i);
                }
            }
            
            // 计算需要在前半部分查找的目标值
            let target_sum = target - sum;
            let lower_bound = target_sum - precision;
            let upper_bound = target_sum + precision;
            
            // 二分查找满足条件的前半部分
            let start_pos = binary_search_lower_bound(&first_half, lower_bound);
            
            for i in start_pos..first_half.len() {
                let (sum1, indices1) = &first_half[i];
                
                if *sum1 > upper_bound {
                    break;
                }
                
                // 合并两个子集的索引
                let mut combined_indices = indices1.clone();
                combined_indices.extend_from_slice(&indices);
                
                // 添加到结果中
                let mut results_guard = results_for_closure.lock().unwrap();
                results_guard.push(combined_indices);
                
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
    
    final_results
}

/*
/// 使用Meet-in-the-Middle算法查找子集和
/// 
/// 适用于中等规模的数据集(25<n≤40)
/// 时间复杂度: O(2^(n/2) * log(2^(n/2)))
/// 
/// # 参数
/// * `numbers` - 整数数组
/// * `target` - 目标和值
/// * `precision` - 精度（绝对值）
/// * `find_all` - 是否查找所有解
pub fn find_subset_sum_meet_middle(
    py: Python,
    numbers: &[i64],
    target: i64,
    precision: i64,
    find_all: bool,
) -> Vec<Vec<usize>> {
    let results = Arc::new(Mutex::new(Vec::new()));
    let results_for_closure = results.clone();
    let found = Arc::new(Mutex::new(false));
    let found_for_closure = found.clone();
    
    py.allow_threads(move || {
        let n = numbers.len();
        let mid = n / 2;
        
        // 计算前半部分所有可能的子集和
        let mut first_half = Vec::with_capacity(1 << mid);
        for mask in 0..(1 << mid) {
            let mut sum = 0;
            let mut indices = Vec::new();
            for i in 0..mid {
                if (mask & (1 << i)) != 0 {
                    sum += numbers[i];
                    indices.push(i);
                }
            }
            first_half.push((sum, indices));
        }
        
        // 排序以便二分查找
        first_half.sort_by(|a, b| a.0.cmp(&b.0));
        
        // 并行计算后半部分
        let second_half_len = n - mid;
        let max_second_half = 1 << second_half_len;
        
        // 将后半部分分成多个块并行处理
        let num_cpus = num_cpus::get() as u64;
        let block_size = (max_second_half as u64 / num_cpus) + 1;
        
        (0..num_cpus).into_par_iter().for_each(|cpu_id| {
            let start = cpu_id * block_size;
            let end = std::cmp::min(start + block_size, max_second_half as u64);
            
            for mask in start..end {
                // 如果只需要找到一个解且已经找到，则提前退出
                if !find_all && *found_for_closure.lock().unwrap() {
                    break;
                }
                
                let mut sum = 0;
                let mut indices = Vec::new();
                for i in 0..second_half_len {
                    if (mask & (1 << i)) != 0 {
                        sum += numbers[mid + i];
                        indices.push(mid + i);
                    }
                }
                
                // 计算需要在前半部分查找的目标值
                let target_sum = target - sum;
                let lower_bound = target_sum - precision;
                let upper_bound = target_sum + precision;
                
                // 二分查找满足条件的前半部分
                let start_pos = binary_search_lower_bound(&first_half, lower_bound);
                
                for i in start_pos..first_half.len() {
                    let (sum1, indices1) = &first_half[i];
                    
                    if *sum1 > upper_bound {
                        break;
                    }
                    
                    // 合并两个子集的索引
                    let mut combined_indices = indices1.clone();
                    combined_indices.extend_from_slice(&indices);
                    
                    // 添加到结果中
                    let mut results_guard = results_for_closure.lock().unwrap();
                    results_guard.push(combined_indices);
                    
                    if !find_all {
                        let mut found_guard = found_for_closure.lock().unwrap();
                        *found_guard = true;
                        break;
                    }
                }
            }
        });
    });
    
    // 返回结果 - 修改此部分以避免try_unwrap导致的线程恐慌
    let final_results = {
        let guard = results.lock().unwrap();
        guard.clone()  // 直接克隆锁内的数据，而不是尝试unwrap Arc
    };
    
    final_results
}
*/

/// 二分查找下界
fn binary_search_lower_bound(arr: &[(i64, Vec<usize>)], target: i64) -> usize {
    let mut left = 0;
    let mut right = arr.len();
    
    while left < right {
        let mid = left + (right - left) / 2;
        match arr[mid].0.cmp(&target) {
            Ordering::Less => left = mid + 1,
            _ => right = mid,
        }
    }
    
    left
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_meet_middle_simple() {
        let numbers = vec![1, 2, 3, 4, 5, 6, 7, 8];
        let target = 15;
        let precision = 0;
        
        let results = find_subset_sum_meet_middle_raw(&numbers, target, precision, true);
        
        // 验证结果
        for indices in &results {
            let sum: i64 = indices.iter().map(|&i| numbers[i]).sum();
            assert_eq!(sum, target);
        }
    }
}
