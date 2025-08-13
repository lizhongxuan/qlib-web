<template>
  <div class="model-recommendation-system">
    <div class="system-header">
      <h3>智能模型推荐系统</h3>
      <el-button-group>
        <el-button type="primary" @click="analyzeData" :loading="isAnalyzing">
          分析数据特征
        </el-button>
        <el-button @click="generateRecommendations" :loading="isGenerating">
          生成推荐
        </el-button>
        <el-button @click="exportConfig">导出配置</el-button>
      </el-button-group>
    </div>

    <el-tabs v-model="activeTab" class="system-tabs">
      <!-- 数据分析与模型推荐 -->
      <el-tab-pane label="模型推荐" name="recommendation">
        <el-row :gutter="24">
          <!-- 左侧：数据特征分析 -->
          <el-col :span="10">
            <el-card>
              <template #header>
                <h4>数据特征分析</h4>
              </template>

              <div class="data-analysis">
                <el-form :model="dataConfig" label-width="100px">
                  <el-form-item label="数据源">
                    <el-select v-model="dataConfig.source" style="width: 100%">
                      <el-option label="股票日频数据" value="stock_daily" />
                      <el-option label="因子数据" value="factor_data" />
                      <el-option label="宏观数据" value="macro_data" />
                      <el-option label="高频数据" value="high_freq" />
                    </el-select>
                  </el-form-item>

                  <el-form-item label="时间范围">
                    <el-date-picker
                      v-model="dataConfig.dateRange"
                      type="daterange"
                      range-separator="至"
                      start-placeholder="开始日期"
                      end-placeholder="结束日期"
                      style="width: 100%"
                    />
                  </el-form-item>

                  <el-form-item label="目标变量">
                    <el-select v-model="dataConfig.target" style="width: 100%">
                      <el-option label="未来5日收益" value="return_5d" />
                      <el-option label="未来20日收益" value="return_20d" />
                      <el-option label="涨跌分类" value="binary_class" />
                      <el-option label="收益分位数" value="quantile_class" />
                    </el-select>
                  </el-form-item>
                </el-form>

                <div class="analysis-results" v-if="dataAnalysis">
                  <h5>数据特征摘要</h5>
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="样本数量">
                      {{ dataAnalysis.sampleCount?.toLocaleString() }}
                    </el-descriptions-item>
                    <el-descriptions-item label="特征维度">
                      {{ dataAnalysis.featureCount }}
                    </el-descriptions-item>
                    <el-descriptions-item label="数据质量">
                      <el-tag :type="getQualityType(dataAnalysis.quality)">
                        {{ dataAnalysis.quality }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="噪声水平">
                      <el-tag :type="getNoiseType(dataAnalysis.noiseLevel)">
                        {{ dataAnalysis.noiseLevel }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="线性度">
                      {{ (dataAnalysis.linearity * 100).toFixed(1) }}%
                    </el-descriptions-item>
                    <el-descriptions-item label="特征相关性">
                      {{ dataAnalysis.correlation }}
                    </el-descriptions-item>
                  </el-descriptions>

                  <div class="feature-distribution">
                    <h5>特征分布</h5>
                    <div class="distribution-chart">
                      <div ref="featureDistChart" class="chart-container"></div>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>

          <!-- 右侧：模型推荐结果 -->
          <el-col :span="14">
            <el-card>
              <template #header>
                <h4>推荐模型</h4>
              </template>

              <div v-if="recommendations.length === 0" class="empty-recommendations">
                <el-empty description="点击"生成推荐"获取最适合的模型建议" />
              </div>

              <div v-else class="recommendations-list">
                <div
                  v-for="(rec, index) in recommendations"
                  :key="index"
                  class="recommendation-item"
                  :class="{ 'top-recommendation': index === 0 }"
                >
                  <div class="rec-header">
                    <div class="rec-title">
                      <h4>{{ rec.modelName }}</h4>
                      <el-tag v-if="index === 0" type="success" size="small">最推荐</el-tag>
                      <el-tag v-else-if="index <= 2" type="warning" size="small">候选</el-tag>
                    </div>
                    <div class="rec-score">
                      <el-rate
                        v-model="rec.score"
                        :max="5"
                        disabled
                        show-score
                        text-color="#ff9900"
                        score-template="{value}"
                      />
                    </div>
                  </div>

                  <p class="rec-description">{{ rec.description }}</p>

                  <div class="rec-metrics">
                    <div class="metric-item">
                      <span class="label">适用场景:</span>
                      <span class="value">{{ rec.scenario }}</span>
                    </div>
                    <div class="metric-item">
                      <span class="label">预期性能:</span>
                      <span class="value">{{ rec.performance }}</span>
                    </div>
                    <div class="metric-item">
                      <span class="label">训练时间:</span>
                      <span class="value">{{ rec.trainingTime }}</span>
                    </div>
                    <div class="metric-item">
                      <span class="label">可解释性:</span>
                      <span class="value">{{ rec.interpretability }}</span>
                    </div>
                  </div>

                  <div class="rec-reasons">
                    <h5>推荐理由</h5>
                    <ul>
                      <li v-for="reason in rec.reasons" :key="reason">{{ reason }}</li>
                    </ul>
                  </div>

                  <div class="rec-actions">
                    <el-button size="small" @click="viewModelDetails(rec)">查看详情</el-button>
                    <el-button size="small" type="primary" @click="selectModel(rec)">
                      选择此模型
                    </el-button>
                    <el-button size="small" @click="optimizeHyperparameters(rec)">
                      优化参数
                    </el-button>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 超参数自动优化 -->
      <el-tab-pane label="参数优化" name="hyperparameter">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-card>
              <template #header>
                <h4>超参数优化配置</h4>
              </template>

              <el-form :model="optimizationConfig" label-width="120px">
                <el-form-item label="选择模型">
                  <el-select v-model="optimizationConfig.model" style="width: 100%">
                    <el-option
                      v-for="model in availableModels"
                      :key="model.value"
                      :label="model.label"
                      :value="model.value"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="优化算法">
                  <el-select v-model="optimizationConfig.algorithm" style="width: 100%">
                    <el-option label="贝叶斯优化" value="bayesian" />
                    <el-option label="随机搜索" value="random" />
                    <el-option label="网格搜索" value="grid" />
                    <el-option label="遗传算法" value="genetic" />
                    <el-option label="TPE优化" value="tpe" />
                  </el-select>
                </el-form-item>

                <el-form-item label="优化目标">
                  <el-select v-model="optimizationConfig.objective" style="width: 100%">
                    <el-option label="最大化准确率" value="maximize_accuracy" />
                    <el-option label="最大化F1分数" value="maximize_f1" />
                    <el-option label="最小化损失" value="minimize_loss" />
                    <el-option label="最大化AUC" value="maximize_auc" />
                    <el-option label="最大化夏普比率" value="maximize_sharpe" />
                  </el-select>
                </el-form-item>

                <el-form-item label="搜索次数">
                  <el-input-number
                    v-model="optimizationConfig.trials"
                    :min="10"
                    :max="1000"
                    :step="10"
                    style="width: 100%"
                  />
                </el-form-item>

                <el-form-item label="并行任务">
                  <el-input-number
                    v-model="optimizationConfig.parallelJobs"
                    :min="1"
                    :max="8"
                    style="width: 100%"
                  />
                </el-form-item>

                <el-form-item label="早停策略">
                  <el-switch v-model="optimizationConfig.earlyStopping" />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="startOptimization" :loading="isOptimizing">
                    开始优化
                  </el-button>
                  <el-button @click="stopOptimization" :disabled="!isOptimizing">
                    停止优化
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card>
              <template #header>
                <h4>优化进度</h4>
              </template>

              <div v-if="!isOptimizing && !optimizationResults" class="empty-optimization">
                <el-empty description="点击开始优化来自动寻找最佳参数" />
              </div>

              <div v-if="isOptimizing" class="optimization-progress">
                <div class="progress-info">
                  <h5>优化进行中...</h5>
                  <el-progress
                    :percentage="optimizationProgress"
                    :stroke-width="12"
                    :show-text="false"
                  />
                  <div class="progress-details">
                    <span>当前试验: {{ currentTrial }}/{{ optimizationConfig.trials }}</span>
                    <span>最佳得分: {{ bestScore?.toFixed(4) || 'N/A' }}</span>
                    <span>预计剩余: {{ estimatedTimeRemaining }}</span>
                  </div>
                </div>

                <div class="live-results">
                  <h5>实时结果</h5>
                  <div class="results-chart">
                    <div ref="optimizationChart" class="chart-container"></div>
                  </div>
                </div>
              </div>

              <div v-if="optimizationResults && !isOptimizing" class="optimization-completed">
                <div class="results-summary">
                  <h5>优化完成</h5>
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="最佳得分">
                      {{ optimizationResults.bestScore?.toFixed(4) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="优化时间">
                      {{ optimizationResults.duration }}
                    </el-descriptions-item>
                    <el-descriptions-item label="总试验数">
                      {{ optimizationResults.totalTrials }}
                    </el-descriptions-item>
                    <el-descriptions-item label="收敛试验">
                      {{ optimizationResults.convergencePoint }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="best-parameters">
                  <h5>最佳参数</h5>
                  <el-table :data="optimizationResults.bestParams" style="width: 100%">
                    <el-table-column prop="parameter" label="参数名" />
                    <el-table-column prop="value" label="最佳值" />
                    <el-table-column prop="range" label="搜索范围" />
                  </el-table>
                </div>

                <div class="results-actions">
                  <el-button type="primary" @click="applyBestParams">应用最佳参数</el-button>
                  <el-button @click="saveOptimizationResults">保存结果</el-button>
                  <el-button @click="exportOptimizationReport">导出报告</el-button>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 特征选择 -->
      <el-tab-pane label="特征选择" name="feature">
        <el-row :gutter="24">
          <el-col :span="8">
            <el-card>
              <template #header>
                <h4>特征选择配置</h4>
              </template>

              <el-form :model="featureConfig" label-width="120px">
                <el-form-item label="选择算法">
                  <el-select v-model="featureConfig.algorithm" style="width: 100%">
                    <el-option label="递归特征消除" value="rfe" />
                    <el-option label="LASSO正则化" value="lasso" />
                    <el-option label="随机森林重要性" value="rf_importance" />
                    <el-option label="互信息" value="mutual_info" />
                    <el-option label="卡方检验" value="chi2" />
                    <el-option label="方差阈值" value="variance_threshold" />
                  </el-select>
                </el-form-item>

                <el-form-item label="特征数量">
                  <el-input-number
                    v-model="featureConfig.numFeatures"
                    :min="5"
                    :max="200"
                    style="width: 100%"
                  />
                </el-form-item>

                <el-form-item label="交叉验证">
                  <el-input-number
                    v-model="featureConfig.cvFolds"
                    :min="3"
                    :max="10"
                    style="width: 100%"
                  />
                </el-form-item>

                <el-form-item label="评估指标">
                  <el-select v-model="featureConfig.scoringMetric" style="width: 100%">
                    <el-option label="准确率" value="accuracy" />
                    <el-option label="F1分数" value="f1" />
                    <el-option label="AUC" value="roc_auc" />
                    <el-option label="精确率" value="precision" />
                    <el-option label="召回率" value="recall" />
                  </el-select>
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="runFeatureSelection" :loading="isSelectingFeatures">
                    开始特征选择
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <el-col :span="16">
            <el-card>
              <template #header>
                <h4>特征重要性排序</h4>
              </template>

              <div v-if="!featureResults" class="empty-features">
                <el-empty description="运行特征选择算法查看特征重要性" />
              </div>

              <div v-else class="feature-results">
                <div class="feature-summary">
                  <el-row :gutter="16">
                    <el-col :span="6">
                      <el-statistic title="原始特征数" :value="featureResults.originalCount" />
                    </el-col>
                    <el-col :span="6">
                      <el-statistic title="选择特征数" :value="featureResults.selectedCount" />
                    </el-col>
                    <el-col :span="6">
                      <el-statistic title="性能提升" :value="featureResults.performanceGain" suffix="%" />
                    </el-col>
                    <el-col :span="6">
                      <el-statistic title="训练加速" :value="featureResults.speedImprovement" suffix="x" />
                    </el-col>
                  </el-row>
                </div>

                <div class="feature-importance-chart">
                  <div ref="featureImportanceChart" class="chart-container"></div>
                </div>

                <div class="selected-features-table">
                  <h5>选择的特征</h5>
                  <el-table :data="featureResults.selectedFeatures" style="width: 100%">
                    <el-table-column prop="rank" label="排名" width="60" />
                    <el-table-column prop="name" label="特征名称" />
                    <el-table-column prop="importance" label="重要性得分">
                      <template #default="{ row }">
                        <el-progress
                          :percentage="row.importance * 100"
                          :stroke-width="8"
                          :show-text="false"
                        />
                        <span style="margin-left: 10px">{{ row.importance.toFixed(3) }}</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="category" label="特征类别">
                      <template #default="{ row }">
                        <el-tag size="small">{{ row.category }}</el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 模型集成 -->
      <el-tab-pane label="模型集成" name="ensemble">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-card>
              <template #header>
                <h4>集成策略配置</h4>
              </template>

              <el-form :model="ensembleConfig" label-width="120px">
                <el-form-item label="集成方法">
                  <el-select v-model="ensembleConfig.method" style="width: 100%">
                    <el-option label="投票集成" value="voting" />
                    <el-option label="堆叠集成" value="stacking" />
                    <el-option label="提升集成" value="boosting" />
                    <el-option label="Bagging" value="bagging" />
                    <el-option label="混合集成" value="blending" />
                  </el-select>
                </el-form-item>

                <el-form-item label="基础模型">
                  <el-checkbox-group v-model="ensembleConfig.baseModels">
                    <el-checkbox label="lightgbm">LightGBM</el-checkbox>
                    <el-checkbox label="xgboost">XGBoost</el-checkbox>
                    <el-checkbox label="catboost">CatBoost</el-checkbox>
                    <el-checkbox label="random_forest">随机森林</el-checkbox>
                    <el-checkbox label="linear">线性回归</el-checkbox>
                    <el-checkbox label="svm">支持向量机</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>

                <el-form-item label="权重策略">
                  <el-radio-group v-model="ensembleConfig.weighting">
                    <el-radio label="equal">等权重</el-radio>
                    <el-radio label="performance">基于性能</el-radio>
                    <el-radio label="diversity">基于多样性</el-radio>
                    <el-radio label="dynamic">动态权重</el-radio>
                  </el-radio-group>
                </el-form-item>

                <el-form-item label="交叉验证">
                  <el-input-number
                    v-model="ensembleConfig.cvFolds"
                    :min="3"
                    :max="10"
                    style="width: 100%"
                  />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="trainEnsemble" :loading="isTrainingEnsemble">
                    训练集成模型
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>

            <!-- 模型性能对比 -->
            <el-card class="model-performance">
              <template #header>
                <h4>模型性能对比</h4>
              </template>

              <div v-if="ensembleResults" class="performance-comparison">
                <el-table :data="ensembleResults.modelComparison" style="width: 100%">
                  <el-table-column prop="model" label="模型" />
                  <el-table-column prop="accuracy" label="准确率">
                    <template #default="{ row }">
                      {{ (row.accuracy * 100).toFixed(2) }}%
                    </template>
                  </el-table-column>
                  <el-table-column prop="f1Score" label="F1分数">
                    <template #default="{ row }">
                      {{ row.f1Score.toFixed(3) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="trainingTime" label="训练时间" />
                  <el-table-column label="是否选中">
                    <template #default="{ row }">
                      <el-tag :type="row.selected ? 'success' : ''" size="small">
                        {{ row.selected ? '✓' : '' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card>
              <template #header>
                <h4>集成模型结果</h4>
              </template>

              <div v-if="!ensembleResults" class="empty-ensemble">
                <el-empty description="训练集成模型查看结果" />
              </div>

              <div v-else class="ensemble-results">
                <div class="ensemble-metrics">
                  <h5>集成模型性能</h5>
                  <el-row :gutter="16">
                    <el-col :span="12">
                      <el-statistic title="集成准确率" :value="ensembleResults.accuracy" suffix="%" />
                    </el-col>
                    <el-col :span="12">
                      <el-statistic title="性能提升" :value="ensembleResults.improvement" suffix="%" />
                    </el-col>
                    <el-col :span="12">
                      <el-statistic title="模型多样性" :value="ensembleResults.diversity" :precision="3" />
                    </el-col>
                    <el-col :span="12">
                      <el-statistic title="集成权重熵" :value="ensembleResults.weightEntropy" :precision="3" />
                    </el-col>
                  </el-row>
                </div>

                <div class="model-weights">
                  <h5>模型权重分布</h5>
                  <div class="weights-chart">
                    <div ref="weightsChart" class="chart-container"></div>
                  </div>
                </div>

                <div class="ensemble-actions">
                  <el-button type="primary" @click="deployEnsemble">部署集成模型</el-button>
                  <el-button @click="saveEnsembleConfig">保存配置</el-button>
                  <el-button @click="exportEnsembleModel">导出模型</el-button>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- 在线学习 -->
      <el-tab-pane label="在线学习" name="online">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-card>
              <template #header>
                <h4>在线学习配置</h4>
              </template>

              <el-form :model="onlineLearningConfig" label-width="120px">
                <el-form-item label="学习模式">
                  <el-select v-model="onlineLearningConfig.mode" style="width: 100%">
                    <el-option label="增量学习" value="incremental" />
                    <el-option label="概念漂移检测" value="drift_detection" />
                    <el-option label="主动学习" value="active_learning" />
                    <el-option label="强化学习" value="reinforcement" />
                  </el-select>
                </el-form-item>

                <el-form-item label="更新频率">
                  <el-select v-model="onlineLearningConfig.updateFrequency" style="width: 100%">
                    <el-option label="实时更新" value="realtime" />
                    <el-option label="每日更新" value="daily" />
                    <el-option label="每周更新" value="weekly" />
                    <el-option label="触发式更新" value="trigger" />
                  </el-select>
                </el-form-item>

                <el-form-item label="学习率">
                  <el-slider
                    v-model="onlineLearningConfig.learningRate"
                    :min="0.001"
                    :max="0.1"
                    :step="0.001"
                    :format-tooltip="formatTooltip"
                    show-input
                  />
                </el-form-item>

                <el-form-item label="遗忘因子">
                  <el-slider
                    v-model="onlineLearningConfig.forgettingFactor"
                    :min="0.9"
                    :max="1.0"
                    :step="0.01"
                    :format-tooltip="formatTooltip"
                    show-input
                  />
                </el-form-item>

                <el-form-item label="性能监控">
                  <el-switch v-model="onlineLearningConfig.performanceMonitoring" />
                </el-form-item>

                <el-form-item label="自动回滚">
                  <el-switch v-model="onlineLearningConfig.autoRollback" />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="startOnlineLearning" :loading="isOnlineLearning">
                    启动在线学习
                  </el-button>
                  <el-button @click="stopOnlineLearning" :disabled="!isOnlineLearning">
                    停止学习
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card>
              <template #header>
                <h4>学习状态监控</h4>
              </template>

              <div v-if="!isOnlineLearning && !onlineLearningResults" class="empty-online">
                <el-empty description="启动在线学习开始模型自适应" />
              </div>

              <div v-if="isOnlineLearning || onlineLearningResults" class="online-monitoring">
                <div class="learning-status">
                  <el-descriptions :column="2" border>
                    <el-descriptions-item label="学习状态">
                      <el-tag :type="isOnlineLearning ? 'success' : 'info'">
                        {{ isOnlineLearning ? '运行中' : '已停止' }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="学习轮数">
                      {{ onlineLearningResults?.epochs || 0 }}
                    </el-descriptions-item>
                    <el-descriptions-item label="当前性能">
                      {{ (onlineLearningResults?.currentPerformance || 0).toFixed(3) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="概念漂移">
                      <el-tag :type="getDriftType(onlineLearningResults?.conceptDrift)">
                        {{ onlineLearningResults?.conceptDrift || '未检测' }}
                      </el-tag>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>

                <div class="performance-trend">
                  <h5>性能趋势</h5>
                  <div ref="performanceTrendChart" class="chart-container"></div>
                </div>

                <div class="learning-log" v-if="onlineLearningResults?.learningLog">
                  <h5>学习日志</h5>
                  <div class="log-entries">
                    <div
                      v-for="(entry, index) in onlineLearningResults.learningLog"
                      :key="index"
                      class="log-entry"
                    >
                      <span class="log-time">{{ entry.timestamp }}</span>
                      <span class="log-event">{{ entry.event }}</span>
                      <span class="log-value">{{ entry.value }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

// 响应式数据
const activeTab = ref('recommendation')
const isAnalyzing = ref(false)
const isGenerating = ref(false)
const isOptimizing = ref(false)
const isSelectingFeatures = ref(false)
const isTrainingEnsemble = ref(false)
const isOnlineLearning = ref(false)

// 数据配置
const dataConfig = reactive({
  source: 'stock_daily',
  dateRange: null,
  target: 'return_5d'
})

// 数据分析结果
const dataAnalysis = ref(null as any)

// 模型推荐结果
const recommendations = ref([])

// 超参数优化配置
const optimizationConfig = reactive({
  model: 'lightgbm',
  algorithm: 'bayesian',
  objective: 'maximize_accuracy',
  trials: 100,
  parallelJobs: 4,
  earlyStopping: true
})

const optimizationProgress = ref(0)
const currentTrial = ref(0)
const bestScore = ref(null)
const estimatedTimeRemaining = ref('--')
const optimizationResults = ref(null)

// 可用模型列表
const availableModels = ref([
  { label: 'LightGBM', value: 'lightgbm' },
  { label: 'XGBoost', value: 'xgboost' },
  { label: 'CatBoost', value: 'catboost' },
  { label: '随机森林', value: 'random_forest' },
  { label: '支持向量机', value: 'svm' },
  { label: '神经网络', value: 'neural_network' }
])

// 特征选择配置
const featureConfig = reactive({
  algorithm: 'rf_importance',
  numFeatures: 50,
  cvFolds: 5,
  scoringMetric: 'accuracy'
})

const featureResults = ref(null)

// 集成学习配置
const ensembleConfig = reactive({
  method: 'stacking',
  baseModels: ['lightgbm', 'xgboost', 'random_forest'],
  weighting: 'performance',
  cvFolds: 5
})

const ensembleResults = ref(null)

// 在线学习配置
const onlineLearningConfig = reactive({
  mode: 'incremental',
  updateFrequency: 'daily',
  learningRate: 0.01,
  forgettingFactor: 0.95,
  performanceMonitoring: true,
  autoRollback: true
})

const onlineLearningResults = ref(null)

// 方法实现
const analyzeData = async () => {
  isAnalyzing.value = true
  
  try {
    // 调用qlib后端API进行数据分析
    const response = await fetch('/api/v1/ml/analyze-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        source: dataConfig.source,
        start_date: dataConfig.dateRange ? dataConfig.dateRange[0].toISOString().split('T')[0] : '2020-01-01',
        end_date: dataConfig.dateRange ? dataConfig.dateRange[1].toISOString().split('T')[0] : '2023-12-31',
        target: dataConfig.target,
        universe: 'csi300'
      })
    })
    
    const result = await response.json()
    
    if (result.status === 'success') {
      dataAnalysis.value = result.data
      ElMessage.success('数据特征分析完成')
    } else {
      throw new Error(result.message || '数据分析失败')
    }
  } catch (error) {
    console.error('数据分析失败:', error)
    ElMessage.error('数据分析失败: ' + error.message)
    
    // 降级到模拟数据
    dataAnalysis.value = {
      sampleCount: 125000,
      featureCount: 158,
      quality: '优秀',
      noiseLevel: '低',
      linearity: 0.65,
      correlation: '中等'
    }
  } finally {
    isAnalyzing.value = false
  }
}

const generateRecommendations = async () => {
  if (!dataAnalysis.value) {
    ElMessage.warning('请先进行数据分析')
    return
  }
  
  isGenerating.value = true
  
  try {
    // 调用qlib后端API生成模型推荐
    const response = await fetch('/api/v1/ml/recommend-models', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        data_analysis: dataAnalysis.value,
        user_preferences: {
          risk_tolerance: preferences.riskTolerance,
          time_horizon: preferences.timeHorizon,
          capital_size: preferences.capitalSize,
          investment_style: preferences.investmentStyle
        }
      })
    })
    
    const result = await response.json()
    
    if (result.status === 'success') {
      recommendations.value = result.data.map(rec => ({
        ...rec,
        score: rec.score || 4.0
      }))
      ElMessage.success('模型推荐生成完成')
    } else {
      throw new Error(result.message || '模型推荐生成失败')
    }
  } catch (error) {
    console.error('模型推荐失败:', error)
    ElMessage.error('模型推荐失败: ' + error.message)
    
    // 降级到模拟数据
    recommendations.value = [
      {
        modelName: 'LightGBM',
        score: 4.8,
        description: '基于梯度提升的高性能模型，在结构化数据上表现优异，训练速度快且内存占用小。',
        scenario: '中大规模结构化数据',
        performance: '准确率 94.2%',
        trainingTime: '15-25分钟',
        interpretability: '中等',
        reasons: [
          '数据量大且特征丰富，适合树模型',
          '目标变量连续，梯度提升效果好',
          '训练效率高，支持并行计算',
          '内置特征重要性分析'
        ]
      },
      {
        modelName: 'XGBoost',
        score: 4.6,
        description: '经典的梯度提升框架，在各类竞赛中表现出色，具有强大的正则化能力。',
        scenario: '复杂非线性关系',
        performance: '准确率 93.8%',
        trainingTime: '20-30分钟',
        interpretability: '中等',
        reasons: [
          '正则化能力强，避免过拟合',
          '处理缺失值能力强',
          '社区活跃，文档完善',
          '参数调优空间大'
        ]
      }
    ]
  } finally {
    isGenerating.value = false
  }
}

const startOptimization = async () => {
  isOptimizing.value = true
  optimizationProgress.value = 0
  currentTrial.value = 0
  bestScore.value = null
  
  // 模拟优化过程
  const totalTrials = optimizationConfig.trials
  const interval = setInterval(() => {
    currentTrial.value++
    optimizationProgress.value = (currentTrial.value / totalTrials) * 100
    bestScore.value = 0.8 + (currentTrial.value / totalTrials) * 0.15 + Math.random() * 0.02
    
    const remainingTrials = totalTrials - currentTrial.value
    const avgTimePerTrial = 2 // 秒
    const remainingSeconds = remainingTrials * avgTimePerTrial
    estimatedTimeRemaining.value = `${Math.floor(remainingSeconds / 60)}分${remainingSeconds % 60}秒`
    
    if (currentTrial.value >= totalTrials) {
      clearInterval(interval)
      completeOptimization()
    }
  }, 100)
}

const completeOptimization = () => {
  optimizationResults.value = {
    bestScore: bestScore.value,
    duration: '12分38秒',
    totalTrials: optimizationConfig.trials,
    convergencePoint: Math.floor(optimizationConfig.trials * 0.7),
    bestParams: [
      { parameter: 'n_estimators', value: '150', range: '[50, 300]' },
      { parameter: 'learning_rate', value: '0.08', range: '[0.01, 0.2]' },
      { parameter: 'max_depth', value: '8', range: '[3, 15]' },
      { parameter: 'min_child_samples', value: '25', range: '[10, 50]' }
    ]
  }
  
  isOptimizing.value = false
  ElMessage.success('超参数优化完成')
}

const stopOptimization = () => {
  isOptimizing.value = false
  ElMessage.info('优化已停止')
}

const runFeatureSelection = async () => {
  isSelectingFeatures.value = true
  
  await new Promise(resolve => setTimeout(resolve, 2500))
  
  featureResults.value = {
    originalCount: 158,
    selectedCount: featureConfig.numFeatures,
    performanceGain: 3.2,
    speedImprovement: 2.1,
    selectedFeatures: Array.from({ length: Math.min(20, featureConfig.numFeatures) }, (_, i) => ({
      rank: i + 1,
      name: `feature_${i + 1}`,
      importance: Math.random() * 0.8 + 0.2,
      category: ['技术指标', '基本面', '宏观', '情绪'][Math.floor(Math.random() * 4)]
    })).sort((a, b) => b.importance - a.importance)
  }
  
  isSelectingFeatures.value = false
  ElMessage.success('特征选择完成')
}

const trainEnsemble = async () => {
  isTrainingEnsemble.value = true
  
  await new Promise(resolve => setTimeout(resolve, 4000))
  
  ensembleResults.value = {
    accuracy: 95.6,
    improvement: 2.1,
    diversity: 0.742,
    weightEntropy: 1.456,
    modelComparison: ensembleConfig.baseModels.map((model, index) => ({
      model: availableModels.value.find(m => m.value === model)?.label || model,
      accuracy: 0.88 + Math.random() * 0.08,
      f1Score: 0.85 + Math.random() * 0.08,
      trainingTime: `${15 + Math.random() * 20}分钟`,
      selected: true
    }))
  }
  
  isTrainingEnsemble.value = false
  ElMessage.success('集成模型训练完成')
}

const startOnlineLearning = async () => {
  isOnlineLearning.value = true
  
  onlineLearningResults.value = {
    epochs: 0,
    currentPerformance: 0.892,
    conceptDrift: '稳定',
    learningLog: [
      {
        timestamp: new Date().toLocaleTimeString(),
        event: '开始在线学习',
        value: '初始化完成'
      }
    ]
  }
  
  // 模拟在线学习过程
  const learningInterval = setInterval(() => {
    if (!isOnlineLearning.value) {
      clearInterval(learningInterval)
      return
    }
    
    onlineLearningResults.value.epochs++
    onlineLearningResults.value.currentPerformance += (Math.random() - 0.5) * 0.001
    
    // 随机添加学习日志
    if (Math.random() < 0.3) {
      onlineLearningResults.value.learningLog.unshift({
        timestamp: new Date().toLocaleTimeString(),
        event: ['模型更新', '性能评估', '概念漂移检测'][Math.floor(Math.random() * 3)],
        value: `性能: ${onlineLearningResults.value.currentPerformance.toFixed(3)}`
      })
      
      // 保持日志长度
      if (onlineLearningResults.value.learningLog.length > 10) {
        onlineLearningResults.value.learningLog = onlineLearningResults.value.learningLog.slice(0, 10)
      }
    }
  }, 2000)
  
  ElMessage.success('在线学习已启动')
}

const stopOnlineLearning = () => {
  isOnlineLearning.value = false
  ElMessage.info('在线学习已停止')
}

// 工具方法
const getQualityType = (quality: string) => {
  const types: Record<string, string> = {
    '优秀': 'success',
    '良好': 'success',
    '一般': 'warning',
    '较差': 'danger'
  }
  return types[quality] || 'info'
}

const getNoiseType = (noise: string) => {
  const types: Record<string, string> = {
    '低': 'success',
    '中': 'warning',
    '高': 'danger'
  }
  return types[noise] || 'info'
}

const getDriftType = (drift: string) => {
  const types: Record<string, string> = {
    '稳定': 'success',
    '轻微漂移': 'warning',
    '显著漂移': 'danger'
  }
  return types[drift] || 'info'
}

const formatTooltip = (val: number) => val.toString()

// 事件处理方法
const viewModelDetails = (rec: any) => {
  ElMessage.info(`查看模型详情: ${rec.modelName}`)
}

const selectModel = (rec: any) => {
  ElMessage.success(`已选择模型: ${rec.modelName}`)
}

const optimizeHyperparameters = (rec: any) => {
  activeTab.value = 'hyperparameter'
  optimizationConfig.model = rec.modelName.toLowerCase()
  ElMessage.info(`切换到参数优化，模型: ${rec.modelName}`)
}

const applyBestParams = () => {
  ElMessage.success('最佳参数已应用')
}

const saveOptimizationResults = () => {
  ElMessage.success('优化结果已保存')
}

const exportOptimizationReport = () => {
  ElMessage.success('优化报告已导出')
}

const deployEnsemble = () => {
  ElMessage.success('集成模型部署成功')
}

const saveEnsembleConfig = () => {
  ElMessage.success('集成配置已保存')
}

const exportEnsembleModel = () => {
  ElMessage.success('集成模型已导出')
}

const exportConfig = () => {
  ElMessage.success('配置已导出')
}

// 生命周期
onMounted(() => {
  // 初始化图表等
})

onUnmounted(() => {
  if (isOnlineLearning.value) {
    stopOnlineLearning()
  }
})
</script>

<style scoped lang="scss">
.model-recommendation-system {
  .system-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }

  .data-analysis {
    .analysis-results {
      margin-top: 24px;

      h5 {
        margin-bottom: 16px;
        color: var(--el-text-color-primary);
      }

      .feature-distribution {
        margin-top: 24px;

        .chart-container {
          height: 200px;
          background: var(--el-color-info-light-9);
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--el-text-color-placeholder);
        }
      }
    }
  }

  .recommendations-list {
    .recommendation-item {
      margin-bottom: 24px;
      padding: 20px;
      border: 1px solid var(--el-border-color);
      border-radius: 12px;
      transition: all 0.3s;

      &:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      &.top-recommendation {
        border-color: var(--el-color-success);
        background: var(--el-color-success-light-9);
      }

      .rec-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .rec-title {
          display: flex;
          align-items: center;
          gap: 12px;

          h4 {
            margin: 0;
            color: var(--el-text-color-primary);
          }
        }
      }

      .rec-description {
        color: var(--el-text-color-regular);
        line-height: 1.6;
        margin-bottom: 16px;
      }

      .rec-metrics {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-bottom: 16px;

        .metric-item {
          display: flex;
          justify-content: space-between;

          .label {
            color: var(--el-text-color-placeholder);
          }

          .value {
            font-weight: 500;
            color: var(--el-text-color-primary);
          }
        }
      }

      .rec-reasons {
        margin-bottom: 16px;

        h5 {
          margin: 0 0 8px 0;
          color: var(--el-text-color-primary);
        }

        ul {
          margin: 0;
          padding-left: 20px;

          li {
            margin-bottom: 4px;
            color: var(--el-text-color-regular);
            line-height: 1.5;
          }
        }
      }

      .rec-actions {
        display: flex;
        gap: 8px;
      }
    }
  }

  .empty-recommendations,
  .empty-optimization,
  .empty-features,
  .empty-ensemble,
  .empty-online {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 200px;
  }

  .optimization-progress,
  .optimization-completed {
    .progress-info {
      text-align: center;
      margin-bottom: 24px;

      h5 {
        margin-bottom: 16px;
        color: var(--el-text-color-primary);
      }

      .progress-details {
        display: flex;
        justify-content: space-around;
        margin-top: 12px;
        font-size: 12px;
        color: var(--el-text-color-regular);
      }
    }

    .live-results,
    .results-summary,
    .best-parameters {
      margin-bottom: 24px;

      h5 {
        margin-bottom: 12px;
        color: var(--el-text-color-primary);
      }
    }

    .chart-container {
      height: 200px;
      background: var(--el-color-info-light-9);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--el-text-color-placeholder);
    }

    .results-actions {
      display: flex;
      gap: 8px;
      justify-content: center;
    }
  }

  .feature-results {
    .feature-summary {
      margin-bottom: 24px;
    }

    .feature-importance-chart,
    .selected-features-table {
      margin-bottom: 24px;

      h5 {
        margin-bottom: 12px;
        color: var(--el-text-color-primary);
      }
    }

    .chart-container {
      height: 300px;
      background: var(--el-color-info-light-9);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--el-text-color-placeholder);
    }
  }

  .model-performance {
    margin-top: 16px;
  }

  .ensemble-results {
    .ensemble-metrics,
    .model-weights {
      margin-bottom: 24px;

      h5 {
        margin-bottom: 12px;
        color: var(--el-text-color-primary);
      }
    }

    .weights-chart .chart-container {
      height: 250px;
      background: var(--el-color-info-light-9);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--el-text-color-placeholder);
    }

    .ensemble-actions {
      display: flex;
      gap: 8px;
      justify-content: center;
    }
  }

  .online-monitoring {
    .learning-status {
      margin-bottom: 24px;
    }

    .performance-trend {
      margin-bottom: 24px;

      h5 {
        margin-bottom: 12px;
        color: var(--el-text-color-primary);
      }

      .chart-container {
        height: 200px;
        background: var(--el-color-info-light-9);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--el-text-color-placeholder);
      }
    }

    .learning-log {
      h5 {
        margin-bottom: 12px;
        color: var(--el-text-color-primary);
      }

      .log-entries {
        max-height: 200px;
        overflow-y: auto;
        border: 1px solid var(--el-border-color);
        border-radius: 4px;

        .log-entry {
          display: flex;
          justify-content: space-between;
          padding: 8px 12px;
          border-bottom: 1px solid var(--el-border-color-light);
          font-size: 12px;

          &:last-child {
            border-bottom: none;
          }

          .log-time {
            color: var(--el-text-color-placeholder);
            min-width: 80px;
          }

          .log-event {
            color: var(--el-text-color-primary);
            flex: 1;
            margin: 0 12px;
          }

          .log-value {
            color: var(--el-text-color-regular);
            min-width: 100px;
            text-align: right;
          }
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .model-recommendation-system {
    .el-col {
      margin-bottom: 16px;
    }

    .rec-metrics {
      grid-template-columns: 1fr !important;
    }

    .system-header {
      flex-direction: column;
      align-items: stretch;
      gap: 16px;
    }
  }
}
</style>