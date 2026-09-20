from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView

from accounts.permissions import AnyStaffMixin

from .models import Notification


class NotificationListView(AnyStaffMixin, ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        qs = Notification.objects.filter(Q(user=self.request.user) | Q(user__isnull=True))
        status = self.request.GET.get('status')
        ntype = self.request.GET.get('type')
        if status == 'unread':
            qs = qs.filter(is_read=False)
        elif status == 'read':
            qs = qs.filter(is_read=True)
        if ntype:
            qs = qs.filter(notification_type=ntype)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['current_type'] = self.request.GET.get('type', '')
        return ctx


@login_required
def mark_read(request, pk):
    notification = get_object_or_404(
        Notification.objects.filter(Q(user=request.user) | Q(user__isnull=True)), pk=pk
    )
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect('notifications:index')


@login_required
def mark_all_read(request):
    Notification.objects.filter(
        Q(user=request.user) | Q(user__isnull=True), is_read=False
    ).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:index')
