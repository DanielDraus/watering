"""Module used for automatic calls of RestApi characteristic endpoints.

script parameters:

    --key', required=True, help='Security key.

example :

    characteristics_script.py --key myKey

available environments:

    DEV, DEV2, PROD, QAS, QAS2, TEST, TEST2

available options:

    1) Create ArticleCharacteristicValue backup with filter fields:characteristics:str, catalog:int

    Example filter value:
        characteristic_id = "02-[R]_05_00_03"
        catalog_id = 1

    2) Create ArticleCharacteristicValue backup from all catalogs with filter fields:characteristics:str

    Example filter value:
        characteristic_id = "02-[R]_05_00_03"

    3) Remove all ArticleCharacteristicValue with filter fields:catalog:int

        Example filter value:
            catalog_id = 1

    4) Remove all ArticleCharacteristicValue for all catalogs
    5) Get all Master catalogs
    6) Get all Supplier catalogs
    7) Restore ArticleCharacteristicValue from backup file with option fields:modify_lookups:bool

        Example option value:
            modify_lookups = True

        if modify_lookups is set to True then
            lookups_cnf.json will be used for modification of read ArticleCharacteristicValue.

        Example content of lookups_cnf.json file :
            { "903": { "Mass Balance": "Mass_Balance"}}
            where:
            - "903": Characteristic Id taken from backup csv ( row 8 )
            - "Mass Balance": search value
            - "Mass_Balance": replace value

"""
import abc
import argparse
import enum
import json
import logging
import os
import pprint
import socket
import time
import typing
import copy
import traceback
import urllib.parse
from logging.handlers import RotatingFileHandler
from multiprocessing import Lock, current_process
from multiprocessing.pool import ThreadPool as Pool
from tkinter import filedialog, Tk, TclError

import tqdm
from urllib3 import HTTPSConnectionPool, make_headers

DEBUG = False
# create logger with 'spam_application'
logger_f = logging.getLogger("CharacteristicToolF" + str(current_process().pid))
logger_f.setLevel(logging.DEBUG)
logger_c = logging.getLogger("CharacteristicToolC" + str(current_process().pid))
logger_c.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = RotatingFileHandler('{0}.log'.format("CharacteristicTool"), maxBytes=2621440, backupCount=100)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger_f.addHandler(fh)
logger_c.addHandler(ch)

SECRET_KEY = "capgemini"  # Secret key used for hash
SERVER = None
parser = argparse.ArgumentParser(description='RF to ALM QC reporter module')
parser.add_argument('--key', required=False, help='Security key.')

root = Tk()
MENU_LIST = dict()


class Util:
    """Util class"""

    @staticmethod
    def millis():
        """Return current millis"""
        return int(round(time.time() * 1000))


class SetValueChoice:
    """Special menu choice with setting fields."""
    BOOL_MAP = {"true": True, "false": False, "True": True, "False": False, "": True, "0": False, "1": True}

    def __init__(self, value_name: str, desc: object, obj_type: type = str, hint: str = ""):
        self.desc = desc
        self.value_name = value_name
        self.obj_type = obj_type
        self.hint = hint

    @staticmethod
    def get_str(value):
        """Get str value from input"""
        if value is None:
            raise Exception("value is not set ")
        return value

    @staticmethod
    def get_bool(value):
        """Get bool value from input"""
        ret_value = SetValueChoice.BOOL_MAP.get(value)
        if ret_value is None:
            raise Exception("'{0}' is not type of {1}".format(value, SetValueChoice.BOOL_MAP.keys()))
        return ret_value

    @staticmethod
    def get_int(value):
        """Get int value from input"""
        if not value.isdigit():
            raise Exception("'{0}' is not type of INT".format(value))
        return int(value)


class SetValuesChoice:
    """Special choices class, used for gathering values from SetValueChoice"""

    def __init__(self, desc: str, choices: [SetValueChoice]):
        self.desc = desc
        self.choices = choices

    def on_selection(self, menu, index):
        """on event selected"""
        print("   Keep old values ? (just press enter :) )")
        return {x.value_name: x.obj_type(input(":-) Hint->{0}\n{1}={2}: ".format(x.hint, x.value_name, x.desc))) for
                i, x in
                enumerate(self.choices)}


