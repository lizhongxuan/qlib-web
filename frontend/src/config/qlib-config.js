/**
 * Qlib-Web 前端配置文件
 * 
 * 此文件定义了Qlib-Web前端应用的所有配置选项，包括：
 * - 数据源配置
 * - 市场和股票池配置
 * - 模型默认参数
 * - 因子表达式语法配置
 * - 错误处理和降级策略
 * - API配置和重试机制
 * 
 * 修改理由：
 * 1. 根据TODO 7.2.6节需求，创建独立的配置文件管理所有qlib相关配置
 * 2. 提供灵活的环境配置切换机制（开发/生产/测试）
 * 3. 集中管理错误处理和API降级策略
 * 4. 为不同使用场景提供预设配置模板
 */

// 环境检测
const isDevelopment = process.env.NODE_ENV === 'development'
const isProduction = process.env.NODE_ENV === 'production'
const isTesting = process.env.NODE_ENV === 'test'

/**
 * Qlib数据源配置
 * 包括数据提供商、区域设置、缓存配置等
 */
export const QLIB_DATA_CONFIG = {
  // 数据提供商配置
  providers: {
    yahoo: {
      name: 'Yahoo Finance',
      region: ['us', 'cn', 'global'],
      data_types: ['stock', 'index', 'forex'],
      rate_limit: 100, // 每分钟请求限制
      retry_count: 3,
      timeout: 30000
    },
    tushare: {
      name: 'Tushare',
      region: ['cn'],
      data_types: ['stock', 'index', 'fund', 'bond'],
      rate_limit: 200,
      retry_count: 3,
      timeout: 30000,
      token_required: true
    },
    baostock: {
      name: 'BaoStock',
      region: ['cn'],
      data_types: ['stock', 'index'],
      rate_limit: 500,
      retry_count: 3,
      timeout: 30000,
      free_tier: true
    },
    custom: {
      name: 'Custom Data Source',
      region: ['global'],
      data_types: ['stock', 'index', 'forex', 'crypto'],
      configurable: true
    }
  },

  // 默认数据源配置
  default: {
    provider: isDevelopment ? 'yahoo' : 'tushare',
    region: 'cn',
    provider_uri: isDevelopment 
      ? 'file:///tmp/qlib_data/cn_data' 
      : 'file:///data/qlib/cn_data',
    cache_dir: isDevelopment 
      ? '/tmp/qlib_cache' 
      : '/data/cache/qlib',
    auto_mount: true,
    provider_config: {
      auto_update: true,
      normalize_names: true,
      data_validation: true
    }
  },

  // 区域配置映射
  regions: {
    cn: {
      name: '中国市场',
      timezone: 'Asia/Shanghai',
      trading_hours: {
        morning: ['09:30', '11:30'],
        afternoon: ['13:00', '15:00']
      },
      currency: 'CNY',
      exchanges: ['SSE', 'SZSE', 'BSE'],
      holidays_provider: 'cn_calendar'
    },
    us: {
      name: '美国市场',
      timezone: 'America/New_York',
      trading_hours: {
        regular: ['09:30', '16:00']
      },
      currency: 'USD',
      exchanges: ['NYSE', 'NASDAQ'],
      holidays_provider: 'us_calendar'
    },
    global: {
      name: '全球市场',
      timezone: 'UTC',
      currency: 'USD',
      exchanges: ['multiple'],
      holidays_provider: 'global_calendar'
    }
  }
}

/**
 * 市场和股票池配置
 * 定义不同市场的股票池和筛选规则
 */
