from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Purchase(models.Model):
    class PaymentStatus(models.TextChoices):
        PAID = 'PAID', 'Paid'
        PARTIAL = 'PARTIAL', 'Partial'
        UNPAID = 'UNPAID', 'Unpaid'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.PROTECT, related_name='purchases')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='purchases'
    )
    purchase_date = models.DateField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-purchase_date', '-id']

    def __str__(self):
        return f"PUR-{self.id:05d} - {self.supplier.company_name}"

    def recalculate_total(self):
        total = sum((item.subtotal for item in self.items.all()), 0)
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='purchase_items')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    @property
    def subtotal(self):
        return self.quantity * self.unit_cost

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
