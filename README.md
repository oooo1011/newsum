# 数字组合求解工具

## 功能概述
- 从TXT/Excel导入数字清单(支持.xls和.xlsx)
- 查找所有组合等于目标值的数字组合
- 实时显示CPU/内存使用率
- 导出结果到Excel并标记选中项

## 技术架构
- 开发语言: C# (.NET 6)
- 界面框架: WPF + ModernWPF
- Excel处理: NPOI 2.6.2
- 并行计算: Task Parallel Library
- 系统监控: PerformanceCounter

## 开发计划
### 第一阶段：基础框架搭建 (已完成)
- [x] 创建解决方案和项目结构
- [x] 配置ModernWPF UI框架
- [x] 设计主界面布局

### 第二阶段：核心功能开发
- [ ] 实现文件导入功能(TXT/Excel)
- [ ] 开发组合算法核心逻辑
- [ ] 添加系统资源监控功能

### 第三阶段：测试与优化
- [ ] 性能测试与优化
- [ ] 用户界面测试
- [ ] 文档完善

## 界面功能
1. 文件导入区
2. 参数设置区
3. 结果展示区
4. 系统监控仪表盘

## 使用说明
1. 点击"导入"按钮选择文件
2. 设置目标值和计算精度
3. 点击"开始计算"按钮
4. 查看结果表格
5. 导出Excel结果

## 构建步骤
```bash
# 还原NuGet包
dotnet restore

# 发布独立应用
dotnet publish -c Release -r win-x64 --self-contained
