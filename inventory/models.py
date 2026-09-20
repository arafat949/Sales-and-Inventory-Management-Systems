from django.conf import settings
from django.db import models


class InventoryTransaction(models.Model):
    class TransactionType(models.TextChoices):
        PURCHASE = 'PURCHASE', 'Purchase'
        SALE = 'SALE', 'Sale'
        RETURN = 'RETURN', 'Return'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'

    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE,
        related_name='inventory_transactions'
    )
    transaction_type = models.CharField(max_length=12, choices=TransactionType.choices)
    quantity = models.IntegerField(help_text='Positive for stock in, negative for stock out')
    previous_stock = models.PositiveIntegerField()
    new_stock = models.PositiveIntegerField()
    reference = models.CharField(max_length=100, blank=True, help_text='e.g. PUR-00001 / INV-00001')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='inventory_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} ({self.quantity:+d})"