class Choice:
    """Base choice class"""

    def __init__(self, _server, desc: typing.Union[str, 'Commands']):
        self.server = _server
        self.desc = desc.value if isinstance(desc, Commands) else desc
        self.command = desc

    def on_selection(self, menu, index):
        """on event selected"""
        print("Help:\n'{}'".format(getattr(self.desc, "desc", self.desc)))
        if DEBUG:
            logger_f.info("'{}' was selected".format(getattr(self.desc, "desc", self.desc).split("\n").pop(0)))
        if hasattr(self.command, "server"):
            with self.server as _server:
                self.command.server = _server
                try:
                    if self.command.ask_for_args():
                        self.command.execute()
                    print("'{}' succesfully executed".format(getattr(self.desc, "desc", self.desc).split("\n").pop(0)))
                    logger_f.info(
                        "'{}' succesfully executed".format(getattr(self.desc, "desc", self.desc).split("\n").pop(0)))
                except Exception as e:
                    traceback.format_exc()
                    logger_f.error(str(e))
                    logger_f.error(traceback.format_exc())
                    logger_c.error(str(e))

        return self


class ExitChoice(Choice):
    """Exit program Choice

    """

    def on_selection(self, menu, index):
        """on event selected"""
        print("bye")
        raise SystemExit


class GoBackChoice(Choice):
    """Go to main menu Choice

    """

    def on_selection(self, menu, index):
        """on event selected"""
        logger_c.info("'{}' was selected".format(self.desc))

        if menu.index == 2:
            main()
        else:
            MENU_LIST.get(menu.index - 1).show()


class Menu(object):
    """Menu class

    """

    def __init__(self, question, index):
        self.question = question
        self.choices = []
        self.index = index
        global MENU_LIST
        MENU_LIST.update({index: self})

    def add_choices(self, choices):
        """Method for add choices to menu"""
        self.choices.extend(choices)
        if self.index > 1:
            self.choices.append(GoBackChoice(None, 'Go back'))
        self.choices.append(ExitChoice(None, 'Exit program'))

    def get_input(self):
        """Method will raise on_selection event on selected choice"""
        choice_list = "\n".join(
            "    {}) {}".format(i, getattr(x.desc, "desc", x.desc).split("\n").pop(0)) for i, x in
            enumerate(self.choices, 1))
        s = """{}\n{}\n""".format(self.question, choice_list)
        prompt = "? "
        while True:
            user = input(s + prompt)
            try:
                c = int(user.strip())
                if not c > 0:
                    raise IndexError()
                choice = self.choices[c - 1]
            except (IndexError, ValueError):
                prompt = "ERROR: please input an integer in {}..{}\n? ".format(1, len(self.choices))
                continue
            return choice.on_selection(self, c - 1)


class MenuItemEnv(Menu):
    """Special menu item used for display all available ENVs"""

    def __init__(self):
        super().__init__("Please select server:", 1)
        choices_list = [Choice(None, x.replace(_Servers.__name__ + "__", "")) for x in dir(_Servers) if
                        _Servers.__name__ in x]
        self.add_choices(choices_list)

    def show(self):
        """Display method"""
        return _Servers.get_server(self.get_input().desc)


class MenuItemToDo(Menu):
    """Menu item with all 'to do' choices"""

    def __init__(self, server):
        super().__init__("Please select what i should do", 2)
        choices_list = [Choice(server, getattr(Commands, x).value()) for x in dir(Commands) if not x.startswith('_')]
        self.add_choices(choices_list)

    def show(self):
        """Display method"""
        try:
            return self.get_input()
        except Exception as e:
            logger_f.error(str(e))
            logger_f.error(traceback.format_exc())
            logger_c.error(str(e))


