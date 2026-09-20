from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import render

from accounts.permissions import role_required
from customers.models import Customer
from expenses.models import Expense
from products.models import Product
from sales.models import Sale, SaleItem

from .utils import resolve_date_range


@role_required('ADMIN', 'MANAGER')
def index(request):
    return render(request, 'reports/index.html')


@role_required('ADMIN', 'MANAGER')
def sales_report(request):
    date_from, date_to, preset = resolve_date_range(request)
    sales = Sale.objects.filter(status='COMPLETED', sale_date__date__gte=date_from, sale_date__date__lte=date_to)

    daily = (
        sales.annotate(day=TruncDate('sale_date'))
        .values('day')
        .annotate(orders=Count('id'), revenue=Sum('total'))
        .order_by('day')
    )
    total_orders = sales.count()
    total_revenue = sales.aggregate(s=Sum('total'))['s'] or 0
    avg_order_value = (total_revenue / total_orders) if total_orders else 0

    return render(request, 'reports/sales_report.html', {
        'date_from': date_from, 'date_to': date_to, 'preset': preset,
        'daily': daily, 'total_orders': total_orders,
        'total_revenue': total_revenue, 'avg_order_value': avg_order_value,
    })


@role_required('ADMIN', 'MANAGER')
def product_sales_report(request):
    date_from, date_to, preset = resolve_date_range(request)
    items = (
        SaleItem.objects.filter(
            sale__status='COMPLETED', sale__sale_date__date__gte=date_from, sale__sale_date__date__lte=date_to
        )
        .values('product__id', 'product__name', 'product__sku')
        .annotate(qty_sold=Sum('quantity'), revenue=Sum(F('quantity') * F('unit_price')))
        .order_by('-revenue')
    )
    total_revenue = sum(i['revenue'] or 0 for i in items)

    return render(request, 'reports/product_sales_report.html', {
        'date_from': date_from, 'date_to': date_to, 'preset': preset,
        'items': items, 'total_revenue': total_revenue,
    })


@role_required('ADMIN', 'MANAGER')
def customer_report(request):
    date_from, date_to, preset = resolve_date_range(request)
    sale_filter = Q(sales__status='COMPLETED', sales__sale_date__date__gte=date_from, sales__sale_date__date__lte=date_to)

    customers = (
        Customer.objects.annotate(
            orders=Count('sales', filter=sale_filter),
            spent=Sum('sales__total', filter=sale_filter),
        )
        .filter(orders__gt=0)
        .order_by('-spent')
    )

    return render(request, 'reports/customer_report.html', {
        'date_from': date_from, 'date_to': date_to, 'preset': preset, 'customers': customers,
    })


@role_required('ADMIN', 'MANAGER')
def inventory_report(request):
    products = Product.objects.filter(is_active=True).select_related('category').order_by('name')
    total_stock_value = sum((p.current_stock * p.purchase_price) for p in products)
    low_stock_count = sum(1 for p in products if p.stock_status == 'LOW_STOCK')
    out_of_stock_count = sum(1 for p in products if p.stock_status == 'OUT_OF_STOCK')

    return render(request, 'reports/inventory_report.html', {
        'products': products, 'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_count, 'out_of_stock_count': out_of_stock_count,
    })


@role_required('ADMIN', 'MANAGER')
def expense_report(request):
    date_from, date_to, preset = resolve_date_range(request)
    expenses = Expense.objects.filter(expense_date__gte=date_from, expense_date__lte=date_to)

    by_category = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    total_amount = expenses.aggregate(s=Sum('amount'))['s'] or 0

    return render(request, 'reports/expense_report.html', {
        'date_from': date_from, 'date_to': date_to, 'preset': preset,
        'by_category': by_category, 'total_amount': total_amount,
    })


@role_required('ADMIN', 'MANAGER')
def profit_report(request):
    date_from, date_to, preset = resolve_date_range(request)

    revenue_monthly = list(
        Sale.objects.filter(status='COMPLETED', sale_date__date__gte=date_from, sale_date__date__lte=date_to)
        .annotate(month=TruncMonth('sale_date')).values('month')
        .annotate(revenue=Sum('total')).order_by('month')
    )
    expense_monthly = list(
        Expense.objects.filter(expense_date__gte=date_from, expense_date__lte=date_to)
        .annotate(month=TruncMonth('expense_date')).values('month')
        .annotate(total=Sum('amount')).order_by('month')
    )

    def _to_date(value):
        return value.date() if hasattr(value, 'date') else value

    revenue_map = {_to_date(r['month']): r['revenue'] or 0 for r in revenue_monthly}
    expense_map = {_to_date(e['month']): e['total'] or 0 for e in expense_monthly}
    months = sorted(set(revenue_map) | set(expense_map))

    rows = []
    for m in months:
        rev = revenue_map.get(m, 0)
        exp = expense_map.get(m, 0)
        rows.append({'month': m, 'revenue': rev, 'expenses': exp, 'profit': rev - exp})

    total_revenue = sum(r['revenue'] for r in rows)
    total_expenses = sum(r['expenses'] for r in rows)
    net_profit = total_revenue - total_expenses

    return render(request, 'reports/profit_report.html', {
        'date_from': date_from, 'date_to': date_to, 'preset': preset,
        'rows': rows, 'total_revenue': total_revenue,
        'total_expenses': total_expenses, 'net_profit': net_profit,
    })
