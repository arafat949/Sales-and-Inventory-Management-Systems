from django import forms
from django.forms import inlineformset_factory

from config.mixins import StyledModelForm
from products.models import Product

from .models import Sale, SaleItem


class SaleForm(StyledModelForm):
    class Meta:
        model = Sale
        fields = ['customer', 'payment_method', 'payment_status', 'discount', 'tax']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].required = False
        self.fields['customer'].empty_label = 'Walk-in customer'
        self.fields['discount'].widget.attrs.update({'min': 0, 'step': '0.01'})
        self.fields['tax'].widget.attrs.update({'min': 0, 'step': '0.01'})


class SaleItemForm(StyledModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity', 'unit_price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')
        self.fields['quantity'].widget.attrs['min'] = 1
        self.fields['unit_price'].widget.attrs['min'] = 0
        self.fields['unit_price'].widget.attrs['step'] = '0.01'

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('DELETE'):
            return cleaned
        product = cleaned.get('product')
        quantity = cleaned.get('quantity')
        if product and quantity and quantity > product.current_stock:
            raise forms.ValidationError(
                f'Insufficient stock for "{product.name}" — requested {quantity}, only {product.current_stock} available.'
            )
        return cleaned


SaleItemFormSet = inlineformset_factory(
    Sale, SaleItem,
    form=SaleItemForm,
    fields=['product', 'quantity', 'unit_price'],
    extra=1, can_delete=True, min_num=1, validate_min=True,
)
