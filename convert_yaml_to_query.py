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

def extract_sql_like_query(chart_data):
    try:
        query_context = chart_data.get("query_context")
        if isinstance(query_context, str):
            query_context = json.loads(query_context)
        query = query_context["queries"][0]

        metrics = [m.get("label", m.get("column", {}).get("column_name", "")) for m in query.get("metrics", [])]
        columns = query.get("columns", [])
        groupby = [c["label"] if isinstance(c, dict) else c for c in columns if isinstance(c, (dict, str))]
        filters = query.get("filters", [])
        where_clauses = []
        for f in filters:
            where_clauses.append(f"{f['col']} {f['op']} '{f['val']}'")

        select_clause = ", ".join(metrics + groupby) or "*"
        from_clause = f"FROM dataset_id_{query_context['datasource']['id']}"
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        group_clause = f"GROUP BY {', '.join(groupby)}" if groupby else ""

        sql_query = f"SELECT {select_clause} {from_clause} {where_clause} {group_clause}".strip()
        return sql_query
    except Exception as e:
        return f"-- Failed to extract SQL-like query: {e}"
