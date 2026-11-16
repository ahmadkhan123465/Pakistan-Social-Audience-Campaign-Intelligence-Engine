import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_document():
    doc = Document()
    
    # 1 inch margins
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)
        
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    # Title & Header
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("Database Architecture & SQL Queries Documentation")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    run_sub = sub_p.add_run("1NF, 2NF, 3NF Normalization, YouTube Sentiment Data Integration & CRUD Query Reference")
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    # Metadata Card
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    col_widths = [Inches(3.2), Inches(3.2)]
    metadata = [
        [("Student Name:", " Kashif Hafeez"), ("Student ID:", " F2024376314")],
        [("Project:", " Campaign Intelligence Engine (Project 3)"), ("Database:", " SQLite 3.x (data/campaign.db)")]
    ]
    for r_idx, row in enumerate(meta_table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = col_widths[c_idx]
            set_cell_background(cell, "F0F4F8")
            set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            label, val = metadata[r_idx][c_idx]
            r1 = p.add_run(label)
            r1.bold = True
            r1.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
            r2 = p.add_run(val)
            r2.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        r = h.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        r = h.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(12.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x5A, 0x9E)
        return h

    def add_code(text):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.right_indent = Inches(0.2)
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(text)
        r.font.name = 'Consolas'
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0x11, 0x18, 0x27)
        return p

    # 1. Normalization
    add_h1("1. Relational Normalization Architecture (1NF, 2NF, 3NF)")
    doc.add_paragraph(
        "The project database (campaign.db) is modeled under strict relational database theory principles to ensure "
        "referential integrity, eliminate duplicate records, and prevent update/deletion anomalies:"
    )
    doc.add_paragraph(
        "• 1NF (First Normal Form): All table attributes store scalar, atomic values. Repeating arrays (such as multiple comments on a post) are decoupled into dedicated child tables with foreign key relationships. Every entity possesses an explicit Primary Key.\n"
        "• 2NF (Second Normal Form): Eliminates partial functional dependencies. In relationships where multiple keys exist (such as brand and platform), attributes like follower count depend on the composite pair and are isolated in the 'account' table (account_id PK with UNIQUE(brand_id, platform_id)).\n"
        "• 3NF (Third Normal Form): Eliminates transitive dependencies (X -> Y -> Z). Categorical attributes (brand names, platform names, topic categories, languages, sentiments, purchase intents) are normalized into standalone dimension tables. Furthermore, derived numbers (such as engagement rate and totals) are never persisted; they are computed dynamically via SQL views."
    )

    # 2. Database Entities Table
    add_h1("2. Database Entity Dictionary (All 13 Entities)")
    entities = [
        ("brand", "Lookup / Dimension", "brand_id (PK), brand_name (UNIQUE)", "Stores unique fashion and corporate brand names."),
        ("platform", "Lookup / Dimension", "platform_id (PK), platform_name (UNIQUE)", "Social platforms: Instagram, Facebook, TikTok, YouTube."),
        ("campaign", "Lookup / Dimension", "campaign_id (PK), campaign_name (UNIQUE)", "Campaign designations (e.g. Summer Lawn, Gillette ad)."),
        ("content_type", "Lookup / Dimension", "content_type_id (PK), content_type_name", "Content formats: Video ad, Image carousel, Reel, Story."),
        ("product_category", "Lookup / Dimension", "category_id (PK), category_name", "Category classification (e.g. Lawn suit, Advertisement)."),
        ("language_type", "Lookup / Dimension", "language_id (PK), language_name", "Detected languages: English, Urdu, Roman Urdu, Mixed."),
        ("sentiment", "Lookup / Dimension", "sentiment_id (PK), sentiment_label", "Sentiment categories: Positive, Neutral, Negative."),
        ("purchase_intent", "Lookup / Dimension", "intent_id (PK), intent_label", "Intent classification: High, Medium, Low, None."),
        ("topic", "Lookup / Dimension", "topic_id (PK), topic_name, theme", "High-level themes (Quality, Delivery, Price, Boycott)."),
        ("data_source", "Provenance Metadata", "source_id (PK), provenance, source_url", "Tracks observed (real) vs. simulated campaign data."),
        ("account", "Relational Mapping", "account_id (PK), brand_id (FK), platform_id (FK)", "Tracks brand followers per platform (2NF resolution)."),
        ("post", "Table A (Master Entity)", "post_id (PK), account_id (FK), likes, comments", "3,000+ posts tracking metrics, views, shares, age."),
        ("comment", "Table B (Child Entity)", "comment_id (PK), post_id (FK), sentiment_id", "31,795 comments with polarity, scores, like counts.")
    ]

    ent_t = doc.add_table(rows=len(entities) + 1, cols=4)
    ent_t.alignment = WD_TABLE_ALIGNMENT.CENTER
    ent_headers = ["Entity Name", "Type", "Key Columns", "Description"]
    col_w = [Inches(1.2), Inches(1.3), Inches(2.2), Inches(1.8)]

    for c_i, h_txt in enumerate(ent_headers):
        c = ent_t.rows[0].cells[c_i]
        c.width = col_w[c_i]
        set_cell_background(c, "1B365D")
        set_cell_margins(c, 80, 80, 80, 80)
        p = c.paragraphs[0]
        r = p.add_run(h_txt)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_i, (e_name, e_type, e_cols, e_desc) in enumerate(entities):
        row = ent_t.rows[r_i + 1]
        bg = "F9FBFD" if r_i % 2 == 0 else "FFFFFF"
        for c_i, val in enumerate([e_name, e_type, e_cols, e_desc]):
            c = row.cells[c_i]
            c.width = col_w[c_i]
            set_cell_background(c, bg)
            set_cell_margins(c, 60, 60, 60, 60)
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(val)
            r.font.size = Pt(8.5)
            if c_i == 0: r.bold = True

    # 3. Data Retrieval Queries
    add_h1("3. Core Data Retrieval Queries (SELECT & Reporting)")
    doc.add_paragraph("The queries below are used directly by the frontend views and the interactive SQL console:")

    add_h2("Query 1: Retrieving YouTube Sentiment Analyzer Comments (2,600+ Real Comments)")
    add_code(
        "SELECT c.comment_id, c.external_id AS yt_comment_id, cu.display_name AS author,\n"
        "       c.comment_text, s.sentiment_label, c.sentiment_score, c.like_count, c.published_at\n"
        "FROM comment c\n"
        "JOIN commenter cu ON cu.commenter_id = c.commenter_id\n"
        "JOIN sentiment s ON s.sentiment_id = c.sentiment_id\n"
        "WHERE c.post_id LIKE 'YT-%'\n"
        "ORDER BY c.like_count DESC\n"
        "LIMIT 20;"
    )

    add_h2("Query 2: YouTube Sentiment Distribution & Like Consensus")
    add_code(
        "SELECT s.sentiment_label,\n"
        "       COUNT(*) AS comment_count,\n"
        "       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM comment WHERE post_id LIKE 'YT-%'), 1) AS pct_share,\n"
        "       SUM(c.like_count) AS total_likes,\n"
        "       ROUND(AVG(c.like_count), 1) AS avg_likes_per_comment\n"
        "FROM comment c\n"
        "JOIN sentiment s ON s.sentiment_id = c.sentiment_id\n"
        "WHERE c.post_id LIKE 'YT-%'\n"
        "GROUP BY s.sentiment_label\n"
        "ORDER BY comment_count DESC;"
    )

    add_h2("Query 3: Normalized 4-Table Join for Post Engagement Intelligence")
    add_code(
        "SELECT p.post_id, b.brand_name, pl.platform_name, p.comments_count, p.likes, a.followers\n"
        "FROM post p\n"
        "JOIN account a ON a.account_id = p.account_id\n"
        "JOIN brand b ON b.brand_id = a.brand_id\n"
        "JOIN platform pl ON pl.platform_id = a.platform_id\n"
        "ORDER BY p.comments_count DESC\n"
        "LIMIT 15;"
    )

    add_h2("Query 4: Dynamic Engagement Rate per Content Format (Using SQL View)")
    add_code(
        "SELECT content_type, platform,\n"
        "       COUNT(*) AS total_posts,\n"
        "       ROUND(AVG(likes + comments_count + COALESCE(shares, 0)) * 100.0 / AVG(followers), 2) AS calculated_er_pct\n"
        "FROM v_post_flat\n"
        "WHERE followers > 0\n"
        "GROUP BY content_type, platform\n"
        "ORDER BY calculated_er_pct DESC;"
    )

    add_h2("Query 5: Topic Mix and Sentiment Polarity per Brand")
    add_code(
        "SELECT p.brand, c.topic,\n"
        "       COUNT(*) AS total_comments,\n"
        "       ROUND(AVG(c.sentiment_score), 2) AS avg_polarity,\n"
        "       SUM(CASE WHEN c.sentiment = 'Positive' THEN 1 ELSE 0 END) AS positive_cnt,\n"
        "       SUM(CASE WHEN c.sentiment = 'Negative' THEN 1 ELSE 0 END) AS negative_cnt\n"
        "FROM v_comment_flat c\n"
        "JOIN v_post_flat p ON p.post_id = c.post_id\n"
        "GROUP BY p.brand, c.topic\n"
        "ORDER BY total_comments DESC\n"
        "LIMIT 15;"
    )

    # 4. Data Mutation Queries
    add_h1("4. Data Mutation & Management Queries (INSERT, UPDATE, DELETE)")

    add_h2("Insert: Importing Analyzed Comments into 3NF Schema")
    add_code(
        "INSERT INTO comment (\n"
        "    post_id, external_id, commenter_id, comment_text, published_at, like_count, reply_count,\n"
        "    language_id, topic_id, sentiment_id, sentiment_score, sentiment_confidence, intent_id\n"
        ") VALUES (\n"
        "    'YT-UYaY2Kb_PKI', 'UgxXJ-Sample123', 142,\n"
        "    'Great razor but price is too high compared to local alternatives.',\n"
        "    '2024-03-12T14:32:00Z', 14, 2, 1, 3, 2, -0.05, 0.89, 2\n"
        ");"
    )

    add_h2("Update: Synchronizing Post Totals from Child Comments")
    add_code(
        "UPDATE post\n"
        "SET comments_count = (\n"
        "    SELECT COUNT(*) FROM comment c WHERE c.post_id = post.post_id\n"
        ")\n"
        "WHERE post_id LIKE 'YT-%';"
    )

    add_h2("Update: Correcting Sentiment Polarity After Model Review")
    add_code(
        "UPDATE comment\n"
        "SET sentiment_id = (SELECT sentiment_id FROM sentiment WHERE sentiment_label = 'Negative'),\n"
        "    sentiment_score = -0.75,\n"
        "    sentiment_confidence = 0.98\n"
        "WHERE comment_id = 104;"
    )

    add_h2("Delete: Referential Cascade Deletions")
    add_code(
        "-- Because PRAGMA foreign_keys = ON is enabled,\n"
        "-- deleting a post automatically removes all related comments and anomalies via CASCADE:\n"
        "DELETE FROM post WHERE post_id = 'P_TEMP_TEST_01';"
    )

    # 5. Ad Budget Optimizer & Frontend Integration
    add_h1("5. Integration of Ad Budget Optimizer & Frontend Visualizations")
    doc.add_paragraph(
        "In addition to audience sentiment analysis, Project 3 incorporates the multi-channel advertising budget optimizer:\n"
        "• Responsive Web Interface: Accessible at '/budget' in the web app, featuring a live interactive budget slider allowing marketers to simulate total budgets from Rs. 100,000 to Rs. 10,000,000.\n"
        "• High-Resolution Analytical Charts: All 5 pipeline charts (ROAS by platform, spend vs revenue, budget share current vs recommended, diminishing return response curves, and monthly revenue breakdown) are served from '/static/charts/' with interactive zoom.\n"
        "• Cross-Engine Performance Benchmarks: Benchmarking results comparing Pandas, Simulated MapReduce (multiprocessing byte splits), and PySpark across 10K to 10M records are embedded directly in the frontend table.\n"
        "• Real Scraped Data Validation: The 2,600 comments from Project 2 (YouTube sentiment analyzer) are fully loaded into the SQLite relational database under post 'YT-UYaY2Kb_PKI', accessible via Table B and the dedicated '/youtube' analytics tab."
    )

    output_filename = "Database_and_SQL_Queries_Documentation.docx"
    doc.save(output_filename)
    print(f"Successfully generated: {output_filename}")

if __name__ == "__main__":
    create_document()

