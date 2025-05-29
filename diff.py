import requests
import json
import difflib
import os
import tempfile

SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"
CHART_ID = 110  

def login_and_get_token():
    session = requests.Session()
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "provider": "db",
        "refresh": True,
    }
    response = session.post(f"{SUPERSET_URL}/api/v1/security/login", json=payload)
    response.raise_for_status()
    token = response.json()["access_token"]
    return session, token

def get_csrf_token(session, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token", headers=headers)
    return response.json()["result"]

def get_chart(session, chart_id, token, csrf_token):
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRFToken": csrf_token
    }
    response = session.get(f"{SUPERSET_URL}/api/v1/chart/{chart_id}", headers=headers)
    response.raise_for_status()
    return response.json()["result"]

def save_chart_to_file(chart_data):
    fd, file_path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w') as f:
        json.dump(chart_data, f, indent=2)
    print(f"\n📝 Chart saved to: {file_path}\nEdit the file then press ENTER to continue...")
    input()
    with open(file_path, 'r') as f:
        updated_chart_data = json.load(f)
    os.remove(file_path)
    return updated_chart_data

def update_chart(session, chart_id, new_data, token, csrf_token):
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/json"
    }

    # Create a properly formatted payload with only the allowed fields
    payload = {
        "slice_name": new_data.get("slice_name"),
        "viz_type": new_data.get("viz_type"),
        "datasource_id": new_data.get("datasource_id"),
        "datasource_type": new_data.get("datasource_type"),
        "owners": new_data.get("owners", []),
        "description": new_data.get("description"),
    }

    # Handle params and query_context - ensure they are strings
    if "params" in new_data:
        payload["params"] = json.dumps(new_data["params"]) if isinstance(new_data["params"], dict) else new_data["params"]
    
    if "query_context" in new_data:
        payload["query_context"] = json.dumps(new_data["query_context"]) if isinstance(new_data["query_context"], dict) else new_data["query_context"]

    # Remove any None values
    payload = {k: v for k, v in payload.items() if v is not None}

    response = session.put(f"{SUPERSET_URL}/api/v1/chart/{chart_id}", headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error response: {response.text}")
    response.raise_for_status()
    
    print("✅ Chart updated successfully.")
    return response.json()

def print_diff(original, updated):
    original_str = json.dumps(original, indent=2, sort_keys=True)
    updated_str = json.dumps(updated, indent=2, sort_keys=True)
    diff = difflib.unified_diff(
        original_str.splitlines(keepends=True),
        updated_str.splitlines(keepends=True),
        fromfile='original',
        tofile='updated',
    )
    print("\n🆚 Diff:")
    print("".join(diff))


if __name__ == "__main__":
    session, token = login_and_get_token()
    csrf_token = get_csrf_token(session, token)

    original_chart = get_chart(session, CHART_ID, token, csrf_token)

    editable_fields = {
        "slice_name": original_chart["slice_name"],
        "viz_type": original_chart["viz_type"],
        "params": json.loads(original_chart["params"]),
        "query_context": json.loads(original_chart["query_context"]),
        "description": original_chart.get("description"),
        "datasource_id": original_chart.get("datasource_id"),
        "datasource_type": original_chart.get("datasource_type", "table"),
        "owners": original_chart.get("owners", [])
    }

    edited_chart = save_chart_to_file(editable_fields)

    print_diff(editable_fields, edited_chart)

    update_chart(session, CHART_ID, edited_chart, token, csrf_token)
