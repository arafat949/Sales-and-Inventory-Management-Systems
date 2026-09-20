from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from inventory.models import InventoryTransaction
from products.models import Category, Product

from .models import Sale


class SaleStockTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('salesuser', password='pass12345', role='EMPLOYEE')
        self.category = Category.objects.create(name='Sales Test Category')
        self.product = Product.objects.create(
            name='Sale Test Product', sku='SKU-SALE-1', category=self.category,
            purchase_price=Decimal('10'), selling_price=Decimal('25'),
            current_stock=10, minimum_stock=3,
        )
        self.client.login(username='salesuser', password='pass12345')

    def _post_sale(self, quantity):
        return self.client.post(reverse('sales:add'), {
            'customer': '', 'payment_method': 'CASH', 'payment_status': 'PAID',
            'discount': '0', 'tax': '0',
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '1', 'items-MAX_NUM_FORMS': '1000',
            'items-0-product': self.product.id, 'items-0-quantity': str(quantity),
            'items-0-unit_price': str(self.product.selling_price),
        }, follow=True)

    def test_sale_reduces_stock_and_logs_transaction(self):
        self._post_sale(4)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 6)

        sale = Sale.objects.latest('id')
        self.assertEqual(sale.status, 'COMPLETED')
        self.assertEqual(sale.total, Decimal('100.00'))

        txn = InventoryTransaction.objects.filter(reference=f"INV-{sale.id:05d}").first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.transaction_type, 'SALE')
        self.assertEqual(txn.quantity, -4)

    def test_insufficient_stock_blocks_sale(self):
        initial_count = Sale.objects.count()
        response = self._post_sale(999)
        self.assertEqual(Sale.objects.count(), initial_count)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10)
        self.assertContains(response, 'Insufficient stock')

    def test_cancel_sale_restores_stock(self):
        self._post_sale(5)
        self.product.refresh_from_db()
        self.assertEqual(self.product.current_stock, 5)

        sale = Sale.objects.latest('id')
        # Cancelling requires Manager/Admin
        manager = User.objects.create_user('salesmgr', password='pass12345', role='MANAGER')
        self.client.login(username='salesmgr', password='pass12345')
        self.client.get(reverse('sales:cancel', args=[sale.id]))

        self.product.refresh_from_db()
        sale.refresh_from_db()
        self.assertEqual(self.product.current_stock, 10)
        self.assertEqual(sale.status, 'CANCELLED')
