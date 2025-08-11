"""
分享相关API端点
"""
from typing import Any, Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.auth import get_current_user, get_current_user_optional, get_client_ip, get_user_agent
from ...models.user import User
from ...schemas.share import (
    ShareCreate, ShareUpdate, ShareResponse, ShareSummary, ShareListResponse,
    ShareAccess, ShareApiResponse, ShareStatistics, PublicShareInfo,
    ShareAccessResult
)
from ...models.share import SharePermission
from ...services.share import share_service

router = APIRouter()


@router.post("/quick/{experiment_id}", response_model=ShareApiResponse, status_code=status.HTTP_201_CREATED)
async def create_quick_share(
    experiment_id: str,
    permissions: SharePermission = SharePermission.VIEW,
    expires_in_hours: int = Query(24, ge=1, le=168, description="分享有效期（小时）"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    一键分享实验
    """
    try:
        share = share_service.create_quick_share(
            db=db,
            experiment_id=experiment_id,
            owner_id=current_user.id,
            permissions=permissions,
            expires_in_hours=expires_in_hours
        )
        
        return ShareApiResponse(
            success=True,
            message="一键分享创建成功",
            data=ShareResponse.from_orm(share)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"一键分享失败: {str(e)}"
        )


@router.post("/", response_model=ShareApiResponse, status_code=status.HTTP_201_CREATED)
async def create_share(
    share_data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    创建分享链接
    """
    try:
        share = share_service.create_share(db, share_data, current_user.id)
        
        return ShareApiResponse(
            success=True,
            message="分享创建成功",
            data=ShareResponse.from_orm(share)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建分享失败: {str(e)}"
        )


@router.get("/", response_model=ShareListResponse)
async def get_user_shares(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取用户的分享列表
    """
    try:
        return share_service.get_user_shares(db, current_user.id, page, size)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享列表失败: {str(e)}"
        )


@router.get("/{share_id}", response_model=ShareApiResponse)
async def get_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取分享详情
    """
    try:
        from ...models.share import ExperimentShare
        share = db.query(ExperimentShare).filter(
            ExperimentShare.id == share_id
        ).first()
        
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享不存在"
            )
        
        # 检查权限
        if share.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return ShareApiResponse(
            success=True,
            message="获取分享详情成功",
            data=ShareResponse.from_orm(share)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享详情失败: {str(e)}"
        )


@router.put("/{share_id}", response_model=ShareApiResponse)
async def update_share(
    share_id: int,
    share_update: ShareUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    更新分享
    """
    try:
        share = share_service.update_share(db, share_id, share_update, current_user.id)
        
        return ShareApiResponse(
            success=True,
            message="分享更新成功",
            data=ShareResponse.from_orm(share)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新分享失败: {str(e)}"
        )


@router.delete("/{share_id}")
async def delete_share(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    删除分享
    """
    try:
        share_service.delete_share(db, share_id, current_user.id)
        
        return {"success": True, "message": "分享删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除分享失败: {str(e)}"
        )


@router.get("/{share_id}/statistics", response_model=ShareStatistics)
async def get_share_statistics(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取分享统计信息
    """
    try:
        return share_service.get_share_statistics(db, share_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享统计失败: {str(e)}"
        )


@router.get("/{share_id}/logs")
async def get_share_access_logs(
    share_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    获取分享访问日志
    """
    try:
        logs_data = share_service.get_share_access_logs(db, share_id, current_user.id, page, size)
        return {"success": True, "data": logs_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取访问日志失败: {str(e)}"
        )


# 公开分享访问端点
@router.get("/public/{share_token}/info", response_model=PublicShareInfo)
async def get_public_share_info(
    share_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    获取公开分享信息（不需要登录）
    """
    try:
        share_info = share_service.get_public_share_info(db, share_token)
        if not share_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享不存在或不是公开分享"
            )
        
        return share_info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享信息失败: {str(e)}"
        )


@router.post("/public/{share_token}/access", response_model=ShareAccessResult)
async def access_public_share(
    share_token: str,
    share_access: ShareAccess,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Any:
    """
    访问公开分享（不需要登录，但可以记录登录用户信息）
    """
    try:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        user_id = current_user.id if current_user else None
        
        result = share_service.access_share(
            db=db,
            share_token=share_token,
            password=share_access.password,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"访问分享失败: {str(e)}"
        )


@router.post("/public/{share_token}/copy")
async def copy_shared_experiment(
    share_token: str,
    share_access: ShareAccess,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    复制分享的实验（需要登录）
    """
    try:
        # 首先访问分享以验证权限
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        access_result = share_service.access_share(
            db=db,
            share_token=share_token,
            password=share_access.password,
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=current_user.id
        )
        
        if not access_result.success:
            return access_result
        
        # 检查复制权限
        share = share_service.get_share_by_token(db, share_token)
        if share.permissions not in ["copy", "comment"]:  # copy权限包含comment权限
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="该分享不允许复制"
            )
        
        # TODO: 实现实验复制逻辑
        # 这里需要调用实验服务的复制方法
        
        # 记录复制操作
        share_service._log_access(db, share.id, ip_address, user_agent, current_user.id, "copy", True)
        db.commit()
        
        return {
            "success": True,
            "message": "实验复制成功",
            "data": {
                "new_experiment_id": "generated-id",  # 替换为实际的新实验ID
                "message": "实验已复制到您的账户"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"复制实验失败: {str(e)}"
        )


# 批量操作端点
@router.post("/batch/delete")
async def batch_delete_shares(
    share_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    批量删除分享
    """
    try:
        deleted_count = 0
        failed_ids = []
        
        for share_id in share_ids:
            try:
                share_service.delete_share(db, share_id, current_user.id)
                deleted_count += 1
            except HTTPException:
                failed_ids.append(share_id)
        
        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 个分享",
            "data": {
                "deleted_count": deleted_count,
                "failed_count": len(failed_ids),
                "failed_ids": failed_ids
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除失败: {str(e)}"
        )


@router.post("/batch/toggle-status")
async def batch_toggle_share_status(
    share_ids: List[int],
    is_active: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    批量切换分享状态
    """
    try:
        updated_count = 0
        failed_ids = []
        
        for share_id in share_ids:
            try:
                share_update = ShareUpdate(is_active=is_active)
                share_service.update_share(db, share_id, share_update, current_user.id)
                updated_count += 1
            except HTTPException:
                failed_ids.append(share_id)
        
        action = "激活" if is_active else "禁用"
        
        return {
            "success": True,
            "message": f"成功{action} {updated_count} 个分享",
            "data": {
                "updated_count": updated_count,
                "failed_count": len(failed_ids),
                "failed_ids": failed_ids
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作失败: {str(e)}"
        )


@router.get("/{share_id}/public-url")
async def get_public_share_url(
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    生成公开访问链接
    """
    try:
        from ...models.share import ExperimentShare
        from ...core.config import settings
        
        share = db.query(ExperimentShare).filter(
            ExperimentShare.id == share_id
        ).first()
        
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享不存在"
            )
        
        # 检查权限
        if share.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        # 检查分享是否可访问
        if not share.is_accessible():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分享已过期或不可访问"
            )
        
        # 生成公开链接
        public_url = f"{settings.FRONTEND_URL}/share/{share.share_token}"
        
        return {
            "success": True,
            "data": {
                "share_id": share.id,
                "share_token": share.share_token,
                "public_url": public_url,
                "qr_code_url": f"{settings.FRONTEND_URL}/api/v1/shares/public/{share.share_token}/qr",
                "title": share.title,
                "description": share.description,
                "permissions": share.permissions,
                "expires_at": share.expires_at.isoformat() if share.expires_at else None,
                "current_views": share.current_views,
                "max_views": share.max_views,
                "requires_password": bool(share.password)
            },
            "message": "公开链接生成成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成公开链接失败: {str(e)}"
        )


@router.get("/public/{share_token}/qr")
async def get_share_qr_code(
    share_token: str,
    size: int = Query(200, ge=100, le=500, description="二维码大小"),
    db: Session = Depends(get_db)
) -> Any:
    """
    生成分享链接的二维码
    """
    try:
        from ...core.config import settings
        import qrcode
        from io import BytesIO
        from fastapi.responses import StreamingResponse
        
        # 检查分享是否存在
        share = share_service.get_share_by_token(db, share_token)
        if not share or not share.is_accessible():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享不存在或已失效"
            )
        
        # 生成二维码
        share_url = f"{settings.FRONTEND_URL}/share/{share_token}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size // 25,  # 调整大小
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)
        
        # 创建二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为字节流
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        
        return StreamingResponse(
            BytesIO(img_buffer.getvalue()),
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=qr_code_{share_token[:8]}.png"}
        )
        
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="二维码生成功能不可用，请安装 qrcode 库"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成二维码失败: {str(e)}"
        )


@router.post("/generate-link/{experiment_id}")
async def generate_public_link(
    experiment_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    permissions: SharePermission = SharePermission.VIEW,
    expires_in_hours: int = Query(24, ge=1, le=168),
    max_views: Optional[int] = Query(None, ge=1, le=10000),
    password: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    为实验生成公开访问链接（完整功能版本）
    """
    try:
        from ...core.config import settings
        
        # 创建分享数据
        share_create = ShareCreate(
            experiment_id=experiment_id,
            title=title or f"实验分享",
            description=description or "公开分享的实验",
            is_public=True,
            permissions=permissions,
            password=password,
            max_views=max_views,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        )
        
        # 创建分享
        share = share_service.create_share(db, share_create, current_user.id)
        
        # 生成完整的链接信息
        public_url = f"{settings.FRONTEND_URL}/share/{share.share_token}"
        
        return {
            "success": True,
            "data": {
                "share_id": share.id,
                "share_token": share.share_token,
                "public_url": public_url,
                "qr_code_url": f"{settings.FRONTEND_URL}/api/v1/shares/public/{share.share_token}/qr",
                "embed_code": f'<iframe src="{settings.FRONTEND_URL}/embed/share/{share.share_token}" width="100%" height="600" frameborder="0"></iframe>',
                "title": share.title,
                "description": share.description,
                "permissions": share.permissions,
                "expires_at": share.expires_at.isoformat() if share.expires_at else None,
                "max_views": share.max_views,
                "requires_password": bool(share.password),
                "created_at": share.created_at.isoformat(),
                "social_share": {
                    "twitter": f"https://twitter.com/intent/tweet?url={public_url}&text={share.title or '查看这个有趣的量化实验'}",
                    "facebook": f"https://www.facebook.com/sharer/sharer.php?u={public_url}",
                    "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={public_url}"
                }
            },
            "message": "公开访问链接生成成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成公开链接失败: {str(e)}"
        )