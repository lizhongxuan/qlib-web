"""
用户行为分析服务
提供用户行为追踪、分析和洞察功能
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
import threading
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_db
from ..models.user import User


class ActionType(Enum):
    """用户行为类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW_PAGE = "view_page"
    CREATE_EXPERIMENT = "create_experiment"
    RUN_EXPERIMENT = "run_experiment"
    VIEW_EXPERIMENT = "view_experiment"
    DELETE_EXPERIMENT = "delete_experiment"
    SHARE_EXPERIMENT = "share_experiment"
    DOWNLOAD_RESULT = "download_result"
    SEARCH = "search"
    FILTER = "filter"
    EXPORT = "export"
    ERROR = "error"


class DeviceType(Enum):
    """设备类型"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    UNKNOWN = "unknown"


@dataclass
class UserAction:
    """用户行为记录"""
    timestamp: datetime
    user_id: int
    action_type: ActionType
    page: Optional[str] = None
    resource_id: Optional[str] = None
    duration: Optional[float] = None
    device_type: DeviceType = DeviceType.UNKNOWN
    browser: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['action_type'] = self.action_type.value
        data['device_type'] = self.device_type.value
        return data


@dataclass
class UserSession:
    """用户会话"""
    session_id: str
    user_id: int
    start_time: datetime
    last_activity: datetime
    duration: float = 0.0
    page_views: int = 0
    actions_count: int = 0
    device_type: DeviceType = DeviceType.UNKNOWN
    browser: Optional[str] = None
    ip_address: Optional[str] = None
    ended: bool = False


class UserBehaviorStorage:
    """用户行为存储"""
    
    def __init__(self, max_memory_records: int = 10000):
        self.max_memory_records = max_memory_records
        self.actions: deque = deque(maxlen=max_memory_records)
        self.sessions: Dict[str, UserSession] = {}
        self.user_stats: defaultdict = defaultdict(lambda: {
            'total_actions': 0,
            'total_sessions': 0,
            'total_duration': 0.0,
            'last_activity': None,
            'favorite_actions': defaultdict(int),
            'device_usage': defaultdict(int)
        })
        self.lock = threading.Lock()
    
    def record_action(self, action: UserAction):
        """记录用户行为"""
        with self.lock:
            self.actions.append(action)
            
            # 更新用户统计
            user_stats = self.user_stats[action.user_id]
            user_stats['total_actions'] += 1
            user_stats['last_activity'] = action.timestamp
            user_stats['favorite_actions'][action.action_type.value] += 1
            user_stats['device_usage'][action.device_type.value] += 1
    
    def start_session(self, session: UserSession):
        """开始用户会话"""
        with self.lock:
            self.sessions[session.session_id] = session
            self.user_stats[session.user_id]['total_sessions'] += 1
    
    def update_session(self, session_id: str, **kwargs):
        """更新会话信息"""
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                for key, value in kwargs.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                
                # 计算会话持续时间
                session.duration = (session.last_activity - session.start_time).total_seconds()
                self.user_stats[session.user_id]['total_duration'] += session.duration
    
    def end_session(self, session_id: str):
        """结束会话"""
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].ended = True
    
    def get_user_actions(self, user_id: int, hours: int = 24, limit: int = 100) -> List[UserAction]:
        """获取用户行为记录"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            user_actions = []
            for action in reversed(self.actions):
                if action.user_id == user_id and action.timestamp >= cutoff_time:
                    user_actions.append(action)
                    if len(user_actions) >= limit:
                        break
            
            return user_actions
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取用户统计信息"""
        with self.lock:
            return dict(self.user_stats[user_id])
    
    def get_active_sessions(self) -> List[UserSession]:
        """获取活跃会话"""
        cutoff_time = datetime.now() - timedelta(minutes=30)  # 30分钟无活动视为会话结束
        
        with self.lock:
            active_sessions = []
            for session in self.sessions.values():
                if not session.ended and session.last_activity >= cutoff_time:
                    active_sessions.append(session)
            
            return active_sessions
    
    def get_global_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取全局统计"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self.lock:
            # 过滤最近的行为
            recent_actions = [
                action for action in self.actions 
                if action.timestamp >= cutoff_time
            ]
            
            if not recent_actions:
                return {"total": 0, "unique_users": 0}
            
            # 统计分析
            unique_users = len(set(action.user_id for action in recent_actions))
            action_counts = defaultdict(int)
            device_counts = defaultdict(int)
            page_counts = defaultdict(int)
            hourly_counts = defaultdict(int)
            
            for action in recent_actions:
                action_counts[action.action_type.value] += 1
                device_counts[action.device_type.value] += 1
                if action.page:
                    page_counts[action.page] += 1
                
                # 按小时统计
                hour_key = action.timestamp.strftime("%Y-%m-%d %H:00")
                hourly_counts[hour_key] += 1
            
            # 活跃会话统计
            active_sessions = self.get_active_sessions()
            
            return {
                "time_range": f"最近{hours}小时",
                "total_actions": len(recent_actions),
                "unique_users": unique_users,
                "active_sessions": len(active_sessions),
                "avg_actions_per_user": len(recent_actions) / unique_users if unique_users > 0 else 0,
                "top_actions": dict(sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "device_breakdown": dict(device_counts),
                "top_pages": dict(sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                "hourly_trend": dict(hourly_counts)
            }


class UserAnalyticsService:
    """用户行为分析服务"""
    
    def __init__(self):
        self.storage = UserBehaviorStorage()
        self.enabled = True
    
    def track_action(self, 
                    user_id: int,
                    action_type: ActionType,
                    page: Optional[str] = None,
                    resource_id: Optional[str] = None,
                    duration: Optional[float] = None,
                    request_info: Optional[Dict[str, Any]] = None) -> UserAction:
        """追踪用户行为"""
        if not self.enabled:
            return None
        
        # 解析请求信息
        device_type = DeviceType.UNKNOWN
        browser = None
        ip_address = None
        user_agent = None
        
        if request_info:
            user_agent = request_info.get('user_agent', '')
            ip_address = request_info.get('ip_address')
            
            # 简单的设备类型检测
            if user_agent:
                user_agent_lower = user_agent.lower()
                if 'mobile' in user_agent_lower or 'android' in user_agent_lower or 'iphone' in user_agent_lower:
                    device_type = DeviceType.MOBILE
                elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
                    device_type = DeviceType.TABLET
                elif 'mozilla' in user_agent_lower:
                    device_type = DeviceType.DESKTOP
                
                # 简单的浏览器检测
                if 'chrome' in user_agent_lower:
                    browser = 'Chrome'
                elif 'firefox' in user_agent_lower:
                    browser = 'Firefox'
                elif 'safari' in user_agent_lower:
                    browser = 'Safari'
                elif 'edge' in user_agent_lower:
                    browser = 'Edge'
        
        # 创建行为记录
        action = UserAction(
            timestamp=datetime.now(),
            user_id=user_id,
            action_type=action_type,
            page=page,
            resource_id=resource_id,
            duration=duration,
            device_type=device_type,
            browser=browser,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_data=request_info or {}
        )
        
        # 存储行为
        self.storage.record_action(action)
        
        return action
    
    def start_user_session(self, 
                          user_id: int,
                          session_id: str,
                          request_info: Optional[Dict[str, Any]] = None) -> UserSession:
        """开始用户会话"""
        if not self.enabled:
            return None
        
        # 解析设备信息
        device_type = DeviceType.UNKNOWN
        browser = None
        ip_address = None
        
        if request_info:
            user_agent = request_info.get('user_agent', '')
            ip_address = request_info.get('ip_address')
            
            if user_agent:
                user_agent_lower = user_agent.lower()
                if 'mobile' in user_agent_lower:
                    device_type = DeviceType.MOBILE
                elif 'tablet' in user_agent_lower:
                    device_type = DeviceType.TABLET
                else:
                    device_type = DeviceType.DESKTOP
                
                if 'chrome' in user_agent_lower:
                    browser = 'Chrome'
                elif 'firefox' in user_agent_lower:
                    browser = 'Firefox'
                elif 'safari' in user_agent_lower:
                    browser = 'Safari'
        
        # 创建会话
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now(),
            last_activity=datetime.now(),
            device_type=device_type,
            browser=browser,
            ip_address=ip_address
        )
        
        self.storage.start_session(session)
        return session
    
    def update_user_session(self, session_id: str):
        """更新用户会话活动"""
        if self.enabled:
            self.storage.update_session(
                session_id, 
                last_activity=datetime.now()
            )
    
    def end_user_session(self, session_id: str):
        """结束用户会话"""
        if self.enabled:
            self.storage.end_session(session_id)
    
    def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """获取用户行为洞察"""
        user_stats = self.storage.get_user_statistics(user_id)
        recent_actions = self.storage.get_user_actions(user_id, hours=24, limit=50)
        
        # 用户活跃度分析
        activity_level = "低"
        if user_stats['total_actions'] > 100:
            activity_level = "高"
        elif user_stats['total_actions'] > 20:
            activity_level = "中"
        
        # 偏好分析
        favorite_action = max(user_stats['favorite_actions'].items(), key=lambda x: x[1])[0] if user_stats['favorite_actions'] else "无"
        primary_device = max(user_stats['device_usage'].items(), key=lambda x: x[1])[0] if user_stats['device_usage'] else "unknown"
        
        # 最近活动模式
        if recent_actions:
            avg_session_duration = user_stats['total_duration'] / user_stats['total_sessions'] if user_stats['total_sessions'] > 0 else 0
            last_action_time = recent_actions[0].timestamp if recent_actions else None
        else:
            avg_session_duration = 0
            last_action_time = None
        
        return {
            "user_id": user_id,
            "activity_summary": {
                "level": activity_level,
                "total_actions": user_stats['total_actions'],
                "total_sessions": user_stats['total_sessions'],
                "avg_session_duration": avg_session_duration,
                "last_activity": user_stats['last_activity'].isoformat() if user_stats['last_activity'] else None
            },
            "preferences": {
                "favorite_action": favorite_action,
                "primary_device": primary_device,
                "action_distribution": dict(user_stats['favorite_actions']),
                "device_distribution": dict(user_stats['device_usage'])
            },
            "recent_activity": {
                "actions_24h": len(recent_actions),
                "last_action_time": last_action_time.isoformat() if last_action_time else None,
                "recent_actions": [action.to_dict() for action in recent_actions[:10]]
            }
        }
    
    def get_platform_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """获取平台整体分析"""
        global_stats = self.storage.get_global_statistics(hours)
        active_sessions = self.storage.get_active_sessions()
        
        # 用户留存分析（简化版）
        cutoff_7d = datetime.now() - timedelta(days=7)
        cutoff_30d = datetime.now() - timedelta(days=30)
        
        with self.storage.lock:
            users_7d = set()
            users_30d = set()
            
            for action in self.storage.actions:
                if action.timestamp >= cutoff_7d:
                    users_7d.add(action.user_id)
                if action.timestamp >= cutoff_30d:
                    users_30d.add(action.user_id)
        
        # 热门功能分析
        popular_features = global_stats.get("top_actions", {})
        
        # 用户参与度分析
        engagement_metrics = {
            "daily_active_users": global_stats.get("unique_users", 0),
            "weekly_active_users": len(users_7d),
            "monthly_active_users": len(users_30d),
            "avg_session_duration": sum(s.duration for s in active_sessions) / len(active_sessions) if active_sessions else 0,
            "bounce_rate": self._calculate_bounce_rate(),
            "retention_rate_7d": len(users_7d) / len(users_30d) if users_30d else 0
        }
        
        return {
            **global_stats,
            "engagement_metrics": engagement_metrics,
            "popular_features": popular_features,
            "user_journey": self._analyze_user_journey(),
            "performance_insights": {
                "most_active_hour": max(global_stats.get("hourly_trend", {}).items(), key=lambda x: x[1])[0] if global_stats.get("hourly_trend") else None,
                "peak_concurrent_users": len(active_sessions),
                "avg_actions_per_session": global_stats.get("avg_actions_per_user", 0)
            }
        }
    
    def get_user_segmentation(self) -> Dict[str, Any]:
        """用户分群分析"""
        with self.storage.lock:
            user_segments = {
                "high_activity": [],  # 高活跃用户
                "medium_activity": [],  # 中等活跃用户
                "low_activity": [],   # 低活跃用户
                "dormant": [],        # 休眠用户
                "new_users": []       # 新用户
            }
            
            cutoff_7d = datetime.now() - timedelta(days=7)
            
            for user_id, stats in self.storage.user_stats.items():
                total_actions = stats['total_actions']
                last_activity = stats['last_activity']
                
                # 新用户判断（注册时间需要从数据库获取）
                if last_activity and last_activity >= cutoff_7d:
                    if total_actions >= 50:
                        user_segments["high_activity"].append(user_id)
                    elif total_actions >= 10:
                        user_segments["medium_activity"].append(user_id)
                    else:
                        user_segments["low_activity"].append(user_id)
                else:
                    user_segments["dormant"].append(user_id)
            
            return {
                "segments": {k: len(v) for k, v in user_segments.items()},
                "segment_details": user_segments,
                "total_users": sum(len(v) for v in user_segments.values())
            }
    
    def _calculate_bounce_rate(self) -> float:
        """计算跳出率"""
        # 简化的跳出率计算：只有一个行为的会话占比
        with self.storage.lock:
            single_action_sessions = 0
            total_sessions = len(self.storage.sessions)
            
            for session in self.storage.sessions.values():
                if session.actions_count <= 1:
                    single_action_sessions += 1
            
            return single_action_sessions / total_sessions if total_sessions > 0 else 0
    
    def _analyze_user_journey(self) -> Dict[str, Any]:
        """分析用户路径"""
        # 简化的用户路径分析
        with self.storage.lock:
            page_transitions = defaultdict(lambda: defaultdict(int))
            
            # 按用户分组分析页面跳转
            user_actions = defaultdict(list)
            for action in self.storage.actions:
                if action.page:
                    user_actions[action.user_id].append(action)
            
            for user_id, actions in user_actions.items():
                actions.sort(key=lambda x: x.timestamp)
                for i in range(len(actions) - 1):
                    from_page = actions[i].page
                    to_page = actions[i + 1].page
                    if from_page and to_page:
                        page_transitions[from_page][to_page] += 1
            
            # 找出最常见的路径
            common_paths = []
            for from_page, transitions in page_transitions.items():
                for to_page, count in transitions.items():
                    common_paths.append({
                        "from": from_page,
                        "to": to_page,
                        "count": count
                    })
            
            common_paths.sort(key=lambda x: x["count"], reverse=True)
            
            return {
                "common_paths": common_paths[:10],
                "page_transitions": dict(page_transitions)
            }


# 全局用户分析服务实例
user_analytics_service = UserAnalyticsService()