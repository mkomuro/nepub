# This code was generated using Google Gemini and Microsoft Copilot.
#
import os
import textwrap
import unicodedata
from io import BytesIO
from datetime import datetime
from dataclasses import dataclass

import piexif
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
            v_px = int(mm / 25.4 * dpi)
            v_px += 1 if v_px % 2 == 1 else 0   # ← 三項演算子で偶数化
            return v_px

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

    # --- 色テーマの定義 ---
    # (背景色, 文字・枠線色) のタプル
    COLOR_THEMES = {
        "brown": ((203, 185, 148), (51, 46, 37)),
        "red":   ((230, 200, 200), (120, 40, 40)),
        "green": ((200, 230, 200), (40, 100, 40)),
        "blue":  ((200, 215, 230), (40, 60, 120)),
        "gray":  ((192, 192, 192), (60, 60, 60)),
        "BROWN": ((51, 46, 37), (203, 185, 148),),
        "RED":   ((120, 40, 40), (230, 200, 200)),
        "GREEN": ((40, 100, 40), (200, 230, 200)),
        "BLUE":  ((40, 60, 120), (200, 215, 230)),
        "GRAY":  ((60, 60, 60), (192, 192, 192)),
    }

    def __init__(self, img_size: CoverSize = CoverSizeDefaults.A6):
        self.img_size = img_size

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def generate(self, title: str, author: str, user_cover_jpeg: str, theme: str = "brown") -> CoverImage:
        """既存 JPEG があれば読み込み、なければ指定した色のテーマで生成して返す"""

        if os.path.exists(user_cover_jpeg):
            img_bytes = self._load_cover_jpeg(user_cover_jpeg)
            print(f"Loaded a user-specified JPEG image: '{user_cover_jpeg}'.")
        else:
            print(
                f"Specified cover page size: W={self.img_size.width}, "
                f"H={self.img_size.height}, DPI={self.img_size.dpi}"
            )
            # テーマ名に基づいて色を取得（存在しない場合は brown を使用）
            base_color, text_color = self.COLOR_THEMES.get(theme, self.COLOR_THEMES["brown"])
            img_bytes = self._generate_cover_jpeg(title, author, base_color, text_color)

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
            return self._image_to_bytes_with_jpeg_metadata(img)

    def _generate_cover_jpeg(self, title: str, author: str, base_color: tuple, text_color: tuple) -> bytes:
        """タイトルと作者名を描画した表紙画像を生成"""
        title = self._truncate_text_full(title)
        author = self._truncate_text_half(author)

        w, h = self.img_size.width, self.img_size.height
        img = PILImage.new("RGB", (w, h), color=base_color)
        draw = PILImageDraw.Draw(img)

        font = self._load_font(w)
        frame_width = int(w * self.FRAME_RATIO)
        border_width = int(w * self.FRAME_RATIO * 0.25) # was 15

        # フレーム描画
        draw.rectangle(
            [frame_width, frame_width, w - frame_width, h - frame_width],
            fill=base_color,
            outline=text_color,
            width=border_width,
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
            fill=text_color,
            font=font,
            anchor="mm",
            align="center",
            spacing=self.TITLE_SPACING,
        )

        draw.multiline_text(
            (center_x, author_y),
            wrapped_author,
            fill=text_color,
            font=font,
            anchor="mm",
            align="center",
            spacing=self.AUTHOR_SPACING,
        )

        # UserComment のみ ASCII 以外を受け付ける
        meta = {
            "ImageDescription": "Web novel cover image for nepub",
            "Artist": "N/A",
            "Copyright": "Copyright (c) 2025 mkomuro",
            "Software": "nepub",
            "UserComment": f"小説タイトル：{title}／著者：{author}",
        }

        return self._image_to_bytes_with_jpeg_metadata(img, jpeg_metadata=meta)

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

    def _make_exif_user_comment(self, text: str) -> bytes:
        """
        EXIF 2.3: https://www.cipa.jp/std/documents/j/DC-008-2012_J.pdf

        表 9 文字コードと文字コード欄記入方法:
            | 文字コード |           コード記入方法 (8Bytes)             |   リファレンス    |
            |-----------+----------------------------------------------+------------------+
            |   ASCII   |41.H, 53.H, 43.H, 49.H, 49.H, 00.H, 00.H, 00.H|  ITU-T T.50 IA5  |
            |    JIS    |4A.H, 49.H, 53.H, 00.H, 00.H, 00.H, 00.H, 00.H|  JIS X0208-1990  |
            |  Unicode  |55.H, 4E.H, 49.H, 43.H, 4F.H, 44.H, 45.H, 00.H| Unicode Standard |
            | Undefined |00.H, 00.H, 00.H, 00.H, 00.H, 00.H, 00.H, 00.H|    Undefined     |

        EXIF 3.0: CIPA DC-008-2024 (https://www.cipa.jp/j/std/std-sec.html)

        表 4 文字コードと文字コード欄記入方法:
            |           |                          |      準拠規格 / 参照先       |
            | 文字コード |    識別コード (8Bytes)    |  符号化方式   |   文字集合   |
            |-----------+--------------------------+-----------------------------+
            |   ASCII   |41.53.43.49. 49.00.00.00.H|      ANSI INCITS 4[17]      |
            |    JIS    |4A.49.53.00. 00.00.00.00.H|ISO-2022-JP[5]| JIS 漢字[6]  |
            |  Unicode  |55.4E.49.43. 4F.44.45.00.H|   UTF-8[22]  | Unicode[21]  |
            | Undefined |00.00.00.00. 00.00.00.00.H|      -       |       -      |

        上記の表によれば UserComment に入れる文字列の先頭 8 バイトは "Unicode\0" を
        指定しなければならない。しかし、"UNICODE\x00" を指定しないと Linux、Windows の
        いずれの場合も正しく表示されないため、実際には実装依存のようだ。
        尚、EXIF では UTF-8 ではなく UTF-16 へエンコードしておく方が良いようだ。
        """
        prefix = b"UNICODE\x00"
        return prefix + text.encode("utf-16-be")

    def _image_to_bytes_with_jpeg_metadata(
        self,
        img: PILImage.Image,
        jpeg_metadata: dict | None = None,
    ) -> bytes:
        """
        PIL Image → JPEG bytes
        jpeg_metadata=None の場合は EXIF も DPI も埋め込まない
        jpeg_metadata が dict の場合のみ EXIF + DPI を埋め込む

        jpeg_metadata = {
            "ImageDescription": "Web novel cover image for nepub",
            "Artist": "N/A",
            "Copyright": "Copyright (c) 2025 mkomuro",
            "Software": "nepub",
            "UserComment": f"小説タイトル：{title}／著者：{author}",
        }
        """

        # jpeg_metadata が None → EXIF なし、DPI なし
        if jpeg_metadata is None:
            buf = BytesIO()
            img.save(buf, format="JPEG")  # DPI も EXIF も付けない
            return buf.getvalue()

        # --- jpeg_metadata がある場合のみ EXIF を構築 ---
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

        # 1. ユーザー指定メタデータ
        if "ImageDescription" in jpeg_metadata:
            exif_dict["0th"][piexif.ImageIFD.ImageDescription] = jpeg_metadata["ImageDescription"]

        if "Artist" in jpeg_metadata:
            exif_dict["0th"][piexif.ImageIFD.Artist] = jpeg_metadata["Artist"]

        if "Copyright" in jpeg_metadata:
            exif_dict["0th"][piexif.ImageIFD.Copyright] = jpeg_metadata["Copyright"]

        if "Software" in jpeg_metadata:
            exif_dict["0th"][piexif.ImageIFD.Software] = jpeg_metadata["Software"]

        # UserComment のみ 日本語 OK (他は ASCII)
        if "UserComment" in jpeg_metadata:
            user_comment = self._make_exif_user_comment(jpeg_metadata["UserComment"])
            exif_dict["Exif"][piexif.ExifIFD.UserComment] = user_comment

        # 2. 自動付与メタデータ（作成日時 + 固定 author）
        now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        exif_dict["0th"][piexif.ImageIFD.DateTime] = now
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = now
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = now

        # 固定 author を埋め込む（ユーザー指定 Artist より優先, ASCII のみ）
        FIXED_AUTHOR = "nepub/dev"
        exif_dict["0th"][piexif.ImageIFD.Artist] = FIXED_AUTHOR

        # EXIF バイナリ化
        exif_bytes = piexif.dump(exif_dict)

        # --- JPEG 保存（jpeg_metadata がある場合のみ DPI を付ける） ---
        buf = BytesIO()
        img.save(
            buf,
            format="JPEG",
            dpi=(self.img_size.dpi, self.img_size.dpi),
            exif=exif_bytes,
        )

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
            "A6-short",
            "brown"
        ),
        (
            "小説のタイトル名（Ａ６）",
            "小説の作者名",
            CoverSizeDefaults.A6,
            "A6-short-r",
            "BROWN"
        ),
        (
            ("これは非常に長い小説のタ"
             "イトルで画像幅を超えてし"
             "まう場合のテストです。（"
             "Ａ６）"
            ),
            "すごく名前が長い作者名のテスト",
            CoverSizeDefaults.A6,
            "A6-long",
            "red"
        ),
        (
            ("これは非常に長い小説のタ"
             "イトルで画像幅を超えてし"
             "まう場合のテストです。（"
             "Ａ６）"
            ),
            "すごく名前が長い作者名のテスト",
            CoverSizeDefaults.A6,
            "A6-long-r",
            "RED"
        ),
        (
            "小説のタイトル名（Ｂ６）",
            "小説の作者名",
            CoverSizeDefaults.B6,
            "B6-short",
            "green"
        ),
        (
            "小説のタイトル名（Ｂ６）",
            "小説の作者名",
            CoverSizeDefaults.B6,
            "B6-short-r",
            "GREEN"
        ),
        (
            ("これは非常に長い小説のタ"
             "イトルで画像幅を超えてし"
             "まう場合のテストです。（"
             "Ｂ６）"
            ),
            "すごく名前が長い作者名のテスト",
            CoverSizeDefaults.B6,
            "B6-long",
            "blue"
        ),
        (
            ("これは非常に長い小説のタ"
             "イトルで画像幅を超えてし"
             "まう場合のテストです。（"
             "Ｂ６）"
            ),
            "すごく名前が長い作者名のテスト",
            CoverSizeDefaults.B6,
            "B6-long-r",
            "BLUE"
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
            "KINDLE-very-long",
            "gray"
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
            "KINDLE-very-long-r",
            "GRAY"
         ),
    ]

    # --- 引数解析 ---
    args = sys.argv[1:]

    # ------------------------------------------------------------
    # 引数なし → test_cases を実行
    # ------------------------------------------------------------
    if len(args) == 0:
        print("引数が無いため test_cases を実行します")

        for title, author, size, label, color_theme in test_cases:
            generator = CoverGenerator(size)
            cover = generator.generate(title, author, "cover.jpg", theme = color_theme)

            file_path = f"size-{label}-{cover['name']}"
            with open(file_path, "wb") as f:
                f.write(cover["data"])

            print(f"Saved: {file_path}")

    # ------------------------------------------------------------
    # 引数4つ → (title, author, output_filename, size_name)
    # ------------------------------------------------------------
    elif len(args) == 5:
        title, author, output_filename, size_name, color_theme = args

        try:
            size = resolve_size(size_name)
        except ValueError as e:
            print(e)
            print("使い方: python cover.py \"タイトル\" \"著者名\" \"出力ファイル名\" \"サイズ名\" \"色テーマ\"")
            sys.exit(1)

        generator = CoverGenerator(size)
        cover = generator.generate(title, author, "cover.jpg", theme = color_theme)

        with open(output_filename, "wb") as f:
            f.write(cover["data"])

        print(f"Saved: {output_filename}")

    # ------------------------------------------------------------
    # 引数の数が不正
    # ------------------------------------------------------------
    else:
        print("引数の数が正しくありません。")
        print("使い方: python cover.py \"タイトル\" \"著者名\" \"出力ファイル名\" \"サイズ名\" \"色テーマ\"")
        print("または: python -m nepub.cover \"タイトル\" \"著者名\" \"出力ファイル名\" \"サイズ名\" \"色テーマ\"")

