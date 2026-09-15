"""Exercise real API routes against synthetic data and mocked AI, entirely offline."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run_demo():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    with ExitStack() as guards:
        guards.enter_context(patch("dotenv.load_dotenv", return_value=False))
        for target in ("socket.create_connection", "httpx.HTTPTransport.handle_request",
                       "httpx.AsyncHTTPTransport.handle_async_request"):
            guards.enter_context(patch(target, side_effect=AssertionError("Demo must stay offline")))
        guards.enter_context(patch.dict("os.environ", {
            "OPENAI_API_KEY": "", "OPENAI_MODEL": "offline-demo-model",
            "OPENAI_BRAND_RESEARCH_MODEL": "offline-demo-model",
        }))
        from backend.database.connection import Base, engine as application_engine, get_db
        from backend.models.brand import Brand
        from backend.models.brand_asset import BrandAsset
        from backend.models.brand_source import BrandSource
        from backend.models.product_reference import ProductReference
        from backend.routers import brand, brand_source, product_reference, brand_intelligence, brand_research
        from backend.services import brand_research as research

        guards.enter_context(patch.object(application_engine, "connect",
            side_effect=AssertionError("Demo must not open the on-disk database")))
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        guards.callback(engine.dispose)
        Base.metadata.create_all(engine, tables=[
            Brand.__table__, BrandAsset.__table__, BrandSource.__table__, ProductReference.__table__,
        ])
        sessions = sessionmaker(bind=engine)
        app = FastAPI(title="Offline synthetic demonstration")
        for module in (brand, brand_source, product_reference, brand_intelligence, brand_research):
            app.include_router(module.router)

        def demo_db():
            with sessions() as session:
                yield session
        app.dependency_overrides[get_db] = demo_db

        data = json.loads((ROOT / "examples/demo_data.json").read_text(encoding="utf-8"))
        summary = "SYNTHETIC DEMO: Northstar is a fictional label. [source]"
        response = NS(status="completed", usage=NS(total_tokens=0), output=[
            NS(type="web_search_call", status="completed"),
            NS(type="message", content=[NS(type="output_text", text=summary, annotations=[NS(
                type="url_citation", url=data["source"]["source_url"], title="Synthetic fixture",
                start_index=summary.index("[source]"), end_index=len(summary),
            )])]),
        ])
        fake_client = MagicMock()
        fake_client.with_options.return_value.responses.create.return_value = response
        guards.enter_context(patch.object(research, "get_openai_client", return_value=fake_client))
        research._cache.clear()
        guards.callback(research._cache.clear)

        with TestClient(app) as client:
            def request(method, path, **kwargs):
                result = client.request(method, path, **kwargs)
                if result.status_code != 200:
                    raise RuntimeError(f"Demo failed: {method} {path} returned {result.status_code}")
                return result.json()

            created_brand = request("POST", "/brands", json=data["brand"])
            source = request("POST", "/brand-sources", json={**data["source"], "brand_id": created_brand["id"]})
            request("POST", "/product-references", json={
                **data["product"], "brand_id": created_brand["id"], "source_id": source["id"],
            })
            lookup = request("GET", "/brands/by-name", params={"brand_name": "  NORTHSTAR  "})
            evidence = request("GET", "/brand-intelligence/by-name/evidence", params={"brand_name": "Northstar"})
            preview = request("GET", "/brand-research", params={"brand_name": "Northstar"})
            cached = request("GET", "/brand-research", params={"brand_name": "northstar"})
            after = request("GET", "/brand-intelligence/by-name/evidence", params={"brand_name": "Northstar"})
            assert lookup["id"] == created_brand["id"]
            assert evidence["summary"] == {"asset_count": 0, "source_count": 1, "product_count": 1}
            assert preview["needs_review"] and not preview["saved_to_database"]
            assert cached["cache_hit"] and after == evidence
            fake_client.with_options.return_value.responses.create.assert_called_once()

        return {
            "mode": "offline_synthetic_demo",
            "brand": lookup["brand_name"],
            "evidence": evidence["summary"],
            "research": {
                "summary": preview["summary"],
                "needs_review": preview["needs_review"],
                "saved_to_database": preview["saved_to_database"],
                "second_request_cache_hit": cached["cache_hit"],
                "provider": "mock; no AI or web-search request was sent",
            },
            "storage": "temporary in-memory database, discarded on exit",
        }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2, ensure_ascii=True))
