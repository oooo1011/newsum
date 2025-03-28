using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Threading.Tasks;
using System.Diagnostics;
using System.IO;

namespace NumberCombinationFinder
{
    public partial class MainWindow : Window
    {
        private List<decimal> numbers = new List<decimal>();

        public MainWindow()
        {
            InitializeComponent();
        }

        private void ImportTxt_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var dialog = new Microsoft.Win32.OpenFileDialog
                {
                    Filter = "文本文件|*.txt|所有文件|*.*"
                };
                
                if (dialog.ShowDialog() == true)
                {
                    FilePathText.Text = dialog.FileName;
                    numbers = File.ReadAllLines(dialog.FileName)
                        .Where(line => !string.IsNullOrWhiteSpace(line))
                        .Select(line => 
                        {
                            if (decimal.TryParse(line.Trim(), out var num))
                                return num;
                            throw new FormatException($"无效数字格式: {line}");
                        })
                        .ToList();
                    
                    MessageBox.Show($"成功导入 {numbers.Count} 个数字");
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"导入失败: {ex.Message}");
            }
        }

        private async void Calculate_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                if (!numbers.Any())
                {
                    MessageBox.Show("请先导入数字文件");
                    return;
                }

                decimal target = decimal.Parse(TargetValueTextBox.Text);
                int precision = int.Parse(((ComboBoxItem)PrecisionComboBox.SelectedItem).Content.ToString());
                bool findAll = FindAllCheckBox.IsChecked == true;
                
                // 优化计算性能
                Process.GetCurrentProcess().PriorityClass = ProcessPriorityClass.High;
                var sw = Stopwatch.StartNew();
                var progress = new Progress<int>(count => 
                    CpuUsageText.Text = $"已找到 {count} 个组合");

                ResultsDataGrid.ItemsSource = null;
                CpuUsageText.Text = "计算中...";

                var result = await Task.Run(() => 
                    FindCombinationsParallel(numbers, target, precision, findAll, progress));

                sw.Stop();
                
                ResultsDataGrid.ItemsSource = result.Select(c => new {
                    Combination = string.Join(" + ", c),
                    Sum = c.Sum().ToString($"F{precision}")
                }).ToList();

                CpuUsageText.Text = $"计算完成，耗时 {sw.Elapsed.TotalSeconds:F2} 秒";
                MessageBox.Show($"找到 {result.Count} 个组合");
            }
            catch (Exception ex)
            {
                MessageBox.Show($"计算错误: {ex.Message}");
            }
        }

        private List<List<decimal>> FindCombinationsParallel(List<decimal> numbers, decimal target,
            int precision, bool findAll, IProgress<int> progress)
        {
            var result = new List<List<decimal>>();
            object lockObj = new object();
            int foundCount = 0;

            Parallel.For(0, numbers.Count, i => 
            {
                var current = new List<decimal> { numbers[i] };
                FindCombinations(numbers.Skip(i + 1).ToList(), target - numbers[i], 
                    precision, current, result, findAll, lockObj, ref foundCount, progress);
            });

            return result;
        }

        private void FindCombinations(List<decimal> numbers, decimal target, int precision,
            List<decimal> current, List<List<decimal>> result, bool findAll, 
            object lockObj, ref int foundCount, IProgress<int> progress)
        {
            decimal currentSum = current.Sum();
            if (Math.Round(currentSum, precision) == Math.Round(target, precision))
            {
                lock (lockObj)
                {
                    result.Add(new List<decimal>(current));
                    foundCount++;
                    progress?.Report(foundCount);
                }
                if (!findAll) return;
            }

            if (Math.Round(currentSum, precision) > Math.Round(target, precision) || 
                numbers.Count == 0)
                return;

            for (int i = 0; i < numbers.Count; i++)
            {
                var remaining = numbers.Skip(i + 1).ToList();
                current.Add(numbers[i]);
                FindCombinations(remaining, target, precision, current, result, findAll, 
                    lockObj, ref foundCount, progress);
                current.RemoveAt(current.Count - 1);
            }
        }

        private List<List<decimal>> FindCombinations(List<decimal> numbers, decimal target, 
            int precision, bool findAll)
        {
            var result = new List<List<decimal>>();
            FindCombinations(numbers, target, precision, new List<decimal>(), result, findAll);
            return result;
        }

        private void FindCombinations(List<decimal> numbers, decimal target, int precision,
            List<decimal> current, List<List<decimal>> result, bool findAll)
        {
            decimal currentSum = current.Sum();
            if (Math.Round(currentSum, precision) == Math.Round(target, precision))
            {
                result.Add(new List<decimal>(current));
                if (!findAll) return;
            }

            if (Math.Round(currentSum, precision) > Math.Round(target, precision) || 
                numbers.Count == 0)
                return;

            for (int i = 0; i < numbers.Count; i++)
            {
                var remaining = numbers.Skip(i + 1).ToList();
                current.Add(numbers[i]);
                FindCombinations(remaining, target, precision, current, result, findAll);
                current.RemoveAt(current.Count - 1);
            }
        }
    }
}
