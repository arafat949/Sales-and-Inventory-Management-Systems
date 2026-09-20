from django.contrib import messages
from django.db.models import F, OuterRef, Q, Subquery
from django.shortcuts import redirect, render
from django.views.generic import ListView

from accounts.permissions import AnyStaffMixin, role_required
from notifications.services import check_stock_notification
from products.models import Product

from .forms import StockAdjustmentForm
from .models import InventoryTransaction


class InventoryListView(AnyStaffMixin, ListView):
    """Dedicated inventory page (spec section 14) — viewable by all roles."""
    model = Product
    template_name = 'inventory/inventory_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        last_txn = InventoryTransaction.objects.filter(product=OuterRef('pk')).order_by('-created_at')
        qs = (
            Product.objects.filter(is_active=True)
            .select_related('category')
            .annotate(last_stock_update=Subquery(last_txn.values('created_at')[:1]))
        )
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
        if status == 'low_stock':
            qs = qs.filter(current_stock__lte=F('minimum_stock'), current_stock__gt=0)
        elif status == 'out_of_stock':
            qs = qs.filter(current_stock=0)
        elif status == 'in_stock':
            qs = qs.filter(current_stock__gt=F('minimum_stock'))
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_status'] = self.request.GET.get('status', '')
        return ctx


class StockHistoryListView(AnyStaffMixin, ListView):
    """Every stock-changing action logs here (spec section 15)."""
    model = InventoryTransaction
    template_name = 'inventory/stock_history.html'
    context_object_name = 'transactions'
    paginate_by = 25

    def get_queryset(self):
        qs = InventoryTransaction.objects.select_related('product', 'created_by')
        product_id = self.request.GET.get('product')
        ttype = self.request.GET.get('type')
        q = self.request.GET.get('q')
        if product_id:
            qs = qs.filter(product_id=product_id)
        if ttype:
            qs = qs.filter(transaction_type=ttype)
        if q:
            qs = qs.filter(Q(product__name__icontains=q) | Q(reference__icontains=q))
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['products'] = Product.objects.filter(is_active=True).order_by('name')
        ctx['current_product'] = self.request.GET.get('product', '')
        ctx['current_type'] = self.request.GET.get('type', '')
        ctx['current_q'] = self.request.GET.get('q', '')
        return ctx


@role_required('ADMIN', 'MANAGER')
def stock_adjustment(request):
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            new_stock = form.cleaned_data['new_stock']
            reason = form.cleaned_data['reason'] or 'Manual stock adjustment'
            previous_stock = product.current_stock
            delta = new_stock - previous_stock

            if delta == 0:
                messages.info(request, 'No change — new stock equals the current stock.')
            else:
                product.current_stock = new_stock
                product.save(update_fields=['current_stock'])
                InventoryTransaction.objects.create(
                    product=product, transaction_type='ADJUSTMENT',
                    quantity=delta, previous_stock=previous_stock, new_stock=new_stock,
                    reference=reason, created_by=request.user,
                )
                check_stock_notification(product)
                messages.success(
                    request,
                    f"Stock for \"{product.name}\" adjusted from {previous_stock} to {new_stock}."
                )
            return redirect('inventory:index')
        messages.error(request, 'Please fix the errors below.')
    else:
        form = StockAdjustmentForm()
    return render(request, 'inventory/stock_adjustment_form.html', {'form': form})
