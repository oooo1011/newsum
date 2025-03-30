use std::collections::HashMap;
use rayon::prelude::*;
use std::sync::{Arc, Mutex};

/// 使用分支限界法查找子集和（直接实现，不依赖Python）
/// 
/// 适用于大规模数据集(n>40)
/// 平均时间复杂度优于O(2^n)
/// 
/// # 参数
/// * `numbers` - 整数数组
/// * `target` - 目标和值
/// * `precision` - 精度（绝对值）
/// * `find_all` - 是否查找所有解
pub fn find_subset_sum_branch_bound_raw(
    numbers: &[i64],
    target: i64,
    precision: i64,
    find_all: bool,
) -> Vec<Vec<usize>> {
    let results = Arc::new(Mutex::new(Vec::new()));
    let results_for_closure = results.clone();
    
    // 排序并创建索引映射
    let mut sorted_numbers: Vec<(i64, usize)> = numbers.iter()
        .enumerate()
        .map(|(i, &val)| (val, i))
        .collect();
    
    // 按绝对值降序排序，优先选择较大的数字
    sorted_numbers.sort_by(|a, b| b.0.abs().cmp(&a.0.abs()));
    
    let sorted_values: Vec<i64> = sorted_numbers.iter().map(|&(val, _)| val).collect();
    let indices_map: Vec<usize> = sorted_numbers.iter().map(|&(_, idx)| idx).collect();
    
    // 并行执行分支限界搜索
    parallel_branch_and_bound(&sorted_values, &indices_map, target, precision, results_for_closure, find_all);
    
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
/// 使用分支限界法查找子集和
/// 
/// 适用于大规模数据集(n>40)
/// 平均时间复杂度优于O(2^n)
/// 
/// # 参数
/// * `numbers` - 整数数组
/// * `target` - 目标和值
/// * `precision` - 精度（绝对值）
/// * `find_all` - 是否查找所有解
pub fn find_subset_sum_branch_bound(
    py: Python,
    numbers: &[i64],
    target: i64,
    precision: i64,
    find_all: bool,
) -> Vec<Vec<usize>> {
    // 这里是原始实现，现在由于不再使用PyO3，所以注释掉
    find_subset_sum_branch_bound_raw(numbers, target, precision, find_all)
}
*/

/// 并行分支定界搜索
fn parallel_branch_and_bound(
    numbers: &[i64],
    indices_map: &[usize],
    target: i64,
    precision: i64,
    results: Arc<Mutex<Vec<Vec<usize>>>>,
    find_all: bool,
) {
    let n = numbers.len();
    let num_threads = num_cpus::get();
    
    // 确定并行搜索的起始层级
    let parallel_depth = (n as f64 / 4.0).ceil() as usize;
    let parallel_depth = std::cmp::min(parallel_depth, 10); // 最多10层，避免创建过多任务
    
    // 创建任务队列
    let mut tasks = Vec::new();
    
    // 递归生成初始任务
    fn generate_tasks(
        depth: usize,
        max_depth: usize,
        current_sum: i64,
        path: Vec<usize>,
        numbers: &[i64],
        indices_map: &[usize],
        tasks: &mut Vec<(i64, Vec<usize>)>,
    ) {
        if depth == max_depth {
            tasks.push((current_sum, path));
            return;
        }
        
        // 不选当前元素
        let mut new_path = path.clone();
        generate_tasks(depth + 1, max_depth, current_sum, new_path, numbers, indices_map, tasks);
        
        // 选择当前元素
        new_path = path;
        new_path.push(indices_map[depth]);
        generate_tasks(depth + 1, max_depth, current_sum + numbers[depth], new_path, numbers, indices_map, tasks);
    }
    
    // 生成初始任务
    generate_tasks(0, parallel_depth, 0, Vec::new(), numbers, indices_map, &mut tasks);
    
    // 并行执行任务
    tasks.into_par_iter().for_each(|(sum, path)| {
        // 对每个任务执行串行分支定界
        let mut local_results = Vec::new();
        serial_branch_and_bound(
            parallel_depth,
            n,
            sum,
            path,
            numbers,
            indices_map,
            target,
            precision,
            &mut local_results,
            find_all,
        );
        
        // 合并结果
        if !local_results.is_empty() {
            let mut results_guard = results.lock().unwrap();
            results_guard.extend(local_results);
            
            // 如果只需要一个解且已找到，可以提前退出
            // 但由于并行执行，可能会找到多个解
        }
    });
}

/// 串行分支定界搜索
fn serial_branch_and_bound(
    start_depth: usize,
    n: usize,
    current_sum: i64,
    current_path: Vec<usize>,
    numbers: &[i64],
    indices_map: &[usize],
    target: i64,
    precision: i64,
    results: &mut Vec<Vec<usize>>,
    find_all: bool,
) {
    // 检查当前和是否满足要求
    // 当精度为0时，要求完全匹配
    if precision == 0 {
        if current_sum == target {
            results.push(current_path.clone());
            if !find_all {
                return;
            }
        }
    } else if (current_sum - target).abs() <= precision {
        results.push(current_path.clone());
        if !find_all {
            return;
        }
    }
    
    // 计算剩余数字的上下界
    let remaining_sum: i64 = numbers[start_depth..].iter().filter(|&&x| x > 0).sum();
    let remaining_negative: i64 = numbers[start_depth..].iter().filter(|&&x| x < 0).sum();
    
    // 剪枝：如果当前和加上所有剩余正数仍小于目标值减精度，或者加上所有剩余负数仍大于目标值加精度，则剪枝
    // 当精度为0时，使用精确匹配进行剪枝
    if precision == 0 {
        if current_sum + remaining_sum < target || current_sum + remaining_negative > target {
            return;
        }
    } else if current_sum + remaining_sum < target - precision || 
               current_sum + remaining_negative > target + precision {
        return;
    }
    
    // 递归搜索
    for depth in start_depth..n {
        // 不选当前元素
        serial_branch_and_bound(
            depth + 1,
            n,
            current_sum,
            current_path.clone(),
            numbers,
            indices_map,
            target,
            precision,
            results,
            find_all,
        );
        
        if !find_all && !results.is_empty() {
            return;
        }
        
        // 选择当前元素
        let mut new_path = current_path.clone();
        new_path.push(indices_map[depth]);
        
        serial_branch_and_bound(
            depth + 1,
            n,
            current_sum + numbers[depth],
            new_path,
            numbers,
            indices_map,
            target,
            precision,
            results,
            find_all,
        );
        
        if !find_all && !results.is_empty() {
            return;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_find_subset_sum_branch_bound_raw() {
        let numbers = vec![1, 2, 3, 4, 5, 6, 7, 8, 9];
        let target = 10;
        let precision = 0;
        let find_all = false;
        
        let results = find_subset_sum_branch_bound_raw(&numbers, target, precision, find_all);
        
        assert_eq!(results.len(), 1);
        assert_eq!(results[0], vec![0, 1]);
    }
}
