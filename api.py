from curses import raw
import json
from pickle import OBJ
import requests

from typing import Any, Dict, List, Union

from requests import Request, get, head
from file_ops import SetF
from pprint import pprint


def get_keys() -> Dict:
    with SetF() as s:
        if s.d.get("keys"):
            return s.d["keys"]
        else:
            s.d["keys"] = {}
            return {}


def add_key(name: str, key: str) -> None:
    with SetF() as s:
        if name in list(get_keys().keys()):
            return
        else:
            s.d["keys"][name] = key


class PtObj:
    def __init__(self, raw_data: dict = {}) -> None:
        self.raw_data = raw_data
        self.type = "null"

        if self.validate_obj():
            self.type = raw_data["object"]

    def validate_obj(self) -> bool:
        return bool(self.raw_data.get("object"))


"""        "limits": {
          "memory": 512,
          "swap": 0,
          "disk": 200,
          "io": 500,
          "cpu": 0
        },"""


class ServLim:
    def __init__(self, data: dict) -> None:
        self.mem: int = data["memory"]
        self.swp: int = data["swap"]
        self.dsk: int = data["disk"]
        self.io: int = data["io"]
        self.cpu: float = data["cpu"] / 100

    def __repr__(self) -> str:
        return f"<Server Limits: mem={self.mem} MB, swp={self.swp}, dsk={self.dsk} MB, io={self.io}, cpu={str(self.cpu).strip('.0')} Core(s)>"


class PtArr(PtObj):
    def __init__(self, raw_data: dict = {}) -> None:
        super().__init__(raw_data)

        self.data: List[Any] = []

        if self.validate_obj():
            self.data = raw_data["data"]

    def validate_obj(self) -> bool:
        return super().validate_obj() and bool(self.raw_data.get("data"))

    def __repr__(self) -> str:
        if len(self.data):
            return "[\n    " + ",\n    ".join(map(str, self.data)) + "\n]"
        else:
            return "[]"

    def __iter__(self):
        return iter(self.data)


class PtAlloc(PtObj):
    def __init__(self, raw_data: Dict = {}) -> None:
        super().__init__(raw_data)

        self.id: int = None
        self.ip: str = None
        self.ip_alias: str = None
        self.port: int = None

        if self.validate_obj():
            data = raw_data["data"]

            self.id = data["id"]
            self.ip = data["ip"]
            self.ip_alias = data["ip_alias"]
            self.port = data["port"]

    def __repr__(self) -> str:
        return f"<PtAlloc id={self.id}, ip={self.ip}, port={self.port}>"

    def validate_obj(self) -> bool:
        return super().validate_obj() and self.raw_data.get("data")


class PtEggVar(PtObj):
    def __init__(self, raw_data: Dict = {}) -> None:
        super().__init__(raw_data)

        self.name: str = None
        self.desc: str = None
        self.env: str = None
        self.defVal: str = None
        self.serVal: str = None
        self.editable: bool = None
        self.rules: str = None

        if self.validate_obj():
            data = raw_data["attributes"]

            self.name = data["name"]
            self.desc = data["description"]
            self.env = data["env_variable"]
            self.defVal = data["default_value"]
            self.serVal = data["server_value"]
            self.editable = data["is_editable"]
            self.rules = data["rules"]

    def __repr__(self) -> str:
        return f'<PtEggVar {self.name}, value="{self.serVal}", editable={self.editable}, rules={self.rules}>'

    def validate_obj(self) -> bool:
        return super().validate_obj() and self.raw_data.get("attributes")


class PtServ(PtObj):
    def __init__(self, raw_data: dict = {}) -> None:
        super().__init__(raw_data)

        self.owner: bool = True
        self.ident: str = None
        self.int_id: int = None
        self.uuid: str = None
        self.name: str = None
        self.desc: str = None
        self.limits: ServLim = None
        self.rels: Dict[str, Any]

        if self.validate_obj():
            data = raw_data["attributes"]

            self.owner = data["server_owner"]
            self.ident = data["identifier"]
            self.uuid = data["uuid"]
            self.name = data["name"]
            self.desc = data["description"]
            self.limits = ServLim(data["limits"])
            self.rels = filter_data(data["relationships"])

    def validate_obj(self) -> bool:
        return super().validate_obj() and bool(self.raw_data.get("attributes"))

    def __repr__(self) -> str:
        return f'<Server "{self.name}" - uuid: {self.uuid}, identifier: {self.ident}>'


class PtAPI:
    def __init__(self, do_stuff: bool = True):

        self.keys = {}
        self.server_info = {}
        self.API_URL = "https://panel.embotic.xyz/api/client/"
        self.rateLeft = 720
        self.rateMax = 720

        if do_stuff:
            self.refresh_keys()

    def p_get(self, url: str, key: str) -> Union[dict, List]:
        url = self.API_URL + url
        headers = {"Authorization": "Bearer " + key, "accept": "application/json"}

        resp = requests.request("GET", url=url, headers=headers)

        data = filter_data(json.loads(resp.text))

        self.rateMax = resp.headers["x-ratelimit-limit"]
        self.rateLeft = resp.headers["x-ratelimit-remaining"]

        return data

    def refresh_keys(self):
        self.keys = get_keys()

    def refresh_serv_info(self):
        acc_servers = []
        for key, value in self.keys.items:
            acc_servers[key] = self.get_serv_info(key)

    def get_serv_info(self, key) -> dict:
        return self.p_get(url="", key=key)


OBJECT_NAMES = {
    "list": PtArr,
    "server": PtServ,
    "allocation": PtAlloc,
    "egg_variable": PtEggVar,
}


def filter_data(d):
    data = None

    if type(d) == dict:
        if obType := d.get("object"):
            if obTypeC := OBJECT_NAMES.get(obType):
                data = obTypeC(d)

                if type(data) == PtArr:
                    data.data = list(map(lambda x: filter_data(x), data.data))

                return data
        else:
            data = {}
            for k, v in list(d.items()):
                data[k] = filter_data(v)

            return data
    return d


d = PtAPI().get_serv_info(list(get_keys().values())[0])
