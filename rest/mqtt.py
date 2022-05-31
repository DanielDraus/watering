""""Client to talk to MQTT."""  # pylint: disable=invalid-name

import usocket
import machine

from ubinascii import hexlify
from umqtt.simple import MQTTClient


class RealMQTTClient:
    """Writer interface over umqtt API."""

    __variables__ = ("host", "client", "port", "user", "password")
    __flag = False

    def __init__(self, host, user, password , port):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        if self.host:
            self.client = MQTTClient(
                client_id=hexlify(machine.unique_id()), server=self.host,
                port=self.port, password=self.password, user=self.user
            )
            self.check_ip_up()
            self._connect()

    def check_ip_up(self):
        try:
            s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((self.host, self.port))
            print("[INFO] Host %s is UP!" % self.host)
            self.__flag = True
        except Exception:
            print("[ERROR] Host %s is DOWN!" % self.host)
            utime.sleep(1)
        finally:
            s.close()

    def _connect(self):
        print("[INFO] Connecting to %s" % (self.host))
        if True: #self.__flag:
            self.client.connect()
            print("[INFO] Connection successful")
            self.__flag = True
        else:
            print("[ERROR] Cannot connect to host:%s" % self.host)

    def publish(self, topic="", msg="", encoder="utf-8"):
        print("[INFO] Publishing message: %s on topic: %s" % (msg, topic))
        if not self.__flag:
            self.check_ip_up()
            self._connect()
        if self.__flag:
            self.client.publish(bytes(topic, encoder), bytes(msg, encoder))
            print("[INFO] Published Successfully!")
        else:
            print("[ERROR] Failed to Publish the message, Link is not UP!")

    def connect_and_subscribe(self, callback):
        if self.__flag:
            self.check_ip_up()
            self._connect()
        self.client.set_callback(callback)
        self.client.subscribe("/home/watering")
        print("Subscribed to {}".format("/home/watering"))

