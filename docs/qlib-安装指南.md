# Qlib 安装指南

## 概述

Qlib 是微软开源的 AI 量化投资平台。本指南基于实际安装过程，详细说明如何在 Apple Silicon Mac 上成功安装 Qlib。

## 系统要求

### 硬件要求
- **处理器**: Apple Silicon (M1/M2/M3/M4) 或 Intel x86_64
- **内存**: 至少 8GB RAM，推荐 16GB+
- **存储**: 至少 5GB 可用空间

### 软件要求
- **操作系统**: macOS 11.0+ (Big Sur 或更高版本)
- **Python**: 3.7-3.9 (推荐 3.8)
- **包管理器**: conda 或 pip
- **编译工具**: Xcode Command Line Tools

## 兼容性说明

### ⚠️ 重要提示
- **Python 版本限制**: Qlib 目前仅支持 Python 3.7-3.9，不支持 Python 3.10+
- **Apple Silicon 支持**: 需要从源码安装，预编译包不可用
- **系统依赖**: Apple Silicon 需要额外安装 OpenMP 支持

### 已知问题
- 官方 PyPI 包不支持 Apple Silicon
- Python 3.9 版本绘图功能受限
- 某些依赖包在 Apple Silicon 上需要特殊处理

## 安装步骤

### 第一步：安装系统依赖

#### 1.1 安装 Homebrew（如未安装）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 1.2 安装 OpenMP（Apple Silicon 必需）
```bash
brew install libomp
```

### 第二步：安装 Miniconda

#### 2.1 下载并安装 Miniconda
```bash
# 下载 ARM64 版本（Apple Silicon）
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh

# 静默安装
bash Miniconda3-latest-MacOSX-arm64.sh -b -p $HOME/miniconda3
```

#### 2.2 接受服务条款
```bash
$HOME/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
$HOME/miniconda3/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

### 第三步：创建 Python 环境

#### 3.1 创建专用环境
```bash
$HOME/miniconda3/bin/conda create -n qlib python=3.8 -y
```

#### 3.2 激活环境
```bash
source $HOME/miniconda3/bin/activate qlib
```

#### 3.3 验证环境
```bash
python --version  # 应显示 Python 3.8.x
```

### 第四步：安装基础依赖

#### 4.1 设置编译环境变量（Apple Silicon 必需）
```bash
export LDFLAGS="-L/opt/homebrew/opt/libomp/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libomp/include"
```

#### 4.2 安装基础包
```bash
pip install numpy cython
```

### 第五步：从源码安装 Qlib

#### 5.1 克隆源码
```bash
git clone https://github.com/microsoft/qlib.git
cd qlib
```

#### 5.2 安装 Qlib
```bash
# 确保环境变量已设置
export LDFLAGS="-L/opt/homebrew/opt/libomp/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libomp/include"

# 可编辑模式安装
pip install -e .
```

## 验证安装

### 基础验证
```bash
# 激活环境
source $HOME/miniconda3/bin/activate qlib

# 验证导入
python -c "import qlib; print(f'Qlib 版本: {qlib.__version__}')"

# 验证依赖
python -c "
import qlib
import numpy as np
import pandas as pd
print('✅ 核心库导入成功')
print(f'- qlib: {qlib.__version__}')
print(f'- numpy: {np.__version__}')
print(f'- pandas: {pd.__version__}')
"
```

### 高级验证
```bash
# 测试数据功能（需要数据）
python -c "
try:
    import qlib
    from qlib.config import REG_CN
    qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region=REG_CN)
    print('✅ Qlib 初始化成功')
except Exception as e:
    print(f'⚠️ 数据初始化失败（正常，需要先下载数据）: {e}')
"
```

## 环境配置

### Shell 配置
将以下内容添加到 `~/.zshrc` 或 `~/.bash_profile`：

```bash
# Qlib 环境快速激活
alias qlib-activate="source $HOME/miniconda3/bin/activate qlib"

# Apple Silicon 编译环境变量
export LDFLAGS="-L/opt/homebrew/opt/libomp/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libomp/include"
```

### IDE 配置
如果使用 VS Code 或 PyCharm，设置 Python 解释器为：
```
/Users/$(whoami)/miniconda3/envs/qlib/bin/python
```

## 故障排除

### 常见问题

#### 1. "No matching distribution found for pyqlib"
**原因**: 尝试使用 `pip install pyqlib`，但 Apple Silicon 没有预编译包。
**解决**: 必须从源码安装。

#### 2. LightGBM 编译失败
**原因**: 缺少 OpenMP 支持。
**解决**: 
```bash
brew install libomp
export LDFLAGS="-L/opt/homebrew/opt/libomp/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libomp/include"
```

#### 3. Python 版本不兼容
**原因**: 使用了 Python 3.10+ 版本。
**解决**: 创建 Python 3.8 环境：
```bash
conda create -n qlib python=3.8 -y
```

#### 4. 权限错误
**原因**: conda 或 pip 权限问题。
**解决**: 
```bash
# 修复 conda 权限
sudo chown -R $(whoami) $HOME/miniconda3

# 使用用户安装
pip install --user -e .
```

### 性能优化

#### 1. 启用多核编译
```bash
export CC=clang
export CXX=clang++
pip install -e . --global-option="--parallel=$(nproc)"
```

#### 2. 使用 conda-forge
```bash
conda config --add channels conda-forge
```

## 卸载指南

### 完全卸载
```bash
# 删除 conda 环境
conda remove -n qlib --all

# 删除源码目录
rm -rf qlib

# 删除 miniconda（可选）
rm -rf $HOME/miniconda3
```

## 升级指南

### 升级到最新版本
```bash
# 激活环境
source $HOME/miniconda3/bin/activate qlib

# 进入源码目录
cd qlib

# 拉取最新代码
git pull origin main

# 重新安装
pip install -e . --force-reinstall
```

## 技术支持

### 官方资源
- **GitHub**: https://github.com/microsoft/qlib
- **文档**: https://qlib.readthedocs.io/
- **论文**: https://arxiv.org/abs/2009.11189

### 社区支持
- **Issues**: GitHub Issues 页面
- **讨论**: GitHub Discussions
- **中文社区**: 各大技术论坛 Qlib 板块

## 版本历史

| 版本 | 发布日期 | 主要变化 |
|------|----------|----------|
| 0.9.6.99 | 2024+ | 开发版本，持续更新 |
| 0.9.x | 2023-2024 | 稳定版本系列 |
| 0.8.x | 2022-2023 | 早期版本 |

---

## 结语

本指南基于实际安装经验编写，涵盖了 Apple Silicon Mac 上安装 Qlib 的所有关键步骤和问题解决方案。如果遇到其他问题，请参考官方文档或在 GitHub 上提交 Issue。

**安装成功后**，请继续阅读《qlib-使用指南.md》了解如何使用 Qlib 进行量化研究。