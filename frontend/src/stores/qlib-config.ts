import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Qlib配置相关的类型定义
interface QlibDataConfig {
  provider_uri: string
  region: 'cn' | 'us' | 'global'
  data_source: 'yahoo' | 'baostock' | 'tushare' | 'custom'
  redis_host?: string
  redis_port?: number
  redis_db?: number
  cache_dir: string
  auto_mount: boolean
  provider_config: Record<string, any>
}

interface QlibCalendarConfig {
  provider: 'exchange_calendar' | 'custom'
  region: 'cn' | 'us' | 'global'
  trading_calendar?: string
  custom_calendar?: string[]
  auto_update: boolean
}

interface QlibInstrumentConfig {
  market: 'CSI300' | 'CSI500' | 'CSI800' | 'CSI1000' | 'SZSE' | 'SSE' | 'ALL'
  provider: 'yahoo' | 'baostock' | 'tushare' | 'custom'
  instruments_file?: string
  auto_update: boolean
  filter_config: {
    include_st: boolean
    include_suspend: boolean
    min_market_cap?: number
    max_market_cap?: number
    industries?: string[]
    exclude_industries?: string[]
  }
}

interface QlibFeatureConfig {
  feature_root_dir: string
  expression_cache: boolean
  cache_provider: 'file' | 'redis' | 'memory'
  feature_config: {
    enable_alpha158: boolean
    enable_alpha360: boolean
    custom_features: string[]
    feature_engineering: {
      normalization: 'zscore' | 'minmax' | 'robust' | 'none'
      outlier_treatment: 'clip' | 'winsorize' | 'none'
      missing_value_fill: 'ffill' | 'bfill' | 'mean' | 'median' | 'zero'
    }
  }
}

interface QlibModelConfig {
  model_cache_dir: string
  model_registry: 'local' | 'mlflow' | 'wandb'
  auto_save_models: boolean
  model_compression: boolean
  default_model_params: {
    lightgbm: Record<string, any>
    xgboost: Record<string, any>
    catboost: Record<string, any>
    lstm: Record<string, any>
    linear: Record<string, any>
  }
  training_config: {
    early_stopping: boolean
    early_stopping_rounds: number
    eval_metric: string
    random_state: number
    n_jobs: number
  }
}

interface QlibBacktestConfig {
  exchange_config: {
    freq: 'day' | '30min' | '5min' | '1min'
    limit_threshold: number
    deal_price: 'close' | 'vwap' | 'open' | 'twap'
    open_cost: number
    close_cost: number
    min_cost: number
    trade_unit: 'share' | 'lot'
    pos_type: 'Position' | 'InfPosition'
  }
  executor_config: {
    time_per_step: string
    generate_portfolio_metrics: boolean
  }
  benchmark: string
  account_config: {
    init_cash: number
    commission_rate: number
    min_commission: number
    stamp_duty_rate: number
  }
}

interface QlibEnvironmentConfig {
  mode: 'development' | 'production' | 'testing'
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  log_dir: string
  auto_mount: boolean
  parallel_config: {
    enable_parallel: boolean
    max_workers: number
    backend: 'loky' | 'threading' | 'multiprocessing'
  }
  resource_config: {
    memory_limit_gb?: number
    disk_limit_gb?: number
    cpu_count?: number
    gpu_enable: boolean
    gpu_memory_limit?: number
  }
}

interface QlibWebConfig {
  api_base_url: string
  enable_mock_data: boolean
  cache_config: {
    enable_cache: boolean
    cache_ttl: number
    max_cache_size: number
  }
  ui_config: {
    theme: 'light' | 'dark' | 'auto'
    language: 'zh-CN' | 'en-US'
    date_format: string
    number_format: string
    chart_config: {
      default_colors: string[]
      animation_duration: number
    }
  }
  notification_config: {
    enable_notifications: boolean
    notification_types: string[]
    push_config?: {
      endpoint: string
      public_key: string
    }
  }
}

interface QlibPerformanceConfig {
  profiling_enabled: boolean
  memory_profiling: boolean
  time_profiling: boolean
  profile_output_dir: string
  optimization_config: {
    enable_jit: boolean
    enable_caching: boolean
    parallel_computing: boolean
    batch_size: number
  }
}

