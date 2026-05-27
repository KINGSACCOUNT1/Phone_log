"""Call Analytics Module - Statistics and insights for phone call records."""

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

import phone_log


def get_call_statistics(data_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive call statistics.
    
    Returns:
        dict: Statistics including totals, averages, and breakdowns
    """
    calls = phone_log.get_all(data_file)
    
    if not calls:
        return {
            "total_calls": 0,
            "incoming": 0,
            "outgoing": 0,
            "missed": 0,
            "total_duration_seconds": 0,
            "average_duration_seconds": 0,
            "calls_by_day": {},
            "calls_by_hour": {},
            "top_contacts": [],
            "longest_call": None,
        }
    
    # Basic counts
    incoming = sum(1 for c in calls if c["direction"] == "incoming")
    outgoing = sum(1 for c in calls if c["direction"] == "outgoing")
    missed = sum(1 for c in calls if c["direction"] == "missed")
    
    # Duration statistics
    durations = [c["duration_seconds"] for c in calls if c["duration_seconds"] is not None]
    total_duration = sum(durations)
    avg_duration = total_duration / len(durations) if durations else 0
    
    # Find longest call
    longest_call = None
    if durations:
        max_duration = max(durations)
        longest_call = next(
            (c for c in calls if c["duration_seconds"] == max_duration), None
        )
    
    # Calls by day of week
    calls_by_day = defaultdict(int)
    calls_by_hour = defaultdict(int)
    
    for call in calls:
        try:
            ts = datetime.fromisoformat(call["timestamp"].replace("Z", "+00:00"))
            day_name = ts.strftime("%A")
            hour = ts.hour
            calls_by_day[day_name] += 1
            calls_by_hour[hour] += 1
        except (ValueError, KeyError):
            pass
    
    # Top contacts by call count
    contact_counts = defaultdict(int)
    for call in calls:
        contact_counts[call["contact_name"]] += 1
    
    top_contacts = sorted(
        [{"name": name, "count": count} for name, count in contact_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:10]
    
    return {
        "total_calls": len(calls),
        "incoming": incoming,
        "outgoing": outgoing,
        "missed": missed,
        "total_duration_seconds": total_duration,
        "average_duration_seconds": round(avg_duration, 1),
        "total_duration_formatted": phone_log.format_duration(total_duration),
        "average_duration_formatted": phone_log.format_duration(int(avg_duration)),
        "calls_by_day": dict(calls_by_day),
        "calls_by_hour": dict(calls_by_hour),
        "top_contacts": top_contacts,
        "longest_call": longest_call,
    }


def get_calls_per_day(days: int = 30, data_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get call counts per day for the last N days.
    
    Args:
        days: Number of days to include (default 30)
        data_file: Optional override for data file path
        
    Returns:
        list: Daily call counts with dates
    """
    calls = phone_log.get_all(data_file)
    
    # Initialize daily counts
    now = datetime.now(timezone.utc)
    daily_counts = {}
    
    for i in range(days):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_counts[date] = {"incoming": 0, "outgoing": 0, "missed": 0, "total": 0}
    
    # Count calls per day
    for call in calls:
        try:
            ts = datetime.fromisoformat(call["timestamp"].replace("Z", "+00:00"))
            date = ts.strftime("%Y-%m-%d")
            if date in daily_counts:
                daily_counts[date][call["direction"]] += 1
                daily_counts[date]["total"] += 1
        except (ValueError, KeyError):
            pass
    
    # Convert to list sorted by date
    result = [
        {"date": date, **counts}
        for date, counts in sorted(daily_counts.items())
    ]
    
    return result


def get_contact_summary(data_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get summary statistics for each contact.
    
    Returns:
        list: Contact summaries sorted by total calls
    """
    calls = phone_log.get_all(data_file)
    
    contacts = defaultdict(lambda: {
        "total_calls": 0,
        "incoming": 0,
        "outgoing": 0,
        "missed": 0,
        "total_duration": 0,
        "phone_numbers": set(),
        "last_call": None,
    })
    
    for call in calls:
        name = call["contact_name"]
        contacts[name]["total_calls"] += 1
        contacts[name][call["direction"]] += 1
        contacts[name]["phone_numbers"].add(call["phone_number"])
        
        if call["duration_seconds"]:
            contacts[name]["total_duration"] += call["duration_seconds"]
        
        # Track most recent call
        if contacts[name]["last_call"] is None or call["timestamp"] > contacts[name]["last_call"]:
            contacts[name]["last_call"] = call["timestamp"]
    
    # Convert to list
    result = []
    for name, data in contacts.items():
        result.append({
            "name": name,
            "total_calls": data["total_calls"],
            "incoming": data["incoming"],
            "outgoing": data["outgoing"],
            "missed": data["missed"],
            "total_duration": data["total_duration"],
            "total_duration_formatted": phone_log.format_duration(data["total_duration"]),
            "phone_numbers": list(data["phone_numbers"]),
            "last_call": data["last_call"],
        })
    
    return sorted(result, key=lambda x: x["total_calls"], reverse=True)


def get_hourly_distribution(data_file: Optional[str] = None) -> Dict[int, int]:
    """
    Get call distribution by hour of day.
    
    Returns:
        dict: Hour (0-23) to call count mapping
    """
    calls = phone_log.get_all(data_file)
    
    # Initialize all hours to 0
    hourly = {hour: 0 for hour in range(24)}
    
    for call in calls:
        try:
            ts = datetime.fromisoformat(call["timestamp"].replace("Z", "+00:00"))
            hourly[ts.hour] += 1
        except (ValueError, KeyError):
            pass
    
    return hourly


def get_weekly_trends(weeks: int = 4, data_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get weekly call trends.
    
    Args:
        weeks: Number of weeks to include
        data_file: Optional override for data file path
        
    Returns:
        list: Weekly statistics
    """
    calls = phone_log.get_all(data_file)
    
    now = datetime.now(timezone.utc)
    weekly_data = []
    
    for week in range(weeks):
        week_start = now - timedelta(days=now.weekday() + (week * 7))
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        week_calls = [
            c for c in calls
            if week_start.isoformat() <= c["timestamp"] < week_end.isoformat()
        ]
        
        weekly_data.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "total_calls": len(week_calls),
            "incoming": sum(1 for c in week_calls if c["direction"] == "incoming"),
            "outgoing": sum(1 for c in week_calls if c["direction"] == "outgoing"),
            "missed": sum(1 for c in week_calls if c["direction"] == "missed"),
        })
    
    return list(reversed(weekly_data))


