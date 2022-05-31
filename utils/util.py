import gc
import json
import time
import machine
import network
import ntptime
import utime



class WiFi:
    """
    Connect to the WiFi.
    Based on the example in the micropython documentation.
    """

    def __init__(self, essid, password):
        self.essid = essid
        self.password = password

    def wifi_connect(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print(f"connecting to network{self.essid} : {self.password}")
            wlan.connect(self.essid, self.password)
            # connect() appears to be async - waiting for it to complete
            while not wlan.isconnected():
                print("[DEBUG] Waiting for connection...")
                utime.sleep(5)
            print(
                "[INFO] WiFi connect successful, network config: %s"
                % repr(wlan.ifconfig())
            )
        else:
            # Note that connection info is stored in non-volatile memory. If
            # you are connected to the wrong network, do an explicity disconnect()
            # and then reconnect.
            print(
                "[INFO] WiFi already connected, network config: %s"
                % repr(wlan.ifconfig())
            )

    def wifi_disconnect(self):
        # Disconnect from the current network. You may have to
        # do this explicitly if you switch networks, as the params are stored
        # in non-volatile memory.
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            print("[DEBUG] Disconnecting...")
            wlan.disconnect()
        else:
            print("[ERROR] WiFi not connected.")

    def disable_wifi_ap(self):
        # Disable the built-in access point.
        wlan = network.WLAN(network.AP_IF)
        wlan.active(False)
        print("[INFO] Disabled access point, network status is %s" % wlan.status())


class InitialSetUp:
    def __init__(self, config_dict, utc_shift=2):
        self.utc_shift = utc_shift
        self.setup_wifi = WiFi(
            config_dict["wifi_config"]["ssid"], config_dict["wifi_config"]["password"]
        )

    def wifi_config(self, disableAP=False):
        if disableAP:
            self.setup_wifi.disable_wifi_ap()

        try:
            print("[INFO] Connecting to WiFi")
            print("Local time before synchronization：%s" % str(time.localtime()))
            self.setup_wifi.wifi_connect()
            print("[INFO] Connected to WiFi")
        except Exception:
            print("[ERROR] Failed to connect to WiFi")
            utime.sleep(5)
            self.setup_wifi.wifi_disconnect()
            machine.reset()

    def set_tz(self):
        # Timezone setup
        ntptime.settime()
        rtc = machine.RTC()
        tm = utime.localtime(utime.mktime(utime.localtime()) + (self.utc_shift * 3600))
        tm = tm[0:3] + (0,) + tm[3:6] + (0,)
        rtc.datetime(tm)
        print("Local time after synchronization：%s" % str(time.localtime()))



def force_garbage_collect():
    # Not so ideal but someone has to do it
    gc.collect()
    gc.mem_free()


def current_time():
    year, month, day, hours, mins, secs, _, _ = utime.localtime()
    hours = "0" + str(hours) if hours < 10 else hours
    secs = "0" + str(secs) if secs < 10 else secs
    mins = "0" + str(mins) if mins < 10 else secs
    datetime = "%s-%s-%s %s:%s:%s" % (year, month, day, hours, mins, secs)
    return datetime


def enter_deep_sleep(secs):
    # For some weird reason, my Wemos D1 does not wake up from deepsleep
    """
    Ensure that pin RST & D0 are connected!
    """
    # configure RTC.ALARM0 to be able to wake the device
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    # set RTC.ALARM0 to fire after Xseconds, waking the device
    sleep_timeout = secs * 1000
    rtc.alarm(rtc.ALARM0, sleep_timeout)
    print("Sleep for %d sec" % sleep_timeout)
    # put the device to sleep
    machine.deepsleep()


def adc_map(current_val, from_Low, from_High, to_Low=0, to_High=100):
    """
    Re-maps a number from one range to another.
    That is, a value of 'from_Low' would get mapped to 'to_Low',
    a value of 'from_High' to 'to_High', values in-between to values in-between, etc.

    Does not constrain values to within the range, because out-of-range values are
    sometimes intended and useful.

    y = adc_map(x, 1, 50, 50, 1);

    The function also handles negative numbers well, so that this example

    y = adc_map(x, 1, 50, 50, -100);

    is also valid and works well.

    The adc_map() function uses integer math so will not generate fractions,
    when the math might indicate that it should do so.
    Fractional remainders are truncated, and are not rounded or averaged.

    Parameters
    ----------
    value: the number to map.
    from_Low: the lower bound of the value’s current range.
    from_High: the upper bound of the value’s current range.
    to_Low: the lower bound of the value’s target range.
    to_High: the upper bound of the value’s target range.

    Adapted from https://www.arduino.cc/reference/en/language/functions/math/map/
    """

    return (current_val - from_Low) * (to_High - to_Low) / (from_High - from_Low) + to_Low


def average(samples):
    ave = sum(samples, 0.0) / len(samples)
    return ave if ave > 0 else 0
