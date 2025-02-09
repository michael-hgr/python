from prophet import Prophet
import pandas as pd
from monthlyDataFinal import monthlyData


def prognoseMonthlyData(latitude, longitude, peakpower, loss, angle, aspect, mountingplace):
    monthly_energy, optimal_slope, optimal_azimuth = monthlyData(latitude, longitude, peakpower, loss, angle, aspect, mountingplace)

    model = Prophet(yearly_seasonality=True, weekly_seasonality=False, growth='flat', changepoint_prior_scale=0.1)
    model.add_seasonality(name='monthly', period=30.5, fourier_order=2)
    model.add_seasonality(name='custom_yearly', period=12, fourier_order=2)
    
    model.fit(monthly_energy)

    future = model.make_future_dataframe(periods=120, freq='MS')
    future = future[future['ds'].dt.year >= 2024]
    
    forecast = model.predict(future)
    forecast['yhat'] = forecast['yhat'].clip(lower=0)
    forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
    forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)

    prognoseResult = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    
    return prognoseResult.to_dict(orient='records'), optimal_slope, optimal_azimuth
