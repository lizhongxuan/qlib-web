#!/bin/bash

# Git Hooks 设置脚本

echo "设置 Git Hooks..."

# 检查是否安装了 pre-commit
if ! command -v pre-commit &> /dev/null; then
    echo "安装 pre-commit..."
    pip install pre-commit
fi

# 安装 pre-commit hooks
echo "安装 pre-commit hooks..."
pre-commit install

# 安装 commit-msg hook
echo "安装 commit-msg hook..."
pre-commit install --hook-type commit-msg

# 测试 hooks
echo "测试 hooks..."
pre-commit run --all-files

echo "Git Hooks 设置完成！"