class BaseEntity:
    """Base entity class"""

    JSON_BASE = "<{0}>"
    """String representation of serialized class to json. Characters '<' and '>' will be replaced by '{' and '}'"""

    def __members(self) -> tuple:
        """Method used for comparison's value creation """
        return tuple(self.get_fields_value())
        # return "{0}{1}{2}".format(self.field_object.field_id, self.field_object.field_entityId, self.field_object.field_label)

    def __eq__(self, other):
        """Method used for comparison"""
        if type(other) is type(self):
            return self.__members() == other.__members()
        else:
            return False

    def __hash__(self):
        """Method used generating comparison hash"""
        return hash(self.__members())

    def __init__(self, catalog_id=0, **kwargs):
        self.catalog_id = catalog_id
        _kwargs = kwargs.copy()
        for item in _kwargs.items():
            value = item[1]
            if isinstance(item[1], dict):
                value = type(self.__class__.__name__ + item[0], (self.__class__,), {})(catalog_id, **value)
            setattr(self, "field_{0}".format(item[0]), value)

    def __str__(self):
        if DEBUG:

            for x in self.__dict__.keys():
                if x.startswith("field_"):
                    print(x, type(self.__dict__.get(x)))
                    print(str(self.__dict__.get(x)))
        return json.dumps({x.replace("field_", ""): str(self.__dict__.get(x)) for x in self.__dict__.keys() if
                           x.startswith("field_")})

    @classmethod
    def get_arg7_value(cls, arg):
        import codecs
        arg = codecs.decode(arg, 'unicode_escape')
        arg = codecs.decode(arg.encode("utf-8"), 'utf-8')
        try:
            try:
                _loaded = eval(arg.replace("\\'", "").replace("[[", "[").replace("]]", "]").replace('"', "'"))
            except:
                _loaded = arg
            if isinstance(_loaded, list) or isinstance(_loaded, tuple):
                if len(_loaded) > 1:
                    _loaded = _loaded[0][0] if _loaded[0][0] else _loaded[1][0]
                else:
                    _loaded = _loaded[0] if not isinstance(_loaded[0], list) else _loaded[0][0]
                return _loaded.strip().replace('"', "'")
            elif isinstance(_loaded, str):
                return _loaded.strip().replace('"', "'")

        except Exception as e:
            logger_f.error(str(e))
            logger_f.error("Wrong string found in csv: {0}".format(arg))
            logger_c.error("Wrong string found in csv: {0}".format(arg))
            return arg

    @classmethod
    def deserialize_csv(cls, line: str):
        """Change csv formatted line to self"""
        try:
            split_chr = ";" if len(line.split(";")) >= 8 else ","
            all_args = [x.replace("\n", "").strip().replace('"', "'") for x in line.split(split_chr)]
            if len(all_args) > 9:
                _args_new = all_args[:7]
                _args_new.append(all_args[7:-1])
                _args_new.append(all_args[-1])
                _args = _args_new[:8]
            else:
                _args = all_args[:8]

            _args[7] = cls.get_arg7_value(str(_args[7]))

            json_str = cls.JSON_BASE.format(*_args).replace("<", "{").replace(">", "}")
            return cls.deserialize(json.loads(json_str), int(_args[0]))

        except Exception as e:
            logger_c.error("line not serialized {0}".format(line))
            logger_f.error("line not serialized {0},{1}".format(line, str(e)))
            logger_f.error(traceback.format_exc())
        return cls()

    @classmethod
    def deserialize(cls, json_content: dict, catalog_id: int = 0) -> 'BaseEntity':
        """Change json to self"""
        return cls(catalog_id, **json_content)

    def get_fields_name(self) -> list:
        """Method will return class fields name"""
        return [x.replace("field_", "") for x in self.__dict__.keys() if x.startswith("field_")]

    def get_fields_value(self) -> list:
        """Method will return class fields value"""
        return [str(self.__dict__.get(x)) if not isinstance(self.__dict__.get(x), list) else json.dumps(
            self.__dict__.get(x)) for x in self.__dict__.keys() if x.startswith("field_")]

    def serialize(self) -> json:
        """Change self to json"""
        return {x.replace("field_", ""):
                    getattr(self, x).serialize() if isinstance(getattr(self, x), self.__class__) else getattr(self, x)
                for x in dir(self) if x.startswith("field_")}

    def to_csv(self):
        """Change self to csv formatted line"""
        fields = self.get_fields_value()
        return "; ".join(fields)

    def modify_record_key(self, record_key: str):
        if not hasattr(self, "field_qualification"):
            # in case of wrong structure just return
            return
        self.field_qualification.field_recordKey = record_key

    def modify_parent_record_key(self, parent_record_key):
        if not hasattr(self, "field_qualification"):
            # in case of wrong structure just return
            return
        self.field_qualification.field_parentRecordKey = parent_record_key

    def modify_lookups(self, lookups_dict):
        """Method will modify self values to taken from lookups_dict"""
        if not hasattr(self, "field_qualification"):
            # in case of wrong structure just return
            return
        new_field_values = list()
        to_change = lookups_dict.get(self.field_qualification.field_characteristic.field_id)
        if to_change:
            if isinstance(self.field_values[0], str) and to_change.get(self.field_values[0]):
                logger_f.info("change value" + self.field_values[0], to_change.get(self.field_values[0]))
                setattr(self, "field_values", [to_change.get(self.field_values[0])])
            else:
                # in case of double lookup [[...][...]] or [[{}][{}]]
                old_values = copy.deepcopy(self.field_values)
                for i in range(len(self.field_values)):
                    was_list = isinstance(self.field_values[i], list)
                    value = self.field_values[i].pop() if isinstance(self.field_values[i], list) else self.field_values[
                        i]
                    if isinstance(value, dict):
                        new_value = to_change.get(value.get("label"))
                        if not new_value:
                            logger_f.error("Could not find correct value for {0}".format(value.get("label")))
                            logger_c.warning("Could not find correct value for {0}".format(value.get("label")))
                            return
                        value["label"] = new_value
                        value = [value] if was_list else value
                        new_field_values.append(value)
                    elif isinstance(value, str):
                        new_field_values.append(value)
                if len(new_field_values) == 2 and new_field_values[0] == new_field_values[1]:
                    common_value = new_field_values.pop(0)
                    # in case of double lookup as list unpack
                    common_value = common_value.pop(0) if isinstance(common_value, list) else common_value
                    label = common_value["label"] if isinstance(common_value, dict) else common_value
                    logger_f.info("change value{0} to {1}".format(old_values, label))
                    setattr(self, "field_values", label)
                else:
                    logger_f.info("change value{0} to {1}".format(old_values, new_field_values))
                    setattr(self, "field_values", new_field_values)


