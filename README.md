# SubsetSum Solver

一个高性能子集和问题求解器，使用Rust核心算法和Python GUI界面。

## 项目概述

本应用程序用于解决子集和问题：从给定的数字集合中找出特定组合，使其和等于目标值。特点包括：

- 高性能Rust计算核心
- 通过CFFI实现Python与Rust无缝集成
- 直观的Python GUI界面
- 支持txt和Excel文件导入
- 灵活的算法选择
- 精确的整数计算（通过整数化）
- 结果导出为Excel

## 功能需求

### 数据处理
- 导入10-200个数字（最多两位小数）
- 支持txt和Excel格式
- 每个数字最多使用一次
- 可能包含重复数字

### 计算特性
- 设置目标求和值
- 可调整的匹配精度（绝对值）
- 选择计算单个解或所有可能解
- 多种算法选择，针对不同数据规模优化
- 可中断计算过程
- 计算时最大化利用系统资源

### 结果展示
- GUI界面显示计算结果
- 导出结果到Excel
- 在结果中按原始顺序排列数字
- 高亮显示选中的数字

## 技术方案

### 技术栈
- 计算核心：Rust (通过CFFI实现C接口绑定)
- GUI界面：Python + PyQt6
- 数据处理：Pandas, NumPy
- 接口技术：CFFI
- 打包工具：PyInstaller

### 核心算法
1. **位运算枚举** (适用于n≤25)
   - 并行处理所有可能组合
   - 时间复杂度：O(2^n)

2. **Meet-in-the-Middle算法** (适用于25<n≤40)
   - 将问题分解为两半分别处理
   - 时间复杂度：O(2^(n/2) * log(2^(n/2)))

3. **动态规划算法** (适用于整数，目标值较小)
   - 使用整数化处理小数
   - 时间复杂度：O(n*target)

4. **分支定界算法** (适用于n>40，寻找单个解)
   - 使用估计函数剪枝
   - 可提前终止搜索

### 优化策略
- **整数化**：将小数乘以100转换为整数处理，避免浮点数精度问题
- **并行计算**：通过Rayon库充分利用多核CPU
- **内存优化**：减少不必要的数据复制和使用Arc+Mutex安全共享数据
- **结果缓存**：避免重复计算
- **基本剪枝**：
  - 空集检查：输入为空时直接返回
  - 范围检查：目标值超出可能范围时直接返回
  - 符号一致性检查：正负数与目标值符号不匹配时直接返回
  - 特殊情况处理：目标值接近0时的处理
- **排序预处理**：
  - 按算法特性选择最优排序策略
  - 位运算和Meet-in-the-Middle：按绝对值从大到小排序
  - 动态规划：按值从小到大排序
  - 分支定界：按贡献度（绝对值）从大到小排序
  - 保留原始索引映射，确保结果正确性

## 项目结构

```
subset_sum_solver/
├── rust_solver/              # Rust计算核心
│   ├── src/
│   │   ├── lib.rs            # Rust核心算法与C接口导出
│   │   ├── bit_enum.rs       # 位运算枚举算法
│   │   ├── meet_middle.rs    # Meet-in-the-Middle算法
│   │   ├── dynamic_prog.rs   # 动态规划算法
│   │   └── branch_bound.rs   # 分支定界算法
│   └── Cargo.toml            # Rust依赖配置
├── python_app/               # Python GUI应用
│   ├── main.py               # 主程序入口
│   ├── ui/                   # GUI界面定义
│   │   ├── main_window.py    # 主窗口UI定义
│   │   └── resources.py      # UI资源
│   ├── handlers/             # 事件处理
│   │   ├── file_handler.py   # 文件导入导出
│   │   └── calc_handler.py   # 计算操作处理与CFFI集成
│   └── requirements.txt      # Python依赖
├── tests/                    # 测试目录
│   └── test_algorithms.py    # 算法功能测试
└── README.md                 # 项目文档
```

## 算法详细介绍

### 位运算枚举 (Bit Enumeration)
通过利用二进制位运算，枚举所有可能的子集组合。这个算法对于小规模数据集(n≤25)效率很高。在并行环境下，将全部可能组合分成多块，由多个线程同时处理，大幅提高计算速度。

### Meet-in-the-Middle算法
将数据集分成两半，分别计算每一半所有可能子集的和，然后通过高效的查找算法找到互补的子集对。这种方法将时间复杂度从O(2^n)降到O(2^(n/2) * log(2^(n/2)))，适合中等规模数据(25<n≤40)。

### 动态规划算法
使用自底向上的动态规划方法，构建可能的和值表格，最后回溯找出具体组合。这种方法在目标值相对较小且数据为整数时效率很高。同时使用整数化（将浮点数乘以100转为整数）避免精度问题。

### 分支定界算法
使用深度优先搜索，通过估计剩余元素可能贡献的最大和最小值，尽早剪枝无法满足条件的分支。这种方法特别适合寻找单个解决方案，在大数据集上(n>40)效率显著优于枚举法。

## Rust与Python集成

项目使用CFFI（C Foreign Function Interface）将Rust编译的动态库与Python应用程序集成：

1. **Rust端**：
   - 将所有算法实现为纯C接口函数
   - 使用`#[no_mangle]`和`extern "C"`导出函数
   - 实现内存管理和资源释放函数
   - 通过cdylib形式编译为动态库

2. **Python端**：
   - 使用CFFI加载Rust编译的动态库
   - 定义C接口函数签名
   - 封装底层调用，提供友好的Python接口
   - 处理数据类型转换和错误处理

这种集成方式保留了Rust的高性能，同时提供了Python的易用性和灵活性。

## 精度处理

为解决浮点数计算中的精度问题，项目使用了"整数化"策略：

- 所有输入的浮点数都乘以100转换为整数
- 目标值和精度参数也同样转换
- 所有计算基于整数进行，避免浮点数累积误差
- 结果显示时再除以100转回浮点数

测试表明，这种方法可以有效地处理两位小数精度的计算，同时保持结果的准确性。

## 构建与运行

1. 构建Rust库：
```
cd rust_solver
cargo build --release
```

2. 运行Python应用：
```
cd python_app
python main.py
```

3. 运行测试：
```
python -m tests.test_algorithms
```
