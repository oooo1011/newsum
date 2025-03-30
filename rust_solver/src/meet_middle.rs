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
    
    // 处理空数组的特殊情况
    if numbers.is_empty() {
        return Vec::new();
    }
    
    // 处理单个元素的特殊情况
    if numbers.len() == 1 {
        // 当精度为0时，只有完全匹配才返回
        let is_match = if precision == 0 {
            numbers[0] == target
        } else {
            (numbers[0] - target).abs() <= precision
        };
        
        if is_match {
            return vec![vec![0]];
        } else {
            return Vec::new();
        }
    }
    
    // 将数组分为两半
    let mid = numbers.len() / 2;
    let first_half = &numbers[..mid];
    let second_half = &numbers[mid..];
    
    // 计算两半的所有可能的子集和
    let mut first_half_sums = Vec::new();
    let mut second_half_sums = Vec::new();
    
    // 计算第一半部分的所有子集和
    for i in 0..(1 << first_half.len()) {
        let mut sum = 0;
        let mut indices = Vec::new();
        for j in 0..first_half.len() {
            if (i & (1 << j)) != 0 {
                sum += first_half[j];
                indices.push(j);
            }
        }
        first_half_sums.push((sum, indices));
    }
    
    // 计算第二半部分的所有子集和
    for i in 0..(1 << second_half.len()) {
        let mut sum = 0;
        let mut indices = Vec::new();
        for j in 0..second_half.len() {
            if (i & (1 << j)) != 0 {
                sum += second_half[j];
                indices.push(j + mid);
            }
        }
        second_half_sums.push((sum, indices));
    }
    
    // 对第二半部分的和进行排序，便于二分查找
    second_half_sums.sort_by_key(|&(sum, _)| sum);
    
    // 处理第一半部分的和，并在第二半部分中查找互补的和
    first_half_sums.into_par_iter().for_each(|(sum, indices)| {
        if *found_for_closure.lock().unwrap() && !find_all {
            return;
        }
        
        // 计算需要在前半部分查找的目标值
        let target_sum = target - sum;
        
        // 定义查找条件
        if precision == 0 {
            // 精度为0时，使用精确匹配
            let pos = binary_search_exact(&second_half_sums, target_sum);
            if pos.is_some() {
                let mut complete_solution = indices.clone();
                complete_solution.extend(second_half_sums[pos.unwrap()].1.clone());
                
                let mut results_guard = results_for_closure.lock().unwrap();
                results_guard.push(complete_solution);
                
                if !find_all {
                    let mut found_guard = found_for_closure.lock().unwrap();
                    *found_guard = true;
                }
            }
        } else {
            // 使用精度范围查找
            let lower_bound = target_sum - precision;
            let upper_bound = target_sum + precision;
            
            // 二分查找满足条件的前半部分
            let start_pos = binary_search_lower_bound(&second_half_sums, lower_bound);
            if start_pos < second_half_sums.len() {
                for i in start_pos..second_half_sums.len() {
                    if second_half_sums[i].0 > upper_bound {
                        break;
                    }
                    
                    // 找到一个解
                    let mut complete_solution = indices.clone();
                    complete_solution.extend(second_half_sums[i].1.clone());
                    
                    let mut results_guard = results_for_closure.lock().unwrap();
                    results_guard.push(complete_solution);
                    
                    // 如果只需要一个解，设置标志并返回
                    if !find_all {
                        let mut found_guard = found_for_closure.lock().unwrap();
                        *found_guard = true;
                        break;
                    }
                }
            }
        }
    });
    
    // 返回结果
    let final_results = {
        let guard = results.lock().unwrap();
        guard.clone()
    };
    
    final_results
}

/// 二分查找一个精确值
fn binary_search_exact(arr: &[(i64, Vec<usize>)], target: i64) -> Option<usize> {
    let mut low = 0;
    let mut high = arr.len();
    
    while low < high {
        let mid = (low + high) / 2;
        match arr[mid].0.cmp(&target) {
            std::cmp::Ordering::Equal => return Some(mid),
            std::cmp::Ordering::Less => low = mid + 1,
            std::cmp::Ordering::Greater => high = mid,
        }
    }
    
    None
}

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
