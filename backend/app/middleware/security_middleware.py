"""
安全中间件
提供API接口安全认证、输入验证、访问频率限制等安全功能
"""
import hashlib
import hmac
import time
import json
import re
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import jwt
from passlib.context import CryptContext

from ..core.config import settings
from ..services.error_logging_service import error_logging_service, ErrorCategory


class SecurityConfig:
    """安全配置"""
    
    # API密钥设置
    API_KEY_HEADER = "X-API-Key"
    API_SECRET_HEADER = "X-API-Secret"
    
    # JWT设置
    JWT_ALGORITHM = "HS256"
    JWT_SECRET_KEY = settings.SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # 速率限制设置
    RATE_LIMIT_ENABLED = True
    DEFAULT_RATE_LIMIT = 1000  # 每小时请求数
    
    # CORS设置
    ALLOWED_ORIGINS = ["http://localhost:3000", "https://qlib-web.com"]
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS = ["*"]
    
    # 安全头设置
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }


class APIKeyAuth:
    """API密钥认证"""
    
    def __init__(self):
        self.valid_keys = {
            "admin_key": {
                "secret": "admin_secret_key_hash",
                "permissions": ["admin", "read", "write"],
                "rate_limit": 5000
            },
            "readonly_key": {
                "secret": "readonly_secret_key_hash", 
                "permissions": ["read"],
                "rate_limit": 2000
            }
        }
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_api_key(self, api_key: str, api_secret: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        if api_key not in self.valid_keys:
            return None
        
        key_info = self.valid_keys[api_key]
        expected_secret = key_info["secret"]
        
        # 验证密钥
        if not self._verify_secret(api_secret, expected_secret):
            return None
        
        return key_info
    
    def _verify_secret(self, secret: str, expected_hash: str) -> bool:
        """验证密钥哈希"""
        # 简化版本，实际应该使用更安全的哈希验证
        return hashlib.sha256(secret.encode()).hexdigest() == expected_hash


class RateLimiter:
    """访问频率限制器"""
    
    def __init__(self):
        self.requests = defaultdict(lambda: deque())
        self.blocked_ips = defaultdict(datetime)
        
    def is_allowed(self, identifier: str, limit: int = 1000, window: int = 3600) -> bool:
        """检查是否允许访问"""
        now = time.time()
        
        # 检查是否被临时封禁
        if identifier in self.blocked_ips:
            if datetime.now() < self.blocked_ips[identifier]:
                return False
            else:
                del self.blocked_ips[identifier]
        
        # 清理过期记录
        request_times = self.requests[identifier]
        while request_times and request_times[0] < now - window:
            request_times.popleft()
        
        # 检查频率限制
        if len(request_times) >= limit:
            # 临时封禁1小时
            self.blocked_ips[identifier] = datetime.now() + timedelta(hours=1)
            return False
        
        # 记录当前请求
        request_times.append(now)
        return True
    
    def get_remaining_requests(self, identifier: str, limit: int = 1000, window: int = 3600) -> int:
        """获取剩余请求次数"""
        now = time.time()
        request_times = self.requests[identifier]
        
        # 清理过期记录
        while request_times and request_times[0] < now - window:
            request_times.popleft()
        
        return max(0, limit - len(request_times))


class InputValidator:
    """输入验证器"""
    
    def __init__(self):
        # 危险模式匹配
        self.sql_injection_patterns = [
            r"(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bUNION\b)",
            r"(\bOR\s+\d+\s*=\s*\d+|\bAND\s+\d+\s*=\s*\d+)",
            r"(\'\s*OR\s*\'|\'\s*AND\s*\')",
            r"(--|\#|\/\*|\*\/)"
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"<iframe[^>]*>.*?</iframe>",
            r"javascript:",
            r"on\w+\s*=",
            r"<[^>]*\bon\w+\s*="
        ]
        
        self.file_upload_patterns = [
            r"\.php$", r"\.jsp$", r"\.asp$", r"\.aspx$",
            r"\.exe$", r"\.bat$", r"\.sh$", r"\.com$"
        ]
    
    def validate_input(self, data: Any, field_name: str = "input") -> Dict[str, Any]:
        """验证输入数据"""
        issues = []
        
        if isinstance(data, str):
            # SQL注入检测
            for pattern in self.sql_injection_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    issues.append(f"{field_name}: 检测到潜在的SQL注入攻击")
                    break
            
            # XSS检测
            for pattern in self.xss_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    issues.append(f"{field_name}: 检测到潜在的XSS攻击")
                    break
            
            # 文件上传安全检测
            for pattern in self.file_upload_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    issues.append(f"{field_name}: 检测到不安全的文件类型")
                    break
        
        elif isinstance(data, dict):
            for key, value in data.items():
                sub_issues = self.validate_input(value, f"{field_name}.{key}")
                issues.extend(sub_issues["issues"])
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                sub_issues = self.validate_input(item, f"{field_name}[{i}]")
                issues.extend(sub_issues["issues"])
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def sanitize_input(self, data: str) -> str:
        """清理输入数据"""
        if not isinstance(data, str):
            return data
        
        # HTML实体编码
        data = (data.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))
        
        # 移除危险字符
        data = re.sub(r"[<>\"'%;)(&+]", "", data)
        
        return data


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    def __init__(self, app: FastAPI, config: SecurityConfig = None):
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.api_key_auth = APIKeyAuth()
        self.rate_limiter = RateLimiter()
        self.input_validator = InputValidator()
        
        # 不需要认证的路径
        self.public_paths = [
            "/docs", "/openapi.json", "/favicon.ico",
            "/api/v1/auth/login", "/api/v1/auth/register",
            "/api/v1/monitoring/health"
        ]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求"""
        try:
            # 1. 基本安全检查
            if not await self._basic_security_check(request):
                return Response(status_code=403, content="Forbidden")
            
            # 2. 速率限制检查
            if not await self._rate_limit_check(request):
                return Response(
                    status_code=429, 
                    content="Too Many Requests",
                    headers={"Retry-After": "3600"}
                )
            
            # 3. 输入验证（对POST/PUT请求）
            if request.method in ["POST", "PUT"]:
                validation_result = await self._validate_request_body(request)
                if not validation_result["valid"]:
                    error_logging_service.log_warning(
                        f"输入验证失败: {validation_result['issues']}", 
                        ErrorCategory.VALIDATION
                    )
                    return Response(
                        status_code=400,
                        content=f"Invalid input: {', '.join(validation_result['issues'])}"
                    )
            
            # 4. API认证检查
            if not self._is_public_path(request.url.path):
                auth_result = await self._authenticate_request(request)
                if not auth_result["authenticated"]:
                    return Response(
                        status_code=401,
                        content="Unauthorized"
                    )
                
                # 将认证信息添加到请求状态
                request.state.api_auth = auth_result
            
            # 5. 执行请求
            response = await call_next(request)
            
            # 6. 添加安全头
            response = self._add_security_headers(response)
            
            return response
            
        except Exception as e:
            error_logging_service.log_error(
                e, ErrorCategory.SYSTEM, 
                {"endpoint": request.url.path, "method": request.method}
            )
            return Response(status_code=500, content="Internal Server Error")
    
    async def _basic_security_check(self, request: Request) -> bool:
        """基本安全检查"""
        # 检查User-Agent
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or len(user_agent) > 512:
            return False
        
        # 检查请求大小
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB限制
            return False
        
        # 检查恶意IP（简化实现）
        client_ip = self._get_client_ip(request)
        if client_ip in ["127.0.0.1"]:  # 这里可以添加恶意IP列表
            pass
        
        return True
    
    async def _rate_limit_check(self, request: Request) -> bool:
        """速率限制检查"""
        if not self.config.RATE_LIMIT_ENABLED:
            return True
        
        client_ip = self._get_client_ip(request)
        
        # 根据认证类型设置不同的限制
        limit = self.config.DEFAULT_RATE_LIMIT
        
        api_key = request.headers.get(self.config.API_KEY_HEADER)
        if api_key and api_key in self.api_key_auth.valid_keys:
            limit = self.api_key_auth.valid_keys[api_key].get("rate_limit", limit)
        
        return self.rate_limiter.is_allowed(client_ip, limit)
    
    async def _validate_request_body(self, request: Request) -> Dict[str, Any]:
        """验证请求体"""
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                # 克隆请求体用于验证
                body = await request.body()
                if body:
                    data = json.loads(body)
                    return self.input_validator.validate_input(data)
            
            return {"valid": True, "issues": []}
        except Exception as e:
            return {"valid": False, "issues": [f"请求体解析失败: {str(e)}"]}
    
    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """请求认证"""
        # 1. 检查JWT令牌
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            try:
                payload = jwt.decode(
                    token, 
                    self.config.JWT_SECRET_KEY, 
                    algorithms=[self.config.JWT_ALGORITHM]
                )
                return {
                    "authenticated": True,
                    "type": "jwt",
                    "user_id": payload.get("sub"),
                    "permissions": payload.get("permissions", [])
                }
            except jwt.ExpiredSignatureError:
                return {"authenticated": False, "error": "Token expired"}
            except jwt.JWTError:
                return {"authenticated": False, "error": "Invalid token"}
        
        # 2. 检查API密钥
        api_key = request.headers.get(self.config.API_KEY_HEADER)
        api_secret = request.headers.get(self.config.API_SECRET_HEADER)
        
        if api_key and api_secret:
            key_info = self.api_key_auth.verify_api_key(api_key, api_secret)
            if key_info:
                return {
                    "authenticated": True,
                    "type": "api_key",
                    "api_key": api_key,
                    "permissions": key_info["permissions"]
                }
        
        return {"authenticated": False, "error": "No valid authentication method"}
    
    def _is_public_path(self, path: str) -> bool:
        """检查是否为公开路径"""
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return True
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _add_security_headers(self, response: Response) -> Response:
        """添加安全头"""
        for header, value in self.config.SECURITY_HEADERS.items():
            response.headers[header] = value
        
        # 添加速率限制信息
        # response.headers["X-RateLimit-Limit"] = str(limit)
        # response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


class CSRFProtection:
    """CSRF保护"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_token(self, session_id: str) -> str:
        """生成CSRF令牌"""
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{timestamp}:{signature}"
    
    def validate_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """验证CSRF令牌"""
        try:
            timestamp_str, signature = token.split(":", 1)
            timestamp = int(timestamp_str)
            
            # 检查令牌是否过期
            if time.time() - timestamp > max_age:
                return False
            
            # 验证签名
            message = f"{session_id}:{timestamp_str}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except ValueError:
            return False


