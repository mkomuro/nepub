import hashlib
from importlib.metadata import version
import urllib.request

from nepub.type import Image

__version__ = version("nepub")


def get(url: str):
    headers = {"User-agent": f"nepub/{__version__}"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as res:
        return res.read().decode("utf-8")


def get_image(url: str) -> Image:
    headers = {"User-agent": f"nepub/{__version__}"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as res:
        content_type = res.headers["Content-Type"]
        img_data = res.read()
        if content_type == "image/jpeg":
            img_ext = "jpg"
        elif content_type == "image/png":
            img_ext = "png"
        elif content_type == "image/gif":
            img_ext = "gif"
        else:
            raise Exception(f"対応していない画像の形式です: {content_type}")
        img_md5 = hashlib.md5(img_data).hexdigest()
        # MD5 ハッシュ値をファイル名にする
        img_name = f"{img_md5}.{img_ext}"
        return {
            "type": content_type,
            "id": img_md5,
            "name": img_name,
            "data": img_data,
        }
