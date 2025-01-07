from typing import Any

from pydantic import AfterValidator, BaseModel, Field, ImportString, ValidationError, model_validator
from typing_extensions import Annotated, Self

from .args import BaseArgs
from .threading import AbstractThread


class SubmoduleArgs(BaseArgs):
    module: ImportString
    args: Any

    @model_validator(mode="after")
    def instantiate_args(self) -> Self:
        args_cls = self.module.args_cls
        if not isinstance(self.args, args_cls):
            self.args = args_cls(**self.args)
        return self


class DesktopArgs(BaseArgs):
    submodules: list[SubmoduleArgs] = Field(default_factory=list)
