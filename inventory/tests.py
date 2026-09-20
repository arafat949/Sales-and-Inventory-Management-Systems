from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from products.models import Category, Product

from .models import InventoryTransaction


class StockAdjustmentTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user('invmgr', password='pass12345', role='MANAGER')
        self.employee = User.objects.create_user('invemp', password='pass12345', role='EMPLOYEE')
        self.category = Category.objects.create(name='Inventory Test Category')
        self.product = Product.objects.create(
            name='Adjustment Test Product', sku='SKU-ADJ-1', category=self.category,
            purchase_price=Decimal('10'), selling_price=Decimal('20'),
            current_stock=20, minimum_stock=5,
        )

    def test_manual_adjustment_updates_stock_and_logs_transaction(self):
        self.client.login(username='invmgr', password='pass12345')
        self.client.post(reverse('inventory:adjust'), {
            'product': self.product.id, 'new_stock': 35, 'reason': 'Physical count',
        })
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 35)

        txn = InventoryTransaction.objects.filter(product=self.product, transaction_type='ADJUSTMENT').first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.quantity, 15)
        self.assertEqual(txn.previous_stock, 20)
        self.assertEqual(txn.new_stock, 35)

    def test_employee_cannot_adjust_stock(self):
        self.client.login(username='invemp', password='pass12345')
        response = self.client.get(reverse('inventory:adjust'))
        self.assertEqual(response.status_code, 403)

    def test_employee_can_view_inventory(self):
        self.client.login(username='invemp', password='pass12345')
        response = self.client.get(reverse('inventory:index'))
        self.assertEqual(response.status_code, 200)
