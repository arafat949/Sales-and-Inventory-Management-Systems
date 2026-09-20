from django import forms

from products.models import Product


class StockAdjustmentForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    new_stock = forms.IntegerField(
        min_value=0, label='New Stock Quantity',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    reason = forms.CharField(
        max_length=200, required=False,
        help_text='e.g. Physical count correction, damaged goods, theft, etc.',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
