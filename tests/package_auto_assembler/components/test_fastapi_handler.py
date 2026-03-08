from fastapi import FastAPI

from python_modules.components.paa_deps.fastapi_handler import FastApiHandler


def test_fastapi_handler_prepare_routes_copies_file(tmp_path):
    src_routes = tmp_path / "my_routes.py"
    src_routes.write_text("from fastapi import APIRouter\nrouter = APIRouter()\n", encoding="utf-8")
    setup_dir = tmp_path / "setup"
    setup_dir.mkdir()

    handler = FastApiHandler()
    assert handler.prepare_routes(str(src_routes), str(setup_dir)) is True

    copied = setup_dir / "routes.py"
    assert copied.exists()
    assert "APIRouter" in copied.read_text(encoding="utf-8")


def test_fastapi_handler_include_docs_mounts_expected_paths(tmp_path):
    docs_one = tmp_path / "docs_one"
    docs_two = tmp_path / "docs_two"
    docs_one.mkdir()
    docs_two.mkdir()

    app = FastAPI()
    handler = FastApiHandler(docs_prefix="/docs")
    app = handler._include_docs(app=app, docs_paths=[str(docs_one), str(docs_two)])

    mount_paths = [route.path for route in app.routes if getattr(route, "path", "").startswith("/docs")]
    assert "/docs" in mount_paths
    assert "/docs1" in mount_paths
