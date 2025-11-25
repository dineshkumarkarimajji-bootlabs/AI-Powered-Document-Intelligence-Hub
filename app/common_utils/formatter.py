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
        import re

        # 1. Replace weird PDF line breaks like "e\ng\n" -> "e.g."
        text_clean = text.replace("e\ng\n", "e.g.")

        # 2. Remove all newlines
        text_clean = re.sub(r"\s*\n\s*", " ", text_clean)

        # 3. Remove isolated numbering like "1.", "2.", "3." when they appear alone
        text_clean = re.sub(r"\s*\b\d+\.\b\s*", " ", text_clean)

        # 4. Collapse multiple spaces
        text_clean = re.sub(r"\s+", " ", text_clean).strip()

        # 5. Split into real sentences using punctuation
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text_clean)

        # 6. Build table rows
        rows = [
            {"index": i + 1, "sentence": s.strip()}
            for i, s in enumerate(sentences)
            if s.strip()
        ]

        return format_table(rows)


    else:
        return "Content not supported."
        
