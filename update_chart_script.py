import requests
from extract_and_load_YAML import load_yaml_generic, YAML_FILE, filter_chart_fields

# Limitations: If there is no slice ID in the YAML file the script will not work
# only works for charts that are already in the database, cannot create new charts
# To Fix:
# 1. Changes can break the chart, figure out
# 2. Add a new chart to the database
# 2. Add the slice ID to the YAML file
# 3. 


SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"
YAML_FILE = "dashboard_export_20250522T195733/charts/Total_Revenue_88.yaml"

def login_and_get_session():
    session = requests.Session()
    login_payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "provider": "db",
        "refresh": True,
    }
    login_response = session.post(f"{SUPERSET_URL}/api/v1/security/login", json=login_payload)
    login_response.raise_for_status()
    # Store the access token in the session object
    session.access_token = login_response.json()["access_token"]
    return session

def get_csrf_token(session):
    headers = {
        "Authorization": f"Bearer {session.access_token}"
    }
    response = session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token", headers=headers)
    response.raise_for_status()
    return response.json()["result"]


def get_chart(session, chart_id, csrf_token):
    headers = {
        "Authorization": f"Bearer {session.access_token}",
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/json"
    }
    url = f"{SUPERSET_URL}/api/v1/chart/{chart_id}"

    response = session.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["result"]


def update_chart(session, chart_id, chart_data, slice_name, csrf_token):
    headers = {
        "Authorization": f"Bearer {session.access_token}",
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/json"
    }

    # Get the existing chart data
    existing_data = get_chart(session, chart_id, csrf_token)
    print("Available fields in existing data:", existing_data.keys())
    print("Existing data:", existing_data)

    # Start with a clean payload
    updated_payload = {
        "slice_name": slice_name or existing_data["slice_name"],
        "viz_type": chart_data.get("viz_type") or existing_data["viz_type"],
        "datasource_id": existing_data.get("datasource_id") or existing_data.get("datasource", {}).get("id"),
        "datasource_type": existing_data.get("datasource_type") or existing_data.get("datasource", {}).get("type"),
        "params": chart_data.get("params", {}),
        "query_context": chart_data.get("query_context"),
        "description": chart_data.get("description"),
        "cache_timeout": chart_data.get("cache_timeout"),
        "owners": existing_data.get("owners", [])
    }

    # Remove any None values
    updated_payload = {k: v for k, v in updated_payload.items() if v is not None}

    # Ensure params is a string
    if isinstance(updated_payload.get("params"), dict):
        import json
        updated_payload["params"] = json.dumps(updated_payload["params"])

    print("Updated payload:", updated_payload)

    response = session.put(f"{SUPERSET_URL}/api/v1/chart/{chart_id}", headers=headers, json=updated_payload)

    try:
        response.raise_for_status()
        print(f"✅ Chart {chart_id} updated successfully.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to update chart {chart_id}: {e}")
        print("Response:", response.text)
        raise



if __name__ == "__main__":
    session = login_and_get_session()
    csrf_token = get_csrf_token(session)

    chart_data, chart_name, chart_id = load_yaml_generic(YAML_FILE)
    if not chart_id:
        # Try to get chart_id from params if not found at top level
        chart_id = chart_data.get("params", {}).get("slice_id")
        print(chart_id)
        if not chart_id:
            raise ValueError("❌ 'slice_id' not found in YAML. Cannot proceed.")

    update_chart(session, chart_id, chart_data, chart_name, csrf_token)
