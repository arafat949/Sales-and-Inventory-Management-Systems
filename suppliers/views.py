from django.contrib import messages
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.permissions import ManagerOrAdminMixin, role_required

from .forms import SupplierForm
from .models import Supplier


class SupplierListView(ManagerOrAdminMixin, ListView):
    """Suppliers are managed by Admin/Manager only (spec section 4)."""
    model = Supplier
    template_name = 'suppliers/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 15

    def get_queryset(self):
        qs = Supplier.objects.all()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(company_name__icontains=q) | Q(contact_person__icontains=q) | Q(phone__icontains=q))
        return qs.order_by('company_name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_q'] = self.request.GET.get('q', '')
        return ctx


class SupplierDetailView(ManagerOrAdminMixin, DetailView):
    model = Supplier
    template_name = 'suppliers/supplier_detail.html'
    context_object_name = 'supplier'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['supplied_products'] = self.object.products.all()[:20]
        ctx['purchase_history'] = self.object.purchases.order_by('-purchase_date')[:20]
        return ctx


class SupplierCreateView(ManagerOrAdminMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'
    success_url = reverse_lazy('suppliers:list')

    def form_valid(self, form):
        messages.success(self.request, 'Supplier added successfully.')
        return super().form_valid(form)


class SupplierUpdateView(ManagerOrAdminMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'
    success_url = reverse_lazy('suppliers:list')

    def form_valid(self, form):
        messages.success(self.request, 'Supplier updated successfully.')
        return super().form_valid(form)


@role_required('ADMIN', 'MANAGER')
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    try:
        supplier.delete()
        messages.success(request, 'Supplier deleted.')
    except ProtectedError:
        messages.error(
            request,
            f'Cannot delete "{supplier.company_name}" — it has purchase history. Remove related purchases first.'
        )
    return redirect('suppliers:list')
