from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import render
from django.utils import timezone

from customers.models import Customer
from expenses.models import Expense
from products.models import Product
from purchases.models import Purchase
from sales.models import Sale, SaleItem
from suppliers.models import Supplier


def _daily_series(days):
    """Revenue series for the last `days` days, including today."""
    today = timezone.localdate()
    start_date = today - timedelta(days=days - 1)

    qs = (
        Sale.objects.filter(status='COMPLETED', sale_date__date__gte=start_date)
        .annotate(day=TruncDate('sale_date'))
        .values('day')
        .annotate(revenue=Sum('total'))
    )
    data_map = {row['day']: float(row['revenue'] or 0) for row in qs}

    labels, values = [], []
    current = start_date
    while current <= today:
        labels.append(current.strftime('%b %d'))
        values.append(data_map.get(current, 0))
        current += timedelta(days=1)
    return labels, values


def _monthly_series(months_count):
    """Revenue series for the last `months_count` months, including this month."""
    today = timezone.localdate()
    months = []
    year, month = today.year, today.month
    for _ in range(months_count):
        months.append((year, month))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    months.reverse()

    start_date = date(months[0][0], months[0][1], 1)
    qs = (
        Sale.objects.filter(status='COMPLETED', sale_date__date__gte=start_date)
        .annotate(month=TruncMonth('sale_date'))
        .values('month')
        .annotate(revenue=Sum('total'))
    )
    data_map = {(row['month'].year, row['month'].month): float(row['revenue'] or 0) for row in qs}

    labels, values = [], []
    for y, m in months:
        labels.append(date(y, m, 1).strftime('%b %Y'))
        values.append(data_map.get((y, m), 0))
    return labels, values


def _build_chart_data():
    ranges = {}
    for key, days in (('7d', 7), ('30d', 30)):
        labels, values = _daily_series(days)
        ranges[key] = {'labels': labels, 'values': values}
    for key, months in (('6m', 6), ('12m', 12)):
        labels, values = _monthly_series(months)
        ranges[key] = {'labels': labels, 'values': values}
    return ranges


def _recent_transactions(limit=8):
    """Merge recent sales, purchases and expenses into one timeline."""
    items = []

    for s in Sale.objects.select_related('customer').order_by('-sale_date')[:limit]:
        items.append({
            'type': 'Sale', 'icon': 'fa-cash-register', 'color': 'success',
            'reference': f"INV-{s.id:05d}",
            'detail': s.customer.name if s.customer else 'Walk-in customer',
            'amount': s.total,
            'date': timezone.localtime(s.sale_date).date() if s.sale_date else None,
        })

    for p in Purchase.objects.select_related('supplier').order_by('-purchase_date')[:limit]:
        items.append({
            'type': 'Purchase', 'icon': 'fa-cart-arrow-down', 'color': 'primary',
            'reference': f"PUR-{p.id:05d}",
            'detail': p.supplier.company_name,
            'amount': p.total_amount,
            'date': p.purchase_date,
        })

    for e in Expense.objects.order_by('-expense_date')[:limit]:
        items.append({
            'type': 'Expense', 'icon': 'fa-receipt', 'color': 'danger',
            'reference': e.title,
            'detail': e.get_category_display(),
            'amount': e.amount,
            'date': e.expense_date,
        })

    items.sort(key=lambda x: x['date'] or date.min, reverse=True)
    return items[:limit]


@login_required
def index(request):
    total_sales = Sale.objects.filter(status='COMPLETED').count()
    total_revenue = Sale.objects.filter(status='COMPLETED').aggregate(s=Sum('total'))['s'] or 0
    total_expenses = Expense.objects.aggregate(s=Sum('amount'))['s'] or 0
    net_profit = total_revenue - total_expenses

    total_products = Product.objects.filter(is_active=True).count()
    total_customers = Customer.objects.count()
    total_suppliers = Supplier.objects.count()
    low_stock_qs = Product.objects.filter(is_active=True, current_stock__lte=F('minimum_stock'))
    low_stock_count = low_stock_qs.count()

    top_products = (
        SaleItem.objects.filter(sale__status='COMPLETED')
        .values('product__id', 'product__name', 'product__sku')
        .annotate(qty_sold=Sum('quantity'), revenue=Sum(F('quantity') * F('unit_price')))
        .order_by('-qty_sold')[:5]
    )

    low_stock_products = low_stock_qs.select_related('category').order_by('current_stock')[:5]

    context = {
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'total_products': total_products,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
        'low_stock_count': low_stock_count,
        'top_products': top_products,
        'low_stock_products': low_stock_products,
        'recent_transactions': _recent_transactions(),
        'chart_data': _build_chart_data(),
        'currency': settings.CURRENCY_SYMBOL,
    }
    return render(request, 'dashboard/index.html', context)
