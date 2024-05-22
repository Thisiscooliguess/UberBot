import json


SECRET_FILE = "settings.secret"


def get_data() -> dict:
    with open(SECRET_FILE) as f:
        return json.load(f)


def put_data(data: dict) -> None:
    with open(SECRET_FILE, "w") as f:
        return json.dump(data, f)


class SetF:
    def __init__(self) -> None:
        self.d = get_data()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        put_data(self.d)