export const QLIB_MARKET_CONFIG = {
  // 中国市场股票池
  markets: {
    CSI300: {
      name: '沪深300',
      description: '沪深300指数成分股',
      universe_size: 300,
      rebalance_freq: 'semi_annual',
      data_start: '2005-01-01',
      benchmark: '000300.SH',
      sectors: ['金融', '消费', '科技', '工业', '医疗', '能源'],
      market_cap_range: [50, null], // 亿元
      liquidity_requirement: true
    },
    CSI500: {
      name: '中证500',
      description: '中证500指数成分股',
      universe_size: 500,
      rebalance_freq: 'semi_annual',
      data_start: '2007-01-01',
      benchmark: '000905.SH',
      sectors: ['制造业', '信息技术', '材料', '可选消费'],
      market_cap_range: [10, 200], // 亿元
      liquidity_requirement: true
    },
    CSI800: {
      name: '中证800',
      description: '中证800指数成分股（沪深300+中证500）',
      universe_size: 800,
      rebalance_freq: 'semi_annual',
      data_start: '2007-01-01',
      benchmark: '000906.SH',
      market_cap_range: [10, null],
      liquidity_requirement: true
    },
    CSI1000: {
      name: '中证1000',
      description: '中证1000指数成分股',
      universe_size: 1000,
      rebalance_freq: 'semi_annual',
      data_start: '2014-01-01',
      benchmark: '000852.SH',
      market_cap_range: [5, 50], // 亿元
      liquidity_requirement: true
    },
    ALL: {
      name: '全市场',
      description: '沪深两市全部A股',
      universe_size: 4500,
      rebalance_freq: 'monthly',
      data_start: '2000-01-01',
      benchmark: '000001.SH', // 上证指数作为基准
      market_cap_range: [1, null],
      liquidity_requirement: false
    }
  },

  // 股票筛选配置
  filter_config: {
    default: {
      include_st: false, // 排除ST股票
      include_suspend: false, // 排除停牌股票
      min_market_cap: 10, // 最小市值（亿元）
      min_price: 5, // 最小股价
      min_volume: 1000000, // 最小日成交额
      max_new_stock_days: 60, // 新股上市天数限制
      liquidity_filter: true, // 流动性筛选
      fundamental_filter: false // 基本面筛选
    },
    strict: {
      include_st: false,
      include_suspend: false,
      min_market_cap: 50,
      min_price: 10,
      min_volume: 10000000,
      max_new_stock_days: 252,
      liquidity_filter: true,
      fundamental_filter: true,
      min_roe: 0.05, // 最低ROE
      max_debt_ratio: 0.7 // 最高负债率
    },
    loose: {
      include_st: true,
      include_suspend: false,
      min_market_cap: 1,
      min_price: 1,
      min_volume: 100000,
      max_new_stock_days: 30,
      liquidity_filter: false,
      fundamental_filter: false
    }
  },

  // 行业分类配置
  industries: {
    sw_l1: {
      name: '申万一级行业',
      categories: [
        '银行', '非银金融', '房地产', '建筑装饰', '钢铁', '有色金属',
        '电子', '家用电器', '食品饮料', '纺织服装', '轻工制造', '医药生物',
        '公用事业', '交通运输', '化工', '建筑材料', '机械设备', '电气设备',
        '国防军工', '计算机', '传媒', '通信', '汽车', '农林牧渔',
        '休闲服务', '综合', '商业贸易', '石油石化', '环保', '美容护理'
      ]
    },
    zx_l1: {
      name: '中信一级行业',
      categories: [
        '石油石化', '煤炭', '有色金属', '电力及公用事业', '钢铁',
        '基础化工', '建筑', '建材', '轻工制造', '机械', '电力设备',
        '国防军工', '汽车', '商贸零售', '消费者服务', '家电',
        '纺织服装', '医药', '食品饮料', '农林牧渔', '银行', '非银行金融',
        '房地产', '交通运输', '电子', '通信', '计算机', '传媒'
      ]
    }
  }
}

/**
 * 模型默认参数配置
 * 为不同的机器学习模型提供合理的默认参数
 */
