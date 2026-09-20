from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.permissions import AnyStaffMixin, ManagerOrAdminMixin, role_required

from .forms import CustomerForm
from .models import Customer


class CustomerListView(AnyStaffMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 15

    def get_queryset(self):
        qs = Customer.objects.all()
        q = self.request.GET.get('q')
        ctype = self.request.GET.get('type')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q))
        if ctype:
            qs = qs.filter(customer_type=ctype)
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_type'] = self.request.GET.get('type', '')
        return ctx


class CustomerDetailView(AnyStaffMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['purchase_history'] = self.object.sales.order_by('-sale_date')[:20]
        return ctx


class CustomerCreateView(AnyStaffMixin, CreateView):
    """Employees are allowed to add customers (spec section 4)."""
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        messages.success(self.request, 'Customer added successfully.')
        return super().form_valid(form)


class CustomerUpdateView(ManagerOrAdminMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        messages.success(self.request, 'Customer updated successfully.')
        return super().form_valid(form)


@role_required('ADMIN', 'MANAGER')
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    messages.success(request, 'Customer deleted.')
    return redirect('customers:list')
