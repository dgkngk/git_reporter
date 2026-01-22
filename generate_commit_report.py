import argparse
import csv
import datetime
import json
import os
import subprocess
import sys
import textwrap

import google.genai as genai
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# Load environment variables from .env file immediately
load_dotenv()

# --- CONFIGURATION ---
TEMP_DIFF_FILE = "temp_commit_context.txt"

# Files to exclude to keep diffs readable
IGNORED_FILES = [
    "package-lock.json",
    "yarn.lock",
    "composer.lock",
    "*.svg",
    "*.png",
    "dist/*",
    "build/*",
    "*.min.js",
]


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate report using git diffs and Gemini API."
    )
    parser.add_argument("--name", required=True, help="Display name for the report.")
    parser.add_argument(
        "--aliases", required=True, help="Author aliases (comma-separated)."
    )
    parser.add_argument("--repos", nargs="+", default=["."], help="List of repo paths.")
    parser.add_argument(
        "--output", default="Engineering_Value_Report.csv", help="Output CSV path."
    )

    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument(
        "--last-month", action="store_true", help="Auto-select previous month."
    )
    date_group.add_argument(
        "--dates", nargs=2, metavar=("START", "END"), help="YYYY-MM-DD range."
    )

    return parser.parse_args()


def calculate_dates(args):
    if args.last_month:
        today = datetime.date.today()
        first_of_current = today.replace(day=1)
        start_date = first_of_current - relativedelta(months=1)
        end_date = first_of_current
        month_label = start_date.strftime("%Y-%m")
        return (
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            month_label,
        )
    else:
        start_str, end_str = args.dates
        return start_str, end_str, start_str


def get_git_commits_with_diffs(aliases, start, end, repo_path):
    if not os.path.exists(repo_path):
        print(f"Warning: Path {repo_path} not found.")
        return None

    repo_name = os.path.basename(os.path.abspath(repo_path))
    alias_list = [a.strip() for a in aliases.split(",")]

    cmd = [
        "git",
        "log",
        "-p",
        "--no-color",
        f"--since={start}",
        f"--until={end}",
        "--pretty=format:===COMMIT_START===%nAuthor: %an%nMessage: %s%n",
        "--no-merges",
    ]
    for alias in alias_list:
        cmd.append(f"--author={alias}")

    cmd.append("--")
    for ignore in IGNORED_FILES:
        cmd.append(f":(exclude){ignore}")

    try:
        result = subprocess.run(
            cmd, cwd=repo_path, capture_output=True, text=True, check=True
        )
        raw_output = result.stdout.strip()
        if not raw_output:
            return None
        return f"\n--- REPOSITORY: {repo_name} ---\n{raw_output}"
    except subprocess.CalledProcessError:
        return None


def run_gemini_pipeline(context_file_path):
    """
    Reads the temp file and sends it to Gemini API directly.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print(
            "Error: GOOGLE_API_KEY not found. Please set it in a .env file or environment variable."
        )
        sys.exit(1)
    client = genai.Client(api_key=api_key)
    chat = client.chats.create(model="gemini-2.5-flash")

    with open(context_file_path, "r", encoding="utf-8") as f:
        diff_data = f.read()

    prompt = textwrap.dedent(f"""
    You are a Data Analysis AI. Your job is to analyze Git Commits and output strict JSON.

    INPUT DATA:
    {diff_data[:100000]}

    OUTPUT FORMAT (JSON ONLY):
    {{
        "projects": ["list", "of", "repos"],
        "completed_summary": "Concise technical summary of work completed...",
        "next_steps": "Inferred next steps..."
    }}
    """)

    try:
        response = chat.send_message(prompt)
        text = response.text.replace("```json", "").replace("```", "")
        print(text)
        return json.loads(text)
    except Exception as e:
        print(f"AI Error: {e}")
        return None


def update_csv(filename, data, month_label, author_name):
    headers = ["Month", "Name", "Project(s)", "Completed Tasks", "Next Steps"]

    file_exists = os.path.isfile(filename)
    try:
        with open(filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            if not file_exists:
                writer.writeheader()

            projects = data.get("projects", [])
            project_str = (
                ", ".join(projects) if isinstance(projects, list) else str(projects)
            )

            row = {
                "Month": month_label,
                "Name": author_name,
                "Project(s)": project_str,
                "Completed Tasks": data.get("completed_summary", ""),
                "Next Steps": data.get("next_steps", ""),
            }
            writer.writerow(row)
            print(f"Success! Report appended to: {filename}")
    except IOError as e:
        print(f"Error writing to file: {e}")


if __name__ == "__main__":
    args = parse_arguments()
    start_d, end_d, month_lbl = calculate_dates(args)

    all_content = []
    for repo in args.repos:
        repo_data = get_git_commits_with_diffs(args.aliases, start_d, end_d, repo)
        if repo_data:
            print(f"Extracted data from {repo}...")
            all_content.append(repo_data)

    if all_content:
        full_payload = "\n".join(all_content)
        with open(TEMP_DIFF_FILE, "w", encoding="utf-8") as f:
            f.write(full_payload)

        ai_data = run_gemini_pipeline(TEMP_DIFF_FILE)
        if ai_data:
            update_csv(args.output, ai_data, month_lbl, args.name)
            if os.path.exists(TEMP_DIFF_FILE):
                os.remove(TEMP_DIFF_FILE)
    else:
        print("No commits found.")
