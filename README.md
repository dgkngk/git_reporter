# Commit Reporter (AI-Automated Developer Reports) 📊

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Git](https://img.shields.io/badge/Git-Automation-F05032?style=for-the-badge&logo=git)
![Gemini AI](https://img.shields.io/badge/AI-Report%20Generation-8E75B2?style=for-the-badge&logo=googlebard)

**Commit Reporter** is a productivity tool designed to eliminate the manual overhead of writing monthly developer reports. It programmatically extracts a developer's contributions from multiple Git repositories and uses **Google's Gemini 1.5 Flash** to synthesize raw code changes into human-readable business value summaries.

This tool was developed to solve a real-world business problem: accurately tracking developer output across multiple projects without interrupting the development flow.

## 💡 How It Works

1.  **Mining**: Executes `git log` across local repositories to capture developer activity.
2.  **Context Filtering**: Automatically excludes noise (lockfiles, assets, minified code) to keep the context window focused on logic.
3.  **AI Orchestration**: Pipes filtered diffs into the **Gemini Python SDK** to generate a "Story Point" style summary.
4.  **Structured Output**: Appends the analysis to a CSV report, ready for management.

## 🚀 Key Features

* **Multi-Repo Support**: Ingests data from several local repositories in a single run.
* **Privacy First**: Runs locally on your machine; code is sent ephemerally to the API and not stored.
* **Smart Summarization**: Converts "Refactored auth middleware" (technical) into "Improved login security and reduced latency by 20%" (business value).

## 🛠️ Usage

### Prerequisites
1.  Python 3.x installed.
2.  A Google Cloud API Key (free tier works).

### Setup
```bash
pip install -r requirements.txt
echo "GOOGLE_API_KEY=your_key_here" > .env
```

### Run
```bash
python generate_commit_report.py \
  --name "Dogukan" \
  --aliases "dogukan@example.com, github_username" \
  --repos ../my-project ../another-project \
  --last-month
```

## 🏗️ Technical Stack
*   **Language**: Python
*   **Automation**: Subprocess-based Git CLI integration
*   **SDK**: google-genai (V2 SDK)
*   **AI**: Google Gemini 2.5 Flash
*   **Data Formats**: JSON (Intermediary), CSV (Final Report)
