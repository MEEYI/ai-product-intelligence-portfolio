"""Privacy boundaries using temporary files and mocked AI; no real network or data."""

import base64
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from openai import APIConnectionError

with patch("dotenv.load_dotenv", return_value=False):
    from backend.database.connection import engine as application_engine, get_db
    from backend.routers import product_analysis as router_module
    from backend.services import product_analyzer as service


class ProductPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        self.guards.enter_context(patch.dict(os.environ, {
            "OPENAI_API_KEY": "",
            "OPENAI_MODEL": "explicit-test-model",
        }))
        for target in (
            "socket.create_connection",
            "httpx.HTTPTransport.handle_request",
            "httpx.AsyncHTTPTransport.handle_async_request",
        ):
            self.guards.enter_context(patch(
                target, side_effect=AssertionError("Network forbidden in privacy tests"),
            ))
        self.guards.enter_context(patch.object(
            application_engine, "connect",
            side_effect=AssertionError("Application database forbidden in privacy tests"),
        ))
        self.root = Path(self.guards.enter_context(TemporaryDirectory())).resolve()
        self.uploads = self.root / "uploads" / "product_references"
        self.uploads.mkdir(parents=True)
        self.guards.enter_context(patch.object(service, "PROJECT_ROOT", self.root))
        self.upstream = MagicMock()
        self.upstream.responses.create.return_value = SimpleNamespace(output_text='{"product_type":"cap"}')
        self.get_client = self.guards.enter_context(patch.object(
            service, "get_openai_client", return_value=self.upstream,
        ))

    def test_relative_and_absolute_uploaded_image_paths_are_supported(self):
        image = self.uploads / "fixture.png"
        content = b"\x89PNG\r\n\x1a\nsynthetic-test-image"
        image.write_bytes(content)
        expected = "data:image/png;base64," + base64.b64encode(content).decode("ascii")
        for path in (str(image), "uploads/product_references/fixture.png"):
            with self.subTest(path=path):
                self.assertEqual(service.local_image_to_data_url(path), expected)

    def test_absolute_and_traversal_paths_outside_uploads_are_rejected_before_read(self):
        outside = self.root / "private.png"
        outside.write_bytes(b"private-image-must-not-leave-disk")
        sibling = self.root / "uploads" / "product_references-other"
        sibling.mkdir()
        sibling_image = sibling / "private.png"
        sibling_image.write_bytes(b"private")
        paths = (
            str(outside),
            "uploads/product_references/../../private.png",
            str(sibling_image),
        )
        with patch.object(Path, "read_bytes", side_effect=AssertionError("Must not read private files")):
            for path in paths:
                with self.subTest(path=path), self.assertRaises(ValueError) as raised:
                    service.analyze_product("Demo cap", None, path)
                self.assertNotIn(str(self.root), str(raised.exception))
        self.upstream.responses.create.assert_not_called()

    def test_missing_upload_does_not_expose_filename_or_local_path(self):
        private_name = "confidential-missing-image.png"
        with self.assertRaises(FileNotFoundError) as raised:
            service.local_image_to_data_url(str(self.uploads / private_name))
        self.assertEqual(str(raised.exception), "Product image is unavailable.")
        self.assertNotIn(private_name, str(raised.exception))
        self.assertNotIn(str(self.root), str(raised.exception))

    def test_symlink_to_file_outside_uploads_is_rejected(self):
        outside = self.root / "private.png"
        outside.write_bytes(b"private")
        link = self.uploads / "linked.png"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("File symlink creation is unavailable on this platform")
        with self.assertRaises(ValueError):
            service.local_image_to_data_url(str(link))

    def test_resolved_path_escape_is_rejected_even_when_input_looks_internal(self):
        # Exercise the post-resolution boundary even where symlink creation is restricted.
        candidate = self.uploads / "linked.png"
        original_resolve = Path.resolve

        def resolve(path, *args, **kwargs):
            if path == candidate:
                return self.root / "private.png"
            return original_resolve(path, *args, **kwargs)

        with patch.object(Path, "resolve", resolve), self.assertRaises(ValueError):
            service.local_image_to_data_url(str(candidate))

    def test_upload_directory_redirect_is_rejected(self):
        original_resolve = Path.resolve

        def resolve(path, *args, **kwargs):
            if path == self.uploads:
                return self.root / "elsewhere"
            return original_resolve(path, *args, **kwargs)

        with patch.object(Path, "resolve", resolve), self.assertRaises(ValueError):
            service.local_image_to_data_url(str(self.uploads / "fixture.png"))

    def test_missing_or_blank_model_never_initializes_client(self):
        for model in ("", "  "):
            with self.subTest(model=model), patch.dict(os.environ, {"OPENAI_MODEL": model}):
                with self.assertRaises(service.ProductAnalyzerConfigurationError) as raised:
                    service.analyze_product("Demo cap", None, None)
                self.assertIn("OPENAI_MODEL", str(raised.exception))
        self.get_client.assert_not_called()
        self.upstream.responses.create.assert_not_called()

    def test_explicit_model_and_no_storage_are_used_for_product_analysis(self):
        with patch.dict(os.environ, {"OPENAI_MODEL": "  selected-model  "}):
            result = service.analyze_product("Demo cap", "cap", None)
        self.assertEqual(result, {"product_type": "cap"})
        arguments = self.upstream.responses.create.call_args.kwargs
        self.assertEqual(arguments["model"], "selected-model")
        self.assertIs(arguments["store"], False)

    def test_remote_image_is_forwarded_without_local_file_access(self):
        remote = "https://images.example/demo.png"
        with patch.object(service, "local_image_to_data_url", side_effect=AssertionError("No local read")):
            service.analyze_product("Demo cap", None, remote)
        arguments = self.upstream.responses.create.call_args.kwargs
        self.assertEqual(arguments["input"][0]["content"][1], {"type": "input_image", "image_url": remote})

    def test_api_hides_upstream_sensitive_errors_and_configuration_details(self):
        secret = "synthetic-private-upstream-value"
        request = httpx.Request("POST", "https://api.openai.com/v1/responses")
        errors = (
            (APIConnectionError(message=secret, request=request), 500),
            (FileNotFoundError(str(self.root / "private.png")), 500),
            (service.ProductAnalyzerConfigurationError(secret), 503),
        )
        app = FastAPI()
        app.include_router(router_module.router)
        db = MagicMock()
        product = SimpleNamespace(product_name="Demo cap", product_type="cap", image_url=None)

        def database():
            yield db

        app.dependency_overrides[get_db] = database
        with TestClient(app) as client:
            for error, status in errors:
                with self.subTest(error=type(error).__name__):
                    db.query.return_value.filter.return_value.first.side_effect = [product, None]
                    with patch.object(router_module, "analyze_product", side_effect=error):
                        response = client.post("/product-analyses/product/synthetic-product/analyze")
                    self.assertEqual(response.status_code, status, response.text)
                    self.assertEqual(set(response.json()), {"detail"})
                    self.assertNotIn(secret, response.text)
                    self.assertNotIn("private.png", response.text)
                    self.assertNotIn("api.openai.com", response.text)
                    self.assertNotIn(str(self.root), response.text)
        db.add.assert_not_called()
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
