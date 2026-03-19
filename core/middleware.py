from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

class LastSeenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update last seen every request
            from django.contrib.auth import get_user_model
            User = get_user_model()
            User.objects.filter(id=request.user.id).update(last_seen=timezone.now())