class BaseEntities:
    """Base entities class"""

    def __init__(self, list_key, *args):
        self.list_key = list_key
        self.field_rows = set(args[0]) if len(args) else set()  # remove duplicates

    def __add__(self, other):
        self.field_rows = set.union(self.field_rows, other.field_rows)
        return self

    def is_empty(self):
        """Check if is empty"""
        return len(self.field_rows) == 0

    def modify_lookups(self, path):
        """Method will modify self values to taken from file"""
        with open(path, "r") as f:
            lookups_dict = json.loads("".join(f.readlines()))
            [x.modify_lookups(lookups_dict) for x in self.field_rows]

    def modify_record_key(self, record_key: str):
        for item in self.field_rows:
            item.modify_record_key(record_key)

    def modify_parent_record_key(self, parent_record_key):
        for item in self.field_rows:
            item.modify_parent_record_key(parent_record_key)

    @classmethod
    def deserialize_csv(cls, file_handler: typing.TextIO,
                        list_key: str = "rows", entity: 'BaseEntity' = BaseEntity) -> 'BaseEntities':
        """Change csv formatted file to self"""
        return cls(list_key, [entity.deserialize_csv(line) for _, line in enumerate(file_handler.readlines())])

    @classmethod
    def deserialize(cls, json_content, list_key: str = "rows", entity: 'BaseEntity' = BaseEntity,
                    catalog_id: int = 0) -> 'BaseEntities':
        """Change json to self

        for ex. response structure:
            {rows: [{object: {id : 1, label: Master catalog, entityId: 2900}, {values : {some :1}}}]}
        will be unpacked to:
            baseEntityobject = BaseEntity()
            baseEntityvalues = BaseEntity()
            baseEntityvalues.field_some = 1
            baseEntityobject.field_id = 1
            baseEntityobject.field_label = Master catalog
            baseEntityobject.field_entityId = 2900
            baseEntity = BaseEntity()
            baseEntity.field_object = baseEntityobject
            baseEntity.field_values = baseEntityvalues
            BaseEntities.field_rows = [baseEntity]
        """
        if list_key in json_content.keys():
            return cls(list_key, [entity.deserialize(x, catalog_id) for x in json_content.get(list_key)])
        else:
            return cls(list_key, [])

    def serialize(self) -> json:
        """Change self to json

        for ex. BaseEntities with structure:
            baseEntityobject = BaseEntity()
            baseEntityvalues = BaseEntity()
            baseEntityvalues.field_some = 1
            baseEntityobject.field_id = 1
            baseEntityobject.field_label = Master catalog
            baseEntityobject.field_entityId = 2900
            baseEntity = BaseEntity()
            baseEntity.field_object = baseEntityobject
            baseEntity.field_values = baseEntityvalues
            BaseEntities.field_rows = [baseEntity]
        will be unpacked to:
            {rows: [{object: {id : 1, label: Master catalog, entityId: 2900}, {values : {some :1}}}]}

        """
        return {self.list_key: [x.serialize() for x in self.field_rows]}

    def __iter__(self):
        return (row for row in self.field_rows)

    def to_csv(self):
        """Change self to csv formatted string"""
        l = list()
        for row in self:
            a = row  # type: 'BaseEntity'
            l.append(a.to_csv())
        return "\n".join([x.to_csv() for x in self])

    def get_csv_header(self):
        """Return csv header."""
        # noinspection PyTypeChecker
        return " ;".join(next(iter(self)).get_fields_name())