export const QLIB_MODEL_CONFIG = {
  // LightGBM模型配置
  lightgbm: {
    default: {
      objective: 'regression',
      metric: 'mse',
      boosting_type: 'gbdt',
      num_leaves: 31,
      learning_rate: 0.1,
      feature_fraction: 0.9,
      bagging_fraction: 0.8,
      bagging_freq: 5,
      verbose: -1,
      n_estimators: 100,
      random_state: 42
    },
    fast: {
      // 快速训练配置，用于测试和原型
      n_estimators: 50,
      num_leaves: 15,
      learning_rate: 0.15,
      max_depth: 4
    },
    accurate: {
      // 高精度配置，用于生产环境
      n_estimators: 500,
      num_leaves: 127,
      learning_rate: 0.05,
      max_depth: 8,
      min_child_samples: 20,
      reg_alpha: 0.1,
      reg_lambda: 0.1
    }
  },

  // XGBoost模型配置
  xgboost: {
    default: {
      objective: 'reg:squarederror',
      eval_metric: 'rmse',
      booster: 'gbtree',
      max_depth: 6,
      learning_rate: 0.1,
      n_estimators: 100,
      subsample: 0.8,
      colsample_bytree: 0.8,
      random_state: 42
    },
    fast: {
      n_estimators: 50,
      max_depth: 4,
      learning_rate: 0.15
    },
    accurate: {
      n_estimators: 500,
      max_depth: 8,
      learning_rate: 0.05,
      reg_alpha: 0.1,
      reg_lambda: 0.1
    }
  },

  // CatBoost模型配置
  catboost: {
    default: {
      objective: 'RMSE',
      iterations: 100,
      learning_rate: 0.1,
      depth: 6,
      l2_leaf_reg: 3,
      border_count: 128,
      thread_count: -1,
      random_state: 42,
      verbose: False
    },
    fast: {
      iterations: 50,
      depth: 4,
      learning_rate: 0.15
    },
    accurate: {
      iterations: 500,
      depth: 8,
      learning_rate: 0.05,
      bagging_temperature: 1.0
    }
  },

  // LSTM模型配置
  lstm: {
    default: {
      hidden_size: 128,
      num_layers: 2,
      dropout: 0.2,
      bidirectional: false,
      batch_size: 64,
      seq_len: 20,
      learning_rate: 0.001,
      epochs: 100
    },
    fast: {
      hidden_size: 64,
      num_layers: 1,
      epochs: 50
    },
    accurate: {
      hidden_size: 256,
      num_layers: 3,
      dropout: 0.3,
      epochs: 200
    }
  },

  // 线性模型配置
  linear: {
    default: {
      fit_intercept: true,
      normalize: false,
      alpha: 1.0,
      max_iter: 1000,
      tol: 0.001,
      random_state: 42
    },
    ridge: {
      alpha: 1.0,
      fit_intercept: true,
      normalize: true,
      solver: 'auto'
    },
    lasso: {
      alpha: 1.0,
      fit_intercept: true,
      normalize: true,
      max_iter: 1000,
      selection: 'cyclic'
    },
    elastic_net: {
      alpha: 1.0,
      l1_ratio: 0.5,
      fit_intercept: true,
      normalize: true,
      max_iter: 1000
    }
  },

  // 训练通用配置
  training: {
    validation_split: 0.2,
    test_split: 0.1,
    cross_validation: {
      enabled: false,
      folds: 5,
      shuffle: true
    },
    early_stopping: {
      enabled: true,
      patience: 50,
      monitor: 'val_loss'
    },
    model_selection: {
      metric: 'ic', // IC, ICIR, sharpe, returns
      direction: 'maximize'
    },
    resource_limits: {
      max_memory_gb: 8,
      max_training_time_hours: 2,
      max_concurrent_jobs: 2
    }
  }
}

/**
 * 因子表达式语法配置
 * 定义qlib因子表达式的语法规则和验证配置
 */
