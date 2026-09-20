from rest_framework import serializers

from customers.models import Customer
from expenses.models import Expense
from inventory.models import InventoryTransaction
from notifications.models import Notification
from products.models import Category, Product
from purchases.models import Purchase, PurchaseItem
from sales.models import Sale, SaleItem
from suppliers.models import Supplier


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'product_count', 'created_at', 'updated_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    stock_status = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 'supplier', 'description',
            'purchase_price', 'selling_price', 'current_stock', 'minimum_stock', 'unit',
            'expiry_date', 'image', 'is_active', 'stock_status', 'created_at', 'updated_at',
        ]
        # Stock only changes through Purchases/Sales/Adjustments — never a direct API write.
        read_only_fields = ['current_stock']

    def validate_sku(self, value):
        qs = Product.objects.filter(sku__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('A product with this SKU already exists.')
        return value

    def validate_purchase_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Purchase price cannot be negative.')
        return value

    def validate_selling_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Selling price cannot be negative.')
        return value

    def validate_minimum_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('Minimum stock cannot be negative.')
        return value


class CustomerSerializer(serializers.ModelSerializer):
    total_orders = serializers.ReadOnlyField()
    total_spent = serializers.ReadOnlyField()

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'phone', 'email', 'address', 'customer_type',
            'total_orders', 'total_spent', 'created_at', 'updated_at',
        ]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'company_name', 'contact_person', 'phone', 'email', 'address', 'created_at', 'updated_at']


class PurchaseItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = PurchaseItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_cost', 'subtotal']


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)

    class Meta:
        model = Purchase
        fields = [
            'id', 'supplier', 'supplier_name', 'purchase_date', 'total_amount',
            'payment_status', 'status', 'notes', 'items', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['total_amount', 'status', 'created_by']


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal']


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Sale
        fields = [
            'id', 'customer', 'customer_name', 'sale_date', 'subtotal', 'discount', 'tax', 'total',
            'payment_method', 'payment_status', 'status', 'items', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['subtotal', 'total', 'status', 'created_by']

    def get_customer_name(self, obj):
        return obj.customer.name if obj.customer else 'Walk-in customer'


class InventoryTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'product', 'product_name', 'transaction_type', 'quantity',
            'previous_stock', 'new_stock', 'reference', 'created_by',
            'created_by_username', 'created_at',
        ]
        read_only_fields = ['previous_stock', 'new_stock', 'created_by']


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'title', 'category', 'amount', 'description', 'expense_date', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_by']

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError('Amount cannot be negative.')
        return value


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'message', 'is_read', 'created_at']