class ContentSecurityPolicy:
    """内容安全策略"""
    
    def __init__(self):
        self.directives = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:", "https:"],
            "connect-src": ["'self'"],
            "font-src": ["'self'"],
            "object-src": ["'none'"],
            "media-src": ["'self'"],
            "frame-src": ["'none'"]
        }
    
    def add_source(self, directive: str, source: str):
        """添加CSP源"""
        if directive not in self.directives:
            self.directives[directive] = []
        
        if source not in self.directives[directive]:
            self.directives[directive].append(source)
    
    def generate_header(self) -> str:
        """生成CSP头"""
        policy_parts = []
        for directive, sources in self.directives.items():
            policy_parts.append(f"{directive} {' '.join(sources)}")
        
        return "; ".join(policy_parts)


# 安全工具函数
def hash_password(password: str) -> str:
    """密码哈希"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """密码验证"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """生成安全令牌"""
    import secrets
    return secrets.token_urlsafe(length)


def is_safe_url(url: str, allowed_hosts: List[str]) -> bool:
    """检查URL是否安全"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # 检查协议
        if parsed.scheme not in ["http", "https"]:
            return False
        
        # 检查主机
        if parsed.netloc and parsed.netloc not in allowed_hosts:
            return False
        
        return True
    except Exception:
        return False