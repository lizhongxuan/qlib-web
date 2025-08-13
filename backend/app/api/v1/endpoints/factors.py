from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
import re
from datetime import datetime

router = APIRouter()

# 请求模型
class AIGenerateFactorRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    investment_logic: Optional[str] = None

class ValidateFactorRequest(BaseModel):
    expression: str
    data_columns: Optional[List[str]] = None

class FactorTestRequest(BaseModel):
    expression: str
    start_date: str
    end_date: str
    universe: Optional[str] = "CSI300"
    frequency: Optional[str] = "daily"

class SaveFactorRequest(BaseModel):
    name: str
    expression: str
    description: Optional[str] = None
    category: str
    tags: Optional[List[str]] = None

class OptimizationSuggestionsRequest(BaseModel):
    factor_id: Optional[str] = None
    expression: Optional[str] = None

# 响应模型
class AIGeneratedFactor(BaseModel):
    name: str
    expression: str
    description: str
    investment_logic: str
    confidence: float
    estimated_performance: Dict[str, float]

class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    syntax_score: float

class FactorLibraryItem(BaseModel):
    id: str
    name: str
    expression: str
    description: str
    category: str
    type: str
    tags: List[str]
    performance: Optional[Dict[str, float]]
    usage_count: int
    created_at: datetime
    updated_at: datetime

class FactorTestResult(BaseModel):
    test_id: str
    status: str
    metrics: Optional[Dict[str, float]] = None
    charts_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class OptimizationSuggestion(BaseModel):
    type: str
    title: str
    description: str
    suggested_expression: Optional[str] = None
    expected_improvement: Optional[Dict[str, float]] = None

@router.post("/ai-generate", response_model=AIGeneratedFactor)
async def ai_generate_factor(request: AIGenerateFactorRequest):
    """
    AI生成因子表达式
    """
    try:
        # 模拟AI生成过程
        await asyncio.sleep(2)
        
        # 基于prompt生成因子表达式
        factor_expressions = {
            "动量": "($close / Ref($close, 20)) - 1",
            "均值回归": "($close - MA($close, 20)) / $close",
            "成交量": "($volume / MA($volume, 20)) - 1", 
            "波动率": "STD($close / Ref($close, 1), 20)",
            "价值": "1 / $pe_ratio",
            "质量": "$roe * $roa",
            "增长": "($revenue - Ref($revenue, 4)) / Ref($revenue, 4)"
        }
        
        # 根据提示词选择合适的表达式模板
        expression = "($close / MA($close, 20)) - 1"
        for keyword, expr in factor_expressions.items():
            if keyword in request.prompt:
                expression = expr
                break
        
        # 生成因子信息
        ai_factor = AIGeneratedFactor(
            name=f"AI生成因子_{datetime.now().strftime('%H%M%S')}",
            expression=expression,
            description=f"基于提示'{request.prompt}'生成的量化因子",
            investment_logic=f"该因子通过{request.prompt}的逻辑来捕捉市场的异常收益机会",
            confidence=0.75 + (hash(request.prompt) % 25) / 100,
            estimated_performance={
                "ic": 0.05 + (hash(request.prompt) % 10) / 200,
                "icir": 0.8 + (hash(request.prompt) % 15) / 10,
                "sharpe": 1.0 + (hash(request.prompt) % 20) / 20
            }
        )
        
        return ai_factor
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成因子失败: {str(e)}")

