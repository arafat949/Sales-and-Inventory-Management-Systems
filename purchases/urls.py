from django.urls import path

from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.PurchaseListView.as_view(), name='list'),
    path('add/', views.purchase_create, name='add'),
    path('<int:pk>/', views.PurchaseDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.purchase_edit, name='edit'),
    path('<int:pk>/complete/', views.purchase_complete, name='complete'),
    path('<int:pk>/cancel/', views.purchase_cancel, name='cancel'),
    path('<int:pk>/delete/', views.purchase_delete, name='delete'),
]
