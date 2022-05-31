import json as ujson
import os.path

from rest.open_weather import ForecastUrl


class Rain:

    def __init__(self, current=0, forecast_url: ForecastUrl = ForecastUrl.CURRENT):
        self.value = current
        self._forecast_url = forecast_url

    def save(self):
        with open(f"{self.__class__.__name__}{self._forecast_url.name}.json", "w") as f:
            f.write(ujson.dumps({k: v for k, v in self.__dict__.items() if not k.startswith("_")}))

    def get(self):
        try:
            with open(f"{self.__class__.__name__}{self._forecast_url.name}.json", "r") as f:
                return Rain(**ujson.loads(f.read()), forecast_url=self._forecast_url)
        except:
            return Rain(forecast_url=self._forecast_url)

    def __add__(self, other):
        self.value += other.value
        return self
