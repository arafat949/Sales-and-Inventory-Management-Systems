from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index, name='index'),
    path('sales/', views.sales_report, name='sales'),
    path('products/', views.product_sales_report, name='products'),
    path('customers/', views.customer_report, name='customers'),
    path('inventory/', views.inventory_report, name='inventory'),
    path('expenses/', views.expense_report, name='expenses'),
    path('profit/', views.profit_report, name='profit'),
]
