import time
import logging
from typing import Optional

from django.core.cache import cache
from django.http import JsonResponse, HttpRequest, HttpResponse
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware for protection against DDoS.
    
    Uses Redis for distributed rate limiting.
    """
    
    RATE_LIMIT_PER_MINUTE = 100
    RATE_LIMIT_PER_HOUR = 1000
    RATE_LIMIT_PER_DAY = 10000
    
    def process_request(self, request: HttpRequest) -> Optional[JsonResponse]:
        if request.path.startswith('/api/v1/health/'):
            return None
        
        if request.path.startswith('/api/v1/'):
            ip = self.get_client_ip(request)
            user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
            
            if not self.check_rate_limit(f'ip:{ip}', self.RATE_LIMIT_PER_MINUTE, 60):
                logger.warning(f'Rate limit exceeded for IP: {ip}')
                return JsonResponse(
                    {'error': 'Too many requests. Please try again later.'},
                    status=429
                )
            
            if user_id:
                if not self.check_rate_limit(f'user:{user_id}', self.RATE_LIMIT_PER_HOUR, 3600):
                    logger.warning(f'Rate limit exceeded for user: {user_id}')
                    return JsonResponse(
                        {'error': 'Too many requests. Please try again later.'},
                        status=429
                    )
        
        return None
    
    def get_client_ip(self, request: HttpRequest) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        cache_key = f'rate_limit:{key}'
        current = cache.get(cache_key, 0)
        
        if current >= limit:
            return False
        
        cache.set(cache_key, current + 1, window)
        return True


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adding security headers for protection against attacks.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'"
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """Logging all requests for audit."""
    
    def process_request(self, request: HttpRequest) -> None:
        if request.path.startswith('/api/v1/'):
            request.start_time = time.time()
        return None
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
            
            logger.info(
                f'API Request: {request.method} {request.path} | '
                f'User: {user_id} | '
                f'Status: {response.status_code} | '
                f'Duration: {duration:.3f}s'
            )
        
        return response
