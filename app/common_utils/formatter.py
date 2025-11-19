import json
from typing import List, Dict, Any

def format_markdown(text: str) -> str:
    """
    Format text as Markdown.
    """
    return f"**Summary:**\n\n{text}"

def format_json(data: Dict[str, Any]) -> str:
    """
    Convert Python dict into pretty JSON.
    """
    return json.dumps(data, indent=4, ensure_ascii=False)

def format_table(rows: List[Dict[str, Any]]) -> str:
    """
    Convert list of dictionaries into a Markdown table.
    """
    if not rows:
        return "No data available."

    headers = rows[0].keys()
    header_row = " | ".join(headers)
    separator = " | ".join(["---"] * len(headers))

    data_rows = []
    for row in rows:
        data_row = " | ".join(str(row[h]) for h in headers)
        data_rows.append(data_row)

    return f"{header_row}\n{separator}\n" + "\n".join(data_rows)

def format_response(text: str, output: str = "markdown") -> str:
    """
    Generic formatter for API endpoints.
    Valid formats: markdown, json, bullet, table, pretty
    """

    if output == "markdown":
        return format_markdown(text)

    elif output == "json":
        return format_json({"response": text})


    elif output == "table":
        # Fake example conversion: each sentence becomes a row
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        rows = [{"index": i + 1, "sentence": s} for i, s in enumerate(sentences)]
        return format_table(rows)

    else:
        return "Content not supported."
        
