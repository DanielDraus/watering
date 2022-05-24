"""Client to talk to Open Weather Map API."""  # pylint: disable=invalid-name

import urequests
import ujson
import gc

from forecast_data import Data


class OWMClient:  # pylint: disable=invalid-name
    """Open Weather Map Client."""
    # Open Weather Map URL
    # OWM_URL = "http://api.openweathermap.org/data/2.5/onecall?units=metric&lat={}&exclude=current,alerts,minutely,hourly&lon={}&appid={}"
    OWM_URL = "http://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid={}&cnt=2&units=metric"

    def __init__(self, api_key, latitude, longitude):
        """Init."""
        self.api_key = api_key.strip()
        self.longitude = longitude
        self.latitude = latitude
        self.url = self.OWM_URL.format(latitude, longitude, api_key)
        self.rain_forecast = None

    def __str__(self):
        return "\n".join([str(x) for x in self.rain_forecast])

    def get_data(self):
        """Validate and return data."""
        print("get_data")
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
            if "current" in doc:
                if "rain" in doc["current"]:
                    self.rain_forecast.append(Data(latitude=self.latitude, **doc["current"]))
            if "list" in doc:
                print("daily ok")
                for day_ in doc["list"]:
                    if max_forecast_days == 0:
                        break
                    max_forecast_days -= 1
                    if day_["pop"] > 0:
                        self.rain_forecast.append(Data(latitude=self.latitude, **day_))
            else:
                print("Ignoring OWM input: missing required key 'daily' in OWM API return.")
                return None
            return self.rain_forecast
        except Exception as ex:
            print(ex)
            return None


class Forecast:
    def __init__(self, water_demands=[20], api_key="282449fc447357de96461ec06eed1360",
                 latitude=51.10749, longitude=16.8917524):
        """

        :param water_demands: list of water_demands in mm/m2 ( 1 mm/m2 = 1 liter for m2)
        :param api_key: Open Weather Map Client api key
        :param latitude: GPS latitude
        :param longitude: GPS longitude
        """
        self.water_demands = water_demands
        self.data = OWMClient(api_key=api_key, latitude=latitude,
                              longitude=longitude).get_data()

    def get(self):
        print([str(x) for x in self.data])
        if self.data:
            for i, water_demand in enumerate(self.water_demands):
                if hasattr(self.data[0], "evapotranspiration"):
                    print(f"evapotranspiration {self.data[0].evapotranspiration} mm/m2")
                    water_demand += self.data[0].evapotranspiration
                if self.data[0].pop >= 0.8 and hasattr(self.data[0], "rain"):
                    rain_value= list(self.data[0].rain.values()).pop(0)
                    print(f"will be raining {rain_value} mm/m2 current water_demand ={water_demand}")
                    water_demand -= rain_value
                self.water_demands[i] = water_demand
