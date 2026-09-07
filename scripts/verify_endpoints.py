"""Verify all API endpoints against the live application using TestClient"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

endpoints = [
    ("GET", "/health"),
    ("GET", "/api/v1/locations?limit=3"),
    ("GET", "/api/v1/weather?limit=2"),
    ("GET", "/api/v1/rainfall?limit=2"),
    ("GET", "/api/v1/data-sources"),
    ("GET", "/api/v1/ingestion/status"),
    ("GET", "/api/v1/routes?limit=2"),
    ("POST", "/api/v1/routes", {
        "origin": {"name": "Guwahati", "latitude": 26.1445, "longitude": 91.7362},
        "destination": {"name": "Shillong", "latitude": 25.5788, "longitude": 91.8933},
        "alternatives": True
    }),
]

print("Verifying NER-GRID FastAPI Endpoints...")
for item in endpoints:
    method = item[0]
    path = item[1]
    payload = item[2] if len(item) > 2 else None

    if method == "GET":
        resp = client.get(path)
    else:
        resp = client.post(path, json=payload)

    status = resp.status_code
    status_tag = "OK" if status in (200, 201) else "FAIL"
    print(f"[{status_tag}] {method} {path} -> HTTP {status}")
    if status in (200, 201):
        data = resp.json()
        if isinstance(data, list):
            print(f"     Items returned: {len(data)}")
        elif isinstance(data, dict):
            preview_keys = list(data.keys())[:5]
            print(f"     Keys: {preview_keys}")
    else:
        print(f"     Error: {resp.text}")

print("\nEndpoint verification complete!")
