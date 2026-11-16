# 📊 Pakistan Social Audience & Campaign Intelligence Engine (Project 3)

**Author:** Kashif Hafeez  
**Student ID:** F2024376314  
**Framework:** Flask · SQLite 3NF · Scikit-Learn · Chart.js · Pandas  
**Repository:** [https://github.com/kashifkhan117401-bit/pakistan-audience-intel.git](https://github.com/kashifkhan117401-bit/pakistan-audience-intel.git)

---

## 🌟 Executive Overview

The **Pakistan Social Audience & Campaign Intelligence Engine** is a comprehensive multi-channel digital analytics platform and relational database management system. It unifies marketing campaign telemetry across **Facebook, Instagram, TikTok, and YouTube**, bridging big data engineering with quantitative marketing science.

### Key Milestones Integrated
1. **Third Normal Form (3NF) Relational Architecture:**  
   A normalized SQLite database (`data/campaign.db`) designed with 13 entity tables and 2 analytical views. Eliminates all repeating groups (1NF), partial dependencies (2NF), and transitive dependencies (3NF), calculating all derived marketing rates dynamically via SQL views.
2. **Real YouTube Sentiment Analyzer Integration (Project 2):**  
   **2,600+ real YouTube comments** scraped and classified with VADER and Roman Urdu sentiment lexicons from the *Gillette Campaign Video* (`UYaY2Kb_PKI`) are ingested into the database under post `YT-UYaY2Kb_PKI`. Accessible via the interactive YouTube Intelligence dashboard and Table B Comments browser.
3. **Ad Budget Optimizer Integration (Project 1):**  
   Multi-channel advertising budget optimization with power-law diminishing return response curves ($Revenue = a \cdot Spend^b$), exact bisection marginal return solver, live interactive campaign budget simulator, and 5 publication-quality analytical charts embedded directly into the frontend at `/budget`.

---

## 📸 Key Application Dashboards

| View | Route | Description |
|---|---|---|
| **Executive Dashboard** | `/` | Cross-platform audience sentiment, top topics, and engagement index |
| **Ad Budget Optimizer** | `/budget` | **Project 1 Integration** — Live budget slider, 5 charts, and 10M-record KPIs |
| **YouTube Sentiment** | `/youtube` | **Project 2 Integration** — 2,600+ real comments, polarity charts, like consensus |
| **Database & SQL Explorer** | `/database` | **3NF Relational DB** — Entity dictionary, PRAGMA schemas, and live SQL console |
| **Comments (Table B)** | `/comments` | Paginated browser across all 31,795 comments with topic/sentiment search |
| **Posts (Table A)** | `/posts` | 3,000 post records with calculated engagement rates and anomaly flags |
| **NLP Classifier Sandbox** | `/analyze` | Live interactive text classification for English, Urdu, and Roman Urdu |

---

## 🗂 Project Structure

```text
pak-audience-intel-main/
├── manage.py                          # CLI management entrypoint (setup, run, import)
├── app.py                             # Streamlit legacy interface
├── check_db.py                        # Database verification utility
├── generate_db_doc.py                 # Script to build Word documentation
├── Database_and_SQL_Queries_Documentation.docx # Comprehensive Word report
├── DATABASE_AND_QUERIES_DOCUMENTATION.md      # Full SQL schema & queries guide
├── requirements.txt                   # Project dependencies
├── campaign_engine/                   # Core application package
│   ├── config.py                      # Global path configuration & settings
│   ├── database.py                    # SQLite connection & cached DataFrames
│   ├── schema.sql                     # Full 1NF, 2NF, 3NF DDL schema
│   ├── pipeline.py                    # Data generation, clustering & anomaly detection
│   ├── importer.py                    # CSV & YouTube comments import pipeline
│   ├── nlp.py                         # Sentiment & intent classification
│   ├── analytics.py                   # Engagement rate & statistical helpers
│   ├── webapp.py                      # Flask web application & API endpoints
│   ├── static/
│   │   ├── css/app.css                # Dark/light theme styling
│   │   ├── js/app.js                  # Frontend interactions & Chart.js rendering
│   │   ├── charts/                    # Embedded Ad Budget Optimizer PNG charts
│   │   │   ├── 01_roas_by_platform.png
│   │   │   ├── 02_spend_vs_revenue.png
│   │   │   ├── 03_budget_share_current_vs_recommended.png
│   │   │   ├── 04_response_curves.png
│   │   │   └── 05_monthly_revenue_by_platform.png
│   │   └── vendor/chart.umd.js        # Bundled Chart.js library
│   └── templates/                     # Jinja2 frontend templates
│       ├── base.html                  # Responsive layout & sidebar navigation
│       ├── _macros.html               # Reusable UI components & chart canvas
│       ├── dashboard.html             # Executive overview dashboard
│       ├── budget.html                # Ad Budget Optimizer page
│       ├── youtube.html               # Real YouTube Sentiment Intelligence page
│       ├── database.html              # Interactive Database & SQL explorer
│       ├── comments.html              # Paginated Table B comments browser
│       ├── posts.html                 # Master Table A posts browser
│       ├── post_detail.html           # Individual post inspection view
│       ├── analyze.html               # Live NLP classifier sandbox
│       ├── audience.html              # Audience needs & sentiment view
│       ├── anomalies.html             # Unusual engagement & spike detection
│       ├── segments.html              # 14 K-Means audience clusters
│       ├── recommendations.html       # Automated strategic actions
│       └── about.html                 # Data provenance & methodology
└── data/
    ├── campaign.db                    # SQLite 3NF relational database
    ├── classified_comments.csv        # 2,600+ sentiment-classified YouTube comments
    ├── raw_comments.csv               # Raw scraped comment stream
    └── budget/                        # Ad Budget Optimizer results & benchmarks
```

---

## ⚙️ Quick Start & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- Virtual Environment tool (`venv` or `uv`)

### 2. Setup Environment
```bash
# Clone the repository
git clone https://github.com/kashifkhan117401-bit/pakistan-audience-intel.git
cd pakistan-audience-intel

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize Database & Populate 3NF Schema
```bash
# Builds SQLite database, runs ML clustering, and imports 2,600 YouTube comments
python manage.py setup
```

### 4. Launch the Web Application
```bash
python manage.py run --port 5000
```
Open your browser to: **http://127.0.0.1:5000**

---

## 🗄️ Relational 3NF Database & SQL Highlights

The database is accessible via the built-in SQL console at `/database`.

### Sample Query: Retrieve Real YouTube Comments by Consensus
```sql
SELECT c.comment_id, cu.display_name AS author, c.comment_text,
       s.sentiment_label, c.sentiment_score, c.like_count
FROM comment c
JOIN commenter cu ON cu.commenter_id = c.commenter_id
JOIN sentiment s ON s.sentiment_id = c.sentiment_id
WHERE c.post_id LIKE 'YT-%'
ORDER BY c.like_count DESC
LIMIT 10;
```

### Sample Query: Cross-Platform Engagement Rate
```sql
SELECT content_type, platform,
       COUNT(*) AS posts,
       ROUND(AVG(likes + comments_count + COALESCE(shares, 0)) * 100.0 / AVG(followers), 2) AS er_pct
FROM v_post_flat
WHERE followers > 0
GROUP BY content_type, platform
ORDER BY er_pct DESC;
```

---

## 📄 Documentation Files Included
- **[`Database_and_SQL_Queries_Documentation.docx`](Database_and_SQL_Queries_Documentation.docx):** Formal Word document containing full schema specifications, ER models, and CRUD queries for academic and project submission.
- **[`DATABASE_AND_QUERIES_DOCUMENTATION.md`](DATABASE_AND_QUERIES_DOCUMENTATION.md):** Markdown database manual and query reference.
