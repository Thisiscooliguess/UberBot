import datetime
from pathlib import Path
from typing import Any, Dict, List, Union
import urllib.request
from file_ops import SetF
from colored import Fore, Style

import json
import requests
import logging as log
import urllib.parse, urllib.request

LEVEL_COLORS = {
    log.DEBUG: Fore.dark_gray,
    log.INFO: Fore.blue,
    log.WARNING: Fore.yellow,
    log.ERROR: Fore.orange_4a,
    log.CRITICAL: Fore.red,
}


class CustomFormatter(log.Formatter):
    def format(self, record: log.LogRecord) -> str:
        message = ""

        message += (
            f"[{LEVEL_COLORS[record.levelno]}{record.levelname[0]}{Style.reset}] "
        )

        message += (
            f"{Fore.dark_gray}{datetime.datetime.now().isoformat(' ')}{Style.reset} "
        )

        message += "- "
        message += record.getMessage()

        return message


log.basicConfig(level=log.DEBUG)
logger = log.getLogger()

for handler in logger.root.handlers:
    handler.setFormatter(CustomFormatter(handler.formatter._fmt))

log.info("Loading...")


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

    def __getitem__(self, item):
        return self.data[item]


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


class PtUser(PtObj):
    def __init__(self, raw_data: dict = {}) -> None:
        super().__init__(raw_data)

        self.id: int = None
        self.username: str = None
        self.email: str = None
        self.admin: bool = None

        if self.validate_obj():
            data = raw_data["attributes"]

            self.id = data["id"]
            self.username = data["username"]
            self.email = data["email"]
            self.admin = data["admin"]

    def __repr__(self) -> str:
        return f"<PtUser {self.username} {self.email} id={self.id}>"

    def validate_obj(self) -> bool:
        return super().validate_obj() and self.raw_data.get("attributes")


class PtFile(PtObj):
    def __init__(self, raw_data: dict = {}) -> None:
        super().__init__(raw_data)

        self.name: str = None
        self.mode: str = None
        self.size: int = None
        self.is_file: bool = None
        self.is_editable: bool = None
        self.created_at: datetime.datetime = None
        self.modified_at: datetime.datetime = None

        if self.validate_obj():
            data = raw_data["attributes"]

            self.name = data["name"]
            self.mode = data["mode"]
            self.size = data["size"]
            self.is_file = data["is_file"]
            self.created_at = datetime.datetime.fromisoformat(data["created_at"])
            self.modified_at = datetime.datetime.fromisoformat(data["modified_at"])

    def __repr__(self) -> str:
        return f"<PtFile {self.name} - size: {self.size} MB, file: {self.is_file}>"

    def validate_obj(self) -> bool:
        return super().validate_obj() and self.raw_data.get("attributes")


class PtURL(PtObj):
    def __init__(self, raw_data: dict = {}) -> None:
        super().__init__(raw_data)

        self.url: str = None

        if self.validate_obj():
            self.url = raw_data["attributes"]["url"]

    def __repr__(self) -> str:
        return f'<PtURL "{self.url}>"'

    def validate_obj(self) -> bool:
        return super().validate_obj() and self.raw_data.get("attributes")


class PtAPI:
    def __init__(self, do_stuff: bool = True):
        self.keys = {}
        self.server_info = {}
        self.user_info = {}
        self.API_URL = "https://panel.embotic.xyz/api/client/"
        self.rateLeft = 720
        self.rateMax = 720

        if do_stuff:
            self.refresh_keys()
            self.refresh_serv_info()
            self.refresh_user_info()

    def p_get(self, url: str, key: str, is_json: bool = True) -> Union[dict, List]:
        url = self.API_URL + url
        headers = {"Authorization": "Bearer " + key, "accept": "application/json"}

        resp = requests.request("GET", url=url, headers=headers)

        try:
            self.rateMax = resp.headers["x-ratelimit-limit"]
            self.rateLeft = resp.headers["x-ratelimit-remaining"]
        except:
            log.warning("Cannot get ratelimit")

        log.debug(f"Ratelimit: {self.rateLeft}/{self.rateMax}")

        if is_json:
            data = filter_data(json.loads(resp.text))

            if str(resp.status_code)[0] != "2":
                log.error(f"Error: {data}")
                return {}

            return data

        return resp.text

    def refresh_keys(self):
        self.keys = get_keys()

    def refresh_serv_info(self):
        log.info("Refreshing servers...")
        acc_servers = {}
        for key, value in self.keys.items():
            acc_servers[key] = self.get_serv_info(value)

        self.server_info = acc_servers

    def refresh_user_info(self):
        log.info("Refreshing users...")
        acc_users = {}
        for key, value in self.keys.items():
            acc_users[key] = self.get_user_info(value)

        self.user_info = acc_users

    def get_serv_info(self, key: str) -> dict:
        return self.p_get(url="", key=key)

    def get_user_info(self, key: str) -> dict:
        return self.p_get(url="account", key=key)

    def get_files(self, key: str, path: str, server: Union[str, PtServ]) -> list:
        return self.p_get(
            url=f"servers/{server.ident if type(server) == PtServ else server}/files/list?directory={urllib.parse.quote(path, safe='')}",
            key=key,
        )

    def get_file_content(self, key: str, path: str, server: Union[str, PtServ]) -> list:
        return self.p_get(
            url=f"servers/{server.ident if type(server) == PtServ else server}/files/contents?file={urllib.parse.quote(path, safe='')}",
            key=key,
            is_json=False,
        )

    def download_file(
        self,
        key: str,
        path: str,
        server: Union[str, PtServ],
        localPath: Path = Path(__file__).parent,
    ) -> int:
        url = self.p_get(
            url=f"servers/{server.ident if type(server) == PtServ else server}/files/download?file={urllib.parse.quote(path, safe='')}",
            key=key,
        ).url

        localPath = localPath / Path(path).name

        print(url)
        log.info(f"Downloading file {path} to {localPath}...")

        try:
            urllib.request.urlretrieve(url=url, filename=localPath)
        except Exception as e:
            log.error(f"Cannot download file with error {e}")
            return 1

        log.info("Downloaded!")
        return 0


OBJECT_NAMES = {
    "list": PtArr,
    "server": PtServ,
    "allocation": PtAlloc,
    "egg_variable": PtEggVar,
    "user": PtUser,
    "file_object": PtFile,
    "signed_url": PtURL,
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


api = PtAPI(do_stuff=True)
