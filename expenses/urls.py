from django.urls import path

from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.ExpenseListView.as_view(), name='index'),
    path('add/', views.ExpenseCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.expense_delete, name='delete'),
]
