from django.db.models import Q

from .models import Notification


def notifications_processor(request):
    """
    Makes unread notification count / list available to every template
    (used by the top navbar bell icon and the sidebar badge).
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {}

    qs = Notification.objects.filter(
        Q(user=request.user) | Q(user__isnull=True), is_read=False
    ).order_by('-created_at')

    return {
        'unread_notifications_count': qs.count(),
        'unread_notifications': qs[:5],
    }
