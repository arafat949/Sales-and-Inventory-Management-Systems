"""
Notification-generation logic (spec section 19). Called from the places that
change stock (purchases, sales, adjustments) or record an expense, rather
than from a background job — simple and sufficient at this project's scale.
"""
from .models import Notification


def check_stock_notification(product):
    """
    Called after ANY stock-changing action. Creates at most one *unread*
    alert per product+type at a time (no spam on repeated sales of an
    already-known-low item), and auto-resolves stale alerts once stock
    recovers.
    """
    if product.current_stock == 0:
        already_alerted = Notification.objects.filter(
            notification_type=Notification.NotificationType.OUT_OF_STOCK,
            message__icontains=product.name, is_read=False,
        ).exists()
        if not already_alerted:
            Notification.objects.create(
                notification_type=Notification.NotificationType.OUT_OF_STOCK,
                message=f'"{product.name}" is out of stock.',
            )
    elif product.current_stock <= product.minimum_stock:
        already_alerted = Notification.objects.filter(
            notification_type=Notification.NotificationType.LOW_STOCK,
            message__icontains=product.name, is_read=False,
        ).exists()
        if not already_alerted:
            Notification.objects.create(
                notification_type=Notification.NotificationType.LOW_STOCK,
                message=f'"{product.name}" is running low on stock '
                        f'({product.current_stock} left, minimum {product.minimum_stock}).',
            )
        # Stock recovered from zero but is still low — resolve the stale OUT_OF_STOCK alert.
        Notification.objects.filter(
            notification_type=Notification.NotificationType.OUT_OF_STOCK,
            message__icontains=product.name, is_read=False,
        ).update(is_read=True)
    else:
        # Healthy stock again — auto-resolve any stale low/out alerts for this product.
        Notification.objects.filter(
            notification_type__in=[
                Notification.NotificationType.LOW_STOCK,
                Notification.NotificationType.OUT_OF_STOCK,
            ],
            message__icontains=product.name, is_read=False,
        ).update(is_read=True)


def check_high_expense_notification(expense):
    """Flags an expense that's unusually high next to recent expenses in the same category."""
    from expenses.models import Expense

    recent = (
        Expense.objects.filter(category=expense.category)
        .exclude(pk=expense.pk)
        .order_by('-expense_date')[:5]
    )
    amounts = [e.amount for e in recent]
    if not amounts:
        return

    average = sum(amounts) / len(amounts)
    if average > 0 and expense.amount > average * 2:
        Notification.objects.create(
            notification_type=Notification.NotificationType.HIGH_EXPENSE,
            message=(
                f'Expense "{expense.title}" ({expense.amount}) is unusually high compared to '
                f'recent {expense.get_category_display()} expenses (avg {average:.0f}).'
            ),
        )
