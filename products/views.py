from django.contrib import messages
from django.db.models import F, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.permissions import AnyStaffMixin, ManagerOrAdminMixin, role_required
from inventory.models import InventoryTransaction

from .forms import CategoryForm, ProductForm
from .models import Category, Product


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
class CategoryListView(ManagerOrAdminMixin, ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    paginate_by = 12

    def get_queryset(self):
        qs = Category.objects.all().order_by('name')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['current_q'] = self.request.GET.get('q', '')
        return ctx


class CategoryCreateView(ManagerOrAdminMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:categories')

    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully.')
        return super().form_valid(form)


class CategoryUpdateView(ManagerOrAdminMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:categories')

    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully.')
        return super().form_valid(form)


@role_required('ADMIN', 'MANAGER')
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if category.products.exists():
        messages.error(
            request,
            f'Cannot delete "{category.name}" — {category.products.count()} product(s) '
            'still use this category. Reassign or remove them first.'
        )
    else:
        category.delete()
        messages.success(request, 'Category deleted.')
    return redirect('products:categories')


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
class ProductListView(AnyStaffMixin, ListView):
    """Viewable by all roles; write actions are gated separately (Employee = read-only)."""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 15

    def get_queryset(self):
        qs = Product.objects.select_related('category', 'supplier')
        q = self.request.GET.get('q')
        category_id = self.request.GET.get('category')
        status = self.request.GET.get('status')
        sort = self.request.GET.get('sort', 'name')

        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(category__name__icontains=q))
        if category_id:
            qs = qs.filter(category_id=category_id)
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        elif status == 'low_stock':
            qs = qs.filter(current_stock__lte=F('minimum_stock'), current_stock__gt=0)
        elif status == 'out_of_stock':
            qs = qs.filter(current_stock=0)

        allowed_sorts = {
            'name': 'name', '-name': '-name',
            'price': 'selling_price', '-price': '-selling_price',
            'stock': 'current_stock', '-stock': '-current_stock',
        }
        return qs.order_by(allowed_sorts.get(sort, 'name'))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.filter(is_active=True).order_by('name')
        ctx['current_q'] = self.request.GET.get('q', '')
        ctx['current_category'] = self.request.GET.get('category', '')
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['current_sort'] = self.request.GET.get('sort', 'name')
        return ctx


class ProductDetailView(AnyStaffMixin, DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stock_transactions'] = self.object.inventory_transactions.select_related('created_by')[:10]
        return ctx


class ProductCreateView(ManagerOrAdminMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        response = super().form_valid(form)
        initial_stock = form.cleaned_data.get('initial_stock') or 0
        if initial_stock:
            self.object.current_stock = initial_stock
            self.object.save(update_fields=['current_stock'])
            InventoryTransaction.objects.create(
                product=self.object, transaction_type='ADJUSTMENT',
                quantity=initial_stock, previous_stock=0, new_stock=initial_stock,
                reference='Initial stock on product creation', created_by=self.request.user,
            )
        messages.success(self.request, 'Product created successfully.')
        return response


class ProductUpdateView(ManagerOrAdminMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        messages.success(self.request, 'Product updated successfully.')
        return super().form_valid(form)


@role_required('ADMIN', 'MANAGER')
def product_delete(request, pk):
    """Employees cannot delete products (spec section 4)."""
    product = get_object_or_404(Product, pk=pk)
    try:
        product.delete()
        messages.success(request, 'Product deleted.')
    except ProtectedError:
        messages.error(
            request,
            f'Cannot delete "{product.name}" — it has purchase/sale history. '
            'Consider marking it inactive instead.'
        )
    return redirect('products:list')


@role_required('ADMIN', 'MANAGER')
def product_toggle_active(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])
    messages.success(request, f"Product {'activated' if product.is_active else 'deactivated'}.")
    return redirect('products:list')
