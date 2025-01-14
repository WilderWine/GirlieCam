from dataclasses import dataclass
from typing import List
from PIL import Image

@dataclass
class Filter:
    brightness: str
    contrast: str
    saturation: str
    gauss_blur: str
    sharpness: str
    blackwhite: str
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