# This file is executed on every boot (including wake-boot from deepsleep)
import esp

from config.reader import Reader
from utils.util import InitialSetUp

if __name__ == "__main__":
    esp.osdebug(None)
    config = Reader().read()
    run = InitialSetUp(config)
    run.wifi_config()  # Connect to WIFI
    run.set_tz()  # Set timezone
