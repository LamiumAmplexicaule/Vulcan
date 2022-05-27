from enum import Enum
from typing import List

from pydantic import BaseModel


class SearchSite(str, Enum):
    AMAZON = 'amazon'
    YODOBASHI = 'yodobashi'
    FACTORY_GEAR = 'factory_gear'
    EHIME_MACHINE = 'ehime_machine'
    WIT = 'wit'


class SearchIn(BaseModel):
    site: SearchSite
    value: str


class SearchOut(BaseModel):
    site: SearchSite
    result: List[tuple[str, str]] = []