export const QLIB_FACTOR_CONFIG = {
  // 内置因子库
  builtin_factors: {
    // Alpha158因子
    alpha158: {
      enabled: true,
      categories: [
        'close_price', 'volume', 'returns', 'volatility', 'momentum',
        'mean_reversion', 'correlation', 'technical_indicators'
      ],
      count: 158
    },
    // Alpha360因子
    alpha360: {
      enabled: false, // 默认关闭，计算量大
      categories: ['extended_technical', 'cross_sectional', 'time_series'],
      count: 360
    }
  },

  // 语法配置
  expression_syntax: {
    // 基础操作符
    operators: {
      arithmetic: ['+', '-', '*', '/', '**'],
      comparison: ['>', '<', '>=', '<=', '==', '!='],
      logical: ['&', '|', '~'],
      assignment: ['=']
    },
    
    // 内置函数
    functions: {
      math: ['Abs', 'Log', 'Sqrt', 'Sin', 'Cos', 'Exp', 'Max', 'Min'],
      time_series: [
        'Mean', 'Std', 'Var', 'Sum', 'Rank', 'Quantile',
        'Ts_Rank', 'Ts_ArgMax', 'Ts_ArgMin', 'Ts_Max', 'Ts_Min',
        'Delta', 'Delay', 'Ref', 'Shift'
      ],
      cross_sectional: [
        'Rank', 'Quantile', 'Scale', 'Neutralize',
        'GroupByMean', 'GroupByStd', 'GroupByRank'
      ],
      technical: [
        'RSI', 'MACD', 'BOLL', 'KDJ', 'MA', 'EMA',
        'ATR', 'CCI', 'ROC', 'WILLR'
      ],
      statistical: [
        'Correlation', 'Covariance', 'Beta', 'Skew', 'Kurt',
        'ZScore', 'Winsorize', 'Clip'
      ]
    },

    // 数据字段
    data_fields: {
      price: ['$open', '$high', '$low', '$close', '$vwap'],
      volume: ['$volume', '$amount', '$turnover'],
      market_data: ['$market_cap', '$shares', '$pe', '$pb'],
      derived: ['$change', '$pct_chg', '$volume_ratio']
    },

    // 语法规则
    validation_rules: {
      max_expression_length: 1000,
      max_nested_level: 10,
      required_data_fields: ['$close'], // 必须包含的字段
      forbidden_functions: [], // 禁用的函数
      time_window_limits: {
        min: 1,
        max: 252 // 最大时间窗口1年
      }
    }
  },

  // 因子验证配置
  validation: {
    // IC分析配置
    ic_analysis: {
      periods: [1, 5, 10, 20], // 预测周期
      method: 'pearson', // pearson, spearman, kendall
      significance_level: 0.05,
      min_ic_threshold: 0.02,
      ic_ir_threshold: 0.5
    },
    
    // 回测验证
    backtest_validation: {
      lookback_period: 252, // 回看天数
      rebalance_freq: 'daily',
      top_quantile: 0.2, // 选择前20%
      transaction_cost: 0.002,
      benchmark: '000300.SH'
    },
    
    // 数据质量检查
    data_quality: {
      max_nan_ratio: 0.1, // 最大缺失值比例
      outlier_detection: {
        method: 'iqr', // iqr, zscore, isolation_forest
        threshold: 3.0
      },
      stationarity_test: true,
      correlation_threshold: 0.95 // 相关性阈值
    }
  }
}

/**
 * 错误处理和降级策略配置
 * 定义各种错误情况的处理方式和降级方案
 */
