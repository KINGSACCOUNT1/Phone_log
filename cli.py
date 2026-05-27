#!/usr/bin/env python3
"""Phone Log CLI - command-line interface for managing phone call records."""

import argparse
import sys

import phone_log


# ─── Formatting helpers ────────────────────────────────────────────────────────

DIRECTION_ICONS = {
    "incoming": "↙ incoming",
    "outgoing": "↗ outgoing",
    "missed":   "✗ missed  ",
}


def _fmt_entry(entry):
    """Return a single-line summary string for a log entry."""
    icon = DIRECTION_ICONS.get(entry["direction"], entry["direction"])
    duration = phone_log.format_duration(entry["duration_seconds"])
    notes = f'  [{entry["notes"]}]' if entry["notes"] else ""
    return (
        f"[{entry['id']:>4}] {entry['timestamp']}  {icon}  "
        f"{entry['contact_name']} ({entry['phone_number']})  "
        f"duration: {duration}{notes}"
    )


def _print_entries(entries):
    if not entries:
        print("No call records found.")
        return
    for e in entries:
        print(_fmt_entry(e))
    print(f"\n{len(entries)} record(s).")


# ─── Sub-command handlers ──────────────────────────────────────────────────────

def cmd_add(args):
    try:
        entry = phone_log.add_call(
            contact_name=args.name,
            phone_number=args.number,
            direction=args.direction,
            duration_seconds=args.duration,
            notes=args.notes or "",
        )
        print(f"Added: {_fmt_entry(entry)}")
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    entries = phone_log.get_all()
    if args.direction:
        entries = [e for e in entries if e["direction"] == args.direction]
    _print_entries(entries)


def cmd_search(args):
    entries = phone_log.search(args.query)
    _print_entries(entries)


def cmd_delete(args):
    if phone_log.delete_call(args.id):
        print(f"Deleted call record with ID {args.id}.")
    else:
        print(f"No call record found with ID {args.id}.", file=sys.stderr)
        sys.exit(1)


def cmd_update_notes(args):
    entry = phone_log.update_notes(args.id, args.notes)
    if entry:
        print(f"Updated: {_fmt_entry(entry)}")
    else:
        print(f"No call record found with ID {args.id}.", file=sys.stderr)
        sys.exit(1)


# ─── Argument parser ───────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="phone_log",
        description="Phone Log – track and manage your phone call history.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")
    subparsers.required = True

    # add
    p_add = subparsers.add_parser("add", help="Add a new call record.")
    p_add.add_argument("name", help="Contact name.")
    p_add.add_argument("number", help="Phone number.")
    p_add.add_argument(
        "direction",
        choices=phone_log.DIRECTIONS,
        help="Call direction.",
    )
    p_add.add_argument(
        "--duration", "-d",
        type=int,
        metavar="SECONDS",
        default=None,
        help="Call duration in seconds (omit for missed calls).",
    )
    p_add.add_argument(
        "--notes", "-n",
        default="",
        help="Optional notes about the call.",
    )
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = subparsers.add_parser("list", help="List all call records.")
    p_list.add_argument(
        "--direction",
        choices=phone_log.DIRECTIONS,
        default=None,
        help="Filter by call direction.",
    )
    p_list.set_defaults(func=cmd_list)

    # search
    p_search = subparsers.add_parser("search", help="Search call records by name or number.")
    p_search.add_argument("query", help="Name or number to search for.")
    p_search.set_defaults(func=cmd_search)

    # delete
    p_delete = subparsers.add_parser("delete", help="Delete a call record by ID.")
    p_delete.add_argument("id", type=int, help="ID of the record to delete.")
    p_delete.set_defaults(func=cmd_delete)

    # notes
    p_notes = subparsers.add_parser("notes", help="Update notes on an existing call record.")
    p_notes.add_argument("id", type=int, help="ID of the record to update.")
    p_notes.add_argument("notes", help="New notes text.")
    p_notes.set_defaults(func=cmd_update_notes)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
