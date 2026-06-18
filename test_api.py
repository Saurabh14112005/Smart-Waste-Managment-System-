import os

import requests


def _headers():
    tok = os.environ.get("DEVICE_INGEST_SECRET", "").strip()
    if not tok:
        return {}
    return {"X-Device-Token": tok}


def test_api():
    base_url = os.environ.get("CLEANCITY_API_URL", "http://localhost:8000").rstrip("/")

    try:
        r = requests.get(f"{base_url}/", timeout=5)
        print("Root:", r.status_code, r.json())
    except Exception as e:
        print("Root failed:", e)

    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        print("Health:", r.status_code, r.json())
    except Exception as e:
        print("Health failed:", e)

    try:
        r = requests.post(
            f"{base_url}/bins",
            json={
                "id": 1,
                "location": "Integration test bin",
                "lat": 23.2599,
                "lon": 77.4126,
                "zone": "LAB",
                "waste_type": "Mixed",
                "fill_level": 12,
                "gas_level": 15.0,
                "temp": 28.0,
                "battery": 100,
                "moisture": 0,
                "status": "NORMAL",
                "tenant_id": "default",
            },
            headers=_headers(),
            timeout=5,
        )
        print("POST /bins:", r.status_code, r.text)
    except Exception as e:
        print("POST /bins failed:", e)

    try:
        r = requests.get(f"{base_url}/telemetry", timeout=5)
        print("Telemetry:", r.status_code, r.json() if r.status_code == 200 else r.text)
    except Exception as e:
        print("Telemetry failed:", e)

    try:
        r = requests.get(f"{base_url}/route", timeout=5)
        print("Route:", r.status_code, r.json() if r.status_code == 200 else r.text)
    except Exception as e:
        print("Route failed:", e)

    try:
        payload = {
            "bin_id": 1,
            "fill_level": 85,
            "gas_level": 12.0,
            "temperature": 34.5,
            "humidity": 45.0,
            "battery": 90.0,
            "tenant_id": "default",
        }
        r = requests.post(f"{base_url}/iot/update", json=payload, headers=_headers(), timeout=5)
        print("IoT Update:", r.status_code, r.json() if r.status_code == 200 else r.text)
    except Exception as e:
        print("IoT Update failed:", e)


if __name__ == "__main__":
    test_api()
