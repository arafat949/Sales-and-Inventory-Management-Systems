from django.db.models import F, Q, Sum
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from customers.models import Customer
from expenses.models import Expense
from inventory.models import InventoryTransaction
from notifications.models import Notification
from products.models import Category, Product
from purchases.models import Purchase
from sales.models import Sale
from suppliers.models import Supplier

from .permissions import IsAnyStaff, IsManagerOrAdmin, ReadOnlyOrManagerAdmin
from .serializers import (
    CategorySerializer, CustomerSerializer, ExpenseSerializer,
    InventoryTransactionSerializer, NotificationSerializer, ProductSerializer,
    PurchaseSerializer, SaleSerializer, SupplierSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyOrManagerAdmin]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [ReadOnlyOrManagerAdmin]

    def get_queryset(self):
        qs = Product.objects.select_related('category', 'supplier').all().order_by('name')
        category = self.request.query_params.get('category')
        is_active = self.request.query_params.get('is_active')
        search = self.request.query_params.get('search')
        if category:
            qs = qs.filter(category_id=category)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('1', 'true', 'yes'))
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search))
        return qs


class CustomerViewSet(viewsets.ModelViewSet):
    """Employees may add customers per spec, hence IsAnyStaff rather than ReadOnlyOrManagerAdmin."""
    queryset = Customer.objects.all().order_by('name')
    serializer_class = CustomerSerializer
    permission_classes = [IsAnyStaff]


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all().order_by('company_name')
    serializer_class = SupplierSerializer
    permission_classes = [IsManagerOrAdmin]


class PurchaseViewSet(viewsets.ReadOnlyModelViewSet):
    """Purchases involve stock-affecting business logic best handled via the web UI's
    transactional completion flow; the API exposes them read-only for integration/reporting."""
    queryset = Purchase.objects.select_related('supplier').prefetch_related('items').all().order_by('-purchase_date')
    serializer_class = PurchaseSerializer
    permission_classes = [IsManagerOrAdmin]


class SaleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sale.objects.select_related('customer').prefetch_related('items').all().order_by('-sale_date')
    serializer_class = SaleSerializer
    permission_classes = [IsAnyStaff]


class InventoryTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryTransaction.objects.select_related('product', 'created_by').all().order_by('-created_at')
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsAnyStaff]


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all().order_by('-expense_date')
    serializer_class = ExpenseSerializer
    permission_classes = [IsManagerOrAdmin]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAnyStaff]

    def get_queryset(self):
        return Notification.objects.filter(
            Q(user=self.request.user) | Q(user__isnull=True)
        ).order_by('-created_at')


@api_view(['GET'])
@permission_classes([IsAnyStaff])
def dashboard_summary(request):
    """Same figures as the web dashboard, exposed as JSON for external integrations."""
    total_sales = Sale.objects.filter(status='COMPLETED').count()
    total_revenue = Sale.objects.filter(status='COMPLETED').aggregate(s=Sum('total'))['s'] or 0
    total_expenses = Expense.objects.aggregate(s=Sum('amount'))['s'] or 0
    total_products = Product.objects.filter(is_active=True).count()
    total_customers = Customer.objects.count()
    total_suppliers = Supplier.objects.count()
    low_stock_count = Product.objects.filter(is_active=True, current_stock__lte=F('minimum_stock')).count()

    return Response({
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': total_revenue - total_expenses,
        'total_products': total_products,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
        'low_stock_count': low_stock_count,
    })