class Command:
    """Base command class"""

    class Entities(BaseEntities):
        pass

    class Entity(BaseEntity):
        pass

    def __init__(self):
        self.desc = self.__doc__
        self.req_type = None
        self.url = None
        self.result = None
        self.file_path = None
        self.characteristic_id = None
        self.catalog_id = None
        self.choices = None
        self.__server = None

    @property
    def server_host(self) -> str:
        """_Server__session_host"""
        return getattr(self.__server, '_Server__session').host

    @property
    def server(self):
        """Server"""
        return self.__server

    @server.setter
    def server(self, server):
        self.__server = server

    @abc.abstractmethod
    def execute(self, save_data=False):
        """Command execution"""
        pass

    def ask_for_args(self):
        """additional menu for setting variables"""
        if not self.choices:
            return True
        menu = Menu("Please select what i should do", 3)
        menu.add_choices([self.choices])
        input_values = menu.get_input()
        if not input_values:
            return False
        for x in input_values.keys():
            if input_values.get(x) != "":
                setattr(self, x, input_values.get(x))
        return True

    def ask_for_path(self, file_name="characteristic_backup.csv", initialdir=None, save=False) -> str:
        """Set CSV file path for backup.

        :param save:
        :param initialdir:
        :param file_name:
        """
        _func = filedialog.askopenfilename
        if save:
            _func = filedialog.asksaveasfilename
        f_ext = file_name.split(".").pop(-1)
        default_extension = ".{0}".format(f_ext)
        filetypes = ("{0} files".format(f_ext), "*.{0}".format(f_ext))
        f_path = _func(initialfile=file_name, defaultextension=default_extension, filetypes=[filetypes],
                       title="Choose file", initialdir=initialdir)
        try:
            if not f_path:
                raise Exception("please select correct {0}".format(file_name))
            root.destroy()
        except Exception as e:
            if not isinstance(e, TclError):
                raise
        finally:
            return f_path

    @property
    def test_connection(self):
        """Test rest api """
        return self.server.get_session().request('GET', '/rest/V2.0/meta').status == 200

    @property
    def characteristic_enabled(self):
        url = "/rest/V2.0/list/Characteristic/byIdentifiers?identifiers={}&fields=Characteristic.IsActive"
        url_set_active = "/rest/V2.0/list/Characteristic"
        charct_items = [x.strip().replace('"', '').replace("'", "") for x in self.characteristic_id.split(",")]
        for item in charct_items:
            data = json.loads(self.server.get_session().request('GET', url.format(item)).data)
            if data.get("rows", None):
                return bool(data.get("rows")[0].get("values")[0])
                # data = json.loads(self.server.get_session().request('POST', url_set_active.format(item)).data)
            else:
                return False
        return True

    def get_data(self, catalog_id: str = 1, list_key: str = "rows", result: str = None,
                 single_entity: bool = False) -> BaseEntities:
        """Unpack response data to BaseEntities"""

        if not result:
            result = self.result
        if result.status == 200:
            json_data = json.loads(result.data.decode('utf-8-sig'))
            if single_entity:
                out = self.Entity.deserialize(json_data)
            else:
                out = self.Entities.deserialize(json_data, list_key=list_key, entity=self.Entity,
                                                catalog_id=catalog_id)
            return out
        else:
            logger_f.info("{0}:{1}, returned data:{2}".format(result.status, result.reason,
                                                              result.data))
            raise Exception("Wrong status recived:{0} for {1}".format(result.status, result.geturl()))


