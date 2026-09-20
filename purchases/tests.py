from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from products.models import Category, Product
from suppliers.models import Supplier

from .models import Purchase


class PurchaseCompletionTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user('purchmgr', password='pass12345', role='MANAGER')
        self.category = Category.objects.create(name='Purchase Test Category')
        self.supplier = Supplier.objects.create(company_name='Test Supplier', phone='0170000000')
        self.product = Product.objects.create(
            name='Purchase Test Product', sku='SKU-PUR-1', category=self.category,
            purchase_price=Decimal('20'), selling_price=Decimal('35'), current_stock=5,
        )
        self.client.login(username='purchmgr', password='pass12345')

    def _create_pending_purchase(self, quantity=30):
        self.client.post(reverse('purchases:add'), {
            'supplier': self.supplier.id, 'purchase_date': '2026-09-01',
            'payment_status': 'UNPAID', 'notes': '',
            'items-TOTAL_FORMS': '1', 'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '1', 'items-MAX_NUM_FORMS': '1000',
            'items-0-product': self.product.id, 'items-0-quantity': str(quantity),
            'items-0-unit_cost': str(self.product.purchase_price),
        })
        return Purchase.objects.latest('id')

    def test_completion_increases_stock(self):
        purchase = self._create_pending_purchase(30)
        self.assertEqual(purchase.status, 'PENDING')

        self.client.get(reverse('purchases:complete', args=[purchase.id]))
        self.product.refresh_from_db()
        purchase.refresh_from_db()

        self.assertEqual(self.product.current_stock, 35)
        self.assertEqual(purchase.status, 'COMPLETED')

    def test_double_completion_is_blocked(self):
        purchase = self._create_pending_purchase(30)
        self.client.get(reverse('purchases:complete', args=[purchase.id]))
        self.client.get(reverse('purchases:complete', args=[purchase.id]))

        self.product.refresh_from_db()
        # Stock should only have been increased once, not twice
        self.assertEqual(self.product.current_stock, 35)

    def test_completed_purchase_cannot_be_deleted(self):
        purchase = self._create_pending_purchase(30)
        self.client.get(reverse('purchases:complete', args=[purchase.id]))
        self.client.get(reverse('purchases:delete', args=[purchase.id]))
        self.assertTrue(Purchase.objects.filter(id=purchase.id).exists())
