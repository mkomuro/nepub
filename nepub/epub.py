from importlib import resources
from typing import List

from jinja2 import Environment, PackageLoader

from nepub.type import Chapter, Episode, MetadataImage

env = Environment(
    loader=PackageLoader("nepub"),
    # データ取得の際にエスケープ加工するので
    # ここではエスケープしない
    autoescape=False,
)
template_content = env.get_template("content.opf")
template_navigation = env.get_template("navigation.xhtml")
template_text = env.get_template("text.xhtml")


def content(
    title: str,
    author: str,
    timestamp: str,
    episodes: List[Episode],
    images: List[MetadataImage],
):
    return template_content.render(
        {
            "title": title,
            "author": author,
            "timestamp": timestamp,
            "episodes": episodes,
            "images": images,
        }
    )


def nav(chapters: List[Chapter]):
    return template_navigation.render({"chapters": chapters})


def text(title: str, paragraphs: List[str]):
    return template_text.render({"title": title, "paragraphs": paragraphs})


def container():
    return resources.read_text("nepub.files", "container.xml")


def style():
    return resources.read_text("nepub.files", "style.css")
