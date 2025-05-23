import yaml

YAML_FILE = "dashboard_export_20250522T195733/charts/Total_Revenue_88.yaml"

def extract_all_fields(data, result=None, parent_key=""):
    """
    Recursively flattens a nested dictionary structure.
    Builds a flat dictionary of all key-value pairs from YAML.
    """
    if result is None:
        result = {}

    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, dict):
                extract_all_fields(value, result, full_key)
            else:
                result[full_key] = value
    return result

def load_yaml_generic(file_path):
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    # Flatten nested keys (dot-separated paths)
    flat_data = extract_all_fields(data)

    # Build a dynamic payload dictionary with top-level and nested values
    payload = {}

    # Only include leaf values (non-dict), reconstructing nested keys if needed
    for key_path, value in flat_data.items():
        keys = key_path.split(".")
        d = payload
        for part in keys[:-1]:
            d = d.setdefault(part, {})
        d[keys[-1]] = value

    # Extract a name and ID if present
    name = data.get("slice_name") or data.get("dashboard_title") or data.get("dataset_name") or "Unnamed Resource"
    resource_id = data.get("params", {}).get("slice_id")

    return payload, name, resource_id

def filter_chart_fields(chart_data):
    allowed_fields = {
        "slice_name",
        "viz_type",
        "description",
        "params",
        "query_context",
        "cache_timeout",
        "datasource_id",
        "datasource_type",
        "owners",
        "metrics",
        "columns",
        "certified_by",
        "certification_details",
        "external_url",
        "is_managed_externally"
        # Note: 'dashboards' removed due to common UUID errors
    }

    filtered = {
        key: chart_data[key]
        for key in allowed_fields
        if key in chart_data
    }

    # Ensure 'params' is a string (Superset expects it)
    if "params" in filtered and isinstance(filtered["params"], dict):
        import json
        filtered["params"] = json.dumps(filtered["params"])

    return filtered