"""Client to talk to Open Weather Map API."""  # pylint: disable=invalid-name
import enum
import gc
try:
    import urequests
    import ujson
except:
    import requests as urequests
    import json as ujson

from utils.forecast_data import Data

class ForecastUrl(enum.Enum):
    # Open Weather Map URL
    CURRENT = "http://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}&cnt=2&units=metric"
    FORECAST = "http://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid={}&cnt=3&units=metric"

class OWMClient:  # pylint: disable=invalid-name
    """Open Weather Map Client."""
    # OWM_URL = "http://api.openweathermap.org/data/2.5/onecall?units=metric&lat={}&exclude=current,alerts,minutely,hourly&lon={}&appid={}"


    def __init__(self, api_key, latitude, longitude, forecast_url: ForecastUrl = ForecastUrl.CURRENT):
        """Init."""
        self.api_key = api_key.strip()
        self.longitude = longitude
        self.latitude = latitude
        self.url = forecast_url.value.format(latitude, longitude, api_key)
        self.rain_forecast = None

    def __str__(self):
        return "\n".join([str(x) for x in self.rain_forecast])

    def get_data(self):
        """Validate and return data."""
        self.rain_forecast = []
        max_forecast_days = 2
        try:
            gc.mem_free() if hasattr(gc, "mem_free") else gc.collect()
            headers = {"content-type": "application/ujson", "Content-Encoding": "gzip"}
            print(self.url)
            req = urequests.get(self.url, headers=headers)
            doc = ujson.loads(req.text)
            if "cod" in doc:
                if int(doc["cod"]) != 200:
                    raise Exception(f"Cannot talk to OWM API, check API key.cod={doc['cod']}")
            if "main" in doc:
                self.rain_forecast.append(Data(latitude=self.latitude, rain=doc.get("rain", None), **doc))
            if "list" in doc:
                for day_ in doc["list"]:
                    if max_forecast_days == 0:
                        break
                    max_forecast_days -= 1
                    if day_["pop"] > 0:
                        self.rain_forecast.append(Data(latitude=self.latitude, **day_))
            return self.rain_forecast
        except Exception as ex:
            print(doc)
            raise
            return None