class VerifyArticlesStatusesViaRestCommand(Command):
    """Verify Statuses for list of articles
    """

    class Entities(BaseEntities):
        def get_csv_header(self):
            return " ;".join(
                ["Item ID", "Status"])

    class Entity(BaseEntity):
        JSON_BASE = '<"Item ID": "{0}","Status": "{1}">'

        @classmethod
        def deserialize_csv(cls, line: str):
            """Change csv formatted line to self"""
            split_chr = ";" if len(line.split(";")) >= 1 else ","
            all_args = [x.replace("\n", "").strip().replace('"', "'") for x in line.split(split_chr)]
            json_str = cls.JSON_BASE.format(*all_args).replace("<", "{").replace(">", "}")
            return cls.deserialize(json.loads(json_str), int(0))

    def get_list_of_items(self):
        file_path = self.ask_for_path(file_name="test_statuses.csv")
        return CsvReader(file_path).deserialize(enities=self.Entities, entity=self.Entity)

    def get_item_catalog_id(self, item_id):
        url = f'/rest/V1.0/list/SupplierCatalog/bySearch?query=SupplierCatalog.Identifier contains "{item_id.split("_").pop(-1)}"'
        entity = self.get_data(catalog_id=None, single_entity=True, list_key="rows",
                               result=self.server.get_session().request("GET", url))
        if entity.field_rowCount > 0:
            return str(entity.field_rows[0]["object"]["id"])
        return 0

    def get_query_selector(self, id_):
        if "_" in id_:
            return "Article"
        elif len(id_) == 6:
            return "Product2G"
        else:
            return "Variant"

    def execute(self, save_data=False):
        """Execute method"""

        _path = self.ask_for_path(file_name="wrong_statuses.csv", save=True)
        writer = CsvWriter(path=_path, entities=self.Entities("rows"), make_header=False)
        entities = self.get_list_of_items()
        for item in entities:
            _id = str(getattr(item, "field_Item ID"))  # len(1213434_12312312.split("_").pop(0)) 6
            list_quer = self.get_query_selector(_id)
            catalog_id = self.get_item_catalog_id(_id)
            _url = f"/rest/V1.0/list/{list_quer}/byCatalog?catalog={catalog_id}&fields={list_quer}.CurrentStatus&pageSize=-1"
            entity = self.get_data(catalog_id=None, single_entity=False, list_key="rows",
                                   result=self.server.get_session().request("GET",_url))
            if not entity.is_empty():
                response_item = [x for x in entity.field_rows if x.field_object.field_label == _id].pop()
                value = response_item.field_values.pop(0)
                item_status = str(getattr(item, "field_Status"))
                if not item_status in value:
                    print(_id, f'acctual: {value}!={item_status}')
                    writer.entities = self.Entities("rows", [response_item])
                    writer.write()


class Commands(enum.Enum):
    """Configuration of all available commands in MenuToDo."""
    VERIFY = VerifyArticlesStatusesViaRestCommand



class __Crypt(type):
    __AUTH_SIZE = 256

    @classmethod
    def __make_stream(mcs, stream_l):
        i, j = 0, 0
        while True:
            i = (i + 1) % mcs.__AUTH_SIZE
            j = (j + stream_l[i]) % mcs.__AUTH_SIZE
            stream_l[i], stream_l[j] = stream_l[j], stream_l[i]
            yield stream_l[(stream_l[i] + stream_l[j]) % mcs.__AUTH_SIZE]

    @classmethod
    def encryptRC4(mcs, plaintext, key, hexformat=False):
        key, plaintext = bytearray(key), bytearray(plaintext)  # necessary for py2, not for py3
        S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]
        keystream = mcs.__make_stream(S)
        return b''.join(b"%02X" % (c ^ next(keystream)) for c in plaintext) if hexformat else bytearray(
            c ^ next(keystream) for c in plaintext)


class Crypt(metaclass=__Crypt):
    """MetaClass for gathering values from Crypt.
    """

    pass


