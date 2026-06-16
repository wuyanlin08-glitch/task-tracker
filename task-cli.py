#!/usr/bin/env python3
"""

A simple command-line task tracker that stores tasks in a JSON file.
No external dependencies — uses only Python standard library.

Usage:
  python task-cli.py add "Buy groceries"
  python task-cli.py update 1 "Buy groceries and cook dinner"
  python task-cli.py delete 1
  python task-cli.py mark-in-progress 1
  python task-cli.py mark-done 1
  python task-cli.py list
  python task-cli.py list todo
  python task-cli.py list in-progress
  python task-cli.py list done
"""

import json
import os
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# tasks.json is stored in the same directory as this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE = os.path.join(SCRIPT_DIR, "tasks.json")

# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def read_tasks():
    """Read all tasks from the JSON file. Returns an empty list if the file
    doesn't exist or is corrupted."""
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw:
                return []
            return json.loads(raw)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading tasks file: {e}")
        sys.exit(1)


def write_tasks(tasks):
    """Write the tasks list to the JSON file (pretty-printed)."""
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except IOError as e:
        print(f"Error writing tasks file: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def get_next_id(tasks):
    """Return max existing ID + 1, or 1 if there are no tasks."""
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def timestamp():
    """Return an ISO-like timestamp in local time: YYYY-MM-DDTHH:mm:ss"""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def find_task(tasks, task_id):
    """Return (task_dict, index) or (None, -1) if not found."""
    for i, t in enumerate(tasks):
        if t["id"] == task_id:
            return t, i
    return None, -1


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_add(args):
    if not args:
        print("Error: Please provide a task description.")
        print('Usage: task-cli add "Task description"')
        sys.exit(1)

    description = " ".join(args)
    tasks = read_tasks()
    ts = timestamp()
    task = {
        "id": get_next_id(tasks),
        "description": description,
        "status": "todo",
        "createdAt": ts,
        "updatedAt": ts,
    }
    tasks.append(task)
    write_tasks(tasks)
    print(f"Task added successfully (ID: {task['id']})")


def cmd_update(args):
    if len(args) < 2:
        print("Error: Please provide a task ID and new description.")
        print('Usage: task-cli update <id> "New description"')
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print("Error: Task ID must be a number.")
        sys.exit(1)

    new_description = " ".join(args[1:])
    tasks = read_tasks()
    task, index = find_task(tasks, task_id)

    if task is None:
        print(f"Error: Task with ID {task_id} not found.")
        sys.exit(1)

    tasks[index]["description"] = new_description
    tasks[index]["updatedAt"] = timestamp()
    write_tasks(tasks)
    print(f"Task {task_id} updated successfully.")


def cmd_delete(args):
    if not args:
        print("Error: Please provide a task ID.")
        print("Usage: task-cli delete <id>")
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print("Error: Task ID must be a number.")
        sys.exit(1)

    tasks = read_tasks()
    task, index = find_task(tasks, task_id)

    if task is None:
        print(f"Error: Task with ID {task_id} not found.")
        sys.exit(1)

    tasks.pop(index)
    write_tasks(tasks)
    print(f"Task {task_id} deleted successfully.")


def cmd_mark(status, args):
    if not args:
        print("Error: Please provide a task ID.")
        print(f"Usage: task-cli mark-{status} <id>")
        sys.exit(1)

    try:
        task_id = int(args[0])
    except ValueError:
        print("Error: Task ID must be a number.")
        sys.exit(1)

    tasks = read_tasks()
    task, index = find_task(tasks, task_id)

    if task is None:
        print(f"Error: Task with ID {task_id} not found.")
        sys.exit(1)

    tasks[index]["status"] = status
    tasks[index]["updatedAt"] = timestamp()
    write_tasks(tasks)
    print(f"Task {task_id} marked as {status}.")


def cmd_list(args):
    tasks = read_tasks()

    if not tasks:
        print("Nothing task need to do!")
        return

    # Determine filter
    filtered = tasks
    if args:
        filter_status = args[0].lower()
        valid_statuses = {"todo", "in-progress", "done"}
        if filter_status not in valid_statuses:
            print(f'Error: Invalid status "{args[0]}". Valid: todo, in-progress, done')
            sys.exit(1)
        filtered = [t for t in tasks if t["status"] == filter_status]

    if not filtered:
        print("No tasks match the filter.")
        return

    # Pretty-print table
    columns = [
        ("ID", "id"),
        ("Description", "description"),
        ("Status", "status"),
        ("Created At", "createdAt"),
        ("Updated At", "updatedAt"),
    ]

    # Calculate column widths
    widths = {}
    for header, key in columns:
        widths[key] = max(
            len(header),
            max((len(str(t[key])) for t in filtered), default=0),
        )

    # Print header
    def fmt(val, w):
        return str(val).ljust(w)

    header_line = "  ".join(fmt(h, widths[k]) for h, k in columns)
    print(header_line)
    print("  ".join("-" * widths[k] for _, k in columns))

    # Print rows
    for t in filtered:
        row = "  ".join(fmt(t[k], widths[k]) for _, k in columns)
        print(row)


# ---------------------------------------------------------------------------
# Main — dispatch command
# ---------------------------------------------------------------------------

def main():
    argv = sys.argv[1:]  # skip script name

    if not argv:
        print("Task Tracker CLI")
        print()
        print("Usage: task-cli <command> [args]")
        print()
        print("Commands:")
        print("  add <description>           Add a new task")
        print("  update <id> <description>    Update a task description")
        print("  delete <id>                 Delete a task")
        print("  mark-in-progress <id>       Mark a task as in-progress")
        print("  mark-done <id>              Mark a task as done")
        print("  list [status]               List tasks (all / todo / in-progress / done)")
        return

    command = argv[0]
    args = argv[1:]

    match command:
        case "add":
            cmd_add(args)
        case "update":
            cmd_update(args)
        case "delete":
            cmd_delete(args)
        case "mark-in-progress":
            cmd_mark("in-progress", args)
        case "mark-done":
            cmd_mark("done", args)
        case "list":
            cmd_list(args)
        case _:
            print(f'Error: Unknown command "{command}".')
            print("Available: add, update, delete, mark-in-progress, mark-done, list")
            sys.exit(1)


if __name__ == "__main__":
    main()
