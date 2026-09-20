from django.db import models


class Customer(models.Model):
    class CustomerType(models.TextChoices):
        REGULAR = 'REGULAR', 'Regular'
        VIP = 'VIP', 'VIP'
        NEW = 'NEW', 'New'

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    customer_type = models.CharField(max_length=10, choices=CustomerType.choices, default=CustomerType.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_orders(self):
        return self.sales.filter(status='COMPLETED').count()

    @property
    def total_spent(self):
        from django.db.models import Sum
        return self.sales.filter(status='COMPLETED').aggregate(total=Sum('total'))['total'] or 0

    @property
    def last_purchase_date(self):
        last = self.sales.filter(status='COMPLETED').order_by('-sale_date').first()
        return last.sale_date if last else None
