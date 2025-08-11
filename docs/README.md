# Qlib 中文文档

欢迎使用 Qlib 中文文档！本文档提供了详细的安装指南、使用教程和示例代码，帮助您快速上手 Microsoft Qlib 量化投资平台。

## 📚 文档结构

### 🛠️ 安装指南
- **[qlib-安装指南.md](./qlib-安装指南.md)** - 详细的 Qlib 安装教程
  - 系统要求和兼容性说明
  - Apple Silicon Mac 特殊配置
  - 环境配置和故障排除
  - 完整的安装验证流程

### 📖 使用指南  
- **[qlib-使用指南.md](./qlib-使用指南.md)** - 全面的 Qlib 使用教程
  - 数据管理和处理
  - 模型开发和训练
  - 策略开发和回测
  - 风险管理和性能评估
  - 高级主题和最佳实践

### 💡 示例代码
- **[examples/](./examples/)** - 实用的示例代码
  - `quick_start.py` - 快速开始示例
  - `data_preparation.py` - 数据准备和处理示例
  - `backtest_results.png` - 回测结果可视化

### ⚙️ 配置文件
- **[configs/](./configs/)** - 配置文件模板
  - `default_config.yaml` - 默认配置文件

## 🚀 快速开始

### 1. 检查系统要求
确保您的系统满足以下要求：
- **操作系统**: macOS 11.0+ 
- **Python**: 3.7-3.9 (推荐 3.8)
- **内存**: 至少 8GB RAM
- **存储**: 至少 5GB 可用空间

### 2. 安装 Qlib
按照 [安装指南](./qlib-安装指南.md) 中的步骤安装 Qlib：

```bash
# 1. 安装系统依赖
brew install libomp

# 2. 创建 Python 环境
conda create -n qlib python=3.8 -y
conda activate qlib

# 3. 从源码安装 Qlib
git clone https://github.com/microsoft/qlib.git
cd qlib
pip install -e .
```

### 3. 验证安装
```bash
python -c "import qlib; print(f'Qlib {qlib.__version__} 安装成功！')"
```

### 4. 运行示例
```bash
# 运行快速开始示例
python docs/examples/quick_start.py

# 运行数据准备示例  
python docs/examples/data_preparation.py
```

## 📊 主要功能

### 🔍 数据处理
- **多源数据集成**: 支持中国、美国等多个市场数据
- **特征工程**: 内置 Alpha158、Alpha360 等特征集
- **数据清洗**: 自动处理缺失值、异常值
- **技术指标**: 丰富的技术指标计算函数

### 🤖 模型开发
- **机器学习模型**: LightGBM、XGBoost、线性模型
- **深度学习模型**: LSTM、GRU、Transformer 等
- **集成学习**: 多模型融合和集成
- **自动调参**: 超参数优化和模型选择

### 📈 策略开发
- **信号策略**: 基于模型预测的交易信号
- **投资组合优化**: 均值方差优化、风险平价等
- **风险管理**: 位置控制、止损止盈、风险预算
- **多因子模型**: 因子构建、测试和组合

### 🔄 回测系统
- **高保真回测**: 考虑交易成本、滑点、市场冲击
- **多频率支持**: 日频、30分钟、5分钟等
- **绩效分析**: 收益、风险、归因等全面分析
- **基准比较**: 与市场指数的对比分析

## 📈 典型工作流程

```python
import qlib
from qlib.config import REG_CN

# 1. 初始化环境
qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region=REG_CN)

# 2. 准备数据
from qlib.contrib.data.handler import Alpha360
data_handler = Alpha360(instruments='csi300', start_time='2015-01-01', end_time='2023-12-31')

# 3. 训练模型
from qlib.contrib.model.gbdt import LGBModel
model = LGBModel()
model.fit(dataset)

# 4. 生成预测
predictions = model.predict(dataset)

# 5. 构建策略
from qlib.contrib.strategy import TopkDropoutStrategy
strategy = TopkDropoutStrategy(topk=50, n_drop=5)

# 6. 执行回测
from qlib.backtest import backtest
results = backtest(strategy=strategy, start_time='2022-01-01', end_time='2023-12-31')
```

## 🎯 使用场景

### 📊 量化研究
- 因子挖掘和验证
- 策略开发和测试
- 风险模型构建
- 市场微观结构分析

### 💼 投资管理
- 资产配置优化
- 选股和择时
- 风险预算和控制
- 绩效归因分析

### 🎓 教育学习
- 量化投资教学
- 金融数据科学
- 机器学习在金融中的应用
- 策略研究方法论

## ⚠️ 重要提示

### 系统兼容性
- **Apple Silicon**: 需要从源码安装，不支持官方预编译包
- **Python 版本**: 严格要求 Python 3.7-3.9
- **依赖冲突**: 注意 LightGBM 和 PyTorch 版本兼容性

### 数据准备
- **首次使用**: 需要下载历史数据，可能需要较长时间
- **存储空间**: 完整数据集可能占用数GB空间  
- **网络连接**: 数据下载需要稳定的网络连接

### 风险提示
- **仅供研究**: 本文档和示例仅用于学习和研究
- **投资风险**: 量化投资存在风险，请谨慎决策
- **数据准确性**: 请验证数据的准确性和完整性

## 🛠️ 故障排除

### 常见问题
1. **安装失败**: 检查 Python 版本和系统依赖
2. **数据加载错误**: 确认数据路径和数据完整性
3. **模型训练慢**: 考虑减少特征数量或使用GPU加速
4. **内存不足**: 减少数据量或使用数据分块

### 获取帮助
- **官方文档**: https://qlib.readthedocs.io/
- **GitHub Issues**: https://github.com/microsoft/qlib/issues
- **社区讨论**: GitHub Discussions

## 🤝 贡献指南

我们欢迎社区贡献！您可以通过以下方式参与：

1. **报告问题**: 在 GitHub Issues 中报告 bug
2. **提交代码**: 通过 Pull Request 贡献代码
3. **完善文档**: 改进文档和示例
4. **分享经验**: 在社区中分享使用心得

## 📄 许可证

本文档遵循 MIT 许可证。Qlib 遵循其原始许可证条款。

## 🙏 致谢

感谢 Microsoft Qlib 团队的开源贡献，以及所有参与文档编写和完善的贡献者。

---

**免责声明**: 本文档仅供学习和研究使用，不构成任何投资建议。使用者应当充分了解量化投资的风险，并在专业人士指导下进行投资决策。