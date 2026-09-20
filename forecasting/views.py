from django.shortcuts import render

from accounts.permissions import role_required

from .ml import forecast_sales
from .models import Forecast


@role_required('ADMIN')
def index(request):
    """
    /forecast/ — spec section 21. Runs the pipeline fresh on each visit
    (cheap at this data scale) and persists the predicted periods to the
    Forecast model so they're auditable later.
    """
    result = forecast_sales(periods=3)

    if result is None:
        return render(request, 'forecasting/index.html', {'insufficient_data': True})

    for item in result['forecast']:
        Forecast.objects.update_or_create(
            forecast_date=item['month'].date(),
            period_type=Forecast.Period.MONTHLY,
            defaults={
                'estimated_revenue': item['revenue'],
                'model_used': result['model_name'],
                'generated_by': request.user,
            }
        )

    historical = result['historical']
    forecast = result['forecast']

    # Build one continuous Chart.js series: historical line ends exactly where
    # the dashed forecast line begins, sharing the last historical point.
    chart_labels = [h['month'].strftime('%b %Y') for h in historical] + [f['month'].strftime('%b %Y') for f in forecast]
    historical_series = [round(h['revenue'], 2) for h in historical] + [None] * len(forecast)
    forecast_series = [None] * (len(historical) - 1) + [round(historical[-1]['revenue'], 2)] + [f['revenue'] for f in forecast]

    context = {
        'insufficient_data': False,
        'next_forecast': forecast[0],
        'forecast_list': forecast,
        'model_used': result['model_name'],
        'r2_score': result['r2_score'],
        'months_used': result['months_used'],
        'trend_direction': 'increasing' if result['coefficient'] > 0 else 'decreasing' if result['coefficient'] < 0 else 'flat',
        'chart_labels': chart_labels,
        'historical_series': historical_series,
        'forecast_series': forecast_series,
    }
    return render(request, 'forecasting/index.html', context)
