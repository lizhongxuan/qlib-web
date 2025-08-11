"""
实验模板服务
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime
import json

from app.models.template import ExperimentTemplate, TemplateUsage, TemplateCategory
from app.schemas.template import (
    ExperimentTemplateCreate, 
    ExperimentTemplateUpdate,
    TemplateUsageCreate,
    TemplateSearchRequest,
    TemplateCategory as TemplateCategoryEnum
)


class TemplateService:
    """模板服务类"""
    
    async def create_template(self, db: Session, template_data: ExperimentTemplateCreate) -> ExperimentTemplate:
        """创建模板"""
        template = ExperimentTemplate(
            name=template_data.name,
            description=template_data.description,
            category=template_data.category.value,
            config=template_data.config.dict(),
            default_params=template_data.default_params,
            author=template_data.author,
            version=template_data.version,
            tags=template_data.tags,
            is_public=template_data.is_public
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return template
    
    async def get_templates(self, 
                          db: Session,
                          search_request: TemplateSearchRequest) -> Tuple[List[ExperimentTemplate], int]:
        """搜索和获取模板列表"""
        
        # 构建查询条件
        conditions = [ExperimentTemplate.is_active == True]
        
        # 关键词搜索
        if search_request.keyword:
            keyword = f"%{search_request.keyword}%"
            conditions.append(
                or_(
                    ExperimentTemplate.name.ilike(keyword),
                    ExperimentTemplate.description.ilike(keyword),
                    ExperimentTemplate.author.ilike(keyword)
                )
            )
        
        # 分类筛选
        if search_request.category:
            conditions.append(ExperimentTemplate.category == search_request.category.value)
        
        # 作者筛选
        if search_request.author:
            conditions.append(ExperimentTemplate.author.ilike(f"%{search_request.author}%"))
        
        # 公开性筛选
        if search_request.is_public is not None:
            conditions.append(ExperimentTemplate.is_public == search_request.is_public)
        
        # 推荐筛选
        if search_request.is_featured is not None:
            conditions.append(ExperimentTemplate.is_featured == search_request.is_featured)
        
        # 评分筛选
        if search_request.min_rating is not None:
            # 计算平均评分
            avg_rating = func.coalesce(
                func.cast(ExperimentTemplate.rating, db.dialect.FLOAT) / 
                func.nullif(ExperimentTemplate.rating_count, 0), 
                0
            )
            conditions.append(avg_rating >= search_request.min_rating)
        
        # 标签筛选 (使用JSON包含查询)
        if search_request.tags:
            for tag in search_request.tags:
                conditions.append(ExperimentTemplate.tags.contains([tag]))
        
        # 构建查询
        query = db.query(ExperimentTemplate).filter(and_(*conditions))
        
        # 排序
        if search_request.sort_by == "name":
            order_field = ExperimentTemplate.name
        elif search_request.sort_by == "usage_count":
            order_field = ExperimentTemplate.usage_count
        elif search_request.sort_by == "rating":
            order_field = func.coalesce(
                func.cast(ExperimentTemplate.rating, db.dialect.FLOAT) / 
                func.nullif(ExperimentTemplate.rating_count, 0), 
                0
            )
        elif search_request.sort_by == "updated_at":
            order_field = ExperimentTemplate.updated_at
        else:
            order_field = ExperimentTemplate.created_at
        
        if search_request.sort_order == "asc":
            query = query.order_by(asc(order_field))
        else:
            query = query.order_by(desc(order_field))
        
        # 获取总数
        total = query.count()
        
        # 分页
        templates = query.offset(
            (search_request.page - 1) * search_request.page_size
        ).limit(search_request.page_size).all()
        
        return templates, total
    
    async def get_template(self, db: Session, template_id: str) -> Optional[ExperimentTemplate]:
        """获取单个模板"""
        return db.query(ExperimentTemplate).filter(
            ExperimentTemplate.id == template_id,
            ExperimentTemplate.is_active == True
        ).first()
    
    async def update_template(self, 
                            db: Session, 
                            template_id: str, 
                            update_data: ExperimentTemplateUpdate) -> Optional[ExperimentTemplate]:
        """更新模板"""
        template = await self.get_template(db, template_id)
        if not template:
            return None
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if field == "config" and value:
                value = value.dict()
            if hasattr(template, field):
                setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(template)
        
        return template
    
    async def delete_template(self, db: Session, template_id: str) -> bool:
        """删除模板（软删除）"""
        template = await self.get_template(db, template_id)
        if not template:
            return False
        
        template.is_active = False
        template.updated_at = datetime.utcnow()
        db.commit()
        
        return True
    
    async def clone_template(self, db: Session, template_id: str, new_name: str, user_id: Optional[str] = None) -> Optional[ExperimentTemplate]:
        """克隆模板"""
        original = await self.get_template(db, template_id)
        if not original:
            return None
        
        # 创建克隆模板
        cloned = ExperimentTemplate(
            name=new_name,
            description=f"基于 '{original.name}' 的副本",
            category=TemplateCategoryEnum.USER.value,
            config=original.config,
            default_params=original.default_params,
            author=user_id or "匿名用户",
            version="1.0.0",
            tags=original.tags.copy() if original.tags else [],
            is_public=False
        )
        
        db.add(cloned)
        db.commit()
        db.refresh(cloned)
        
        # 记录使用
        await self.record_usage(db, TemplateUsageCreate(
            template_id=template_id,
            usage_type="copy",
            user_id=user_id
        ))
        
        return cloned
    
    async def record_usage(self, db: Session, usage_data: TemplateUsageCreate, success: bool = True, error_message: str = None) -> TemplateUsage:
        """记录模板使用"""
        usage = TemplateUsage(
            template_id=usage_data.template_id,
            experiment_id=usage_data.experiment_id,
            usage_type=usage_data.usage_type.value,
            user_id=usage_data.user_id,
            success=success,
            error_message=error_message
        )
        
        db.add(usage)
        
        # 更新模板使用计数
        if success:
            template = db.query(ExperimentTemplate).filter(
                ExperimentTemplate.id == usage_data.template_id
            ).first()
            if template:
                template.usage_count = (template.usage_count or 0) + 1
        
        db.commit()
        db.refresh(usage)
        
        return usage
    
    async def rate_template(self, db: Session, template_id: str, rating: int, user_id: Optional[str] = None) -> bool:
        """评分模板"""
        template = await self.get_template(db, template_id)
        if not template:
            return False
        
        # 简化评分逻辑：直接更新总分和评分次数
        # 实际应用中可能需要防止重复评分
        template.rating = (template.rating or 0) + rating
        template.rating_count = (template.rating_count or 0) + 1
        
        db.commit()
        return True
    
    async def get_featured_templates(self, db: Session, limit: int = 10) -> List[ExperimentTemplate]:
        """获取推荐模板"""
        return db.query(ExperimentTemplate).filter(
            ExperimentTemplate.is_featured == True,
            ExperimentTemplate.is_active == True,
            ExperimentTemplate.is_public == True
        ).order_by(desc(ExperimentTemplate.usage_count)).limit(limit).all()
    
    async def get_popular_templates(self, db: Session, limit: int = 10) -> List[ExperimentTemplate]:
        """获取热门模板"""
        return db.query(ExperimentTemplate).filter(
            ExperimentTemplate.is_active == True,
            ExperimentTemplate.is_public == True
        ).order_by(desc(ExperimentTemplate.usage_count)).limit(limit).all()
    
    async def get_categories(self, db: Session) -> List[TemplateCategory]:
        """获取模板分类"""
        return db.query(TemplateCategory).filter(
            TemplateCategory.is_active == True
        ).order_by(TemplateCategory.sort_order).all()
    
    async def create_preset_templates(self, db: Session) -> List[ExperimentTemplate]:
        """创建预设模板"""
        preset_templates = [
            {
                "name": "沪深300指数增强策略",
                "description": "基于LightGBM的沪深300指数增强策略，适合稳健投资",
                "category": TemplateCategoryEnum.PRESET,
                "config": {
                    "data_config": {
                        "stock_pool": "CSI300",
                        "start_time": "2020-01-01",
                        "end_time": "2023-12-31"
                    },
                    "model_config": {
                        "name": "LightGBM",
                        "params": {
                            "n_estimators": 100,
                            "learning_rate": 0.1,
                            "max_depth": 6
                        }
                    },
                    "strategy_config": {
                        "name": "TopkDropoutStrategy",
                        "params": {
                            "topk": 50,
                            "n_drop": 5
                        }
                    },
                    "backtest_config": {
                        "trade_cost": 0.0015,
                        "benchmark": "CSI300",
                        "initial_cash": 1000000
                    }
                },
                "tags": ["指数增强", "稳健", "LightGBM"],
                "author": "Qlib团队",
                "is_public": True,
                "is_featured": True
            },
            {
                "name": "中证500量化选股",
                "description": "基于LSTM的中证500量化选股策略，追求超额收益",
                "category": TemplateCategoryEnum.PRESET,
                "config": {
                    "data_config": {
                        "stock_pool": "CSI500",
                        "start_time": "2019-01-01",
                        "end_time": "2023-12-31"
                    },
                    "model_config": {
                        "name": "LSTM",
                        "params": {
                            "hidden_size": 64,
                            "num_layers": 2,
                            "dropout": 0.1
                        }
                    },
                    "strategy_config": {
                        "name": "SignalStrategy",
                        "params": {
                            "signal": "lstm_pred"
                        }
                    },
                    "backtest_config": {
                        "trade_cost": 0.002,
                        "benchmark": "CSI500",
                        "initial_cash": 1000000
                    }
                },
                "tags": ["深度学习", "选股", "LSTM"],
                "author": "Qlib团队",
                "is_public": True,
                "is_featured": True
            },
            {
                "name": "创业板成长策略",
                "description": "专注创业板高成长股票的XGBoost策略",
                "category": TemplateCategoryEnum.PRESET,
                "config": {
                    "data_config": {
                        "stock_pool": "ChiNext",
                        "start_time": "2020-01-01",
                        "end_time": "2023-12-31"
                    },
                    "model_config": {
                        "name": "XGBoost",
                        "params": {
                            "n_estimators": 200,
                            "learning_rate": 0.05,
                            "max_depth": 8
                        }
                    },
                    "strategy_config": {
                        "name": "TopkDropoutStrategy",
                        "params": {
                            "topk": 30,
                            "n_drop": 3
                        }
                    },
                    "backtest_config": {
                        "trade_cost": 0.0025,
                        "benchmark": "ChiNext",
                        "initial_cash": 1000000
                    }
                },
                "tags": ["成长股", "创业板", "XGBoost"],
                "author": "Qlib团队",
                "is_public": True
            }
        ]
        
        created_templates = []
        for template_data in preset_templates:
            # 检查是否已存在
            existing = db.query(ExperimentTemplate).filter(
                ExperimentTemplate.name == template_data["name"]
            ).first()
            
            if not existing:
                template = ExperimentTemplate(**template_data)
                db.add(template)
                created_templates.append(template)
        
        if created_templates:
            db.commit()
            for template in created_templates:
                db.refresh(template)
        
        return created_templates