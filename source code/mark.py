import json
import re
from html import unescape

def clean_html(raw_html):
    """Remove HTML tags, unescape entities, and clean text formatting."""
    text = unescape(raw_html)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()

try:
    with open("markers.json", "r", encoding="utf-8") as file:
        data = json.load(file)
except json.JSONDecodeError as e:
    print("Error decoding JSON:", e)
    exit(1)

output_lines = []
entry_count = 0

def extract_markers(obj):
    global entry_count
    if isinstance(obj, dict):
        if "detail" in obj and "label" in obj and "position" in obj:
            label = obj["label"]
            detail = clean_html(obj["detail"])
            position = obj["position"]

            output_lines.append(f"=== {label} ===")
            output_lines.append(f"Position: X={position['x']}, Y={position['y']}, Z={position['z']}")
            output_lines.append("Details:\n" + detail)
            output_lines.append("\n" + "-" * 40 + "\n")

            entry_count += 1


        for value in obj.values():
            extract_markers(value)

    elif isinstance(obj, list):

        for item in obj:
            extract_markers(item)

extract_markers(data)

if entry_count > 0:
    with open("markers.txt", "w", encoding="utf-8") as output_file:
        output_file.write("\n".join(output_lines))
    print(f"process complete! {entry_count} markers saved in markers.txt.")
else:
    print("no valid markers found.")


# Only me and God knows what the fuck i wrote