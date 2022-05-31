import json
import time

from machine import Pin
# class Pin:
#     OUT=1
#     def __init__(self,pin,pino):
#         pass
#     def __call__(self, *args, **kwargs):
#         pass

class Valve:
    def __init__(self, no=0, finished=0):
        self.no=no
        self.finished=finished

class Valves:
    ON_OFF_THRESHOLD = 1
    def __init__(self, pin, valves):
        self.pin = pin
        self.valve_status = False
        self.valve = Pin(self.pin, Pin.OUT)
        self.last_valve = self.get_last_executed()
        self.valves = valves
        self.valves_no = len(valves)

    def get_last_executed(self):
        _json = {}
        with open("last_valve.json", "r") as f:
            try:
                _json = json.loads(f.read())
            except:
                pass
            return Valve(**_json)

    def set_last_executed(self,no, finished):
        str_val = "{" + f'"no" : {no}, "finished": {int(finished)}' + "}"
        with open("last_valve.json", "w") as f:
            f.write(str_val)
        self.last_valve = Valve(**json.loads(str_val))

    def valve_on(self, valve_no=None):
        cnt =0
        while True:
            time.sleep(self.ON_OFF_THRESHOLD)
            last_valve = self.last_valve.no
            if last_valve == self.valves_no:
                last_valve = 0
            if last_valve == valve_no and cnt > 0:
                break
            cnt += 1
            try:
                print(f"[INFO] {last_valve +1} Valve ON")
                self.valve_status = True
                self.set_last_executed(last_valve+1, False)
                self.valve(1)
            except Exception:
                self.valve(0)
                print("[ERROR] Failed turn Pump On!")


    def valve_off(self):
        try:
            print("[INFO] Valve OFF")
            self.valve_status = False
            self.set_last_executed(True)
            self.valve(0)
        except Exception:
            self.valve(0)
            print("[ERROR] Failed turn Valve Off!")
