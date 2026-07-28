from dataclasses import dataclass

@dataclass(frozen=True)
class Skin:
    id: str
    name: str

    weapon: str
    finish: str
    condition: str

    stattrak: bool
    souvenir: bool

    history_file: str