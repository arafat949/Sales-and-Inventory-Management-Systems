from django import forms

from config.mixins import StyledModelForm

from .models import Category, Product


class CategoryForm(StyledModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProductForm(StyledModelForm):
    initial_stock = forms.IntegerField(
        min_value=0, required=False, initial=0,
        help_text='Starting stock quantity (only used when creating a new product).'
    )

    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'category', 'supplier', 'description',
            'purchase_price', 'selling_price', 'minimum_stock',
            'unit', 'expiry_date', 'image', 'is_active',
        ]
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Editing an existing product should not let you overwrite stock directly —
        # stock changes must flow through Purchases/Sales/Adjustments (spec section 15).
        if self.instance and self.instance.pk:
            self.fields.pop('initial_stock', None)
        else:
            self.fields['initial_stock'].widget.attrs['class'] = 'form-control'

    def clean_sku(self):
        sku = self.cleaned_data['sku'].strip().upper()
        qs = Product.objects.filter(sku__iexact=sku)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('A product with this SKU already exists.')
        return sku

    def clean_purchase_price(self):
        value = self.cleaned_data['purchase_price']
        if value < 0:
            raise forms.ValidationError('Purchase price cannot be negative.')
        return value

    def clean_selling_price(self):
        value = self.cleaned_data['selling_price']
        if value < 0:
            raise forms.ValidationError('Selling price cannot be negative.')
        return value

    def clean_minimum_stock(self):
        value = self.cleaned_data['minimum_stock']
        if value < 0:
            raise forms.ValidationError('Minimum stock cannot be negative.')
        return value
