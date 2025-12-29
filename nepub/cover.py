# This code was generated using Google Gemini and Microsoft Copilot.
#
import os
import textwrap
import unicodedata
from io import BytesIO
from dataclasses import dataclass

from PIL import Image as PILImage, ImageDraw as PILImageDraw, ImageFont as PILImageFont
from nepub.type import Image as CoverImage


# ------------------------------------------------------------
# Cover Size Definitions
# ------------------------------------------------------------

@dataclass(frozen=True)
class CoverSize:
    """EPUB 表紙画像のサイズ定義（300dpi 相当）
    ---
    A6 (文庫 = 1:1.41)
        width:   1240 = (105mm / 25.4) * 300
        height:  1748 = (148mm / 25.4) * 300
    B6 (単行本 = 1:1.42)
        width:   1512 = (128mm / 25.4) * 300
        height:  2150 = (182mm / 25.4) * 300
    KINDLE (1:1.41): https://kdp.amazon.co.jp/ja_JP/help/topic/G6GTK3T3NUHKLEFX
        width:   1816 px
        height:  2560 px
    """
    width: int
    height: int
    dpi: int = 300

    @classmethod
    def from_mm(cls, width_mm: float, height_mm: float, dpi: int = 300):
        def px(mm):
            v = int(mm / 25.4 * dpi)
            v += 1 if v % 2 == 1 else 0   # ← 三項演算子で偶数化
            return v

        return cls(width=px(width_mm), height=px(height_mm), dpi=dpi)


class CoverSizeDefaults:
    A6 = CoverSize.from_mm(105, 148)
    B6 = CoverSize.from_mm(128, 182)
    KINDLE = CoverSize(1816, 2560)


# ------------------------------------------------------------
# Cover Generator Class
# ------------------------------------------------------------

