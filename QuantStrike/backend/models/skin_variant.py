from dataclasses import dataclass
from typing import List


@dataclass
class SkinVariant:

    base_name: str

    stattrak: bool
    souvenir: bool

    conditions: List[str]