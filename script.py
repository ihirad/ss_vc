import requests

SUPERSET_URL = "http://localhost:8088"  # Update with your Superset base URL
USERNAME = "admin"
PASSWORD = "admin"
CHART_ID = 111  # Replace with your actual chart ID

# Step 1: Login and get access token
def get_access_token():
    login_url = f"{SUPERSET_URL}/api/v1/security/login"
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "provider": "db",  # or "ldap", "oauth", etc.
        "refresh": True,
    }

    response = requests.post(login_url, json=payload)
    response.raise_for_status()
    return response.json()["access_token"]

# Step 2: Get CSRF token
def get_csrf_token(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/", headers=headers)
    response.raise_for_status()
    return response.json()["result"]

# Step 3: Get a chart by ID
def get_chart(chart_id, access_token, csrf_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-CSRFToken": csrf_token
    }
    response = requests.get(f"{SUPERSET_URL}/api/v1/chart/{chart_id}", headers=headers)
    response.raise_for_status()
    return response.json()

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

def get_csrf_token2(session):
    headers = {
        "Authorization": f"Bearer {session.access_token}"
    }
    response = session.get(f"{SUPERSET_URL}/api/v1/security/csrf_token/", headers=headers)
    response.raise_for_status()
    return response.json()["result"]

# Step 4: Update chart (PUT)
def update_chart(session, chart_id, csrf_token, updated_title):
    headers = {
        "Authorization": f"Bearer {session.access_token}",
        "X-CSRFToken": csrf_token,
        "Content-Type": "application/json"
    }
    payload = {
        "slice_name": updated_title
    }
    print(chart_id)
    response = session.put(f"{SUPERSET_URL}/api/v1/chart/{chart_id}", headers=headers, json=payload)
    
    try:
        response.raise_for_status()
        print(f"Chart {chart_id} updated successfully.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Failed to update chart {chart_id}: {e}")
        print("Response:", response.text)
        raise

# Run the flow
if __name__ == "__main__":
    # access_token = get_access_token()
    # csrf_token = get_csrf_token(access_token)
    session =login_and_get_session()
    csrf_token2 = get_csrf_token2(session)

    print("Access and CSRF tokens acquired.")

    # chart = get_chart(CHART_ID, access_token, csrf_token)
    # print("📊 Current Chart Title:", chart["result"]["slice_name"])

    new_title = "(Updated)"
    update_response = update_chart(session, CHART_ID, csrf_token2, new_title)
    print("Chart updated:", update_response)
