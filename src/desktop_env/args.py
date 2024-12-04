import yaml
from pydantic import BaseModel


def callback_sink(*args, **kwargs):
    """A dummy callback function that does nothing"""


class BaseArgs(BaseModel):
    @classmethod
    def from_yaml(cls, path: str):
        with open(path, "r") as file:
            return cls(**yaml.safe_load(file))

    def to_yaml(self, path: str):
        with open(path, "w") as file:
            yaml.dump(yaml.safe_load(self.model_dump_json()), file)