@router.post("/validate", response_model=ValidationResult)
async def validate_factor(request: ValidateFactorRequest):
    """
    验证因子表达式语法
    """
    try:
        expression = request.expression
        errors = []
        warnings = []
        suggestions = []
        
        # 基础语法检查
        if not expression.strip():
            errors.append("因子表达式不能为空")
        
        # 检查括号匹配
        if expression.count('(') != expression.count(')'):
            errors.append("括号不匹配")
        
        # 检查常用函数
        valid_functions = ['MA', 'STD', 'MAX', 'MIN', 'Ref', 'Rank', 'Ts_Rank', 'Corr', 'Cov']
        used_functions = re.findall(r'([A-Z_]+)\s*\(', expression)
        for func in used_functions:
            if func not in valid_functions:
                warnings.append(f"未识别的函数: {func}")
        
        # 检查变量
        valid_variables = ['$close', '$open', '$high', '$low', '$volume', '$pe_ratio', '$pb_ratio', '$roe', '$roa', '$revenue']
        used_variables = re.findall(r'\$([a-z_]+)', expression)
        for var in used_variables:
            if f'${var}' not in valid_variables:
                warnings.append(f"未识别的变量: ${var}")
        
        # 生成建议
        if 'MA(' in expression:
            suggestions.append("建议考虑使用EMA(指数移动平均)替代MA以提高响应速度")
        
        if '$volume' in expression:
            suggestions.append("成交量因子建议进行标准化处理")
        
        # 计算语法评分
        syntax_score = 1.0
        syntax_score -= len(errors) * 0.3
        syntax_score -= len(warnings) * 0.1
        syntax_score = max(0.0, syntax_score)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            syntax_score=syntax_score
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证因子失败: {str(e)}")

