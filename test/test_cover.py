# This code was generated using Microsoft Copilot.
#
import os
import tempfile
from io import BytesIO

import pytest
from PIL import Image as PILImage

from nepub.cover import CoverGenerator, CoverSizeDefaults


# ------------------------------------------------------------
# Helper: JPEG を生成する
# ------------------------------------------------------------
def create_dummy_jpeg(path: str, size=(200, 200), color=(255, 0, 0)):
    img = PILImage.new("RGB", size, color)
    img.save(path, "JPEG")


# ------------------------------------------------------------
# Test: 既存 JPEG を読み込む
# ------------------------------------------------------------
def test_load_existing_cover_jpeg():
    with tempfile.TemporaryDirectory() as tmpdir:
        jpeg_path = os.path.join(tmpdir, "cover.jpg")
        create_dummy_jpeg(jpeg_path)

        generator = CoverGenerator(CoverSizeDefaults.A6)
        result = generator.generate("タイトル", "作者", jpeg_path)

        assert isinstance(result, dict)
        assert result["type"] == "image/jpg"
        assert result["name"] == "cover.jpg"
        assert isinstance(result["data"], bytes)

        # JPEG として開けるか
        img = PILImage.open(BytesIO(result["data"]))
        assert img.format == "JPEG"


# ------------------------------------------------------------
# Test: JPEG が存在しない場合は生成される
# ------------------------------------------------------------
def test_generate_cover_when_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        jpeg_path = os.path.join(tmpdir, "not_exist.jpg")

        generator = CoverGenerator(CoverSizeDefaults.A6)
        result = generator.generate("テストタイトル", "テスト作者", jpeg_path)

        assert isinstance(result["data"], bytes)

        img = PILImage.open(BytesIO(result["data"]))
        assert img.format == "JPEG"
        assert img.size == (CoverSizeDefaults.A6.width, CoverSizeDefaults.A6.height)


# ------------------------------------------------------------
# Test: 長いタイトルが truncate されるか
# ------------------------------------------------------------
def test_title_truncation():
    long_title = "あ" * 200  # 全角200文字 → truncate されるはず
    generator = CoverGenerator(CoverSizeDefaults.A6)

    # 内部メソッドを直接テスト（ユニットテストとして有効）
    truncated = generator._truncate_text(long_title)

    assert len(truncated) < len(long_title)
    assert truncated.endswith("…")


# ------------------------------------------------------------
# Test: 返却される dict の構造確認
# ------------------------------------------------------------
def test_return_structure():
    generator = CoverGenerator(CoverSizeDefaults.A6)
    result = generator.generate("タイトル", "作者", "nonexistent.jpg")

    assert set(result.keys()) == {"type", "id", "name", "data"}
    assert result["id"] == "cimage"
    assert result["name"] == "cover.jpg"
    assert isinstance(result["data"], bytes)
