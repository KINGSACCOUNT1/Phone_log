"""Export Module - Export call records to various formats (CSV, PDF, JSON)."""

import csv
import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

import phone_log


def export_to_csv(
    calls: Optional[List[Dict[str, Any]]] = None,
    data_file: Optional[str] = None,
    include_notes: bool = True
) -> str:
    """
    Export call records to CSV format.
    
    Args:
        calls: Optional list of calls to export (uses all calls if None)
        data_file: Optional override for data file path
        include_notes: Whether to include notes column
        
    Returns:
        str: CSV content as string
    """
    if calls is None:
        calls = phone_log.get_all(data_file)
    
    output = io.StringIO()
    
    # Define columns
    fieldnames = ["id", "contact_name", "phone_number", "direction", "timestamp", "duration"]
    if include_notes:
        fieldnames.append("notes")
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    
    for call in calls:
        row = {
            "id": call["id"],
            "contact_name": call["contact_name"],
            "phone_number": call["phone_number"],
            "direction": call["direction"],
            "timestamp": call["timestamp"],
            "duration": phone_log.format_duration(call.get("duration_seconds")),
        }
        if include_notes:
            row["notes"] = call.get("notes", "")
        writer.writerow(row)
    
    return output.getvalue()


def export_to_json(
    calls: Optional[List[Dict[str, Any]]] = None,
    data_file: Optional[str] = None,
    pretty: bool = True
) -> str:
    """
    Export call records to JSON format.
    
    Args:
        calls: Optional list of calls to export (uses all calls if None)
        data_file: Optional override for data file path
        pretty: Whether to format JSON with indentation
        
    Returns:
        str: JSON content as string
    """
    if calls is None:
        calls = phone_log.get_all(data_file)
    
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "total_records": len(calls),
        "calls": calls,
    }
    
    if pretty:
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    return json.dumps(export_data, ensure_ascii=False)


def export_to_html(
    calls: Optional[List[Dict[str, Any]]] = None,
    data_file: Optional[str] = None,
    title: str = "Phone Log Export"
) -> str:
    """
    Export call records to HTML table format.
    
    Args:
        calls: Optional list of calls to export (uses all calls if None)
        data_file: Optional override for data file path
        title: Title for the HTML document
        
    Returns:
        str: HTML content as string
    """
    if calls is None:
        calls = phone_log.get_all(data_file)
    
    direction_icons = {
        "incoming": "↙️",
        "outgoing": "↗️",
        "missed": "✗",
    }
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #6366f1;
            padding-bottom: 10px;
        }}
        .meta {{
            color: #666;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: #6366f1;
            color: white;
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 16px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f9f9f9;
        }}
        .direction-incoming {{ color: #10b981; }}
        .direction-outgoing {{ color: #6366f1; }}
        .direction-missed {{ color: #ef4444; }}
        .notes {{
            font-size: 0.9em;
            color: #666;
            max-width: 200px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p class="meta">Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • {len(calls)} records</p>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Contact</th>
                <th>Phone</th>
                <th>Direction</th>
                <th>Date/Time</th>
                <th>Duration</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for call in calls:
        direction = call["direction"]
        icon = direction_icons.get(direction, "")
        direction_class = f"direction-{direction}"
        
        # Format timestamp
        try:
            ts = datetime.fromisoformat(call["timestamp"].replace("Z", "+00:00"))
            formatted_time = ts.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            formatted_time = call["timestamp"]
        
        duration = phone_log.format_duration(call.get("duration_seconds"))
        notes = call.get("notes", "") or ""
        
        html += f"""            <tr>
                <td>{call['id']}</td>
                <td>{call['contact_name']}</td>
                <td>{call['phone_number']}</td>
                <td class="{direction_class}">{icon} {direction.capitalize()}</td>
                <td>{formatted_time}</td>
                <td>{duration}</td>
                <td class="notes">{notes}</td>
            </tr>
"""
    
    html += """        </tbody>
    </table>
</body>
</html>
"""
    
    return html


def generate_summary_report(data_file: Optional[str] = None) -> str:
    """
    Generate a text summary report of call statistics.
    
    Args:
        data_file: Optional override for data file path
        
    Returns:
        str: Formatted text report
    """
    calls = phone_log.get_all(data_file)
    
    if not calls:
        return "No call records found."
    
    # Calculate statistics
    total = len(calls)
    incoming = sum(1 for c in calls if c["direction"] == "incoming")
    outgoing = sum(1 for c in calls if c["direction"] == "outgoing")
    missed = sum(1 for c in calls if c["direction"] == "missed")
    
    durations = [c["duration_seconds"] for c in calls if c["duration_seconds"]]
    total_duration = sum(durations)
    avg_duration = total_duration / len(durations) if durations else 0
    
    # Top contacts
    from collections import Counter
    contact_counts = Counter(c["contact_name"] for c in calls)
    top_contacts = contact_counts.most_common(5)
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    PHONE LOG SUMMARY REPORT                   ║
╠══════════════════════════════════════════════════════════════╣
║  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):>45} ║
╚══════════════════════════════════════════════════════════════╝

📊 OVERVIEW
────────────────────────────────────────
Total Calls:    {total:>8}
↙️ Incoming:    {incoming:>8} ({incoming/total*100:.1f}%)
↗️ Outgoing:    {outgoing:>8} ({outgoing/total*100:.1f}%)
✗ Missed:      {missed:>8} ({missed/total*100:.1f}%)

⏱️ DURATION STATISTICS
────────────────────────────────────────
Total Time:     {phone_log.format_duration(total_duration):>8}
Average:        {phone_log.format_duration(int(avg_duration)):>8}
Longest:        {phone_log.format_duration(max(durations) if durations else 0):>8}
Shortest:       {phone_log.format_duration(min(durations) if durations else 0):>8}

👥 TOP CONTACTS
────────────────────────────────────────
"""
    
    for i, (name, count) in enumerate(top_contacts, 1):
        report += f"{i}. {name:<25} {count:>3} calls\n"
    
    report += """
════════════════════════════════════════════════════════════════
"""
    
    return report


def import_from_csv(csv_content: str, data_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Import call records from CSV content.
    
    Expected CSV columns: contact_name, phone_number, direction, timestamp (optional),
                         duration_seconds (optional), notes (optional)
    
    Args:
        csv_content: CSV file content as string
        data_file: Optional override for data file path
        
    Returns:
        dict: Import results with counts and errors
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    
    imported = 0
    errors = []
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
        try:
            contact_name = row.get("contact_name", "").strip()
            phone_number = row.get("phone_number", "").strip()
            direction = row.get("direction", "").strip().lower()
            
            if not contact_name or not phone_number or not direction:
                errors.append(f"Row {row_num}: Missing required fields")
                continue
            
            duration = row.get("duration_seconds") or row.get("duration")
            if duration:
                try:
                    # Handle formatted duration like "2m 30s"
                    if isinstance(duration, str) and any(c in duration for c in "hms"):
                        duration = None  # Skip formatted duration
                    else:
                        duration = int(duration)
                except ValueError:
                    duration = None
            
            notes = row.get("notes", "").strip()
            
            phone_log.add_call(
                contact_name=contact_name,
                phone_number=phone_number,
                direction=direction,
                duration_seconds=duration,
                notes=notes,
                data_file=data_file,
            )
            imported += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    return {
        "imported": imported,
        "errors": errors,
        "total_errors": len(errors),
    }
