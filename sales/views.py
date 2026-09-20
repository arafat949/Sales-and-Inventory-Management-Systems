from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from accounts.permissions import AnyStaffMixin, role_required
from inventory.models import InventoryTransaction
from notifications.services import check_stock_notification
from products.models import Product

from .forms import SaleForm, SaleItemFormSet
from .models import Sale


class SaleListView(AnyStaffMixin, ListView):
    """Viewable by everyone; Employees can also create sales (spec section 4)."""
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 15

    def get_queryset(self):
        qs = Sale.objects.select_related('customer', 'created_by')
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if q:
            qs = qs.filter(Q(customer__name__icontains=q) | Q(id__icontains=q))
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-sale_date', '-id')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_status'] = self.request.GET.get('status', '')
        return ctx


class SaleDetailView(AnyStaffMixin, DetailView):
    model = Sale
    template_name = 'sales/sale_detail.html'
    context_object_name = 'sale'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['items'] = self.object.items.select_related('product')
        return ctx


@login_required
@transaction.atomic
def sale_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        formset = SaleItemFormSet(request.POST, instance=Sale(), prefix='items')

        if form.is_valid() and formset.is_valid():
            sale = form.save(commit=False)
            sale.created_by = request.user
            sale.status = Sale.Status.COMPLETED
            sale.save()

            formset.instance = sale
            formset.save()
            sale.recalculate_totals()

            for item in sale.items.select_related('product'):
                product = item.product
                previous_stock = product.current_stock
                product.current_stock = previous_stock - item.quantity
                product.save(update_fields=['current_stock'])
                InventoryTransaction.objects.create(
                    product=product, transaction_type='SALE',
                    quantity=-item.quantity, previous_stock=previous_stock, new_stock=product.current_stock,
                    reference=f"INV-{sale.id:05d}", created_by=request.user,
                )
                check_stock_notification(product)

            messages.success(request, f"Sale INV-{sale.id:05d} completed successfully.")
            return redirect('sales:invoice', pk=sale.pk)
        messages.error(request, 'Please fix the errors below — check product stock availability.')
    else:
        form = SaleForm()
        formset = SaleItemFormSet(instance=Sale(), prefix='items')

    products_json = list(
        Product.objects.filter(is_active=True).values('id', 'name', 'selling_price', 'current_stock')
    )
    return render(request, 'sales/sale_form.html', {
        'form': form, 'formset': formset, 'products_json': products_json,
    })


@role_required('ADMIN', 'MANAGER')
@transaction.atomic
def sale_cancel(request, pk):
    """Cancels a completed sale and restores stock (spec-friendly return flow)."""
    sale = get_object_or_404(Sale.objects.select_for_update(), pk=pk)
    if sale.status != Sale.Status.COMPLETED:
        messages.error(request, 'Only completed sales can be cancelled.')
        return redirect('sales:detail', pk=pk)

    for item in sale.items.select_related('product'):
        product = item.product
        previous_stock = product.current_stock
        product.current_stock = previous_stock + item.quantity
        product.save(update_fields=['current_stock'])
        InventoryTransaction.objects.create(
            product=product, transaction_type='RETURN',
            quantity=item.quantity, previous_stock=previous_stock, new_stock=product.current_stock,
            reference=f"INV-{sale.id:05d} (cancelled)", created_by=request.user,
        )

    sale.status = Sale.Status.CANCELLED
    sale.save(update_fields=['status'])
    messages.success(request, f"Sale INV-{sale.id:05d} cancelled — stock restored.")
    return redirect('sales:detail', pk=pk)


@role_required('ADMIN', 'MANAGER')
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if sale.status == Sale.Status.COMPLETED:
        messages.error(request, 'Completed sales cannot be deleted directly — cancel it first to restore stock.')
        return redirect('sales:detail', pk=pk)
    sale.delete()
    messages.success(request, 'Sale deleted.')
    return redirect('sales:list')


@login_required
def sale_invoice(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('customer', 'created_by'), pk=pk)
    items = sale.items.select_related('product')
    from django.conf import settings
    return render(request, 'sales/invoice.html', {
        'sale': sale, 'items': items,
        'business_name': settings.BUSINESS_NAME, 'currency': settings.CURRENCY_SYMBOL,
    })