export const QLIB_ERROR_CONFIG = {
  // 数据不可用错误处理
  data_unavailable: {
    retry_strategy: {
      max_retries: 3,
      retry_delay: [1000, 2000, 5000], // 递增延迟（毫秒）
      backoff_factor: 2
    },
    fallback_options: [
      {
        type: 'cache',
        description: '使用本地缓存数据',
        max_age_hours: 24
      },
      {
        type: 'alternative_provider',
        description: '切换到备用数据源',
        providers: ['yahoo', 'baostock']
      },
      {
        type: 'mock_data',
        description: '使用模拟数据',
        enabled: isDevelopment
      },
      {
        type: 'notification',
        description: '通知用户并提供手动操作选项'
      }
    ]
  },

  // 因子表达式语法错误
  factor_syntax_error: {
    validation_levels: {
      syntax: {
        enabled: true,
        real_time: true,
        show_suggestions: true
      },
      semantic: {
        enabled: true,
        check_data_availability: true,
        check_function_compatibility: true
      },
      performance: {
        enabled: isProduction,
        estimate_computation_cost: true,
        warn_on_expensive_operations: true
      }
    },
    error_messages: {
      syntax_error: '因子表达式语法错误：{error}',
      unknown_function: '未知函数：{function}，建议使用：{suggestions}',
      invalid_field: '无效数据字段：{field}，可用字段：{available}',
      nested_too_deep: '表达式嵌套层级过深（最大{max}层）',
      expression_too_long: '表达式过长（最大{max}字符）'
    },
    suggestions: {
      auto_complete: true,
      function_hints: true,
      syntax_highlighting: true,
      error_recovery: true
    }
  },

  // 模型训练资源不足
  training_resource_error: {
    resource_monitoring: {
      memory_threshold: 0.85, // 内存使用率阈值
      cpu_threshold: 0.90, // CPU使用率阈值
      disk_threshold: 0.95, // 磁盘使用率阈值
      check_interval: 10000 // 检查间隔（毫秒）
    },
    mitigation_strategies: [
      {
        type: 'reduce_batch_size',
        description: '减少批量大小',
        trigger: 'memory_high'
      },
      {
        type: 'enable_model_compression',
        description: '启用模型压缩',
        trigger: 'memory_high'
      },
      {
        type: 'switch_to_fast_mode',
        description: '切换到快速模式',
        trigger: 'time_limit'
      },
      {
        type: 'queue_training',
        description: '加入训练队列',
        trigger: 'resource_unavailable'
      },
      {
        type: 'distributed_training',
        description: '使用分布式训练',
        trigger: 'large_dataset',
        enabled: isProduction
      }
    ]
  },

  // 回测参数配置错误
  backtest_config_error: {
    validation_rules: {
      date_range: {
        min_period_days: 30,
        max_period_days: 3650, // 10年
        require_valid_trading_days: true
      },
      universe: {
        min_stocks: 10,
        max_stocks: 1000,
        check_availability: true
      },
      parameters: {
        max_position: 1.0,
        min_cash_ratio: 0.0,
        max_transaction_cost: 0.01
      }
    },
    auto_correction: {
      enabled: true,
      fix_date_range: true,
      adjust_universe_size: true,
      optimize_parameters: true
    },
    suggestions: {
      parameter_optimization: true,
      benchmark_recommendation: true,
      universe_recommendation: true
    }
  },

  // API调用失败降级机制
  api_failure: {
    circuit_breaker: {
      enabled: true,
      failure_threshold: 5, // 连续失败次数
      timeout_ms: 60000, // 熔断持续时间
      half_open_max_calls: 3 // 半开状态最大尝试次数
    },
    timeout_config: {
      default: 30000,
      data_fetch: 60000,
      model_training: 300000,
      backtest: 600000
    },
    retry_config: {
      max_retries: 3,
      base_delay: 1000,
      max_delay: 10000,
      jitter: true
    },
    graceful_degradation: [
      {
        service: 'qlib_data',
        fallback: 'cached_data',
        enabled: true
      },
      {
        service: 'model_training',
        fallback: 'simple_model',
        enabled: isDevelopment
      },
      {
        service: 'factor_validation',
        fallback: 'syntax_check_only',
        enabled: true
      },
      {
        service: 'backtest_engine',
        fallback: 'simple_returns',
        enabled: isDevelopment
      }
    ]
  }
}

/**
 * API配置
 * 定义前端与后端API的交互配置
 */
