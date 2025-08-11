# Qlib Web Console 前端

基于 Vue 3 + TypeScript + Element Plus 构建的 Qlib 量化投资策略研究平台前端应用。

## 功能特性

- 🎯 **仪表盘** - 实验概览和快速操作
- 🧪 **实验管理** - 创建、配置和管理量化实验
- 📊 **可视化分析** - 丰富的图表和数据展示
- 📈 **性能监控** - 实时跟踪实验状态和进度
- 🎨 **现代UI** - 响应式设计，支持暗黑主题

## 技术栈

- **框架**: Vue 3 + Composition API
- **构建工具**: Vite
- **语言**: TypeScript
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **图表**: ECharts
- **HTTP客户端**: Axios
- **代码规范**: ESLint + Prettier

## 项目结构

```
src/
├── api/            # API接口定义
├── assets/         # 静态资源
│   ├── images/     # 图片资源
│   └── styles/     # 样式文件
├── components/     # 通用组件
├── router/         # 路由配置
├── stores/         # Pinia状态管理
├── types/          # TypeScript类型定义
├── utils/          # 工具函数
├── views/          # 页面组件
│   ├── Dashboard.vue           # 仪表盘
│   ├── CreateExperiment.vue    # 新建实验
│   ├── ExperimentHistory.vue   # 历史记录
│   ├── ExperimentDetail.vue    # 实验详情
│   └── Layout.vue             # 布局组件
├── App.vue         # 根组件
└── main.ts         # 入口文件
```

## 开发指南

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

应用将在 http://localhost:3000 启动，支持热重载。

### 构建生产版本

```bash
npm run build
```

### 代码检查

```bash
npm run lint
```

### 代码格式化

```bash
npm run format
```

## 页面说明

### 1. 仪表盘 (Dashboard)
- 实验统计概览
- 快速操作入口
- 最近实验列表
- 系统状态监控

### 2. 新建实验 (Create Experiment)
- 向导式实验配置
- 数据源选择和时间范围设定
- 模型和策略配置
- 参数调优和预览
- 一键启动回测

### 3. 历史记录 (Experiment History)
- 实验列表展示
- 状态筛选和搜索
- 实时进度更新
- 批量操作支持

### 4. 实验详情 (Experiment Detail)
- 多标签页详情展示
- 配置信息和关键指标
- 交互式性能图表
- 持仓分析和执行日志

## 开发规范

### 组件命名
- 使用 PascalCase 命名组件文件
- 组件名称应具有描述性

### 代码风格
- 使用 Composition API
- TypeScript 严格模式
- ESLint + Prettier 自动格式化

### 提交规范
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式化
- refactor: 重构
- test: 测试
- chore: 构建工具或辅助工具变动

## API 接口

前端通过 Axios 与后端 API 通信，主要接口包括：

- `GET /api/v1/dashboard/summary` - 获取仪表盘统计
- `POST /api/v1/experiments` - 创建实验
- `GET /api/v1/experiments` - 获取实验列表
- `GET /api/v1/experiments/:id` - 获取实验详情
- `GET /api/v1/config/*` - 获取配置选项

## 部署说明

### 环境变量配置

创建 `.env.production` 文件：

```bash
VITE_APP_TITLE=Qlib Web Console
VITE_API_BASE_URL=https://your-api-domain.com/api/v1
```

### 构建和部署

```bash
# 构建生产版本
npm run build

# 部署 dist 目录到静态服务器
# 如 Nginx、Apache 或 CDN
```

## 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License