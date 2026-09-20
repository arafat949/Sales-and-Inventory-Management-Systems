from django.urls import path

from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.SaleListView.as_view(), name='list'),
    path('add/', views.sale_create, name='add'),
    path('<int:pk>/', views.SaleDetailView.as_view(), name='detail'),
    path('<int:pk>/invoice/', views.sale_invoice, name='invoice'),
    path('<int:pk>/cancel/', views.sale_cancel, name='cancel'),
    path('<int:pk>/delete/', views.sale_delete, name='delete'),
]