export const QLIB_API_CONFIG = {
  base_url: process.env.VUE_APP_API_BASE_URL || 'http://localhost:8000',
  endpoints: {
    // 配置管理相关
    config: {
      current: '/api/v1/qlib/config/current',
      save: '/api/v1/qlib/config/save',
      validate: '/api/v1/qlib/config/validate',
      test_connection: '/api/v1/qlib/config/test-connection',
      optimize: '/api/v1/qlib/config/optimize'
    },
    // 数据服务相关
    data: {
      market_data: '/api/v1/data/market-data',
      factor_data: '/api/v1/data/factor-data',
      create_dataset: '/api/v1/data/create-dataset',
      calculate_factor: '/api/v1/data/calculate-factor',
      instruments: '/api/v1/data/instruments'
    },
    // 因子服务相关
    factors: {
      library: '/api/v1/qlib-factors/factor-library',
      validate: '/api/v1/qlib-factors/validate-factor',
      create: '/api/v1/qlib-factors/create-factor',
      construct_strategy: '/api/v1/qlib-factors/construct-strategy',
      templates: '/api/v1/qlib-factors/strategy-templates'
    },
    // 模型服务相关
    models: {
      train: '/api/v1/models/train',
      evaluate: '/api/v1/models/evaluate',
      backtest: '/api/v1/models/backtest',
      deploy: '/api/v1/models/deploy',
      registry: '/api/v1/models/registry'
    },
    // ML服务相关
    ml: {
      analyze_data: '/api/v1/ml/analyze-data',
      recommend_models: '/api/v1/ml/recommend-models',
      optimize_hyperparameters: '/api/v1/ml/optimize-hyperparameters',
      feature_selection: '/api/v1/ml/feature-selection',
      train_ensemble: '/api/v1/ml/train-ensemble'
    }
  },
  
  // 请求配置
  request_config: {
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    withCredentials: true
  },

  // 缓存配置
  cache_config: {
    enabled: true,
    ttl: {
      config: 5 * 60 * 1000,      // 配置缓存5分钟
      factor_library: 30 * 60 * 1000, // 因子库缓存30分钟
      market_data: 10 * 60 * 1000,     // 市场数据缓存10分钟
      model_registry: 15 * 60 * 1000   // 模型注册表缓存15分钟
    },
    max_size: 100 // 最大缓存条目数
  }
}

/**
 * 环境特定配置
 * 根据当前环境（开发/生产/测试）调整配置
 */
export const ENVIRONMENT_CONFIG = {
  development: {
    enable_debug: true,
    enable_mock_data: true,
    log_level: 'debug',
    api_timeout: 60000,
    auto_save_interval: 30000,
    show_performance_metrics: true,
    enable_hot_reload: true
  },
  production: {
    enable_debug: false,
    enable_mock_data: false,
    log_level: 'error',
    api_timeout: 30000,
    auto_save_interval: 10000,
    show_performance_metrics: false,
    enable_hot_reload: false,
    enable_compression: true,
    enable_analytics: true
  },
  testing: {
    enable_debug: true,
    enable_mock_data: true,
    log_level: 'warn',
    api_timeout: 10000,
    auto_save_interval: 5000,
    show_performance_metrics: true,
    parallel_execution: false
  }
}

// 导出当前环境配置
export const CURRENT_ENV_CONFIG = ENVIRONMENT_CONFIG[process.env.NODE_ENV] || ENVIRONMENT_CONFIG.development

/**
 * 配置工具函数
 */
export const ConfigUtils = {
  /**
   * 获取合并后的配置
   */
  getMergedConfig: () => {
    return {
      data: QLIB_DATA_CONFIG,
      market: QLIB_MARKET_CONFIG,
      model: QLIB_MODEL_CONFIG,
      factor: QLIB_FACTOR_CONFIG,
      error: QLIB_ERROR_CONFIG,
      api: QLIB_API_CONFIG,
      environment: CURRENT_ENV_CONFIG
    }
  },

  /**
   * 验证配置完整性
   */
  validateConfig: (config) => {
    const errors = []
    
    // 检查必要的配置项
    if (!config?.data?.default?.provider) {
      errors.push('缺少数据源配置')
    }
    
    if (!config?.api?.base_url) {
      errors.push('缺少API基础URL配置')
    }
    
    return {
      isValid: errors.length === 0,
      errors
    }
  },

  /**
   * 获取环境特定配置
   */
  getEnvironmentConfig: (env = process.env.NODE_ENV) => {
    return ENVIRONMENT_CONFIG[env] || ENVIRONMENT_CONFIG.development
  },

  /**
   * 深度合并配置对象
   */
  mergeConfigs: (target, source) => {
    const result = { ...target }
    
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = ConfigUtils.mergeConfigs(result[key] || {}, source[key])
      } else {
        result[key] = source[key]
      }
    }
    
    return result
  }
}

// 默认导出完整配置
export default ConfigUtils.getMergedConfig()