@router.get("/library", response_model=List[FactorLibraryItem])
async def get_factor_library(
    category: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    获取因子表达式库
    """
    try:
        # 模拟因子库数据
        factor_library = [
            FactorLibraryItem(
                id="factor_lib_1",
                name="20日动量因子",
                expression="($close / Ref($close, 20)) - 1",
                description="计算当前价格相对于20天前价格的变化率",
                category="技术指标",
                type="technical",
                tags=["动量", "短期"],
                performance={"ic": 0.08, "icir": 1.2, "sharpe": 1.45},
                usage_count=156,
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 15)
            ),
            FactorLibraryItem(
                id="factor_lib_2", 
                name="市盈率倒数",
                expression="1 / $pe_ratio",
                description="市盈率的倒数，用于价值投资策略",
                category="基本面",
                type="fundamental",
                tags=["价值", "长期"],
                performance={"ic": 0.12, "icir": 1.8, "sharpe": 1.65},
                usage_count=89,
                created_at=datetime(2024, 1, 2),
                updated_at=datetime(2024, 1, 12)
            ),
            FactorLibraryItem(
                id="factor_lib_3",
                name="相对强弱指标",
                expression="($close - MIN($close, 14)) / (MAX($close, 14) - MIN($close, 14))",
                description="RSI相对强弱指标，衡量价格动量",
                category="技术指标", 
                type="technical",
                tags=["动量", "超买超卖"],
                performance={"ic": 0.06, "icir": 0.9, "sharpe": 1.1},
                usage_count=234,
                created_at=datetime(2024, 1, 3),
                updated_at=datetime(2024, 1, 10)
            ),
            FactorLibraryItem(
                id="factor_lib_4",
                name="成交量价格趋势",
                expression="Corr($close, $volume, 20)",
                description="价格与成交量的相关性，反映趋势强度",
                category="技术指标",
                type="technical", 
                tags=["成交量", "趋势"],
                performance={"ic": 0.07, "icir": 1.15, "sharpe": 1.25},
                usage_count=67,
                created_at=datetime(2024, 1, 5),
                updated_at=datetime(2024, 1, 8)
            ),
            FactorLibraryItem(
                id="factor_lib_5",
                name="资产回报率质量",
                expression="$roe * $roa",
                description="净资产收益率与总资产回报率的乘积，衡量盈利质量",
                category="基本面",
                type="fundamental",
                tags=["质量", "盈利能力"],
                performance={"ic": 0.09, "icir": 1.4, "sharpe": 1.35},
                usage_count=123,
                created_at=datetime(2024, 1, 7),
                updated_at=datetime(2024, 1, 14)
            )
        ]
        
        # 应用过滤条件
        filtered_factors = factor_library
        
        if category:
            filtered_factors = [f for f in filtered_factors if f.category == category]
        
        if type:
            filtered_factors = [f for f in filtered_factors if f.type == type]
        
        if search:
            search_lower = search.lower()
            filtered_factors = [f for f in filtered_factors if 
                search_lower in f.name.lower() or 
                search_lower in f.description.lower() or
                any(search_lower in tag.lower() for tag in f.tags)
            ]
        
        # 应用分页
        total = len(filtered_factors)
        start = offset
        end = min(offset + limit, total)
        
        return filtered_factors[start:end]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取因子库失败: {str(e)}")

@router.post("/test", response_model=FactorTestResult)
async def test_factor(request: FactorTestRequest, background_tasks: BackgroundTasks):
    """
    因子历史回测验证
    """
    try:
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 启动后台测试任务
        background_tasks.add_task(run_factor_test, test_id, request)
        
        return FactorTestResult(
            test_id=test_id,
            status="running"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动因子测试失败: {str(e)}")

@router.get("/test/{test_id}", response_model=FactorTestResult)
async def get_factor_test_result(test_id: str):
    """
    获取因子测试结果
    """
    # 这里应该从数据库或缓存中获取测试结果
    # 为了演示，返回模拟结果
    return FactorTestResult(
        test_id=test_id,
        status="completed",
        metrics={
            "ic": 0.08,
            "icir": 1.2,
            "sharpe": 1.45,
            "annual_return": 0.285,
            "max_drawdown": -0.082,
            "win_rate": 0.609
        },
        charts_data={
            "cumulative_returns": [1.0, 1.02, 1.05, 1.08, 1.12, 1.15],
            "ic_time_series": [0.05, 0.08, 0.06, 0.09, 0.07, 0.08],
            "factor_distribution": {"bins": [0.1, 0.2, 0.3, 0.4], "counts": [10, 25, 30, 15]}
        }
    )

@router.post("/save", response_model=Dict[str, str])
async def save_factor(request: SaveFactorRequest):
    """
    保存因子到库
    """
    try:
        # 验证因子名称唯一性
        factor_id = f"factor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 这里应该保存到数据库
        # 为了演示，只返回成功信息
        
        return {
            "factor_id": factor_id,
            "message": "因子保存成功",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存因子失败: {str(e)}")

@router.get("/suggestions", response_model=List[OptimizationSuggestion])
async def get_factor_optimization_suggestions(
    factor_id: Optional[str] = None,
    expression: Optional[str] = None
):
    """
    获取因子优化建议
    """
    try:
        suggestions = []
        
        # 根据因子表达式提供优化建议
        if expression:
            if 'MA(' in expression:
                suggestions.append(OptimizationSuggestion(
                    type="performance",
                    title="使用指数移动平均",
                    description="将简单移动平均替换为指数移动平均可以提高响应速度",
                    suggested_expression=expression.replace('MA(', 'EMA('),
                    expected_improvement={"ic": 0.02, "sharpe": 0.15}
                ))
            
            if '$volume' in expression:
                suggestions.append(OptimizationSuggestion(
                    type="normalization",
                    title="成交量标准化",
                    description="对成交量进行标准化处理可以提高因子稳定性",
                    suggested_expression=f"({expression}) / STD({expression}, 20)",
                    expected_improvement={"stability": 0.25}
                ))
            
            if not any(func in expression for func in ['Rank(', 'Ts_Rank(']):
                suggestions.append(OptimizationSuggestion(
                    type="neutralization", 
                    title="添加排序中性化",
                    description="使用排序函数可以降低异常值影响",
                    suggested_expression=f"Rank({expression})",
                    expected_improvement={"icir": 0.3}
                ))
        
        # 通用优化建议
        suggestions.extend([
            OptimizationSuggestion(
                type="risk",
                title="行业中性化",
                description="建议对因子进行行业中性化处理，降低行业暴露风险",
                expected_improvement={"max_drawdown": 0.05}
            ),
            OptimizationSuggestion(
                type="ensemble",
                title="因子组合",
                description="考虑与其他因子组合使用，提高策略多样性",
                expected_improvement={"sharpe": 0.2, "stability": 0.15}
            )
        ])
        
        return suggestions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取优化建议失败: {str(e)}")

# 后台任务函数
async def run_factor_test(test_id: str, request: FactorTestRequest):
    """
    执行因子测试的后台任务
    """
    try:
        # 模拟测试过程
        await asyncio.sleep(10)
        
        # 这里应该执行实际的回测逻辑
        # 并将结果保存到数据库或缓存中
        
        print(f"因子测试 {test_id} 完成")
        
    except Exception as e:
        print(f"因子测试 {test_id} 失败: {str(e)}")