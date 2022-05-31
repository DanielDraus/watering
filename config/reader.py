import ujson
from config.settings import MODE
from utils.crypt import Crypt


class Reader:
    __instance = None
    file_name = "config.json"

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = object.__new__(cls, *args, **kwargs)
            cls.__instance.config = cls.__instance.read()
        return cls.__instance

    def read(self):
        file_name = "dev_" + self.file_name if MODE == 1 else self.file_name
        file_name = "config/" + file_name
        with open(file_name) as _f:
            config = ujson.load(_f)
        assert isinstance(config, dict)
        config["wifi_config"]["password"] = Crypt().encryptRC4(config["wifi_config"]["password"])
        config["MQTT_config"]["user"] = Crypt().encryptRC4(config["MQTT_config"]["user"])
        config["MQTT_config"]["password"] = Crypt().encryptRC4(config["MQTT_config"]["password"])
        return config

