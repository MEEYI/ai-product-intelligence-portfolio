"""Bounded upload reads, matching image signatures, and project-local storage."""

import base64
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from backend.database.connection import engine as application_engine
from backend.routers import product_reference as router_module


# Small signature fixtures. The upload contract checks signatures, not complete
# image decoding; applications needing decoder validation should add it separately.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a/yoAAAAASUVORK5CYII="
)
JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
WEBP = b"RIFF\x04\x00\x00\x00WEBP"


class ProductUploadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        for target in (
            "socket.create_connection",
            "httpx.HTTPTransport.handle_request",
            "httpx.AsyncHTTPTransport.handle_async_request",
        ):
            self.guards.enter_context(patch(
                target, side_effect=AssertionError("Network forbidden in upload tests"),
            ))
        self.guards.enter_context(patch.object(
            application_engine, "connect",
            side_effect=AssertionError("Application database forbidden in upload tests"),
        ))
        self.root = Path(self.guards.enter_context(TemporaryDirectory())).resolve()
        self.guards.enter_context(patch.object(router_module, "PROJECT_ROOT", self.root))
        self.reference = SimpleNamespace(image_url=None)
        self.db = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = self.reference

    def upload(self, content=PNG, filename="fixture.png", content_type="image/png"):
        return SimpleNamespace(filename=filename, content_type=content_type, read=AsyncMock(return_value=content))

    async def submit(self, upload):
        return await router_module.upload_product_reference_image("synthetic-reference", upload, self.db)

    async def assert_rejected(self, upload, status):
        with self.assertRaises(HTTPException) as raised:
            await self.submit(upload)
        self.assertEqual(raised.exception.status_code, status)
        self.assertNotIn(str(self.root), raised.exception.detail)
        self.assertIsNone(self.reference.image_url)
        self.db.commit.assert_not_called()
        return raised.exception

    async def test_supported_signatures_use_project_root_and_portable_paths(self):
        cases = (
            (PNG, "fixture.png", "image/png"),
            (JPEG, "fixture.jpg", "image/jpeg"),
            (JPEG, "fixture.JPEG", "image/jpeg"),
            (WEBP, "fixture.webp", "image/webp"),
        )
        for content, filename, mime in cases:
            with self.subTest(filename=filename):
                upload = self.upload(content, filename, mime)
                result = await self.submit(upload)
                self.assertIs(result, self.reference)
                relative = Path(result.image_url)
                self.assertFalse(relative.is_absolute())
                self.assertEqual(relative.parent.as_posix(), "uploads/product_references")
                self.assertNotIn("\\", result.image_url)
                self.assertEqual((self.root / relative).read_bytes(), content)
                upload.read.assert_awaited_once_with(router_module.MAX_PRODUCT_IMAGE_SIZE + 1)

    async def test_file_signature_extension_and_mime_must_all_agree(self):
        cases = (
            (b"plain text disguised as a picture", "fixture.png", "image/png"),
            (JPEG, "fixture.png", "image/png"),
            (PNG, "fixture.png", "image/jpeg"),
            (WEBP, "fixture.jpg", "image/jpeg"),
            (b"RIFF\x04\x00\x00\x00WAVE", "fixture.webp", "image/webp"),
        )
        for content, filename, mime in cases:
            with self.subTest(filename=filename, mime=mime, signature=content[:12]):
                await self.assert_rejected(self.upload(content, filename, mime), 400)
        self.assertFalse((self.root / "uploads").exists())

    async def test_empty_image_is_rejected_without_creating_files(self):
        error = await self.assert_rejected(self.upload(b""), 400)
        self.assertEqual(error.detail, "Uploaded image is empty")
        self.assertFalse((self.root / "uploads").exists())

    async def test_oversized_image_reads_only_limit_plus_one(self):
        upload = self.upload(PNG + b"x" * router_module.MAX_PRODUCT_IMAGE_SIZE)
        await self.assert_rejected(upload, 413)
        upload.read.assert_awaited_once_with(router_module.MAX_PRODUCT_IMAGE_SIZE + 1)
        self.assertFalse((self.root / "uploads").exists())

    async def test_exact_size_limit_is_accepted(self):
        # A small test limit exercises the boundary without allocating 20 MB.
        with patch.object(router_module, "MAX_PRODUCT_IMAGE_SIZE", len(PNG)):
            upload = self.upload(PNG)
            await self.submit(upload)
            upload.read.assert_awaited_once_with(len(PNG) + 1)

    async def test_unsupported_extension_or_mime_is_rejected_before_read(self):
        for filename, mime in (("fixture.txt", "image/png"), ("fixture.png", "text/plain")):
            with self.subTest(filename=filename, mime=mime):
                upload = self.upload(PNG, filename, mime)
                await self.assert_rejected(upload, 400)
                upload.read.assert_not_awaited()

    async def test_redirected_upload_directory_is_rejected_before_writing(self):
        upload_directory = self.root / "uploads" / "product_references"
        original_resolve = Path.resolve

        def resolve(path, *args, **kwargs):
            if path == upload_directory:
                return self.root / "outside-upload-boundary"
            return original_resolve(path, *args, **kwargs)

        with patch.object(Path, "resolve", resolve):
            error = await self.assert_rejected(self.upload(), 500)
        self.assertEqual(error.detail, "Product upload directory is unavailable")
        self.assertFalse((self.root / "uploads").exists())

    async def test_directory_symlink_escape_does_not_write_to_target(self):
        outside = self.root / "outside-upload-boundary"
        outside.mkdir()
        (self.root / "uploads").mkdir()
        link = self.root / "uploads" / "product_references"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Directory symlink creation is unavailable on this platform")
        await self.assert_rejected(self.upload(), 500)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
