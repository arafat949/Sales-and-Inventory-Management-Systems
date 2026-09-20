from datetime import timedelta

from django.utils import timezone


def resolve_date_range(request, default_preset='month'):
    """
    Resolves a (date_from, date_to, preset) tuple from query params.
    Supports quick presets (today/week/month/year) or an explicit custom range.
    """
    today = timezone.localdate()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if date_from and date_to:
        return date_from, date_to, 'custom'

    preset = request.GET.get('preset', default_preset)
    if preset == 'today':
        return today, today, preset
    if preset == 'week':
        start = today - timedelta(days=today.weekday())
        return start, today, preset
    if preset == 'year':
        start = today.replace(month=1, day=1)
        return start, today, preset

    # default: this month
    start = today.replace(day=1)
    return start, today, 'month'
