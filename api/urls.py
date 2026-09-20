from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('categories', views.CategoryViewSet, basename='category')
router.register('products', views.ProductViewSet, basename='product')
router.register('customers', views.CustomerViewSet, basename='customer')
router.register('suppliers', views.SupplierViewSet, basename='supplier')
router.register('purchases', views.PurchaseViewSet, basename='purchase')
router.register('sales', views.SaleViewSet, basename='sale')
router.register('inventory-transactions', views.InventoryTransactionViewSet, basename='inventory-transaction')
router.register('expenses', views.ExpenseViewSet, basename='expense')
router.register('notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('dashboard/summary/', views.dashboard_summary, name='dashboard-summary'),
    path('', include(router.urls)),
]
