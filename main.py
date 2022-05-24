from soil_moisture import MoistureSensor
from utils import read_config
from forecast import OWMClient
import time
if __name__ == "__main__":
    filename = "config.json"
    config = read_config(filename)
    moisture_Sensor = MoistureSensor(config)
    moisture_Sensor.mqtt.connect_and_subscribe(print)
    print("[INFO] Running moisture_Sensor...")
    moisture_Sensor.run_timer(config["Main"]["timer"])