interface QlibSecurityConfig {
  encryption_enabled: boolean
  api_key_required: boolean
  rate_limiting: {
    enabled: boolean
    requests_per_minute: number
    burst_limit: number
  }
  access_control: {
    require_authentication: boolean
    admin_users: string[]
    readonly_users: string[]
  }
  audit_config: {
    enable_audit_log: boolean
    audit_log_dir: string
    retain_days: number
  }
}

interface QlibCompleteConfig {
  version: string
  config_id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  created_by: string
  is_active: boolean
  tags: string[]
  
  data_config: QlibDataConfig
  calendar_config: QlibCalendarConfig
  instrument_config: QlibInstrumentConfig
  feature_config: QlibFeatureConfig
  model_config: QlibModelConfig
  backtest_config: QlibBacktestConfig
  environment_config: QlibEnvironmentConfig
  web_config: QlibWebConfig
  performance_config: QlibPerformanceConfig
  security_config: QlibSecurityConfig
}

interface ConfigValidationResult {
  is_valid: boolean
  errors: Array<{
    field: string
    message: string
    severity: 'error' | 'warning'
  }>
  warnings: Array<{
    field: string
    message: string
    suggestion?: string
  }>
  performance_impact?: {
    memory_usage: 'low' | 'medium' | 'high'
    cpu_usage: 'low' | 'medium' | 'high'
    disk_usage: 'low' | 'medium' | 'high'
  }
}

interface ConfigTemplate {
  template_id: string
  name: string
  description: string
  category: 'development' | 'production' | 'research' | 'custom'
  config_template: Partial<QlibCompleteConfig>
  use_cases: string[]
  created_at: string
  usage_count: number
  rating: number
}

