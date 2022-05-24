import math
import utime

class Data:
    SOLAR_CONSTANT = 0.0820
    SUN_GRAPH = {1: 8, 2: 9.2, 3: 11, 4: 13, 5: 15, 6: 16.30, 7: 16.23, 8: 15.25, 9: 13.44, 10: 11.42, 11: 10, 12: 8.3}

    class Main:
        def __init__(self, temp, temp_min, temp_max, **kwargs):
            self.temp = temp
            self.temp_min = temp_min
            self.temp_max = temp_max

        def __str__(self):
            return ", ".join([f"{x}={self.__dict__.get(x)}" for x in self.__dict__ if not x.startswith("_")])

    def __init__(self, latitude, dt, clouds, pop, main, rain=None, sunset=None, sunrise=None, **kwargs):
        self.latitude = latitude
        self.dt = utime.gmtime(dt)
        self.day_of_year = self.dt[7]
        self.forecast_day = int((dt - utime.time()) / 86400)
        self.rain = rain
        self.day_light = (sunset - sunrise) / 3600 if sunset and sunrise else self.SUN_GRAPH.get(int(self.dt[1]))
        self.clouds = clouds
        self.main = self.Main(**main)
        self.evapotranspiration = self.hargreaves()
        self.pop = pop

    def sol_dec(self):
        """
        Calculate solar declination from day of the year.
        Based on FAO equation 24 in Allen et al (1998).
        :return: solar declination [radians]
        :rtype: float
        """
        return 0.409 * math.sin(((2.0 * math.pi / 365.0) * self.day_of_year - 1.39))

    def sunset_hour_angle(self):
        """
        Calculate sunset hour angle (*Ws*) from latitude and solar
        declination.
        Based on FAO equation 25 in Allen et al (1998).
        :return: Sunset hour angle [radians].
        :rtype: float
        """

        cos_sha = -math.tan(self.latitude) * math.tan(self.sol_dec())
        return math.acos(min(max(cos_sha, -1.0), 1.0))

    def inv_rel_dist_earth_sun(self):
        """
        Calculate the inverse relative distance between earth and sun from
        day of the year.
        Based on FAO equation 23 in Allen et al (1998).
        :return: Inverse relative distance between earth and the sun
        :rtype: float
        """
        return 1 + (0.033 * math.cos((2.0 * math.pi / 365.0) * self.day_of_year))

    def et_rad(self):
        """
        Estimate daily extraterrestrial radiation (*Ra*, 'top of the atmosphere
        radiation').
        Based on equation 21 in Allen et al (1998). "
        :param ird: Inverse relative distance earth-sun [dimensionless]. Can be
            calculated using ``inv_rel_dist_earth_sun()``.
        :return: Daily extraterrestrial radiation [MJ m-2 day-1]
        :rtype: float
        """
        sha = self.sunset_hour_angle()
        ird = self.inv_rel_dist_earth_sun()
        sol_dec = self.sol_dec()
        tmp1 = (24.0 * 60.0) / math.pi
        tmp2 = sha * math.sin(self.latitude) * math.sin(sol_dec)
        tmp3 = math.cos(self.latitude) * math.cos(sol_dec) * math.sin(sha)
        return tmp1 * self.SOLAR_CONSTANT * ird * (tmp2 + tmp3)

    def hargreaves(self):
        """
        Estimate reference evapotranspiration over grass (ETo) using the Hargreaves
        equation.
        Based on equation 52 in Allen et al (1998).
        :return: Reference evapotranspiration over grass (ETo) [mm day-1]
        :rtype: float
        """
        # Note, multiplied by 0.408 to convert extraterrestrial radiation could
        # be given in MJ m-2 day-1 rather than as equivalent evaporation in
        # mm day-1
        et_rad = self.et_rad()
        value = 0.0023 * (float(self.main.temp) + 17.8)
        value = abs(value) * (float(self.main.temp_min) - float(self.main.temp_max))
        value = abs(value) ** 0.5 * et_rad * 0.408
        return abs(value)

    def __str__(self):
        return ", ".join([f"{x}={self.__dict__.get(x)}" for x in self.__dict__ if not x.startswith("_")])

