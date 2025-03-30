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
    let results = Arc::new(Mutex::new(Vec::new()));
    let results_for_closure = results.clone();
    
    let n = numbers.len();
    let target_range = target - precision..=target + precision;
    
    // 计算正数和负数的和，确定DP表的范围
    let positive_sum: i64 = numbers.iter().filter(|&&x| x > 0).sum();
    let negative_sum: i64 = numbers.iter().filter(|&&x| x < 0).sum();
    
    // 计算DP表需要的范围
    let min_sum = negative_sum;
    let max_sum = positive_sum;
    let offset = min_sum.abs();
    let dp_size = (max_sum + offset + 1) as usize;
    
    // 创建DP表和路径跟踪
    let mut dp = vec![false; dp_size];
    let mut paths: Vec<Vec<Vec<usize>>> = vec![vec![]; dp_size];
    
    // 初始状态：空集和为0
    dp[(0 + offset) as usize] = true;
    paths[(0 + offset) as usize].push(vec![]);
    
    // 填充DP表
    for i in 0..n {
        // 从后向前避免重复计算
        for j in (min_sum..=max_sum).rev() {
            let prev_idx = j - numbers[i];
            
            // 检查前一个状态是否可达且在范围内
            if prev_idx >= min_sum && prev_idx <= max_sum && dp[(prev_idx + offset) as usize] {
                dp[(j + offset) as usize] = true;
                
                // 只在需要所有解或当前和在目标范围内时构建路径
                if find_all || target_range.contains(&j) {
                    // 创建新的路径集合，避免可变和不可变引用冲突
                    let mut new_paths = Vec::new();
                    for prev_path in &paths[(prev_idx + offset) as usize] {
                        let mut new_path = prev_path.clone();
                        new_path.push(i);
                        new_paths.push(new_path);
                    }
                    
                    // 将新路径添加到当前和的路径集合中
                    paths[(j + offset) as usize].extend(new_paths);
                }
            }
        }
    }
    
    // 收集目标范围内的所有结果
    collect_results(dp, paths, target, precision, offset, min_sum, max_sum, find_all, results_for_closure);
    
    // 返回结果 - 修改此部分以避免try_unwrap导致的线程恐慌
    let final_results = {
        let guard = results.lock().unwrap();
        guard.clone()  // 直接克隆锁内的数据，而不是尝试unwrap Arc
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
