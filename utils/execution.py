import ujson
import utime

class Day:
    def __init__(self, day_no=0, finished=0):
        self.day_no=day_no
        self.finished=finished

class Checker:
    def __init__(self, execution):
        self.execution = execution

    def get_exec_day(self):
        date_time = utime.localtime()
        return [x for x in self.execution if date_time[6] == x["code"]].pop(0)

    def check_if_ready_for_exec(self):
        date_time = utime.localtime()
        current_day = self.get_exec_day()
        print(current_day)
        self.set_last_executed(False)
        start_hour, start_min = (int(x) for x in str(current_day["start_hour"]).split("."))
        ready = (start_hour < date_time[3]) and not self.get_last_executed().finished
        ready = ready or ((start_hour == date_time[3]) and (start_min <= date_time[4]))
        return ready and current_day["enable"]

    def get_last_executed(self):
        _json = {}
        with open("was_started.json", "r") as f:
            try:
                _json = ujson.loads(f.read())
            except:
                pass
            return Day(**_json)

    def set_last_executed(self, finished):
        str_val = "{" + f'"day_no" : {self.get_exec_day()["code"]}, "finished": {int(finished)}' + "}"
        with open("was_started.json", "w") as f:
            f.write(str_val)
        self.last_valve = Day(**ujson.loads(str_val))

