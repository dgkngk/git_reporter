# Commit Reporter (AI-Automated Developer Reports) 📊

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Git](https://img.shields.io/badge/Git-Automation-F05032?style=for-the-badge&logo=git)
![Gemini AI](https://img.shields.io/badge/AI-Report%20Generation-8E75B2?style=for-the-badge&logo=googlebard)

**Commit Reporter** is an internal productivity tool designed to eliminate the manual overhead of writing monthly developer reports. It programmatically extracts a developer's contributions from multiple Git repositories and uses **Generative AI (Gemini)** to synthesize raw code changes into human-readable technical summaries.

This tool was developed to solve a real-world business problem: accurately tracking developer output across multiple projects without interrupting the development flow.

## 💡 How It Works

1.  **Mining**: The script executes `git log` with specific author aliases and date ranges across multiple repositories.
2.  **Context Filtering**: It automatically excludes noise (like `package-lock.json`, minified files, and assets) to keep the AI context focused on logic changes.
3.  **AI Orchestration**: The filtered diffs are piped into the **Gemini CLI**. A custom prompt instructs the LLM to extract project names, summarize technical accomplishments, and infer logical next steps.
4.  **Structured Output**: The resulting JSON is parsed and appended to a standardized **CSV Report Template**, ready for management review.

## 🚀 Key Features

*   **Multi-Repo Support**: Ingests data from several local repositories in a single run.
*   **Intelligent Summarization**: Transliterates complex diffs into concise, professional language (e.g., "Implemented JWT-based auth" instead of listing 5 modified files).
*   **Flexible Date Ranges**: Support for `--last-month` auto-selection or custom `--dates`.
*   **Clean Data Pipeline**: In-memory handling of large diffs with smart exclusion patterns.

## 🛠️ Usage

### Prerequisites
*   Python 3.x
*   Git installed and configured
*   Gemini CLI tool authenticated and in your `PATH`

### Command
```bash
python generate_commit_report.py \
  --name "Your Name" \
  --aliases "email@work.com, GithubUsername" \
  --repos /path/to/repo1 /path/to/repo2 \
  --last-month
```

## 🏗️ Technical Stack
*   **Language**: Python
*   **Automation**: Subprocess-based Git CLI integration
*   **AI**: Google Gemini Flash (via CLI)
*   **Data Formats**: JSON (Intermediary), CSV (Final Report)
