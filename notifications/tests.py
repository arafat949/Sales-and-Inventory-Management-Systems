from decimal import Decimal

from django.test import TestCase

from expenses.models import Expense
from products.models import Category, Product

from .models import Notification
from .services import check_high_expense_notification, check_stock_notification


class StockNotificationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Notif Test Category')
        self.product = Product.objects.create(
            name='Notif Test Product', sku='SKU-NOTIF-1', category=self.category,
            purchase_price=Decimal('10'), selling_price=Decimal('20'),
            current_stock=20, minimum_stock=5,
        )

    def test_out_of_stock_notification_created(self):
        self.product.current_stock = 0
        self.product.save()
        check_stock_notification(self.product)

        notif = Notification.objects.filter(notification_type='OUT_OF_STOCK', is_read=False).first()
        self.assertIsNotNone(notif)
        self.assertIn(self.product.name, notif.message)

    def test_duplicate_notification_not_created(self):
        self.product.current_stock = 0
        self.product.save()
        check_stock_notification(self.product)
        check_stock_notification(self.product)

        count = Notification.objects.filter(
            notification_type='OUT_OF_STOCK', is_read=False, message__icontains=self.product.name
        ).count()
        self.assertEqual(count, 1)

    def test_notification_auto_resolves_on_restock(self):
        self.product.current_stock = 0
        self.product.save()
        check_stock_notification(self.product)

        self.product.current_stock = 50
        self.product.save()
        check_stock_notification(self.product)

        unresolved = Notification.objects.filter(
            notification_type='OUT_OF_STOCK', is_read=False, message__icontains=self.product.name
        ).exists()
        self.assertFalse(unresolved)


class HighExpenseNotificationTests(TestCase):
    def test_unusually_high_expense_flagged(self):
        for amount in [100, 120, 110]:
            Expense.objects.create(title='Regular', category='OTHER', amount=Decimal(amount), expense_date='2026-09-01')

        big_expense = Expense.objects.create(
            title='Huge One', category='OTHER', amount=Decimal(5000), expense_date='2026-09-10'
        )
        check_high_expense_notification(big_expense)

        notif = Notification.objects.filter(notification_type='HIGH_EXPENSE').first()
        self.assertIsNotNone(notif)
        self.assertIn('Huge One', notif.message)

    def test_normal_expense_not_flagged(self):
        for amount in [100, 120, 110]:
            Expense.objects.create(title='Regular', category='OTHER', amount=Decimal(amount), expense_date='2026-09-01')

        normal_expense = Expense.objects.create(
            title='Another Regular', category='OTHER', amount=Decimal(115), expense_date='2026-09-10'
        )
        check_high_expense_notification(normal_expense)

        self.assertFalse(Notification.objects.filter(notification_type='HIGH_EXPENSE').exists())
