import time
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.conf import settings
from django.core.cache import cache

class SingleSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Key for storing the valid session key for this user
            cache_key = f"user_session_{request.user.id}"
            current_session_key = request.session.session_key
            
            # Get the stored session key
            stored_session_key = cache.get(cache_key)
            
            if stored_session_key and stored_session_key != current_session_key:
                # If stored key exists and doesn't match current, force logout
                logout(request)
                return redirect('login')  # Adjust 'login' to your actual login url name
            
            # If no stored key or keys match (or just logged in), update the cache
            # We update it to ensure we extend if needed, or set if missing
            if not stored_session_key:
                 cache.set(cache_key, current_session_key, timeout=None)
        
        response = self.get_response(request)
        return response

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            now = time.time()
            
            # 3 minutes in seconds
            timeout = getattr(settings, 'SESSION_COOKIE_AGE', 180) 
            
            if last_activity and (now - last_activity > timeout):
                logout(request)
                return redirect('login')
            
            request.session['last_activity'] = now
            
        response = self.get_response(request)
        return response
