from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def product_count(self):
        return self.products.count()


class Product(models.Model):
    class Unit(models.TextChoices):
        PIECE = 'PCS', 'Piece'
        KG = 'KG', 'Kilogram'
        GRAM = 'G', 'Gram'
        LITER = 'L', 'Liter'
        ML = 'ML', 'Milliliter'
        BOX = 'BOX', 'Box'
        PACK = 'PACK', 'Pack'

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    supplier = models.ForeignKey(
        'suppliers.Supplier', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='products'
    )
    description = models.TextField(blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    current_stock = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=10)
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECE)
    expiry_date = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def stock_status(self):
        if self.current_stock == 0:
            return 'OUT_OF_STOCK'
        if self.current_stock <= self.minimum_stock:
            return 'LOW_STOCK'
        return 'IN_STOCK'

    @property
    def profit_margin(self):
        return self.selling_price - self.purchase_price
