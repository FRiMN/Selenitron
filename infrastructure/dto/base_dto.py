from typing import Any


class BaseDTO:
    """
    Base class that implements magic methods
    """

    def __init__(self, properties: list, record: dict) -> None:
        self._properties = properties
        for prop in self._properties:
            setattr(self, prop, record.get(prop))

    def __dict__(self) -> dict:
        return {prop: getattr(self, prop) for prop in self._properties}

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def __iter__(self) -> Any:
        for prop in self._properties:
            yield prop, getattr(self, prop)

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return str(self.__dict__())
