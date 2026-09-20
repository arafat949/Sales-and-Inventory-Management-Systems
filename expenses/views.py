from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.permissions import ManagerOrAdminMixin, role_required
from notifications.services import check_high_expense_notification

from .forms import ExpenseForm
from .models import Expense


class ExpenseListView(ManagerOrAdminMixin, ListView):
    """Expenses are Admin/Manager only (spec section 4)."""
    model = Expense
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20

    def get_queryset(self):
        qs = Expense.objects.select_related('created_by')
        q = self.request.GET.get('q')
        category = self.request.GET.get('category')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if category:
            qs = qs.filter(category=category)
        if date_from:
            qs = qs.filter(expense_date__gte=date_from)
        if date_to:
            qs = qs.filter(expense_date__lte=date_to)
        return qs.order_by('-expense_date', '-id')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Expense.Category.choices
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['current_date_from'] = self.request.GET.get('date_from', '')
        ctx['current_date_to'] = self.request.GET.get('date_to', '')
        ctx['total_amount'] = sum(e.amount for e in self.get_queryset())
        return ctx


class ExpenseCreateView(ManagerOrAdminMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:index')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Expense recorded successfully.')
        response = super().form_valid(form)
        check_high_expense_notification(self.object)
        return response


class ExpenseUpdateView(ManagerOrAdminMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:index')

    def form_valid(self, form):
        messages.success(self.request, 'Expense updated successfully.')
        return super().form_valid(form)


@role_required('ADMIN', 'MANAGER')
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    messages.success(request, 'Expense deleted.')
    return redirect('expenses:index')
