from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

router = APIRouter()

# 请求模型
class WorkflowStateRequest(BaseModel):
    user_id: str

class WorkflowSyncRequest(BaseModel):
    user_id: str
    current_step: str
    step_data: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None

class SaveProgressRequest(BaseModel):
    user_id: str
    step_key: str
    progress_data: Dict[str, Any]
    auto_save: Optional[bool] = True

class DependencyCheckRequest(BaseModel):
    target_step: str
    user_id: str

# 响应模型
class WorkflowStep(BaseModel):
    key: str
    title: str
    subtitle: str
    icon: str
    route: str
    status: str
    optional: bool
    dependencies: List[str]
    completion_percentage: float
    estimated_time: Optional[int] = None

class WorkflowState(BaseModel):
    user_id: str
    current_step: str
    current_step_index: int
    workflow_type: str
    total_steps: int
    completed_steps: int
    progress_percentage: float
    estimated_completion_time: Optional[int] = None
    steps: List[WorkflowStep]
    last_updated: datetime

class WorkflowRecommendation(BaseModel):
    type: str
    title: str
    description: str
    target_step: str
    priority: str
    estimated_benefit: Optional[str] = None

class DependencyResult(BaseModel):
    step_key: str
    is_accessible: bool
    missing_dependencies: List[str]
    dependency_status: Dict[str, str]
    suggestions: List[str]

class ProgressSaveResult(BaseModel):
    success: bool
    message: str
    auto_save_enabled: bool
    last_save_time: datetime

@router.get("/state", response_model=WorkflowState)
async def get_workflow_state(user_id: str):
    """
    获取用户工作流状态
    """
    try:
        # 模拟从数据库获取用户工作流状态
        workflow_steps = [
            WorkflowStep(
                key="factor-development",
                title="因子开发",
                subtitle="创建量化因子",
                icon="MagicStick",
                route="/factors",
                status="completed",
                optional=False,
                dependencies=[],
                completion_percentage=100.0,
                estimated_time=30
            ),
            WorkflowStep(
                key="model-training",
                title="模型训练",
                subtitle="训练预测模型",
                icon="Cpu",
                route="/training",
                status="current",
                optional=False,
                dependencies=["factor-development"],
                completion_percentage=65.0,
                estimated_time=45
            ),
            WorkflowStep(
                key="strategy-backtest",
                title="策略回测",
                subtitle="测试策略表现",
                icon="TrendCharts", 
                route="/backtest",
                status="pending",
                optional=False,
                dependencies=["model-training"],
                completion_percentage=0.0,
                estimated_time=25
            ),
            WorkflowStep(
                key="results-analysis",
                title="结果分析",
                subtitle="分析策略效果",
                icon="DataAnalysis",
                route="/results",
                status="pending",
                optional=True,
                dependencies=["strategy-backtest"],
                completion_percentage=0.0,
                estimated_time=20
            ),
            WorkflowStep(
                key="strategy-deployment",
                title="策略部署",
                subtitle="上线交易策略",
                icon="Upload",
                route="/deployment",
                status="pending",
                optional=False,
                dependencies=["strategy-backtest"],
                completion_percentage=0.0,
                estimated_time=15
            )
        ]
        
        completed_steps = len([s for s in workflow_steps if s.status == "completed"])
        current_step_index = next((i for i, s in enumerate(workflow_steps) if s.status == "current"), 0)
        current_step_key = workflow_steps[current_step_index].key if workflow_steps else ""
        
        total_estimated_time = sum(s.estimated_time or 0 for s in workflow_steps if s.status in ["current", "pending"])
        
        workflow_state = WorkflowState(
            user_id=user_id,
            current_step=current_step_key,
            current_step_index=current_step_index,
            workflow_type="full",
            total_steps=len(workflow_steps),
            completed_steps=completed_steps,
            progress_percentage=round((completed_steps / len(workflow_steps)) * 100, 1),
            estimated_completion_time=total_estimated_time,
            steps=workflow_steps,
            last_updated=datetime.now()
        )
        
        return workflow_state
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流状态失败: {str(e)}")

@router.post("/sync", response_model=Dict[str, Any])
async def sync_workflow_progress(request: WorkflowSyncRequest):
    """
    同步工作流进度
    """
    try:
        # 模拟同步逻辑
        sync_result = {
            "success": True,
            "message": "工作流进度同步成功",
            "updated_step": request.current_step,
            "progress": request.progress or 0,
            "sync_time": datetime.now().isoformat(),
            "next_recommendations": []
        }
        
        # 根据当前步骤提供下一步建议
        if request.current_step == "factor-development":
            sync_result["next_recommendations"] = [
                "建议创建3-5个不同类型的因子以提高模型稳健性",
                "完成因子验证后可以开始模型训练"
            ]
        elif request.current_step == "model-training":
            sync_result["next_recommendations"] = [
                "模型训练完成后建议进行详细的性能评估",
                "可以尝试不同的算法进行对比"
            ]
        elif request.current_step == "strategy-backtest":
            sync_result["next_recommendations"] = [
                "设置合理的交易成本和滑点参数",
                "建议测试不同市场环境下的表现"
            ]
        
        return sync_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步工作流进度失败: {str(e)}")

