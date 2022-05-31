import machine
from machine import Timer
from config.reader import Reader
from utils.forecast import Forecast

if __name__ == "__main__":
    tim = Timer(-1)
    filename = "config/dev_config.json"
    config = Reader().read()
    print(machine.freq())
    machine.freq(160000000)
    print(machine.freq())
    forecast = Forecast(water_demands=config["valves"],
                        api_key=config["OWMC_config"]["api_key"],
                        latitude=config["OWMC_config"]["latitude"],
                        longitude=config["OWMC_config"]["longitude"])
    forecast.get()

    from utils.soil_moisture import MoistureSensor
    moisture_Sensor = MoistureSensor(config)
    moisture_Sensor.mqtt.connect_and_subscribe(print)
    print("[INFO] Running moisture_Sensor...")
    moisture_Sensor.run_timer(config["Main"]["timer"])
    tim.init(period=500, mode=Timer.PERIODIC, callback=lambda t: print(1))