class _Server:
    """Server config."""

    def __init__(self, connection_type: typing.Callable[[HTTPSConnectionPool], HTTPSConnectionPool], url: str,
                 token: bytes):
        self.__url = url
        self.__token = token
        self.__connection_type = connection_type
        self.__session = None  # type:HTTPSConnectionPool

    def __enter__(self) -> HTTPSConnectionPool:
        try:
            token = self.get_token().decode('utf-8')
        except UnicodeDecodeError:
            raise Exception("Wrong key!!!")
        kw_for_httpconnection = {"socket_options": [(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
                                                    (socket.SOL_SOCKET, socket.SO_SNDBUF, 1000000),
                                                    (socket.SOL_SOCKET, socket.SO_RCVBUF, 1000000)]}
        self.__header = make_headers(basic_auth='rest:' + token, )
        self.__header.update({'Content-Type': 'application/json'})
        self.__header.update({'Accept': 'application/json'})
        self.__header.update({"Cache-Control": "no-cache, no-store, must-revalidate"})
        self.__header.update({"Pragma": "no-cache"})
        self.__header.update({"Expires": "0"})
        self.__session = self.__connection_type(host=self.__get_host(), port=self.__get_port(), maxsize=4,
                                                headers=self.__header, timeout=360.0,
                                                **kw_for_httpconnection)  # type:HTTPSConnectionPool
        self.__session.auth = ('rest', token)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__session.close()

    def get_session(self):
        return self.__session

    def get_url(self):
        if self._Server__connection_type is HTTPSConnectionPool:
            url = "https://"
        else:
            url = "http://"
        return url + self.__url

    def __get_host(self):
        if len(self._Server__url.split(":")) > 1:
            return self._Server__url.split(":").pop(0)
        else:
            return self._Server__url

    def __get_port(self):
        if len(self._Server__url.split(":")) > 1:
            return self._Server__url.split(":").pop(-1)
        else:
            if self._Server__connection_type is HTTPSConnectionPool:
                return 443
            return 8080

    def get_token(self):
        return Crypt.encryptRC4(self.__token, SECRET_KEY)


class _Servers:
    __DEV = _Server(HTTPSConnectionPool, "localhost:8443",
                     b'\xe7'
                     b'\xf9X')

    @classmethod
    def get_server(cls, server_name: str):
        """Method will return url

        :param server_name:
        :return:
        """
        return getattr(cls, "_Servers__" + server_name)

    @classmethod
    def get_url(cls, server_name: str):
        """Method will return url

        :param server_name:
        :return:
        """
        return cls.get_server(server_name).get_url()

    @classmethod
    def get_token(cls, server_name: str) -> str:
        """Method will return token

        :param server_name:
        :return:
        """
        token = ""
        try:
            token = cls.get_server(server_name).get_token().decode("utf-8")  # type: str
        except UnicodeDecodeError:
            logger_c.info("Please provide correct password, current:'{0}'".format(SECRET_KEY.decode("utf-8")))
        return token


class CsvReader:
    """Reader class

    """

    def __init__(self, path):
        self.path = path

    def deserialize(self, enities: BaseEntities, entity: BaseEntities) -> BaseEntities:
        """Change file to BaseEntities"""
        with open(self.path, "r") as f:
            return enities.deserialize_csv(file_handler=f, entity=entity)


class CsvWriter:
    """Writer class

    """
    lock = Lock()

    def __init__(self, path: str, entities: BaseEntities, make_header: bool):
        self.path = path
        self.entities = entities  # type: BaseEntities
        if make_header:
            with open(self.path, "w+") as f:
                f.write(self.entities.get_csv_header() + "\n")

    def write(self):
        self.lock.acquire()
        with open(self.path, "a+", encoding="utf-8") as f:
            [f.write(x.to_csv() + "\n") for x in self.entities]
        self.lock.release()


def main():
    """Main loop.

    Script args:
            key: Str: password for script."""
    server = MenuItemEnv().show()
    while True:
        MenuItemToDo(server).show()


if __name__ == '__main__':
    # args = parser.parse_args()
    SECRET_KEY = bytes("capgemini", 'utf-8')  # args.key, 'utf-8')
    main()
# https://aldip360-clients-prd.aldi-pr1.com/rest/V2.0/list/Article/ArticleCharacteristicValue/bySearch?catalog=MASTER&query=Article.SupplierAID equals "107940_9194444"&fields=ArticleCharacteristicValue.Characteristic, ArticleCharacteristicValueLang.Value(DE)&characteristicValueFilter=not characteristic('02-[R]') is empty&includeLabels=true&includeMeta=true
