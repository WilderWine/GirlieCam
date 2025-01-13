from dataclasses import dataclass
from typing import List
from PIL import Image

@dataclass
class Filter:
    brightness: int
    contrast: int
    saturation: float
    gauss_blur: int
    sharpness: int
    blackwhite: int
    name: str

@dataclass
class Sticker:
    name: str
    img: Image.Image

@dataclass
class Mask:
    name: str
    eye_r: Image.Image
    eye_l: Image.Image
    nose: Image.Image
    mouth: Image.Image

@dataclass
class User:
    name: str
    email: str
    password: str
    masks: List[Mask]
    stickers: List[Sticker]
    filters: List[Filter]