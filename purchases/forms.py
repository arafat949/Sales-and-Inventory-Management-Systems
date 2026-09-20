from django import forms
from django.forms import inlineformset_factory

from config.mixins import StyledModelForm
from products.models import Product

from .models import Purchase, PurchaseItem


class PurchaseForm(StyledModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'purchase_date', 'payment_status', 'notes']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class PurchaseItemForm(StyledModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['product', 'quantity', 'unit_cost']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')
        self.fields['quantity'].widget.attrs['min'] = 1
        self.fields['unit_cost'].widget.attrs['min'] = 0
        self.fields['unit_cost'].widget.attrs['step'] = '0.01'


PurchaseItemFormSet = inlineformset_factory(
    Purchase, PurchaseItem,
    form=PurchaseItemForm,
    fields=['product', 'quantity', 'unit_cost'],
    extra=1, can_delete=True, min_num=1, validate_min=True,
)
