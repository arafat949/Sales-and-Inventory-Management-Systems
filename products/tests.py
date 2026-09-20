from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .forms import ProductForm
from .models import Category, Product


class ProductValidationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Existing Product', sku='SKU-EXIST', category=self.category,
            purchase_price=Decimal('10'), selling_price=Decimal('20'),
            current_stock=50, minimum_stock=10,
        )

    def test_duplicate_sku_rejected(self):
        form = ProductForm(data={
            'name': 'New Product', 'sku': 'SKU-EXIST', 'category': self.category.id,
            'purchase_price': '5', 'selling_price': '15', 'minimum_stock': '5',
            'unit': 'PCS', 'is_active': True, 'initial_stock': 0,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('sku', form.errors)

    def test_negative_purchase_price_rejected(self):
        form = ProductForm(data={
            'name': 'New Product', 'sku': 'SKU-NEW1', 'category': self.category.id,
            'purchase_price': '-5', 'selling_price': '15', 'minimum_stock': '5',
            'unit': 'PCS', 'is_active': True, 'initial_stock': 0,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('purchase_price', form.errors)

    def test_stock_status_property(self):
        self.product.current_stock = 0
        self.assertEqual(self.product.stock_status, 'OUT_OF_STOCK')
        self.product.current_stock = 5
        self.assertEqual(self.product.stock_status, 'LOW_STOCK')
        self.product.current_stock = 100
        self.assertEqual(self.product.stock_status, 'IN_STOCK')


class CategoryDeletionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('cat_admin', password='pass12345', role='ADMIN')
        self.category = Category.objects.create(name='Protected Category')
        Product.objects.create(
            name='Linked Product', sku='SKU-LINK', category=self.category,
            purchase_price=Decimal('10'), selling_price=Decimal('20'),
        )
        self.client.login(username='cat_admin', password='pass12345')

    def test_category_with_products_cannot_be_deleted(self):
        self.client.get(reverse('products:category_delete', args=[self.category.id]))
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())

    def test_empty_category_can_be_deleted(self):
        empty_category = Category.objects.create(name='Empty Category')
        self.client.get(reverse('products:category_delete', args=[empty_category.id]))
        self.assertFalse(Category.objects.filter(id=empty_category.id).exists())
