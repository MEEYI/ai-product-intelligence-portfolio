"""Local lookup tests: isolated SQLite, no application startup or network calls."""

import unittest
from contextlib import ExitStack
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.connection import Base, engine as application_engine, get_db
from backend.models.brand import Brand
from backend.models.brand_asset import BrandAsset
from backend.models.brand_source import BrandSource
from backend.models.product_reference import ProductReference
from backend.routers import brand, brand_intelligence


class BrandLookupTests(unittest.TestCase):
    endpoints = ("/brands/by-name", "/brand-intelligence/by-name/evidence")

    def setUp(self):
        self.guards = ExitStack()
        self.addCleanup(self.guards.close)
        for target in (
            "socket.create_connection",
            "httpx.HTTPTransport.handle_request",
            "httpx.AsyncHTTPTransport.handle_async_request",
        ):
            self.guards.enter_context(
                patch(target, side_effect=AssertionError("Network access forbidden in local tests"))
            )
        self.guards.enter_context(
            patch.object(
                application_engine,
                "connect",
                side_effect=AssertionError("Application database access forbidden in tests"),
            )
        )

        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.addCleanup(self.engine.dispose)
        Base.metadata.create_all(
            self.engine,
            tables=[Brand.__table__, BrandAsset.__table__, BrandSource.__table__, ProductReference.__table__],
        )
        self.session_factory = sessionmaker(bind=self.engine)
        self.db = self.session_factory()
        self.addCleanup(self.db.close)

        app = FastAPI()
        app.include_router(brand.router)
        app.include_router(brand_intelligence.router)

        def test_database():
            with self.session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = test_database
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def add_brand(self, name="Northstar", code="DEMO_BRD-000001", **fields):
        record = Brand(brand_name=name, brand_code=code, **fields)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def test_northstar_case_and_surrounding_whitespace(self):
        record = self.add_brand(
            website="https://www.northstar.example/", primary_market="US", notes="Test fixture"
        )
        for name in ("Northstar", "northstar", "NORTHSTAR", "  Northstar  ", "\u00a0Northstar\u00a0"):
            with self.subTest(name=name):
                response = self.client.get("/brands/by-name", params={"brand_name": name})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(
                    response.json(),
                    {
                        "id": record.id,
                        "brand_code": record.brand_code,
                        "brand_name": "Northstar",
                        "website": "https://www.northstar.example/",
                        "primary_market": "US",
                        "status": "active",
                        "notes": "Test fixture",
                    },
                )

    def test_legacy_stored_spaces_and_unicode_case(self):
        record = self.add_brand(name="  MÜNCHEN\u00a0")
        response = self.client.get("/brands/by-name", params={"brand_name": "münchen"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["id"], record.id)

    def test_missing_and_invalid_names_are_rejected_for_both_routes(self):
        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint, name="missing"):
                self.assertEqual(self.client.get(endpoint).status_code, 422)
            for name in ("", "   ", "\u00a0", "Northstar\n", "North\tstar", "North\x00star", "Northstar\u200b", "x" * 121):
                with self.subTest(endpoint=endpoint, name=repr(name)):
                    response = self.client.get(endpoint, params={"brand_name": name})
                    self.assertEqual(response.status_code, 422, response.text)

    def test_maximum_name_length_is_accepted(self):
        record = self.add_brand(name="x" * 120)
        response = self.client.get("/brands/by-name", params={"brand_name": "x" * 120})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["id"], record.id)

    def test_unknown_partial_and_sql_pattern_names_do_not_match(self):
        self.add_brand()
        for endpoint in self.endpoints:
            for name in ("Other Label", "Northg", "%", "_", "North%", "Northg_er", "' OR 1=1 --"):
                with self.subTest(endpoint=endpoint, name=name):
                    response = self.client.get(endpoint, params={"brand_name": name})
                    self.assertEqual(response.status_code, 404, response.text)
        self.assertEqual(self.db.query(Brand).count(), 1)

    def test_pattern_characters_are_literal_and_internal_spaces_are_preserved(self):
        literal = self.add_brand(name="100%_Brand")
        self.add_brand(name="Two  Words", code="DEMO_BRD-000002")
        response = self.client.get("/brands/by-name", params={"brand_name": "100%_brand"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["id"], literal.id)
        response = self.client.get("/brands/by-name", params={"brand_name": "Two Words"})
        self.assertEqual(response.status_code, 404)

    def test_duplicate_normalized_names_return_409_instead_of_arbitrary_brand(self):
        first = self.add_brand()
        second = self.add_brand(name="  NORTHSTAR ", code="DEMO_BRD-000002")
        for endpoint in self.endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint, params={"brand_name": "northstar"})
                self.assertEqual(response.status_code, 409, response.text)
                detail = response.json()["detail"]
                self.assertEqual(detail["reason"], "brand_name_ambiguous")
                self.assertEqual([item["id"] for item in detail["matches"]], [first.id, second.id])

    def test_empty_evidence_matches_existing_id_route_and_does_not_write(self):
        record = self.add_brand(status="inactive")
        response = self.client.get(
            "/brand-intelligence/by-name/evidence", params={"brand_name": " northstar "}
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload, self.client.get(f"/brand-intelligence/{record.id}/evidence").json())
        self.assertEqual(payload["summary"], {"asset_count": 0, "source_count": 0, "product_count": 0})
        for field in ("assets", "sources", "products"):
            self.assertEqual(payload[field], [])
        self.assertEqual(self.db.query(Brand).count(), 1)

    def test_evidence_keeps_existing_filters_and_excludes_other_brands(self):
        record = self.add_brand()
        other = self.add_brand(name="Other", code="DEMO_BRD-000002")
        self.db.add_all(
            [
                BrandAsset(id="allowed", brand_id=record.id, asset_type="logo", file_name="logo.png", file_url="uploads/logo.png"),
                BrandAsset(id="disabled", brand_id=record.id, asset_type="logo", file_name="disabled.png", file_url="uploads/disabled.png", use_for_analysis=False),
                BrandAsset(id="inactive", brand_id=record.id, asset_type="logo", file_name="inactive.png", file_url="uploads/inactive.png", status="inactive"),
                BrandAsset(id="other-asset", brand_id=other.id, asset_type="logo", file_name="other.png", file_url="uploads/other.png"),
                BrandSource(id="source", brand_id=record.id, source_type="website", source_name="Official", source_url="https://www.northstar.example/"),
                BrandSource(id="inactive-source", brand_id=record.id, source_type="website", source_name="Old", status="inactive"),
                BrandSource(id="other-source", brand_id=other.id, source_type="website", source_name="Other"),
                ProductReference(id="product", brand_id=record.id, source_id="source", product_name="Test cap"),
                ProductReference(id="inactive-product", brand_id=record.id, source_id="source", product_name="Old cap", status="inactive"),
                ProductReference(id="other-product", brand_id=other.id, source_id="other-source", product_name="Other cap"),
            ]
        )
        self.db.commit()
        response = self.client.get(
            "/brand-intelligence/by-name/evidence", params={"brand_name": "northstar"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload, self.client.get(f"/brand-intelligence/{record.id}/evidence").json())
        self.assertEqual(payload["summary"], {"asset_count": 1, "source_count": 1, "product_count": 1})
        self.assertEqual([item["id"] for item in payload["assets"]], ["allowed"])
        self.assertEqual([item["id"] for item in payload["sources"]], ["source"])
        self.assertEqual([item["id"] for item in payload["products"]], ["product"])

    def test_existing_id_route_still_returns_404_for_missing_brand(self):
        response = self.client.get("/brand-intelligence/missing-id/evidence")
        self.assertEqual(response.status_code, 404, response.text)


if __name__ == "__main__":
    unittest.main()