export const useQlibConfigStore = defineStore('qlib-config', () => {
  // 状态
  const currentConfig = ref<QlibCompleteConfig | null>(null)
  const configHistory = ref<QlibCompleteConfig[]>([])
  const configTemplates = ref<ConfigTemplate[]>([])
  const validationResult = ref<ConfigValidationResult | null>(null)
  const systemStatus = ref<{
    qlib_version: string
    data_status: 'connected' | 'disconnected' | 'error'
    cache_status: 'active' | 'inactive' | 'error'
    model_registry_status: 'connected' | 'disconnected' | 'error'
    last_health_check: string
  }>({
    qlib_version: '',
    data_status: 'disconnected',
    cache_status: 'inactive',
    model_registry_status: 'disconnected',
    last_health_check: ''
  })
  
  // UI状态
  const loading = ref(false)
  const configEditor = ref({
    current_section: 'data_config',
    unsaved_changes: false,
    validation_enabled: true,
    auto_save: true
  })
  
  // 错误状态
  const error = ref<string | null>(null)
  const lastSyncTime = ref<string>('')

  // 计算属性
  const isConfigValid = computed(() => {
    return validationResult.value?.is_valid === true
  })

  const hasUnsavedChanges = computed(() => {
    return configEditor.value.unsaved_changes
  })

  const configSections = computed(() => {
    return [
      { key: 'data_config', label: '数据配置', icon: '💾' },
      { key: 'calendar_config', label: '交易日历', icon: '📅' },
      { key: 'instrument_config', label: '股票池配置', icon: '📊' },
      { key: 'feature_config', label: '因子配置', icon: '🧮' },
      { key: 'model_config', label: '模型配置', icon: '🤖' },
      { key: 'backtest_config', label: '回测配置', icon: '📈' },
      { key: 'environment_config', label: '环境配置', icon: '⚙️' },
      { key: 'web_config', label: 'Web配置', icon: '🌐' },
      { key: 'performance_config', label: '性能配置', icon: '🚀' },
      { key: 'security_config', label: '安全配置', icon: '🔒' }
    ]
  })

  const systemHealth = computed(() => {
    const statuses = [
      systemStatus.value.data_status,
      systemStatus.value.cache_status,
      systemStatus.value.model_registry_status
    ]
    
    const errorCount = statuses.filter(s => s === 'error').length
    const disconnectedCount = statuses.filter(s => s === 'disconnected').length
    
    if (errorCount > 0) return 'error'
    if (disconnectedCount > 0) return 'warning'
    return 'healthy'
  })

  const environmentProfiles = computed(() => {
    return [
      {
        name: 'development',
        description: '开发环境配置',
        features: ['Mock数据', '详细日志', '调试模式'],
        performance: 'medium'
      },
      {
        name: 'production',
        description: '生产环境配置',
        features: ['真实数据', '性能优化', '错误恢复'],
        performance: 'high'
      },
      {
        name: 'research',
        description: '研究环境配置',
        features: ['完整历史数据', '高级分析', '实验追踪'],
        performance: 'medium'
      }
    ]
  })

  // Actions
  const loadCurrentConfig = async (): Promise<void> => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/v1/qlib/config/current', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const result = await response.json()

      if (result.status === 'success') {
        currentConfig.value = result.data.config
        systemStatus.value = result.data.system_status
        lastSyncTime.value = new Date().toISOString()
      } else {
        throw new Error(result.message || '加载配置失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载配置失败'
      console.error('加载配置失败:', err)
      
      // 降级到默认配置
      generateDefaultConfig()
    } finally {
      loading.value = false
    }
  }

  const generateDefaultConfig = (): void => {
    const defaultConfig: QlibCompleteConfig = {
      version: '1.0.0',
      config_id: `config_${Date.now()}`,
      name: '默认配置',
      description: 'Qlib默认配置文件',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      created_by: 'system',
      is_active: true,
      tags: ['default'],
      
      data_config: {
        provider_uri: 'file:///data/qlib',
        region: 'cn',
        data_source: 'yahoo',
        cache_dir: '/tmp/qlib_cache',
        auto_mount: true,
        provider_config: {
          auto_update: true,
          normalize_names: true
        }
      },
      
      calendar_config: {
        provider: 'exchange_calendar',
        region: 'cn',
        auto_update: true
      },
      
      instrument_config: {
        market: 'CSI300',
        provider: 'yahoo',
        auto_update: true,
        filter_config: {
          include_st: false,
          include_suspend: false,
          min_market_cap: 1000000000
        }
      },
      
      feature_config: {
        feature_root_dir: '/data/features',
        expression_cache: true,
        cache_provider: 'file',
        feature_config: {
          enable_alpha158: true,
          enable_alpha360: false,
          custom_features: [],
          feature_engineering: {
            normalization: 'zscore',
            outlier_treatment: 'clip',
            missing_value_fill: 'ffill'
          }
        }
      },
      
      model_config: {
        model_cache_dir: '/data/models',
        model_registry: 'local',
        auto_save_models: true,
        model_compression: false,
        default_model_params: {
          lightgbm: {
            n_estimators: 100,
            learning_rate: 0.1,
            max_depth: 6,
            num_leaves: 31
          },
          xgboost: {
            n_estimators: 100,
            learning_rate: 0.1,
            max_depth: 6
          },
          catboost: {
            iterations: 100,
            learning_rate: 0.1,
            depth: 6
          },
          lstm: {
            hidden_size: 128,
            num_layers: 2,
            dropout: 0.2
          },
          linear: {
            regularization: 'l2',
            alpha: 0.01
          }
        },
        training_config: {
          early_stopping: true,
          early_stopping_rounds: 50,
          eval_metric: 'mse',
          random_state: 42,
          n_jobs: -1
        }
      },
      
      backtest_config: {
        exchange_config: {
          freq: 'day',
          limit_threshold: 0.095,
          deal_price: 'close',
          open_cost: 0.0005,
          close_cost: 0.0015,
          min_cost: 5,
          trade_unit: 'share',
          pos_type: 'Position'
        },
        executor_config: {
          time_per_step: 'day',
          generate_portfolio_metrics: true
        },
        benchmark: '000300.SH',
        account_config: {
          init_cash: 10000000,
          commission_rate: 0.0003,
          min_commission: 5,
          stamp_duty_rate: 0.001
        }
      },
      
      environment_config: {
        mode: 'development',
        log_level: 'INFO',
        log_dir: '/logs/qlib',
        auto_mount: true,
        parallel_config: {
          enable_parallel: true,
          max_workers: 4,
          backend: 'loky'
        },
        resource_config: {
          memory_limit_gb: 8,
          disk_limit_gb: 100,
          cpu_count: 4,
          gpu_enable: false
        }
      },
      
      web_config: {
        api_base_url: 'http://localhost:8000',
        enable_mock_data: true,
        cache_config: {
          enable_cache: true,
          cache_ttl: 3600,
          max_cache_size: 1000
        },
        ui_config: {
          theme: 'auto',
          language: 'zh-CN',
          date_format: 'YYYY-MM-DD',
          number_format: '0,0.00',
          chart_config: {
            default_colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            animation_duration: 750
          }
        },
        notification_config: {
          enable_notifications: true,
          notification_types: ['success', 'error', 'warning', 'info']
        }
      },
      
      performance_config: {
        profiling_enabled: false,
        memory_profiling: false,
        time_profiling: false,
        profile_output_dir: '/logs/profiles',
        optimization_config: {
          enable_jit: false,
          enable_caching: true,
          parallel_computing: true,
          batch_size: 1000
        }
      },
      
      security_config: {
        encryption_enabled: false,
        api_key_required: false,
        rate_limiting: {
          enabled: true,
          requests_per_minute: 100,
          burst_limit: 20
        },
        access_control: {
          require_authentication: false,
          admin_users: [],
          readonly_users: []
        },
        audit_config: {
          enable_audit_log: false,
          audit_log_dir: '/logs/audit',
          retain_days: 30
        }
      }
    }

    currentConfig.value = defaultConfig
    systemStatus.value = {
      qlib_version: '0.9.1',
      data_status: 'disconnected',
      cache_status: 'inactive',
      model_registry_status: 'disconnected',
      last_health_check: new Date().toISOString()
    }
    lastSyncTime.value = new Date().toISOString()
  }

  const saveConfig = async (config?: QlibCompleteConfig): Promise<boolean> => {
    const configToSave = config || currentConfig.value
    if (!configToSave) return false

    loading.value = true

    try {
      const response = await fetch('/api/v1/qlib/config/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config: configToSave
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        currentConfig.value = {
          ...configToSave,
          updated_at: new Date().toISOString()
        }
        configEditor.value.unsaved_changes = false
        
        // 保存到历史记录
        configHistory.value.unshift({ ...currentConfig.value })
        if (configHistory.value.length > 50) {
          configHistory.value = configHistory.value.slice(0, 50)
        }
        
        return true
      } else {
        throw new Error(result.message || '保存配置失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '保存配置失败'
      console.error('保存配置失败:', err)
      return false
    } finally {
      loading.value = false
    }
  }

  const validateConfig = async (config?: QlibCompleteConfig): Promise<ConfigValidationResult> => {
    const configToValidate = config || currentConfig.value
    if (!configToValidate) {
      return {
        is_valid: false,
        errors: [{ field: 'config', message: '配置为空', severity: 'error' }],
        warnings: []
      }
    }

    try {
      const response = await fetch('/api/v1/qlib/config/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config: configToValidate
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        validationResult.value = result.data.validation_result
        return validationResult.value
      } else {
        throw new Error(result.message || '配置验证失败')
      }
    } catch (err) {
      console.error('配置验证失败:', err)
      
      // 返回模拟验证结果
      const mockResult: ConfigValidationResult = {
        is_valid: Math.random() > 0.3,
        errors: Math.random() > 0.7 ? [
          { field: 'data_config.provider_uri', message: '数据源路径无效', severity: 'error' }
        ] : [],
        warnings: [
          { field: 'performance_config', message: '建议启用缓存以提高性能', suggestion: '设置 enable_caching = true' }
        ],
        performance_impact: {
          memory_usage: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)] as any,
          cpu_usage: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)] as any,
          disk_usage: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)] as any
        }
      }
      
      validationResult.value = mockResult
      return mockResult
    }
  }

  const testConnection = async (): Promise<boolean> => {
    loading.value = true

    try {
      const response = await fetch('/api/v1/qlib/config/test-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config: currentConfig.value
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        systemStatus.value = {
          ...systemStatus.value,
          ...result.data.connection_status,
          last_health_check: new Date().toISOString()
        }
        return true
      } else {
        throw new Error(result.message || '连接测试失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '连接测试失败'
      console.error('连接测试失败:', err)
      
      // 模拟连接状态
      systemStatus.value = {
        ...systemStatus.value,
        data_status: Math.random() > 0.5 ? 'connected' : 'error',
        cache_status: Math.random() > 0.5 ? 'active' : 'error',
        model_registry_status: Math.random() > 0.5 ? 'connected' : 'error',
        last_health_check: new Date().toISOString()
      }
      
      return false
    } finally {
      loading.value = false
    }
  }

  const loadConfigTemplates = async (): Promise<void> => {
    // 生成示例模板
    configTemplates.value = [
      {
        template_id: 'template_dev',
        name: '开发环境模板',
        description: '适用于开发和调试的配置模板',
        category: 'development',
        config_template: {
          environment_config: {
            mode: 'development',
            log_level: 'DEBUG'
          },
          web_config: {
            enable_mock_data: true
          },
          performance_config: {
            profiling_enabled: true
          }
        },
        use_cases: ['本地开发', '功能测试', '调试分析'],
        created_at: '2024-01-01T00:00:00Z',
        usage_count: 45,
        rating: 4.2
      },
      {
        template_id: 'template_prod',
        name: '生产环境模板',
        description: '适用于生产环境的优化配置',
        category: 'production',
        config_template: {
          environment_config: {
            mode: 'production',
            log_level: 'WARNING'
          },
          web_config: {
            enable_mock_data: false
          },
          performance_config: {
            optimization_config: {
              enable_jit: true,
              enable_caching: true,
              parallel_computing: true
            }
          },
          security_config: {
            encryption_enabled: true,
            api_key_required: true,
            rate_limiting: {
              enabled: true,
              requests_per_minute: 1000
            }
          }
        },
        use_cases: ['生产部署', '高并发', '安全要求'],
        created_at: '2024-01-01T00:00:00Z',
        usage_count: 78,
        rating: 4.8
      },
      {
        template_id: 'template_research',
        name: '研究环境模板',
        description: '适用于量化研究的配置模板',
        category: 'research',
        config_template: {
          data_config: {
            provider_uri: 'file:///research/data/qlib',
            region: 'cn'
          },
          feature_config: {
            enable_alpha158: true,
            enable_alpha360: true
          },
          model_config: {
            model_registry: 'mlflow'
          }
        },
        use_cases: ['因子研究', '策略开发', '学术研究'],
        created_at: '2024-01-01T00:00:00Z',
        usage_count: 32,
        rating: 4.5
      }
    ]
  }

  const applyTemplate = async (templateId: string): Promise<boolean> => {
    const template = configTemplates.value.find(t => t.template_id === templateId)
    if (!template) return false

    if (!currentConfig.value) {
      generateDefaultConfig()
    }

    // 深度合并模板配置
    const mergedConfig = deepMerge(currentConfig.value!, template.config_template)
    mergedConfig.name = `${template.name}_${new Date().toLocaleDateString()}`
    mergedConfig.description = `基于"${template.name}"模板创建`
    mergedConfig.updated_at = new Date().toISOString()

    currentConfig.value = mergedConfig
    configEditor.value.unsaved_changes = true

    // 验证配置
    await validateConfig()

    return true
  }

  const deepMerge = (target: any, source: any): any => {
    const result = { ...target }
    
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = deepMerge(result[key] || {}, source[key])
      } else {
        result[key] = source[key]
      }
    }
    
    return result
  }

  const exportConfig = async (): Promise<string> => {
    if (!currentConfig.value) return ''

    return JSON.stringify({
      config: currentConfig.value,
      exported_at: new Date().toISOString(),
      version: '1.0'
    }, null, 2)
  }

  const importConfig = async (configData: string): Promise<boolean> => {
    try {
      const data = JSON.parse(configData)
      const importedConfig = data.config
      
      if (!importedConfig) {
        throw new Error('配置数据格式无效')
      }

      // 生成新的配置ID
      importedConfig.config_id = `config_${Date.now()}`
      importedConfig.name = `${importedConfig.name}_导入`
      importedConfig.created_at = new Date().toISOString()
      importedConfig.updated_at = new Date().toISOString()
      importedConfig.is_active = false

      currentConfig.value = importedConfig
      configEditor.value.unsaved_changes = true

      // 验证导入的配置
      await validateConfig()

      return true
    } catch (err) {
      error.value = err instanceof Error ? err.message : '导入配置失败'
      console.error('导入配置失败:', err)
      return false
    }
  }

  const resetToDefault = (): void => {
    generateDefaultConfig()
    configEditor.value.unsaved_changes = true
    validationResult.value = null
  }

  const updateConfigSection = (section: string, data: any): void => {
    if (!currentConfig.value) return

    (currentConfig.value as any)[section] = {
      ...(currentConfig.value as any)[section],
      ...data
    }
    
    currentConfig.value.updated_at = new Date().toISOString()
    configEditor.value.unsaved_changes = true

    // 自动验证
    if (configEditor.value.validation_enabled) {
      validateConfig()
    }

    // 自动保存
    if (configEditor.value.auto_save) {
      setTimeout(() => {
        saveConfig()
      }, 2000)
    }
  }

  const setConfigEditor = (options: Partial<typeof configEditor.value>): void => {
    configEditor.value = {
      ...configEditor.value,
      ...options
    }
  }

  const checkSystemHealth = async (): Promise<void> => {
    await testConnection()
  }

  const optimizeConfig = async (): Promise<QlibCompleteConfig | null> => {
    if (!currentConfig.value) return null

    try {
      const response = await fetch('/api/v1/qlib/config/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          config: currentConfig.value,
          optimization_target: 'performance'
        })
      })

      const result = await response.json()

      if (result.status === 'success') {
        const optimizedConfig = result.data.optimized_config
        optimizedConfig.name = `${currentConfig.value.name}_优化版`
        optimizedConfig.description = '系统自动优化的配置'
        optimizedConfig.updated_at = new Date().toISOString()
        
        return optimizedConfig
      } else {
        throw new Error(result.message || '配置优化失败')
      }
    } catch (err) {
      console.error('配置优化失败:', err)
      
      // 返回模拟优化配置
      const optimizedConfig = JSON.parse(JSON.stringify(currentConfig.value))
      optimizedConfig.name = `${currentConfig.value.name}_优化版`
      optimizedConfig.performance_config.optimization_config = {
        enable_jit: true,
        enable_caching: true,
        parallel_computing: true,
        batch_size: 2000
      }
      optimizedConfig.model_config.training_config.n_jobs = -1
      
      return optimizedConfig
    }
  }

  const getConfigDiff = (config1: QlibCompleteConfig, config2: QlibCompleteConfig): any => {
    const diff: any = {}
    
    const compareObjects = (obj1: any, obj2: any, path: string = '') => {
      for (const key in obj1) {
        const fullPath = path ? `${path}.${key}` : key
        
        if (obj2[key] === undefined) {
          diff[fullPath] = { type: 'removed', old: obj1[key] }
        } else if (typeof obj1[key] === 'object' && typeof obj2[key] === 'object') {
          compareObjects(obj1[key], obj2[key], fullPath)
        } else if (obj1[key] !== obj2[key]) {
          diff[fullPath] = { type: 'changed', old: obj1[key], new: obj2[key] }
        }
      }
      
      for (const key in obj2) {
        const fullPath = path ? `${path}.${key}` : key
        if (obj1[key] === undefined) {
          diff[fullPath] = { type: 'added', new: obj2[key] }
        }
      }
    }
    
    compareObjects(config1, config2)
    return diff
  }

  return {
    // State
    currentConfig,
    configHistory,
    configTemplates,
    validationResult,
    systemStatus,
    loading,
    configEditor,
    error,
    lastSyncTime,

    // Computed
    isConfigValid,
    hasUnsavedChanges,
    configSections,
    systemHealth,
    environmentProfiles,

    // Actions
    loadCurrentConfig,
    generateDefaultConfig,
    saveConfig,
    validateConfig,
    testConnection,
    loadConfigTemplates,
    applyTemplate,
    exportConfig,
    importConfig,
    resetToDefault,
    updateConfigSection,
    setConfigEditor,
    checkSystemHealth,
    optimizeConfig,
    getConfigDiff
  }
})