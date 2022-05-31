from rest.open_weather import ForecastUrl
from utils.rain import Rain

a = Rain(2.5, ForecastUrl.CURRENT)
a.save()
b = Rain(forecast_url=ForecastUrl.CURRENT).get()
c = a + b
print(c.value)
print((Rain(2.5, ForecastUrl.CURRENT) + Rain(forecast_url=ForecastUrl.CURRENT).get()).value)
print(Rain(forecast_url=ForecastUrl.CURRENT).get().value)