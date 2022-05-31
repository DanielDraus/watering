import gc
import json

from utils.rain import Rain

print(gc.mem_free() if hasattr(gc, "mem_free") else gc.collect())
from rest.open_weather import OWMClient, ForecastUrl
from config.settings import MODE


class Forecast:
    def __init__(self, water_demands, api_key,
                 latitude, longitude, forecast_url: ForecastUrl.CURRENT):
        """

        :param water_demands: list of water_demands in mm/m2 ( 1 mm/m2 = 1 liter for m2)
        :param api_key: Open Weather Map Client api key
        :param latitude: GPS latitude
        :param longitude: GPS longitude
        """
        self.water_demands = water_demands
        self.data = OWMClient(api_key=api_key, latitude=latitude,
                              longitude=longitude, forecast_url=forecast_url).get_data()
        self.rain = Rain(sum([x.rain for x in self.data if x.rain]), forecast_url)

    def save_rain(self):
        self.rain.save()

    def get_rain(self):
        return Rain().get()

    def get(self):

        if self.data:
            if MODE == 1:
                print([str(x) for x in self.data])

            for i, water_demand in enumerate(self.water_demands):
                if hasattr(self.data[0], "evapotranspiration"):
                    print(f"evapotranspiration {self.data[0].evapotranspiration} mm/m2")
                    water_demand["mm2m"] += self.data[0].evapotranspiration
                if self.data[0].rain:
                    rain_value = self.data[0].rain
                    print(f"will be raining {rain_value} mm/m2 current water_demand ={water_demand['mm2m']}")
                    water_demand["mm2m"] -= rain_value
                self.water_demands[i] = water_demand

f = Forecast(water_demands=[{"no": 1, "mm2m": 10, "on_off": 1}], api_key="282449fc447357de96461ec06eed1360",
             latitude=51.10749, longitude=16.8917524,forecast_url=ForecastUrl.CURRENT )
f.get()
print(f.water_demands)
