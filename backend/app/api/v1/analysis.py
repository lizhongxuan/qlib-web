"""
高级分析功能API端点
"""
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.auth import get_current_user, get_current_user_optional
from ...models.user import User
from ...schemas.analysis import (
    AnalysisCreate, AnalysisUpdate, AnalysisResponse, AnalysisListResponse,
    AnalysisApiResponse, AnalysisExecutionRequest, AnalysisExecutionResponse,
    CustomMetricCreate, CustomMetricUpdate, CustomMetricResponse, CustomMetricListResponse,
    MetricCalculationRequest, MetricCalculationResponse,
    AnalysisTemplateCreate, AnalysisTemplateResponse, AnalysisTemplateListResponse,
    BatchAnalysisRequest, BatchAnalysisResponse, AnalysisStatistics,
    AnalysisTypeEnum, DiagnosticsResponse
)
from ...services.analysis import analysis_service, custom_metric_service

router = APIRouter()


# 分析任务管理
@router.post("/", response_model=AnalysisApiResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    analysis_data: AnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建分析任务
    """
    try:
        analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
        
        return AnalysisApiResponse(
            success=True,
            message="分析任务创建成功",
            data=AnalysisResponse.from_orm(analysis)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建分析任务失败: {str(e)}"
        )


@router.get("/{analysis_id}", response_model=AnalysisApiResponse)
async def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取分析任务详情
    """
    try:
        analysis = analysis_service.get_analysis_by_id(db, analysis_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        # 检查权限
        if analysis.creator_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return AnalysisApiResponse(
            success=True,
            message="获取成功",
            data=AnalysisResponse.from_orm(analysis)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分析任务失败: {str(e)}"
        )


@router.get("/experiment/{experiment_id}", response_model=AnalysisListResponse)
async def get_experiment_analyses(
    experiment_id: str,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    analysis_type: Optional[AnalysisTypeEnum] = Query(None, description="分析类型筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取实验的分析任务列表
    """
    try:
        # TODO: 添加实验访问权限检查
        
        result = analysis_service.get_experiment_analyses(db, experiment_id, page, size)
        
        # 如果指定了分析类型，进行筛选
        if analysis_type:
            filtered_analyses = [
                analysis for analysis in result["analyses"]
                if analysis.analysis_type == analysis_type.value
            ]
            result["analyses"] = filtered_analyses
            result["total"] = len(filtered_analyses)
            result["pages"] = (len(filtered_analyses) + size - 1) // size
        
        return AnalysisListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分析列表失败: {str(e)}"
        )


# 分析执行
@router.post("/{analysis_id}/execute", response_model=AnalysisExecutionResponse)
async def execute_analysis(
    analysis_id: int,
    execution_request: AnalysisExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    执行分析任务
    """
    try:
        analysis = analysis_service.get_analysis_by_id(db, analysis_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析任务不存在"
            )
        
        # 检查权限
        if analysis.creator_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 根据分析类型执行相应的分析
        if execution_request.async_execution:
            # 异步执行
            if analysis.analysis_type == "attribution":
                background_tasks.add_task(
                    analysis_service.execute_attribution_analysis, db, analysis_id
                )
            elif analysis.analysis_type == "risk":
                background_tasks.add_task(
                    analysis_service.execute_risk_analysis, db, analysis_id
                )
            elif analysis.analysis_type == "feature_importance":
                background_tasks.add_task(
                    analysis_service.execute_feature_importance_analysis, db, analysis_id
                )
            elif analysis.analysis_type == "model_diagnosis":
                background_tasks.add_task(
                    analysis_service.execute_ic_decay_analysis, db, analysis_id
                )
            elif analysis.analysis_type == "scenario_analysis":
                background_tasks.add_task(
                    analysis_service.execute_scenario_analysis, db, analysis_id
                )
            elif analysis.analysis_type == "monte_carlo":
                background_tasks.add_task(
                    analysis_service.execute_monte_carlo_analysis, db, analysis_id
                )
            elif analysis.analysis_type == "sensitivity_analysis":
                background_tasks.add_task(
                    analysis_service.execute_sensitivity_analysis, db, analysis_id
                )
            
            return AnalysisExecutionResponse(
                analysis_id=analysis_id,
                status="running",
                estimated_duration=300,  # 预估5分钟
                task_id=f"analysis_{analysis_id}"
            )
        else:
            # 同步执行
            if analysis.analysis_type == "attribution":
                result = analysis_service.execute_attribution_analysis(db, analysis_id)
            elif analysis.analysis_type == "risk":
                result = analysis_service.execute_risk_analysis(db, analysis_id)
            elif analysis.analysis_type == "feature_importance":
                result = analysis_service.execute_feature_importance_analysis(db, analysis_id)
            elif analysis.analysis_type == "model_diagnosis":
                result = analysis_service.execute_ic_decay_analysis(db, analysis_id)
            elif analysis.analysis_type == "scenario_analysis":
                result = analysis_service.execute_scenario_analysis(db, analysis_id)
            elif analysis.analysis_type == "monte_carlo":
                result = analysis_service.execute_monte_carlo_analysis(db, analysis_id)
            elif analysis.analysis_type == "sensitivity_analysis":
                result = analysis_service.execute_sensitivity_analysis(db, analysis_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不支持的分析类型"
                )
            
            return AnalysisExecutionResponse(
                analysis_id=analysis_id,
                status="completed"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行分析失败: {str(e)}"
        )


# 归因分析
@router.post("/attribution/{experiment_id}", response_model=AnalysisApiResponse)
async def create_attribution_analysis(
    experiment_id: str,
    config: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建并执行归因分析
    """
    try:
        # 创建分析任务
        analysis_data = AnalysisCreate(
            experiment_id=experiment_id,
            name=f"归因分析 - {experiment_id}",
            description="收益归因分解分析",
            analysis_type=AnalysisTypeEnum.ATTRIBUTION,
            config=config or {}
        )
        
        analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
        
        # 执行分析
        result = analysis_service.execute_attribution_analysis(db, analysis.id)
        
        return AnalysisApiResponse(
            success=True,
            message="归因分析完成",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"归因分析失败: {str(e)}"
        )


# 风险分析
@router.post("/risk/{experiment_id}", response_model=AnalysisApiResponse)
async def create_risk_analysis(
    experiment_id: str,
    config: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建并执行风险分析
    """
    try:
        analysis_data = AnalysisCreate(
            experiment_id=experiment_id,
            name=f"风险分析 - {experiment_id}",
            description="VaR和风险指标分析",
            analysis_type=AnalysisTypeEnum.RISK,
            config=config or {}
        )
        
        analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
        result = analysis_service.execute_risk_analysis(db, analysis.id)
        
        return AnalysisApiResponse(
            success=True,
            message="风险分析完成",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"风险分析失败: {str(e)}"
        )


# 特征重要性分析
@router.post("/feature-importance/{experiment_id}", response_model=AnalysisApiResponse)
async def create_feature_importance_analysis(
    experiment_id: str,
    config: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建并执行特征重要性分析
    """
    try:
        analysis_data = AnalysisCreate(
            experiment_id=experiment_id,
            name=f"特征重要性分析 - {experiment_id}",
            description="SHAP值和特征贡献分析",
            analysis_type=AnalysisTypeEnum.FEATURE_IMPORTANCE,
            config=config or {}
        )
        
        analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
        result = analysis_service.execute_feature_importance_analysis(db, analysis.id)
        
        return AnalysisApiResponse(
            success=True,
            message="特征重要性分析完成",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"特征重要性分析失败: {str(e)}"
        )


# IC衰减分析
@router.post("/ic-decay/{experiment_id}", response_model=AnalysisApiResponse)
async def create_ic_decay_analysis(
    experiment_id: str,
    config: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建并执行IC衰减分析
    """
    try:
        analysis_data = AnalysisCreate(
            experiment_id=experiment_id,
            name=f"IC衰减分析 - {experiment_id}",
            description="信息系数衰减监控",
            analysis_type=AnalysisTypeEnum.MODEL_DIAGNOSIS,
            config=config or {}
        )
        
        analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
        result = analysis_service.execute_ic_decay_analysis(db, analysis.id)
        
        return AnalysisApiResponse(
            success=True,
            message="IC衰减分析完成",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IC衰减分析失败: {str(e)}"
        )


# 情景分析
@router.post("/scenario/{experiment_id}", response_model=AnalysisApiResponse)
async def create_scenario_analysis(
    experiment_id: str,
    config: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建并执行情景分析
    """
    try:
        analysis_data = AnalysisCreate(
            experiment_id=experiment_id,
            name=f"情景分析 - {experiment_id}",
            description="市场情景模拟与极端情况分析",
            analysis_type=AnalysisTypeEnum.SCENARIO_ANALYSIS,
            config=config or {}
        )
        
        analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
        result = analysis_service.execute_scenario_analysis(db, analysis.id)
        
        return AnalysisApiResponse(
            success=True,
            message="情景分析完成",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"情景分析失败: {str(e)}"
        )


# 蒙特卡洛模拟分析
@router.post("/monte-carlo/{experiment_id}", response_model=AnalysisApiResponse)
async def create_monte_carlo_analysis(
    experiment_id: str,
    config: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建并执行蒙特卡洛模拟分析
    """
    try:
        analysis_data = AnalysisCreate(
            experiment_id=experiment_id,
            name=f"蒙特卡洛模拟 - {experiment_id}",
            description="蒙特卡洛风险模拟与概率分析",
            analysis_type=AnalysisTypeEnum.MONTE_CARLO,
            config=config or {
                "n_simulations": 10000,
                "time_horizon": 252,
                "confidence_levels": [0.05, 0.95]
            }
        )
        
        analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
        result = analysis_service.execute_monte_carlo_analysis(db, analysis.id)
        
        return AnalysisApiResponse(
            success=True,
            message="蒙特卡洛模拟完成",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"蒙特卡洛模拟失败: {str(e)}"
        )


# 敏感性分析
@router.post("/sensitivity/{experiment_id}", response_model=AnalysisApiResponse)
async def create_sensitivity_analysis(
    experiment_id: str,
    config: dict = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建并执行敏感性分析
    """
    try:
        analysis_data = AnalysisCreate(
            experiment_id=experiment_id,
            name=f"敏感性分析 - {experiment_id}",
            description="参数敏感性与稳定性分析",
            analysis_type=AnalysisTypeEnum.SENSITIVITY_ANALYSIS,
            config=config or {}
        )
        
        analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
        result = analysis_service.execute_sensitivity_analysis(db, analysis.id)
        
        return AnalysisApiResponse(
            success=True,
            message="敏感性分析完成",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"敏感性分析失败: {str(e)}"
        )


# 批量高级分析
@router.post("/advanced-batch/{experiment_id}", response_model=AnalysisApiResponse)
async def create_comprehensive_analysis(
    experiment_id: str,
    analysis_types: List[str] = None,
    config: dict = None,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建综合高级分析（包含归因、风险、情景、蒙特卡洛等）
    """
    try:
        # 默认分析类型
        if not analysis_types:
            analysis_types = ["attribution", "risk", "scenario_analysis", "monte_carlo"]
        
        analysis_results = {}
        analysis_ids = []
        
        # 批量创建和执行分析
        for analysis_type in analysis_types:
            try:
                # 根据类型设置配置
                type_config = config.get(analysis_type, {}) if config else {}
                if analysis_type == "monte_carlo" and not type_config:
                    type_config = {
                        "n_simulations": 5000,  # 减少模拟次数以提高速度
                        "time_horizon": 252,
                        "confidence_levels": [0.05, 0.95]
                    }
                
                analysis_data = AnalysisCreate(
                    experiment_id=experiment_id,
                    name=f"{analysis_type.replace('_', ' ').title()} - {experiment_id}",
                    description=f"综合分析中的{analysis_type.replace('_', ' ')}",
                    analysis_type=getattr(AnalysisTypeEnum, analysis_type.upper()),
                    config=type_config
                )
                
                analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
                analysis_ids.append(analysis.id)
                
                # 执行对应分析
                if analysis_type == "attribution":
                    result = analysis_service.execute_attribution_analysis(db, analysis.id)
                elif analysis_type == "risk":
                    result = analysis_service.execute_risk_analysis(db, analysis.id)
                elif analysis_type == "scenario_analysis":
                    result = analysis_service.execute_scenario_analysis(db, analysis.id)
                elif analysis_type == "monte_carlo":
                    result = analysis_service.execute_monte_carlo_analysis(db, analysis.id)
                elif analysis_type == "sensitivity_analysis":
                    result = analysis_service.execute_sensitivity_analysis(db, analysis.id)
                
                analysis_results[analysis_type] = {
                    "analysis_id": analysis.id,
                    "status": "completed",
                    "result": result
                }
                
            except Exception as e:
                analysis_results[analysis_type] = {
                    "analysis_id": None,
                    "status": "failed",
                    "error": str(e)
                }
        
        return AnalysisApiResponse(
            success=True,
            message=f"综合分析完成，成功: {len([r for r in analysis_results.values() if r['status'] == 'completed'])}, 失败: {len([r for r in analysis_results.values() if r['status'] == 'failed'])}",
            data={
                "analysis_results": analysis_results,
                "analysis_ids": analysis_ids,
                "experiment_id": experiment_id
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"综合分析失败: {str(e)}"
        )


# 自定义指标管理
@router.post("/metrics", response_model=CustomMetricResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_metric(
    metric_data: CustomMetricCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建自定义指标
    """
    try:
        metric = custom_metric_service.create_metric(db, metric_data, current_user.id)
        return CustomMetricResponse.from_orm(metric)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建自定义指标失败: {str(e)}"
        )


@router.get("/metrics", response_model=CustomMetricListResponse)
async def get_public_metrics(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    category: Optional[str] = Query(None, description="指标分类"),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取公开指标列表
    """
    try:
        result = custom_metric_service.get_public_metrics(db, page, size)
        
        # 如果指定了分类，进行筛选
        if category:
            filtered_metrics = [
                metric for metric in result["metrics"]
                if metric.category == category
            ]
            result["metrics"] = filtered_metrics
            result["total"] = len(filtered_metrics)
            result["pages"] = (len(filtered_metrics) + size - 1) // size
        
        return CustomMetricListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取指标列表失败: {str(e)}"
        )


@router.post("/metrics/calculate", response_model=MetricCalculationResponse)
async def calculate_custom_metric(
    calculation_request: MetricCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    计算自定义指标
    """
    try:
        result_value = custom_metric_service.calculate_metric(
            db=db,
            metric_id=calculation_request.metric_id,
            experiment_id=calculation_request.experiment_id,
            parameters=calculation_request.parameters,
            user_id=current_user.id
        )
        
        return MetricCalculationResponse(
            metric_id=calculation_request.metric_id,
            experiment_id=calculation_request.experiment_id,
            result_value=result_value,
            execution_time=0.1,
            parameters=calculation_request.parameters,
            calculated_at=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"指标计算失败: {str(e)}"
        )


# 批量操作
@router.post("/batch", response_model=BatchAnalysisResponse)
async def create_batch_analysis(
    batch_request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    批量创建分析任务
    """
    try:
        created_analyses = []
        failed_experiments = []
        
        # TODO: 获取分析模板
        template_config = batch_request.custom_config or {}
        
        for experiment_id in batch_request.experiment_ids:
            try:
                analysis_data = AnalysisCreate(
                    experiment_id=experiment_id,
                    name=f"批量分析 - {experiment_id}",
                    description="批量创建的分析任务",
                    analysis_type=AnalysisTypeEnum.ATTRIBUTION,  # 默认类型
                    config=template_config
                )
                
                analysis = analysis_service.create_analysis(db, analysis_data, current_user.id)
                created_analyses.append(analysis.id)
                
                # 添加到后台任务队列
                background_tasks.add_task(
                    analysis_service.execute_attribution_analysis, db, analysis.id
                )
                
            except Exception:
                failed_experiments.append(experiment_id)
        
        return BatchAnalysisResponse(
            created_analyses=created_analyses,
            failed_experiments=failed_experiments,
            total_created=len(created_analyses),
            total_failed=len(failed_experiments)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量创建分析失败: {str(e)}"
        )


# 分析统计
@router.get("/statistics", response_model=AnalysisStatistics)
async def get_analysis_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取分析统计信息
    """
    try:
        # TODO: 实现统计逻辑
        return AnalysisStatistics(
            total_analyses=100,
            analyses_by_type={
                "attribution": 30,
                "risk": 25,
                "feature_importance": 20,
                "model_diagnosis": 15,
                "custom_metric": 10
            },
            analyses_by_status={
                "completed": 80,
                "running": 5,
                "failed": 10,
                "pending": 5
            },
            avg_execution_time=180.5,
            success_rate=0.85,
            popular_templates=[],
            recent_activity=[]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )