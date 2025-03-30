use std::os::raw::c_double;
use std::os::raw::c_int;
use std::os::raw::c_uint;
use std::slice;

mod bit_enum;
mod meet_middle;
mod dynamic_prog;
mod branch_bound;

/// 查找子集和
/// 
/// 根据数据规模自动选择最合适的算法
/// 
/// C ABI接口，可以被Python通过cffi调用
#[no_mangle]
pub extern "C" fn rust_find_subset_sum(
    numbers_ptr: *const c_double,
    numbers_len: c_uint,
    target: c_double,
    precision: c_double,
    find_all: c_int,
    algorithm_ptr: *const u8,
    algorithm_len: c_uint,
    result_ptr: *mut *mut c_uint,
    result_rows: *mut c_uint,
    result_cols: *mut *mut c_uint,
) -> c_int {
    // 安全检查
    if numbers_ptr.is_null() || algorithm_ptr.is_null() || result_ptr.is_null() || 
        result_rows.is_null() || result_cols.is_null() {
        return -1;
    }
    
    // 将C数据转换为Rust数据
    let numbers = unsafe {
        slice::from_raw_parts(numbers_ptr, numbers_len as usize)
    };
    
    // 转换算法名称
    let algorithm_bytes = unsafe {
        slice::from_raw_parts(algorithm_ptr, algorithm_len as usize)
    };
    
    let algorithm = match std::str::from_utf8(algorithm_bytes) {
        Ok(s) => s,
        Err(_) => return -2,
    };
    
    // 将浮点数转换为整数以提高精度和性能
    let scale = 100.0; // 放大系数
    let int_numbers: Vec<i64> = numbers.iter().map(|&x| (x * scale) as i64).collect();
    let int_target = (target * scale) as i64;
    let int_precision = (precision * scale) as i64;
    
    // 标记是否查找所有解
    let find_all_bool = find_all != 0;
    
    // 根据算法选择合适的实现
    let result = match algorithm {
        "bit_enum" => bit_enum::find_subset_sum_bit_enum_raw(&int_numbers, int_target, int_precision, find_all_bool),
        "meet_middle" => meet_middle::find_subset_sum_meet_middle_raw(&int_numbers, int_target, int_precision, find_all_bool),
        "dp" => dynamic_prog::find_subset_sum_dp_raw(&int_numbers, int_target, int_precision, find_all_bool),
        "branch_bound" => branch_bound::find_subset_sum_branch_bound_raw(&int_numbers, int_target, int_precision, find_all_bool),
        "auto" | _ => {
            // 根据数据规模自动选择算法
            let n = int_numbers.len();
            if n <= 25 {
                bit_enum::find_subset_sum_bit_enum_raw(&int_numbers, int_target, int_precision, find_all_bool)
            } else if n <= 40 {
                meet_middle::find_subset_sum_meet_middle_raw(&int_numbers, int_target, int_precision, find_all_bool)
            } else {
                branch_bound::find_subset_sum_branch_bound_raw(&int_numbers, int_target, int_precision, find_all_bool)
            }
        }
    };
    
    // 将结果转换为C可用的格式
    let (rows, cols_vec, flat_data) = convert_result_to_c_format(&result);
    
    unsafe {
        // 为结果分配内存并复制数据
        let flat_data_ptr = libc::malloc(flat_data.len() * std::mem::size_of::<c_uint>()) as *mut c_uint;
        if flat_data_ptr.is_null() {
            return -3;
        }
        
        std::ptr::copy_nonoverlapping(flat_data.as_ptr(), flat_data_ptr, flat_data.len());
        
        // 为列长度分配内存并复制数据
        let cols_ptr = libc::malloc(cols_vec.len() * std::mem::size_of::<c_uint>()) as *mut c_uint;
        if cols_ptr.is_null() {
            libc::free(flat_data_ptr as *mut libc::c_void);
            return -4;
        }
        
        std::ptr::copy_nonoverlapping(cols_vec.as_ptr(), cols_ptr, cols_vec.len());
        
        // 设置输出参数
        *result_ptr = flat_data_ptr;
        *result_rows = rows;
        *result_cols = cols_ptr;
    }
    
    0  // 成功返回0
}

/// 将结果转换为C可用的格式
/// 
/// 返回(行数, 每行的列数向量, 展平的数据)
fn convert_result_to_c_format(result: &Vec<Vec<usize>>) -> (c_uint, Vec<c_uint>, Vec<c_uint>) {
    let rows = result.len() as c_uint;
    let mut cols_vec = Vec::with_capacity(rows as usize);
    let mut flat_data = Vec::new();
    
    for row in result {
        cols_vec.push(row.len() as c_uint);
        for &item in row {
            flat_data.push(item as c_uint);
        }
    }
    
    (rows, cols_vec, flat_data)
}

/// 释放由rust_find_subset_sum分配的内存
#[no_mangle]
pub extern "C" fn rust_free_result(
    data_ptr: *mut c_uint,
    cols_ptr: *mut c_uint,
) -> c_int {
    if !data_ptr.is_null() {
        unsafe {
            libc::free(data_ptr as *mut libc::c_void);
        }
    }
    
    if !cols_ptr.is_null() {
        unsafe {
            libc::free(cols_ptr as *mut libc::c_void);
        }
    }
    
    0  // 成功返回0
}

/// 获取可用的CPU核心数
#[no_mangle]
pub extern "C" fn rust_get_num_cpus() -> c_uint {
    num_cpus::get() as c_uint
}

/// 设置并行线程池大小
#[no_mangle]
pub extern "C" fn rust_set_thread_pool_size(size: c_uint) -> c_int {
    match rayon::ThreadPoolBuilder::new()
        .num_threads(size as usize)
        .build_global() {
        Ok(_) => 0,   // 成功
        Err(_) => -1, // 失败
    }
}
