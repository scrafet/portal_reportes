from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import UserSession

@receiver(user_logged_in)
def update_user_session(sender, user, request, **kwargs):
    # Ensure session key exists
    if not request.session.session_key:
        request.session.save()
        
    UserSession.objects.update_or_create(
        user=user,
        defaults={
            'session_key': request.session.session_key,
            'last_login_ip': request.META.get('REMOTE_ADDR')
        }
    )
