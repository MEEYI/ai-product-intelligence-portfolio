"""Research contract tests: mocked OpenAI, no .env, network, or business database."""

import json
import os
import unittest
from contextlib import ExitStack
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch

import httpx
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    PermissionDeniedError,
    RateLimitError,
)

# product_analyzer loads .env at import time; these tests must never read it.
with patch("dotenv.load_dotenv", return_value=False):
    from backend.database.connection import engine as application_engine
    from backend.routers import brand_research as router_module
    from backend.services import brand_research as service


SOURCE_URL = "https://www.northstar.example/our-company.html"
SOURCE_TITLE = "Northstar 官方简介"
MARKER = "【来源】"
SUMMARY = "Northstar 是测试专用的虚构品牌。" + MARKER
FAKE_SECRET = "SYNTHETIC_SECRET_MUST_NEVER_APPEAR_IN_RESPONSE"


def citation(url=SOURCE_URL, title=SOURCE_TITLE, text=SUMMARY):
    start = text.index(MARKER)
    return NS(
        type="url_citation", url=url, title=title,
        start_index=start, end_index=start + len(MARKER),
    )


def search_response(*, status="completed", search_status="completed", annotations=None,
                    include_search=True, summary=SUMMARY):
    output = []
    if include_search:
        output.append(NS(type="web_search_call", status=search_status))
    output.append(NS(
        type="message",
        content=[NS(
            type="output_text", text=summary,
            annotations=[citation(text=summary)] if annotations is None else annotations,
        )],
    ))
    return NS(status=status, output=output, usage=NS(total_tokens=321))


