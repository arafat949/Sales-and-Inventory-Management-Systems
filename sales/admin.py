from django.contrib import admin

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'sale_date', 'total', 'payment_method', 'payment_status', 'status')
    list_filter = ('status', 'payment_status', 'payment_method')
    inlines = [SaleItemInline]