@router.get("/recommendations", response_model=List[WorkflowRecommendation])
async def get_workflow_recommendations(user_id: str, current_step: Optional[str] = None):
    """
    获取下一步推荐
    """
    try:
        recommendations = []
        
        # 基于当前步骤生成推荐
        if current_step == "factor-development" or not current_step:
            recommendations.extend([
                WorkflowRecommendation(
                    type="best_practice",
                    title="使用AI助手快速生成因子",
                    description="利用AI因子助手可以快速生成基础因子模板，提高开发效率",
                    target_step="factor-development",
                    priority="high",
                    estimated_benefit="节省60%开发时间"
                ),
                WorkflowRecommendation(
                    type="optimization",
                    title="创建因子组合",
                    description="建议创建不同类型的因子组合，如技术面+基本面的复合因子",
                    target_step="factor-development", 
                    priority="medium",
                    estimated_benefit="提升15%预测精度"
                )
            ])
        
        if current_step == "model-training":
            recommendations.extend([
                WorkflowRecommendation(
                    type="algorithm",
                    title="尝试集成学习算法",
                    description="推荐使用LightGBM或XGBoost，在因子数据上通常表现更好",
                    target_step="model-training",
                    priority="high",
                    estimated_benefit="提升20%模型性能"
                ),
                WorkflowRecommendation(
                    type="validation",
                    title="使用时间序列交叉验证",
                    description="金融数据具有时序特性，建议使用时间序列交叉验证方法",
                    target_step="model-training",
                    priority="high",
                    estimated_benefit="更准确的性能评估"
                )
            ])
        
        if current_step == "strategy-backtest":
            recommendations.extend([
                WorkflowRecommendation(
                    type="risk_control",
                    title="设置风险控制参数",
                    description="建议设置最大回撤限制和止损策略，控制投资风险",
                    target_step="strategy-backtest",
                    priority="high",
                    estimated_benefit="降低35%风险暴露"
                ),
                WorkflowRecommendation(
                    type="cost_analysis",
                    title="考虑交易成本影响",
                    description="设置合理的交易成本参数，更真实地评估策略表现",
                    target_step="strategy-backtest",
                    priority="medium",
                    estimated_benefit="更准确的收益预期"
                )
            ])
        
        # 通用推荐
        recommendations.append(
            WorkflowRecommendation(
                type="general",
                title="保存工作进度",
                description="定期保存工作进度，避免数据丢失",
                target_step="all",
                priority="low",
                estimated_benefit="数据安全保障"
            )
        )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流推荐失败: {str(e)}")

@router.post("/save-progress", response_model=ProgressSaveResult)
async def save_workflow_progress(request: SaveProgressRequest):
    """
    保存工作进度
    """
    try:
        # 模拟保存进度到数据库
        # 这里应该实现实际的数据持久化逻辑
        
        save_result = ProgressSaveResult(
            success=True,
            message=f"步骤 {request.step_key} 的进度已保存",
            auto_save_enabled=request.auto_save or False,
            last_save_time=datetime.now()
        )
        
        return save_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存工作进度失败: {str(e)}")

@router.get("/dependencies", response_model=List[DependencyResult])
async def check_workflow_dependencies(user_id: str, target_step: Optional[str] = None):
    """
    检查页面依赖
    """
    try:
        # 定义步骤依赖关系
        step_dependencies = {
            "factor-development": [],
            "model-training": ["factor-development"],
            "strategy-backtest": ["model-training"],
            "results-analysis": ["strategy-backtest"],
            "strategy-deployment": ["strategy-backtest"]
        }
        
        # 模拟用户完成状态
        user_completed_steps = ["factor-development"]  # 假设用户已完成因子开发
        
        dependency_results = []
        
        # 检查指定步骤或所有步骤
        steps_to_check = [target_step] if target_step else list(step_dependencies.keys())
        
        for step in steps_to_check:
            if step not in step_dependencies:
                continue
                
            dependencies = step_dependencies[step]
            missing_deps = [dep for dep in dependencies if dep not in user_completed_steps]
            
            dependency_status = {}
            for dep in dependencies:
                dependency_status[dep] = "completed" if dep in user_completed_steps else "pending"
            
            suggestions = []
            if missing_deps:
                suggestions.append(f"请先完成以下步骤: {', '.join(missing_deps)}")
                if "factor-development" in missing_deps:
                    suggestions.append("建议先创建至少3个有效因子")
                if "model-training" in missing_deps:
                    suggestions.append("建议训练至少一个模型并达到可接受的性能指标")
            
            result = DependencyResult(
                step_key=step,
                is_accessible=len(missing_deps) == 0,
                missing_dependencies=missing_deps,
                dependency_status=dependency_status,
                suggestions=suggestions
            )
            
            dependency_results.append(result)
        
        return dependency_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查工作流依赖失败: {str(e)}")

@router.post("/reset", response_model=Dict[str, Any])
async def reset_workflow(user_id: str):
    """
    重置用户工作流
    """
    try:
        # 模拟重置逻辑
        reset_result = {
            "success": True,
            "message": "工作流已重置",
            "user_id": user_id,
            "reset_time": datetime.now().isoformat(),
            "new_current_step": "factor-development"
        }
        
        return reset_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置工作流失败: {str(e)}")

@router.get("/statistics", response_model=Dict[str, Any])
async def get_workflow_statistics(user_id: str):
    """
    获取工作流统计信息
    """
    try:
        # 模拟统计数据
        statistics = {
            "user_id": user_id,
            "total_workflows": 15,
            "completed_workflows": 8,
            "average_completion_time": 120,  # 分钟
            "most_time_consuming_step": "model-training",
            "success_rate": 0.85,
            "step_statistics": {
                "factor-development": {
                    "average_time": 45,
                    "success_rate": 0.95,
                    "common_issues": ["因子表达式语法错误", "缺少数据源"]
                },
                "model-training": {
                    "average_time": 65,
                    "success_rate": 0.80,
                    "common_issues": ["过拟合", "训练时间过长"]
                },
                "strategy-backtest": {
                    "average_time": 30,
                    "success_rate": 0.90,
                    "common_issues": ["参数设置不当", "交易成本过高"]
                }
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工作流统计失败: {str(e)}")