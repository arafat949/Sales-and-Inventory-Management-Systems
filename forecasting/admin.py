from django.contrib import admin

from .models import Forecast


@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ('forecast_date', 'period_type', 'estimated_revenue', 'model_used', 'created_at')
