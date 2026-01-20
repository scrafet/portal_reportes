from django.contrib.auth import logout
from .models import UserSession

class OneSessionPerUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                user_session = UserSession.objects.get(user=request.user)
                if user_session.session_key and user_session.session_key != request.session.session_key:
                    logout(request)
            except UserSession.DoesNotExist:
                if request.session.session_key:
                    UserSession.objects.create(
                        user=request.user,
                        session_key=request.session.session_key,
                        last_login_ip=request.META.get('REMOTE_ADDR')
                    )
        
        response = self.get_response(request)
        return response