def get_call_duration_distribution(data_file: Optional[str] = None) -> Dict[str, int]:
    """
    Get distribution of call durations.
    
    Returns:
        dict: Duration buckets with counts
    """
    calls = phone_log.get_all(data_file)
    
    buckets = {
        "< 1 min": 0,
        "1-5 min": 0,
        "5-15 min": 0,
        "15-30 min": 0,
        "30-60 min": 0,
        "> 1 hour": 0,
    }
    
    for call in calls:
        duration = call.get("duration_seconds")
        if duration is None:
            continue
        
        if duration < 60:
            buckets["< 1 min"] += 1
        elif duration < 300:
            buckets["1-5 min"] += 1
        elif duration < 900:
            buckets["5-15 min"] += 1
        elif duration < 1800:
            buckets["15-30 min"] += 1
        elif duration < 3600:
            buckets["30-60 min"] += 1
        else:
            buckets["> 1 hour"] += 1
    
    return buckets


def search_by_date_range(
    start_date: str,
    end_date: str,
    data_file: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search calls within a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        data_file: Optional override for data file path
        
    Returns:
        list: Calls within the date range
    """
    calls = phone_log.get_all(data_file)
    
    try:
        start = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
        end = datetime.fromisoformat(f"{end_date}T23:59:59+00:00")
    except ValueError:
        return []
    
    result = []
    for call in calls:
        try:
            ts = datetime.fromisoformat(call["timestamp"].replace("Z", "+00:00"))
            if start <= ts <= end:
                result.append(call)
        except (ValueError, KeyError):
            pass
    
    return result
