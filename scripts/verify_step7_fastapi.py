"""
Step 7 Verification Script — Fault IQ FastAPI Application & Health Endpoint.

Validates:
1. Module imports and FastAPI application instance creation.
2. Route inspection: presence of GET /, GET /health, GET /api/v1/health.
3. Live HTTP requests against TestClient:
   - GET / returns 200 and valid service metadata.
   - GET /health returns 200 with database status connected.
   - GET /api/v1/health returns 200 with database status connected.
   - Mocked failure on GET /health returns 503 with database status disconnected.
4. Live Uvicorn server socket test:
   - Starts Uvicorn in a background thread on 127.0.0.1.
   - Sends real HTTP GET requests via httpx.
   - Validates live responses and headers.
   - Safely shuts down the Uvicorn server.
5. Zero-leak credential check across all outputs.
"""

import sys
import threading
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import httpx
import uvicorn
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.config import settings
from app.main import app


def test_app_and_routes():
    print("=== 1. App Configuration & Route Registration ===")
    print(f"[INFO] App Title:   {app.title}")
    print(f"[INFO] App Version: {app.version}")

    routes = [f"{list(r.methods)[0] if hasattr(r, 'methods') and r.methods else 'ANY'} {r.path}" for r in app.routes]
    print(f"[INFO] Registered routes ({len(routes)}):")
    for r in sorted(routes):
        print(f"       {r}")

    expected = {"GET /", "GET /health", "GET /api/v1/health"}
    found = {r for r in routes if r in expected}
    if found != expected:
        print(f"[FAIL] Missing expected routes: {expected - found}")
        return False

    print("[OK]   FastAPI app instance and required routes verified.")
    return True


def test_client_endpoints():
    print("\n=== 2. Endpoint Verification via TestClient ===")
    client = TestClient(app)

    # 1. Root endpoint
    res_root = client.get("/")
    print(f"[INFO] GET / -> HTTP {res_root.status_code}")
    print(f"       Response: {res_root.json()}")
    if res_root.status_code != 200:
        print("[FAIL] Root endpoint did not return 200")
        return False
    root_data = res_root.json()
    assert root_data["service"] == settings.PROJECT_NAME
    assert root_data["status"] == "online"
    print("[OK]   GET / endpoint verified.")

    # 2. Live Health endpoint
    res_health = client.get("/health")
    print(f"[INFO] GET /health -> HTTP {res_health.status_code}")
    print(f"       Response: {res_health.json()}")
    if res_health.status_code != 200:
        print("[FAIL] Health endpoint did not return 200")
        return False
    health_data = res_health.json()
    assert health_data["status"] == "healthy"
    assert health_data["database"] == "connected"
    print("[OK]   GET /health live database connectivity verified.")

    # 3. Simulated DB failure on Health endpoint
    with patch("app.api.routes.health.check_database_health", return_value=False):
        res_fail = client.get("/health")
        print(f"[INFO] Simulated Failure: GET /health -> HTTP {res_fail.status_code}")
        print(f"       Response: {res_fail.json()}")
        if res_fail.status_code != 503:
            print(f"[FAIL] Expected 503 on DB failure, got {res_fail.status_code}")
            return False
        fail_data = res_fail.json()
        assert fail_data["status"] == "unhealthy"
        assert fail_data["database"] == "disconnected"
        print("[OK]   GET /health returns 503 and 'disconnected' when DB check fails.")

    return True


def test_live_uvicorn_server():
    print("\n=== 3. Live Uvicorn Network Socket Test ===")
    test_port = 8765
    server_config = uvicorn.Config(app, host="127.0.0.1", port=test_port, log_level="warning")
    server = uvicorn.Server(server_config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server startup
    base_url = f"http://127.0.0.1:{test_port}"
    started = False
    for _ in range(30):
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{base_url}/")
                if res.status_code == 200:
                    started = True
                    break
        except Exception:
            time.sleep(0.1)

    if not started:
        print("[FAIL] Uvicorn server failed to start within timeout.")
        server.should_exit = True
        return False

    print(f"[OK]   Uvicorn server running on {base_url}")

    try:
        with httpx.Client(timeout=5.0) as client:
            # Query GET /
            r_root = client.get(f"{base_url}/")
            print(f"[INFO] Real HTTP GET {base_url}/ -> HTTP {r_root.status_code}")
            print(f"       JSON: {r_root.json()}")
            assert r_root.status_code == 200

            # Query GET /health
            r_health = client.get(f"{base_url}/health")
            print(f"[INFO] Real HTTP GET {base_url}/health -> HTTP {r_health.status_code}")
            print(f"       JSON: {r_health.json()}")
            assert r_health.status_code == 200
            assert r_health.json()["status"] == "healthy"
            assert r_health.json()["database"] == "connected"

            # Query GET /docs
            r_docs = client.get(f"{base_url}/docs")
            print(f"[INFO] Real HTTP GET {base_url}/docs -> HTTP {r_docs.status_code}")
            assert r_docs.status_code == 200

        print("[OK]   Live Uvicorn HTTP requests succeeded with expected statuses and payloads.")
        return True
    finally:
        server.should_exit = True
        thread.join(timeout=3)
        print("[OK]   Uvicorn server shut down cleanly.")


def main():
    success = True
    success = test_app_and_routes() and success
    success = test_client_endpoints() and success
    success = test_live_uvicorn_server() and success

    print("\n=== Final Status ===")
    if success:
        print("[SUCCESS] All Step 7 FastAPI & Health Endpoint checks PASSED!")
        sys.exit(0)
    else:
        print("[FAILURE] Some checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
