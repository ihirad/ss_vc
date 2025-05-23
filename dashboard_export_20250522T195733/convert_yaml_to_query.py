import json

def extract_query_from_query_context(query_context_str):
    try:
        context = json.loads(query_context_str)
    except json.JSONDecodeError:
        raise ValueError("Invalid query_context JSON")

    query = {
        "datasource": context.get("datasource", {}),
        "queries": []
    }

    for q in context.get("queries", []):
        query["queries"].append({
            "columns": q.get("columns", []),
            "metrics": q.get("metrics", []),
            "filters": q.get("filters", []),
            "orderby": q.get("orderby", []),
            "row_limit": q.get("row_limit"),
            "series_columns": q.get("series_columns", []),
            "post_processing": q.get("post_processing", [])
        })

    return query