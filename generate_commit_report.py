import argparse
import csv
import datetime
import json
import os
import shutil
import subprocess
import sys
import textwrap

from dateutil.relativedelta import relativedelta

# --- CONFIGURATION ---
CLI_TOOL_NAME = "gemini"
TEMP_DIFF_FILE = "temp_commit_context.txt"

# Files to exclude to keep diffs readable and within limits
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
        description="Generate report using git diffs and Gemini CLI."
    )
    parser.add_argument("--name", required=True, help="Display name for the report.")
    parser.add_argument(
        "--aliases", required=True, help="Author aliases (comma-separated)."
    )
    parser.add_argument("--repos", nargs="+", default=["."], help="List of repo paths.")
    parser.add_argument(
        "--output", default="Developer_Report_Template.csv", help="Output CSV path."
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
    Pipes the temp file to the CLI with the specific user prompt.
    """
    cli_path = shutil.which(CLI_TOOL_NAME)
    if not cli_path:
        print(f"Error: '{CLI_TOOL_NAME}' not found in PATH.")
        sys.exit(1)

    # --- UPDATED PROMPT ---
    # 1. Removed "current_work"
    # 2. Changed "completed_tasks" (list) to "completed_summary" (string)
    # 3. Updated instructions to focus on summarization.
    prompt_text = textwrap.dedent("""
    You are a Data Analysis and JSON Extraction AI. Your ONLY job is to analyze the provided Git Commits and Diffs, then create a strict JSON object output.

    --- CONTENT EXPECTED
    key:value
    projects: List of project or repo names worked on
    completed_summary: A concise technical summary paragraph describing the work completed, bugs fixed, and features implemented.
    next_steps: A sentence inferring logical next steps based on the code changes
    ---

    --- RULES
    Output valid JSON only. Do NOT write an introduction, conclusion, or markdown analysis. Do NOT use markdown formatting.
    ---

    INPUT DATA TO PROCESS:
    """)

    # Flags first, then prompt
    cmd = [cli_path, "--output-format", "json", prompt_text]

    print(f"Piping context from {context_file_path} to Gemini...")

    try:
        with open(context_file_path, "r", encoding="utf-8") as f:
            result = subprocess.run(
                cmd,
                stdin=f,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
            )

        raw_output = result.stdout.strip()

        try:
            parsed = json.loads(raw_output)

            if "response" in parsed:
                inner = parsed["response"]
                if isinstance(inner, str):
                    print(inner)
                    return json.loads(inner)
                return inner
            return parsed

        except json.JSONDecodeError:
            print("Warning: AI output was not valid JSON.")
            print(f"Raw Output start: {raw_output[:500]}...")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Gemini CLI Error: {e.stderr}")
        return None


def update_csv(filename, data, month_label, author_name):
    # Headers match your provided template
    headers = [
        "Month",
        "Name",
        "Project(s)",
        "Current Work",
        "Completed Tasks / Fixes",
        "Next Steps / Plans for Next Month",
    ]

    file_exists = os.path.isfile(filename)
    try:
        with open(filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            if not file_exists:
                writer.writeheader()

            # Join projects list if it exists
            projects = data.get("projects", [])
            if isinstance(projects, list):
                project_str = ", ".join(projects)
            else:
                project_str = str(projects)

            # Write the row
            # Note: 'Current Work' is left empty ("") as requested.
            row = {
                "Month": month_label,
                "Name": author_name,
                "Project(s)": project_str,
                "Current Work": "",
                "Completed Tasks / Fixes": data.get("completed_summary", ""),
                "Next Steps / Plans for Next Month": data.get("next_steps", ""),
            }
            writer.writerow(row)
            print(f"Success! Report appended to: {filename}")
    except IOError as e:
        print(f"Error writing to file: {e}")


if __name__ == "__main__":
    args = parse_arguments()
    start_d, end_d, month_lbl = calculate_dates(args)
    print(f"Range: {start_d} to {end_d}")

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
    else:
        print("No commits found.")
