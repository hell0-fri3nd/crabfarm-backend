LOG_QUERY_PROMPT = """
Current datetime: {current_datetime}

Extract database query parameters from user request for `sensor_logs` table.

Columns: id, sensor_type (temperature/turbidity/ph/tds/ammonium/do), status (NORMAL/WARNING/DANGER), value (numeric), created_at (timestamp).

Return ONLY JSON:

{{
  "start_date": "YYYY-MM-DD HH:MM:SS or null",
  "end_date": "YYYY-MM-DD HH:MM:SS or null",
  "status_filter": "ALL or NORMAL or WARNING or DANGER",
  "sensor_filter": "ALL or temperature or turbidity or ph or tds or ammonium or do",
  "group_by": "none or date or sensor_type or status",
  "aggregation": "list or count or summary",
  "order": "asc or desc",
  "limit": null or integer
}}

Rules:
- "list" = return raw rows, "count" = just total, "summary" = grouped counts
- "group_by": "date" means count per day, "sensor_type" means count per type, "status" means count per status
- Use current_datetime as reference for relative dates
- today = start of today to current_datetime
- yesterday = previous full day
- Return JSON only.
"""
