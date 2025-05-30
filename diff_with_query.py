import requests
import json
import difflib
import os
import tempfile

SUPERSET_URL = "http://localhost:8088"
USERNAME = "admin"
PASSWORD = "admin"
CHART_ID = 85  # Replace with your actual chart ID

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

def get_dataset(session, datasource_id, token, csrf_token):
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CSRFToken": csrf_token
    }
    response = session.get(f"{SUPERSET_URL}/api/v1/dataset/{datasource_id}", headers=headers)
    response.raise_for_status()
    return response.json()["result"]

def edit_in_tempfile(original_content, suffix=".sql"):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=suffix) as tf:
        tf.write(original_content)
        tf.flush()
        os.system(f"${{EDITOR:-nano}} {tf.name}")
        tf.seek(0)
        updated_content = tf.read()
    os.unlink(tf.name)
    return updated_content

def print_diff(original, updated):
    diff = difflib.unified_diff(
        original.splitlines(), 
        updated.splitlines(), 
        fromfile="original", 
        tofile="updated", 
        lineterm=""
    )
    print("\n".join(diff))

def main():
    session, token = login_and_get_token()
    csrf_token = get_csrf_token(session, token)

    chart = get_chart(session, CHART_ID, token, csrf_token)
    print(f"Chart title: {chart['slice_name']}")
    
    # Get datasource info
    params = chart.get("params")
    if not params:
        raise ValueError("Missing 'params' in chart data.")
    
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            raise ValueError("Failed to parse 'params' as JSON string.")

    datasource_str = params.get("datasource")
    if not datasource_str:
        raise ValueError("Datasource info not found in 'params.datasource'.")

    datasource_id = int(datasource_str.split("__")[0])
    if not datasource_str:
        raise ValueError("Datasource info not found in 'params.datasource'.")
    datasource_id = int(datasource_str.split("__")[0])
    dataset = get_dataset(session, datasource_id, token, csrf_token)

    # Ask user what they want to edit
    choice = input("Edit dataset query, chart YAML, or both? [dataset/yaml/both]: ").strip().lower()

    if choice in ("dataset", "both"):
        original_query = dataset.get("sql") or "-- No SQL query available in dataset"
        print("Opening dataset query for editing...")
        updated_query = edit_in_tempfile(original_query)
        if updated_query != original_query:
            print_diff(original_query, updated_query)
            confirm = input("Save changes to dataset? (y/n): ").strip().lower()
            if confirm == "y":
                headers = {
                    "Authorization": f"Bearer {token}",
                    "X-CSRFToken": csrf_token,
                    "Content-Type": "application/json"
                }
                payload = {"sql": updated_query}
                dataset_id = dataset["id"]
                response = session.put(f"{SUPERSET_URL}/api/v1/dataset/{dataset_id}", headers=headers, json=payload)
                response.raise_for_status()
                print("Dataset query updated.")
            else:
                print("No changes saved to dataset.")
    
    if choice in ("yaml", "both"):
        original_yaml = json.dumps(chart, indent=2)
        print("Opening chart YAML for editing...")
        updated_yaml = edit_in_tempfile(original_yaml, suffix=".yaml")
        if updated_yaml != original_yaml:
            print_diff(original_yaml, updated_yaml)
            confirm = input("Save changes to chart? (y/n): ").strip().lower()
            if confirm == "y":
                headers = {
                    "Authorization": f"Bearer {token}",
                    "X-CSRFToken": csrf_token,
                    "Content-Type": "application/json"
                }
                chart_id = chart["id"]
                updated_data = json.loads(updated_yaml)
                response = session.put(f"{SUPERSET_URL}/api/v1/chart/{chart_id}", headers=headers, json=updated_data)
                response.raise_for_status()
                print("Chart YAML updated.")
            else:
                print("No changes saved to chart.")

if __name__ == "__main__":
    main()