class CoverGenerator:
    """EPUB 表紙画像を生成・読み込みするクラス"""

    # デフォルト設定
    FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    MAX_FULL_WIDTH = 72
    FRAME_RATIO = 0.05  # 外枠 5%
    TITLE_Y_RATIO = 0.25
    AUTHOR_Y_RATIO = 0.75
    TITLE_SPACING = 20
    AUTHOR_SPACING = 10

    BASE_COLOR = (203, 185, 148)
    TEXT_COLOR = (51, 46, 37)

    def __init__(self, img_size: CoverSize = CoverSizeDefaults.A6):
        self.img_size = img_size

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def generate(self, title: str, author: str, user_cover_jpeg: str) -> CoverImage:
        """既存 JPEG があれば読み込み、なければ生成して返す"""
        print(
            f"Specified cover page size: W={self.img_size.width}, "
            f"H={self.img_size.height}, DPI={self.img_size.dpi}"
        )

        if os.path.exists(user_cover_jpeg):
            img_bytes = self._load_cover_jpeg(user_cover_jpeg)
        else:
            img_bytes = self._create_cover_jpeg(title, author)

        '''
          "name" は "cover.jpg" 固定。これは EPUB ファイル内の画僧ファイル名になる。
          固定値以外にしたい場合は、content.opf、cover.xhtml ファイルを変更する必要がある。
        '''
        return {
            "type": "image/jpg",
            "id": "cimage",
            "name": "cover.jpg",
            "data": img_bytes,
        }

    # ------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------

    def _load_cover_jpeg(self, path: str) -> bytes:
        """JPEG を読み込み、必要なら RGB 変換して bytes にする"""
        with PILImage.open(path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            return self._image_to_bytes(img)

    def _create_cover_jpeg(self, title: str, author: str) -> bytes:
        """タイトルと作者名を描画した表紙画像を生成"""
        title = self._truncate_text_full(title)
        author = self._truncate_text_half(author)

        w, h = self.img_size.width, self.img_size.height
        img = PILImage.new("RGB", (w, h), color=self.BASE_COLOR)
        draw = PILImageDraw.Draw(img)

        font = self._load_font(w)
        frame_width = int(w * self.FRAME_RATIO)

        # フレーム描画
        draw.rectangle(
            [frame_width, frame_width, w - frame_width, h - frame_width],
            fill=self.BASE_COLOR,
            outline=self.TEXT_COLOR,
            width=15,
        )

        # テキスト折り返し
        wrapped_title = self._wrap_text(title, font, w)
        wrapped_author = self._wrap_text(author, font, w)

        # 描画位置
        center_x = w // 2
        title_y = int(h * self.TITLE_Y_RATIO)
        author_y = int(h * self.AUTHOR_Y_RATIO)

        draw.multiline_text(
            (center_x, title_y),
            wrapped_title,
            fill=self.TEXT_COLOR,
            font=font,
            anchor="mm",
            align="center",
            spacing=self.TITLE_SPACING,
        )

        draw.multiline_text(
            (center_x, author_y),
            wrapped_author,
            fill=self.TEXT_COLOR,
            font=font,
            anchor="mm",
            align="center",
            spacing=self.AUTHOR_SPACING,
        )

        return self._image_to_bytes(img)

    # ------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------

    def _truncate_text_full(self, text: str) -> str:
        """全角幅ベースで 72 文字相当までに制限"""
        return self._limit_east_asian_width(text, self.MAX_FULL_WIDTH)

    def _truncate_text_half(self, text: str) -> str:
        """全角幅ベースで 36 文字相当までに制限"""
        return self._limit_east_asian_width(text, self.MAX_FULL_WIDTH / 2)

    def _limit_east_asian_width(self, text: str, max_width: int) -> str:
        """
        全角=1.0、半角=0.5 として幅制限.
        指定幅を超える場合は、末尾を「…」に置き換えて返す.
        """
        total = 0.0
        for ch in text:
            total += 1.0 if unicodedata.east_asian_width(ch) in ("F", "W", "A") else 0.5

        if total <= max_width:
            return text

        limit = max_width - 1.0
        cur = 0.0
        result = []

        for ch in text:
            w = 1.0 if unicodedata.east_asian_width(ch) in ("F", "W", "A") else 0.5
            if cur + w > limit:
                break
            cur += w
            result.append(ch)

        return "".join(result) + "…"

    def _wrap_text(self, text: str, font: PILImageFont.ImageFont, width: int) -> str:
        """画像幅に応じて textwrap で折り返し"""
        max_width = width * 0.8
        font_size = font.size
        chars_per_line = max(1, int(max_width // font_size))
        return "\n".join(textwrap.wrap(text, width=chars_per_line))

    def _load_font(self, width: int) -> PILImageFont.ImageFont:
        """フォント読み込み（なければデフォルト）。12文字幅。"""
        font_size = (width // 5 * 4) // 12
        if os.path.exists(self.FONT_PATH):
            return PILImageFont.truetype(self.FONT_PATH, font_size)
        return PILImageFont.load_default()

    def _image_to_bytes(self, img: PILImage.Image) -> bytes:
        """PIL Image → JPEG bytes"""
        buf = BytesIO()
        img.save(buf, format="JPEG") #, dpi=(self.img_size.dpi, self.img_size.dpi))
        return buf.getvalue()


# ------------------------------------------------------------
# Example Usage
# ------------------------------------------------------------

if __name__ == "__main__":
    """
    A6 サイズで生成:
        python cover.py "吾輩は猫である" "夏目漱石" "cover.jpg" "A6"
    B6 サイズで生成:
        python cover.py "吾輩は猫である" "夏目漱石" "cover.jpg" "B6"
            or
        python -m nepub.cover ...

    KINDLE サイズで生成:
        python cover.py "タイトル" "著者名" "mycover.jpg" "KINDLE"

    引数なし → test_cases 実行:
        python cover.py
    """
    import sys

    # --- サイズ名を CoverSizeDefaults から取得する小さなヘルパー ---
    def resolve_size(size_name: str):
        try:
            return getattr(CoverSizeDefaults, size_name)
        except AttributeError:
            valid = ", ".join([attr for attr in dir(CoverSizeDefaults) if not attr.startswith("_")])
            raise ValueError(f"不正なサイズ名です: {size_name}\n利用可能なサイズ: {valid}")

    # --- 引数なしの場合のテストケース ---
    test_cases = [
        (
            "小説のタイトル名（Ａ６）",
            "小説の作者名",
            CoverSizeDefaults.A6,
            "A6-short"
        ),
        (
            "これは非常に長い小説のタイトルで画像幅を超えてしまう場合のテストです。",
            "すごく名前が長い作者名のテスト",
            CoverSizeDefaults.A6,
            "A6-long"
        ),
        (
            "小説のタイトル名（Ｂ６）",
            "小説の作者名",
            CoverSizeDefaults.B6,
            "B6-short"
        ),
        (
            ("あいうえおかきくけこさＡ"
             "あいうえおかきくけこさＢ"
             "あいうえおかきくけこさＣ"
             "あいうえおかきくけこさＤ"
             "あいうえおかきくけこさＥ"
             "あいうえおかきくけこさＦあいうえお"
            ),
            ("寿限無、寿限無、五劫のす"
             "りきれ、海砂利水魚の、水"
             "行末・（略）長久命の長助"
            ),
            CoverSizeDefaults.KINDLE,
            "KINDLE-very-long"
         ),
    ]

    # --- 引数解析 ---
    args = sys.argv[1:]

    # ------------------------------------------------------------
    # 引数なし → test_cases を実行
    # ------------------------------------------------------------
    if len(args) == 0:
        print("引数が無いため test_cases を実行します")

        for title, author, size, label in test_cases:
            generator = CoverGenerator(size)
            cover = generator.generate(title, author, "cover.jpg")

            file_path = f"size-{label}-{cover['name']}"
            with open(file_path, "wb") as f:
                f.write(cover["data"])

            print(f"Saved: {file_path}")

    # ------------------------------------------------------------
    # 引数4つ → (title, author, output_filename, size_name)
    # ------------------------------------------------------------
    elif len(args) == 4:
        title, author, output_filename, size_name = args

        try:
            size = resolve_size(size_name)
        except ValueError as e:
            print(e)
            print("使い方: python cover.py \"タイトル\" \"著者名\" \"出力ファイル名\" \"サイズ名\"")
            sys.exit(1)

        generator = CoverGenerator(size)
        cover = generator.generate(title, author, "cover.jpg")

        with open(output_filename, "wb") as f:
            f.write(cover["data"])

        print(f"Saved: {output_filename}")

    # ------------------------------------------------------------
    # 引数の数が不正
    # ------------------------------------------------------------
    else:
        print("引数の数が正しくありません。")
        print("使い方: python cover.py \"タイトル\" \"著者名\" \"出力ファイル名\" \"サイズ名\"")
        print("または: python -m nepub.cover \"タイトル\" \"著者名\" \"出力ファイル名\" \"サイズ名\"")