class BrandResearchTests(unittest.TestCase):
    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        self.guards.enter_context(patch.dict(os.environ, {
            "OPENAI_API_KEY": "",
            "OPENAI_BRAND_RESEARCH_MODEL": "research-test-model",
            "OPENAI_MODEL": "fallback-test-model",
        }))
        for target in (
            "socket.create_connection",
            "httpx.HTTPTransport.handle_request",
            "httpx.AsyncHTTPTransport.handle_async_request",
        ):
            self.guards.enter_context(patch(
                target, side_effect=AssertionError("Network access forbidden in research tests"),
            ))
        self.database_guard = self.guards.enter_context(patch.object(
            application_engine, "connect",
            side_effect=AssertionError("Business database access forbidden in research tests"),
        ))
        service._cache.clear()
        self.addCleanup(service._cache.clear)

        self.upstream = MagicMock()
        self.upstream.with_options.return_value = self.upstream
        self.upstream.responses.create.return_value = search_response()
        self.get_client = self.guards.enter_context(patch.object(
            service, "get_openai_client", return_value=self.upstream,
        ))

        self.app = FastAPI()
        self.app.include_router(router_module.router)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def request(self, name="Northstar", **params):
        return self.client.get("/brand-research", params={"brand_name": name, **params})

    def test_success_has_clickable_sources_review_metadata_and_usage(self):
        response = self.request("  Northstar  ")
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["brand_name"], "Northstar")
        self.assertEqual(data["data_source"], "openai_web_search")
        self.assertEqual(data["sources"], [{"title": SOURCE_TITLE, "url": SOURCE_URL}])
        self.assertIn(f"[{SOURCE_TITLE}](<{SOURCE_URL}>)", data["summary"])
        self.assertNotIn(MARKER, data["summary"])
        self.assertEqual(data["total_tokens"], 321)
        self.assertEqual(data["web_search_calls"], 1)
        self.assertEqual(data["model"], "research-test-model")
        self.assertTrue(data["needs_review"])
        self.assertFalse(data["saved_to_database"])
        self.assertFalse(data["cache_hit"])
        self.assertEqual(data["cache_ttl_seconds"], 600)
        self.assertIn("retrieved_at", data)
        self.assertEqual(response.headers["cache-control"], "no-store")

        arguments = self.upstream.responses.create.call_args.kwargs
        self.assertEqual(json.loads(arguments["input"]), {"brand_name": "Northstar"})
        self.assertFalse(arguments["store"])
        self.assertEqual(arguments["tool_choice"], "required")
        self.assertEqual(arguments["tools"], [{"type": "web_search", "search_context_size": "low"}])
        self.upstream.with_options.assert_called_once_with(timeout=60.0, max_retries=0)

    def test_case_and_surrounding_whitespace_share_one_paid_call(self):
        first = self.request().json()
        for name in ("northstar", "NORTHSTAR", "  Northstar  ", "\u00a0nOrThStAr\u00a0"):
            with self.subTest(name=name):
                response = self.request(name)
                self.assertEqual(response.status_code, 200, response.text)
                data = response.json()
                self.assertTrue(data["cache_hit"])
                self.assertEqual(data["retrieved_at"], first["retrieved_at"])
                self.assertEqual(data["summary"], first["summary"])
        self.upstream.responses.create.assert_called_once()
        self.get_client.assert_called_once()

    def test_refresh_performs_a_new_call_and_replaces_cached_result(self):
        first = self.request().json()
        second_response = search_response()
        second_response.usage.total_tokens = 654
        self.upstream.responses.create.return_value = second_response
        refreshed = self.request("northstar", refresh="true")
        self.assertEqual(refreshed.status_code, 200, refreshed.text)
        self.assertFalse(refreshed.json()["cache_hit"])
        self.assertEqual(refreshed.json()["total_tokens"], 654)
        self.assertEqual(first["total_tokens"], 321)
        cached = self.request().json()
        self.assertTrue(cached["cache_hit"])
        self.assertEqual(cached["total_tokens"], 654)
        self.assertEqual(self.upstream.responses.create.call_count, 2)

    def test_expired_cache_performs_a_new_paid_call(self):
        with patch.object(service, "monotonic", return_value=100):
            self.assertEqual(self.request().status_code, 200)
        with patch.object(service, "monotonic", return_value=100 + service.CACHE_TTL_SECONDS - 1):
            self.assertTrue(self.request().json()["cache_hit"])
        with patch.object(service, "monotonic", return_value=100 + service.CACHE_TTL_SECONDS):
            response = self.request()
            self.assertEqual(response.status_code, 200, response.text)
            self.assertFalse(response.json()["cache_hit"])
        self.assertEqual(self.upstream.responses.create.call_count, 2)

    def test_model_change_does_not_reuse_a_different_models_cache(self):
        self.assertEqual(self.request().status_code, 200)
        with patch.dict(os.environ, {"OPENAI_BRAND_RESEARCH_MODEL": "second-test-model"}):
            data = self.request().json()
        self.assertEqual(data["model"], "second-test-model")
        self.assertFalse(data["cache_hit"])
        self.assertEqual(self.upstream.responses.create.call_count, 2)

    def test_cache_returns_copies_so_callers_cannot_change_later_results(self):
        first = service.research_brand("Northstar")
        first.sources.clear()
        first.summary = "changed by caller"
        cached = service.research_brand("northstar")
        self.assertTrue(cached.cache_hit)
        self.assertEqual(len(cached.sources), 1)
        self.assertNotEqual(cached.summary, first.summary)
        self.upstream.responses.create.assert_called_once()

    def test_blank_research_override_uses_explicit_base_model(self):
        with patch.dict(os.environ, {"OPENAI_BRAND_RESEARCH_MODEL": "  "}):
            response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["model"], "fallback-test-model")

    def test_missing_base_model_never_calls_upstream_even_with_override(self):
        for model in ("", "   "):
            with self.subTest(model=model), patch.dict(os.environ, {"OPENAI_MODEL": model}):
                response = self.request()
                self.assertEqual(response.status_code, 503, response.text)
                self.assertIn("OPENAI_MODEL", response.json()["detail"])
        self.get_client.assert_not_called()
        self.upstream.responses.create.assert_not_called()
        self.assertFalse(service._cache)

    def test_missing_invalid_and_control_character_names_never_call_upstream(self):
        response = self.client.get("/brand-research")
        self.assertEqual(response.status_code, 422)
        for name in ("", " ", "\u00a0", "Northstar\n", "North\tstar", "North\x00star",
                     "Northstar\u200b", "x" * 121):
            with self.subTest(name=repr(name)):
                response = self.request(name)
                self.assertEqual(response.status_code, 422, response.text)
        self.get_client.assert_not_called()
        self.upstream.responses.create.assert_not_called()
        self.assertFalse(service._cache)

    def test_missing_citations_or_search_or_finished_response_is_not_cached(self):
        cases = {
            "no citations": search_response(annotations=[]),
            "no web search": search_response(include_search=False),
            "unfinished web search": search_response(search_status="in_progress"),
            "unfinished response": search_response(status="incomplete"),
            "failed response": search_response(status="failed"),
            "empty summary": search_response(summary="", annotations=[]),
        }
        for name, upstream_response in cases.items():
            with self.subTest(name=name):
                self.upstream.responses.create.return_value = upstream_response
                response = self.request()
                self.assertEqual(response.status_code, 502, response.text)
                self.assertFalse(service._cache)
                self.assertNotIn("summary", response.json())

    def test_invalid_source_urls_and_citation_offsets_are_not_accepted_as_evidence(self):
        bad_citations = [
            citation(url="javascript:alert(1)"),
            citation(url="file:///C:/private.txt"),
            citation(url="https://user:password@example.com/private"),
            citation(url="https:///no-host"),
            citation(url="https://[broken/"),
            citation(url="https://www.northstar.example:999999/"),
            NS(type="url_citation", url=SOURCE_URL, title=SOURCE_TITLE,
               start_index=-1, end_index=2),
            NS(type="url_citation", url=SOURCE_URL, title=SOURCE_TITLE,
               start_index=0, end_index=len(SUMMARY) + 1),
        ]
        for annotation in bad_citations:
            with self.subTest(url=annotation.url, start=annotation.start_index):
                self.upstream.responses.create.return_value = search_response(annotations=[annotation])
                response = self.request()
                self.assertEqual(response.status_code, 502, response.text)
                self.assertFalse(service._cache)

    def test_multiple_sources_on_same_citation_span_are_clickable_and_unique(self):
        second_url = "https://www.example.org/brands/northstar"
        second_title = "Example Group [品牌]"
        self.upstream.responses.create.return_value = search_response(annotations=[
            citation(), citation(url=second_url, title=second_title),
        ])
        response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(len(data["sources"]), 2)
        self.assertIn(f"[{SOURCE_TITLE}](<{SOURCE_URL}>)", data["summary"])
        self.assertIn(f"[Example Group \\[品牌\\]](<{second_url}>)", data["summary"])

    def test_missing_api_key_returns_safe_configuration_error(self):
        self.get_client.side_effect = service.ProductAnalyzerConfigurationError(FAKE_SECRET)
        response = self.request()
        self.assertEqual(response.status_code, 503, response.text)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])
        self.assertNotIn(FAKE_SECRET, response.text)
        self.upstream.responses.create.assert_not_called()
        self.assertFalse(service._cache)

    def test_upstream_errors_have_safe_statuses_without_secret_or_raw_body(self):
        request = httpx.Request("POST", "https://api.openai.com/v1/responses")
        cases = [
            (AuthenticationError, 401, 503),
            (PermissionDeniedError, 403, 503),
            (RateLimitError, 429, 429),
            (InternalServerError, 500, 502),
        ]
        errors = [
            (error_class(
                FAKE_SECRET,
                response=httpx.Response(upstream_status, request=request),
                body={"error": {"message": FAKE_SECRET}},
            ), expected_status)
            for error_class, upstream_status, expected_status in cases
        ]
        errors.extend([
            (APITimeoutError(request=request), 504),
            (APIConnectionError(message=FAKE_SECRET, request=request), 502),
        ])
        for error, expected_status in errors:
            with self.subTest(error=type(error).__name__):
                self.upstream.responses.create.side_effect = error
                response = self.request()
                self.assertEqual(response.status_code, expected_status, response.text)
                self.assertEqual(set(response.json()), {"detail"})
                self.assertNotIn(FAKE_SECRET, response.text)
                self.assertNotIn("api.openai.com", response.text)
                self.assertFalse(service._cache)

    def test_get_has_no_database_dependency_or_writes(self):
        route = next(route for route in router_module.router.routes if isinstance(route, APIRoute))
        self.assertEqual(route.methods, {"GET"})
        self.assertEqual(route.dependant.dependencies, [])
        with patch("sqlalchemy.orm.Session.add", side_effect=AssertionError("No database writes")), \
             patch("sqlalchemy.orm.Session.commit", side_effect=AssertionError("No database writes")), \
             patch("sqlalchemy.orm.Session.execute", side_effect=AssertionError("No database access")):
            response = self.request()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertFalse(response.json()["saved_to_database"])
        self.database_guard.assert_not_called()


if __name__ == "__main__":
    unittest.main()
