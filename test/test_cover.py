# This code was generated using Microsoft Copilot.
#
from unittest import TestCase
import os
import tempfile
from io import BytesIO

from PIL import Image as PILImage
from nepub.cover import CoverGenerator, CoverSizeDefaults


class TestCover(TestCase):

    # --------------------------------------------------------
    # Helper: JPEG を生成する（クラス内ローカル関数）
    # --------------------------------------------------------
    def _create_dummy_jpeg(self, path: str, size=(200, 200), color=(255, 0, 0)):
        img = PILImage.new("RGB", size, color)
        img.save(path, "JPEG")

    # --------------------------------------------------------
    # Test: 既存 JPEG を読み込む
    # --------------------------------------------------------
    def test_load_existing_cover_jpeg(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            jpeg_path = os.path.join(tmpdir, "cover.jpg")
            self._create_dummy_jpeg(jpeg_path)

            generator = CoverGenerator(CoverSizeDefaults.A6)
            result = generator.generate("タイトル", "作者", jpeg_path)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["type"], "image/jpg")
            self.assertEqual(result["name"], "cover.jpg")
            self.assertIsInstance(result["data"], bytes)

            # JPEG として開けるか
            img = PILImage.open(BytesIO(result["data"]))
            self.assertEqual(img.format, "JPEG")

    # --------------------------------------------------------
    # Test: JPEG が存在しない場合は生成される
    # --------------------------------------------------------
    def test_generate_cover_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            jpeg_path = os.path.join(tmpdir, "not_exist.jpg")

            generator = CoverGenerator(CoverSizeDefaults.A6)
            result = generator.generate("テストタイトル", "テスト作者", jpeg_path)

            self.assertIsInstance(result["data"], bytes)

            img = PILImage.open(BytesIO(result["data"]))
            self.assertEqual(img.format, "JPEG")
            self.assertEqual(
                img.size,
                (CoverSizeDefaults.A6.width, CoverSizeDefaults.A6.height)
            )

    # --------------------------------------------------------
    # Test: 長いタイトルが truncate されるか
    # --------------------------------------------------------
    def test_title_truncation_full(self):
        long_title = "あ" * 200  # 全角200文字 → truncate されるはず
        generator = CoverGenerator(CoverSizeDefaults.A6)

        # 内部メソッドを直接テスト（ユニットテストとして有効）
        truncated = generator._truncate_text_full(long_title)

        self.assertLess(len(truncated), len(long_title))
        self.assertTrue(truncated.endswith("…"))

    # --------------------------------------------------------
    # Test: 返却される dict の構造確認
    # --------------------------------------------------------
    def test_return_structure(self):
        generator = CoverGenerator(CoverSizeDefaults.A6)
        result = generator.generate("タイトル", "作者", "nonexistent.jpg")

        self.assertEqual(set(result.keys()), {"type", "id", "name", "data"})
        self.assertEqual(result["id"], "cimage")
        self.assertEqual(result["name"], "cover.jpg")
        self.assertIsInstance(result["data"], bytes)
