from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.InventoryListView.as_view(), name='index'),
    path('history/', views.StockHistoryListView.as_view(), name='history'),
    path('adjust/', views.stock_adjustment, name='adjust'),
]
