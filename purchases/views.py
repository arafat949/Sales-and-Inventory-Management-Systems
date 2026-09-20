from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from accounts.permissions import ManagerOrAdminMixin, role_required
from inventory.models import InventoryTransaction
from notifications.services import check_stock_notification

from .forms import PurchaseForm, PurchaseItemFormSet
from .models import Purchase


class PurchaseListView(ManagerOrAdminMixin, ListView):
    model = Purchase
    template_name = 'purchases/purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 15

    def get_queryset(self):
        qs = Purchase.objects.select_related('supplier')
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if q:
            qs = qs.filter(Q(supplier__company_name__icontains=q) | Q(id__icontains=q))
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-purchase_date', '-id')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_status'] = self.request.GET.get('status', '')
        return ctx


class PurchaseDetailView(ManagerOrAdminMixin, DetailView):
    model = Purchase
    template_name = 'purchases/purchase_detail.html'
    context_object_name = 'purchase'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['items'] = self.object.items.select_related('product')
        return ctx


@role_required('ADMIN', 'MANAGER')
def purchase_create(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        purchase = form.save(commit=False) if form.is_valid() else Purchase()
        purchase.created_by = request.user
        purchase.status = Purchase.Status.PENDING
        formset = PurchaseItemFormSet(request.POST, instance=purchase, prefix='items')

        if form.is_valid() and formset.is_valid():
            purchase.save()
            formset.instance = purchase
            formset.save()
            purchase.recalculate_total()
            messages.success(request, f"Purchase PUR-{purchase.id:05d} saved as Pending. Complete it to update stock.")
            return redirect('purchases:detail', pk=purchase.pk)
        messages.error(request, 'Please fix the errors below.')
    else:
        form = PurchaseForm()
        formset = PurchaseItemFormSet(instance=Purchase(), prefix='items')

    return render(request, 'purchases/purchase_form.html', {'form': form, 'formset': formset})


@role_required('ADMIN', 'MANAGER')
def purchase_edit(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if purchase.status != Purchase.Status.PENDING:
        messages.error(request, 'Only pending purchases can be edited.')
        return redirect('purchases:detail', pk=pk)

    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseItemFormSet(request.POST, instance=purchase, prefix='items')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            purchase.recalculate_total()
            messages.success(request, 'Purchase updated successfully.')
            return redirect('purchases:detail', pk=pk)
        messages.error(request, 'Please fix the errors below.')
    else:
        form = PurchaseForm(instance=purchase)
        formset = PurchaseItemFormSet(instance=purchase, prefix='items')

    return render(request, 'purchases/purchase_form.html', {'form': form, 'formset': formset, 'object': purchase})


@role_required('ADMIN', 'MANAGER')
@transaction.atomic
def purchase_complete(request, pk):
    """Marks a purchase COMPLETED and increases stock for every item (spec section 12)."""
    purchase = get_object_or_404(Purchase.objects.select_for_update(), pk=pk)
    if purchase.status != Purchase.Status.PENDING:
        messages.error(request, 'Only pending purchases can be completed.')
        return redirect('purchases:detail', pk=pk)
    if not purchase.items.exists():
        messages.error(request, 'Cannot complete a purchase with no items.')
        return redirect('purchases:detail', pk=pk)

    for item in purchase.items.select_related('product'):
        product = item.product
        previous_stock = product.current_stock
        product.current_stock = previous_stock + item.quantity
        product.save(update_fields=['current_stock'])
        InventoryTransaction.objects.create(
            product=product, transaction_type='PURCHASE',
            quantity=item.quantity, previous_stock=previous_stock, new_stock=product.current_stock,
            reference=f"PUR-{purchase.id:05d}", created_by=request.user,
        )
        check_stock_notification(product)

    purchase.status = Purchase.Status.COMPLETED
    purchase.save(update_fields=['status'])
    messages.success(request, f"Purchase PUR-{purchase.id:05d} completed — stock has been updated.")
    return redirect('purchases:detail', pk=pk)


@role_required('ADMIN', 'MANAGER')
def purchase_cancel(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if purchase.status != Purchase.Status.PENDING:
        messages.error(request, 'Only pending purchases can be cancelled.')
    else:
        purchase.status = Purchase.Status.CANCELLED
        purchase.save(update_fields=['status'])
        messages.success(request, f"Purchase PUR-{purchase.id:05d} cancelled.")
    return redirect('purchases:detail', pk=pk)


@role_required('ADMIN', 'MANAGER')
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if purchase.status == Purchase.Status.COMPLETED:
        messages.error(request, 'Completed purchases cannot be deleted, since stock has already been updated.')
        return redirect('purchases:detail', pk=pk)
    purchase.delete()
    messages.success(request, 'Purchase deleted.')
    return redirect('purchases:list')
