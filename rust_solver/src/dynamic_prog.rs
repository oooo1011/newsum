use std::collections::HashMap;
use std::sync::{Arc, Mutex};

/// 使用动态规划算法查找子集和（直接实现，不依赖Python）
/// 
/// 适用于整数问题，特别是当目标值较小时
/// 时间复杂度: O(n*target)
/// 
/// # 参数
/// * `numbers` - 整数数组
/// * `target` - 目标和值
/// * `precision` - 精度（绝对值）
/// * `find_all` - 是否查找所有解
pub fn find_subset_sum_dp_raw(
    numbers: &[i64],
    target: i64,
    precision: i64,
    find_all: bool,
) -> Vec<Vec<usize>> {
    let n = numbers.len();
    let results = Arc::new(Mutex::new(Vec::new()));
    
    // 创建DP表
    let mut dp = vec![vec![false; (target as usize) + 1 + (precision as usize)]; n + 1];
    dp[0][0] = true;
    
    // 填充DP表
    for i in 1..=n {
        dp[i][0] = true;
        for j in 0..=target as usize + precision as usize {
            // 不选当前元素
            dp[i][j] = dp[i-1][j];
            
            // 选当前元素
            let val = numbers[i-1] as usize;
            if j >= val {
                dp[i][j] |= dp[i-1][j - val];
            }
        }
    }
    
    // 查找符合目标和的解
    let mut temp_path = vec![false; n];
    
    fn back_track(
        i: usize, 
        j: usize, 
        path: &mut Vec<bool>, 
        numbers: &[i64], 
        dp: &Vec<Vec<bool>>, 
        target: i64,
        precision: i64,
        results: &Arc<Mutex<Vec<Vec<usize>>>>,
        find_all: bool
    ) -> bool {
        // 基本情况：到达第一行
        if i == 0 {
            // 检查是否找到解
            let indices: Vec<usize> = path.iter()
                .enumerate()
                .filter(|(_, &included)| included)
                .map(|(idx, _)| idx)
                .collect();
            
            // 计算当前和
            let sum: i64 = indices.iter()
                .map(|&idx| numbers[idx])
                .sum();
            
            // 检查是否满足目标和
            let is_valid = if precision == 0 {
                // 精度为0时要求完全匹配
                sum == target
            } else {
                // 有精度时允许在范围内
                (sum - target).abs() <= precision
            };
            
            if is_valid {
                let mut guard = results.lock().unwrap();
                guard.push(indices);
                return !find_all; // 如果find_all为false，返回true表示找到了解并停止
            }
            return false;
        }
        
        // 不选当前元素的情况
        if dp[i-1][j] {
            path[i-1] = false;
            if back_track(i-1, j, path, numbers, dp, target, precision, results, find_all) {
                return true;
            }
        }
        
        // 选当前元素的情况
        let val = numbers[i-1] as usize;
        if j >= val && dp[i-1][j - val] {
            path[i-1] = true;
            if back_track(i-1, j - val, path, numbers, dp, target, precision, results, find_all) {
                return true;
            }
        }
        
        return false;
    }
    
    // 查找解集
    let target_range: Vec<usize> = if precision == 0 {
        // 精度为0时只查找精确匹配
        vec![target as usize]
    } else {
        // 精度不为0时查找范围内的所有值
        let lower_bound = (target - precision) as usize;
        let upper_bound = (target + precision) as usize;
        (lower_bound..=upper_bound)
            .filter(|&j| j < dp[0].len())
            .collect()
    };
    
    for j in target_range {
        if j < dp[0].len() && dp[n][j] {
            back_track(n, j, &mut temp_path, numbers, &dp, target, precision, &results, find_all);
            
            // 如果不需要找到所有解且已经找到解，则退出
            if !find_all {
                let guard = results.lock().unwrap();
                if !guard.is_empty() {
                    break;
                }
            }
        }
    }
    
    // 返回结果
    let final_results = {
        let guard = results.lock().unwrap();
        guard.clone()
    };
    
    final_results
}

/// 收集指定目标范围内的结果
fn collect_results(
    dp: Vec<bool>,
    paths: Vec<Vec<Vec<usize>>>,
    target: i64,
    precision: i64,
    offset: i64,
    min_sum: i64,
    max_sum: i64,
    find_all: bool,
    results: Arc<Mutex<Vec<Vec<usize>>>>
) {
    let target_range = target - precision..=target + precision;
    
    // 收集结果
    let mut local_results = Vec::new();
    for t in target_range {
        if t >= min_sum && t <= max_sum {
            let idx = (t + offset) as usize;
            if idx < dp.len() && dp[idx] {
                local_results.extend(paths[idx].clone());
                if !find_all && !local_results.is_empty() {
                    break;
                }
            }
        }
    }
    
    // 合并结果
    let mut results_guard = results.lock().unwrap();
    results_guard.extend(local_results);
}

/// 使用记忆化搜索优化的动态规划（适用于稀疏DP表的情况）
fn dp_with_memoization(
    numbers: &[i64],
    target: i64,
    precision: i64,
    find_all: bool,
) -> Vec<Vec<usize>> {
    let n = numbers.len();
    let mut memo: HashMap<(usize, i64), Vec<Vec<usize>>> = HashMap::new();
    let target_range = target - precision..=target + precision;
    
    // 递归函数
    fn dp_search(
        numbers: &[i64],
        index: usize,
        remaining: i64,
        memo: &mut HashMap<(usize, i64), Vec<Vec<usize>>>,
        target_range: std::ops::RangeInclusive<i64>,
        find_all: bool,
    ) -> Vec<Vec<usize>> {
        // 基本情况
        if index == numbers.len() {
            if target_range.contains(&remaining) {
                return vec![vec![]];
            }
            return vec![];
        }
        
        // 检查记忆表
        if let Some(result) = memo.get(&(index, remaining)) {
            return result.clone();
        }
        
        // 不选当前元素
        let mut result = dp_search(numbers, index + 1, remaining, memo, target_range.clone(), find_all);
        
        // 选当前元素
        let with_current = dp_search(numbers, index + 1, remaining - numbers[index], memo, target_range.clone(), find_all);
        
        // 将当前索引添加到所有解中
        for mut path in with_current {
            path.push(index);
            result.push(path);
            
            // 如果只需要一个解且已找到，则提前返回
            if !find_all && !result.is_empty() {
                memo.insert((index, remaining), result.clone());
                return result;
            }
        }
        
        // 保存到记忆表
        memo.insert((index, remaining), result.clone());
        result
    }
    
    // 调用递归函数
    dp_search(numbers, 0, target, &mut memo, target_range, find_all)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_dp_simple() {
        let numbers = vec![1, 2, 3, 4, 5];
        let target = 9;
        let precision = 0;
        
        let results = find_subset_sum_dp_raw(&numbers, target, precision, true);
        
        // 验证结果
        for indices in &results {
            let sum: i64 = indices.iter().map(|&i| numbers[i]).sum();
            assert_eq!(sum, target);
        }
    }
}
