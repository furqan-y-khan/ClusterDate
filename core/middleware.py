import time
import json
import logging
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseServerError
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Middleware to implement rate limiting for various endpoints
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Skip rate limiting for local development/admins
        if client_ip in ['127.0.0.1', 'localhost'] or request.user.is_staff:
            return self.get_response(request)
        
        # Check if IP is blocked
        if self.is_ip_blocked(client_ip):
            return self.rate_limit_response(request, "Your IP has been temporarily blocked due to excessive requests.")
        
        # Determine which rate limit to apply based on the request
        rate_limit_type = self.get_rate_limit_type(request)
        
        if rate_limit_type:
            # Check rate limit
            if self.is_rate_limited(client_ip, rate_limit_type):
                self.maybe_block_ip(client_ip, rate_limit_type)
                return self.rate_limit_response(request, f"Rate limit exceeded for {rate_limit_type} requests.")
            
            # Update request counter
            self.update_request_count(client_ip, rate_limit_type)
        
        # Process request normally
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """
        Get client IP address from request, considering proxy headers
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_rate_limit_type(self, request):
        """
        Determine which rate limit type applies to this request
        """
        path = request.path_info.lstrip('/')
        
        # Login rate limiting
        if request.method == 'POST' and path in ['accounts/login/', 'accounts/firebase-login/', 'auth/login/']:
            return 'login'
        
        # API rate limiting
        if path.startswith('api/'):
            return 'api'
        
        # Profile view rate limiting
        if path.startswith('accounts/profile/') and request.method == 'GET':
            return 'profile'
        
        # No rate limiting for this request
        return None
    
    def is_rate_limited(self, client_ip, rate_limit_type):
        """
        Check if the client has exceeded the rate limit
        """
        if rate_limit_type not in settings.RATE_LIMIT:
            return False
        
        limit = settings.RATE_LIMIT[rate_limit_type]['limit']
        cache_key = f"rate_limit:{rate_limit_type}:{client_ip}"
        
        # Get current request count and timestamps
        cached_data = cache.get(cache_key)
        if not cached_data:
            return False
        
        request_data = json.loads(cached_data)
        timestamps = request_data.get('timestamps', [])
        
        # Clean up old timestamps
        window = settings.RATE_LIMIT[rate_limit_type]['window']
        current_time = time.time()
        valid_timestamps = [ts for ts in timestamps if current_time - ts < window]
        
        # Check if number of valid timestamps exceeds limit
        return len(valid_timestamps) >= limit
    
    def update_request_count(self, client_ip, rate_limit_type):
        """
        Update the request count for rate limiting
        """
        if rate_limit_type not in settings.RATE_LIMIT:
            return
        
        cache_key = f"rate_limit:{rate_limit_type}:{client_ip}"
        window = settings.RATE_LIMIT[rate_limit_type]['window']
        
        # Get current request data
        cached_data = cache.get(cache_key)
        current_time = time.time()
        
        if cached_data:
            request_data = json.loads(cached_data)
            timestamps = request_data.get('timestamps', [])
            
            # Clean up old timestamps
            valid_timestamps = [ts for ts in timestamps if current_time - ts < window]
            
            # Add new timestamp
            valid_timestamps.append(current_time)
            request_data['timestamps'] = valid_timestamps
        else:
            request_data = {
                'timestamps': [current_time]
            }
        
        # Store updated data in cache
        cache.set(cache_key, json.dumps(request_data), window * 2)  # Cache for 2x window time
    
    def maybe_block_ip(self, client_ip, rate_limit_type):
        """
        Block an IP if it consistently exceeds rate limits
        """
        cache_key = f"rate_limit_violations:{client_ip}"
        violations = cache.get(cache_key, 0)
        
        # Increment violation count
        violations += 1
        cache.set(cache_key, violations, 3600)  # Store for 1 hour
        
        # Block IP if violations exceed threshold
        if violations >= 3:  # 3 violations within an hour
            blocked_ips = cache.get(settings.BLOCKED_IPS_CACHE_KEY, {})
            blocked_ips[client_ip] = time.time() + settings.IP_BLOCK_DURATION
            cache.set(settings.BLOCKED_IPS_CACHE_KEY, blocked_ips, 86400)  # Store for 1 day
            
            logger.warning(f"IP {client_ip} has been blocked for {settings.IP_BLOCK_DURATION} seconds")
    
    def is_ip_blocked(self, client_ip):
        """
        Check if an IP is currently blocked
        """
        blocked_ips = cache.get(settings.BLOCKED_IPS_CACHE_KEY, {})
        if client_ip in blocked_ips:
            expiry_time = blocked_ips[client_ip]
            if time.time() < expiry_time:
                return True
            else:
                # Remove expired block
                del blocked_ips[client_ip]
                cache.set(settings.BLOCKED_IPS_CACHE_KEY, blocked_ips, 86400)  # Store for 1 day
        return False
    
    def rate_limit_response(self, request, message):
        """
        Return an appropriate response for rate limited requests
        """
        if request.headers.get('Content-Type') == 'application/json' or request.path_info.startswith('/api/'):
            return JsonResponse({'error': message, 'status': 'rate_limited'}, status=429)
        else:
            return render(request, 'core/rate_limited.html', {'message': message}, status=429)


class BlockedIPMiddleware:
    """
    Middleware to block requests from blacklisted IP addresses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check if IP is in the blocklist (admin-defined permanent blocks)
        if self.is_ip_in_blocklist(client_ip):
            return self.blocked_response(request, "This IP address has been blocked.")
        
        # Process request normally
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """
        Get client IP address from request, considering proxy headers
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_ip_in_blocklist(self, client_ip):
        """
        Check if the IP is in the admin-defined blocklist
        """
        # Get blocklist from database or settings
        # For now, we'll use a hardcoded list for illustration
        blocklist = getattr(settings, 'IP_BLOCKLIST', [])
        return client_ip in blocklist
    
    def blocked_response(self, request, message):
        """
        Return an appropriate response for blocked IPs
        """
        if request.headers.get('Content-Type') == 'application/json' or request.path_info.startswith('/api/'):
            return JsonResponse({'error': message, 'status': 'blocked'}, status=403)
        else:
            return render(request, 'core/blocked.html', {'message': message}, status=403)


class ExceptionMiddleware(MiddlewareMixin):
    """
    Middleware to handle exceptions globally and log them properly.
    """
    
    def process_exception(self, request, exception):
        """
        Process exceptions raised during request processing.
        
        Args:
            request: The HTTP request object
            exception: The exception that was raised
            
        Returns:
            HttpResponse or None: If None, Django will continue with its normal
            exception handling. Otherwise, the returned response is used.
        """
        # Get the logger for core.middleware
        logger = logging.getLogger('core.middleware')
        
        # Log the exception with traceback
        logger.error(
            f"Exception caught in middleware: {str(exception)}",
            exc_info=True,
            extra={
                'request_path': request.path,
                'request_method': request.method,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'remote_addr': request.META.get('REMOTE_ADDR', 'Unknown'),
            }
        )
        
        # In production, return a custom 500 error page
        if not settings.DEBUG:
            html = render_to_string('core/errors/500.html', {'request': request})
            return HttpResponseServerError(html)
        
        # In debug mode, let Django handle it with its detailed error page
        return None 