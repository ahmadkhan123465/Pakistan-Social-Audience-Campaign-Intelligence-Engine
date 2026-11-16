# 🗄️ Database Schema & SQL Queries Documentation (1NF, 2NF, 3NF)

**Author:** Kashif Hafeez  
**Student ID:** F2024376314  
**Project:** Pakistan Social Audience & Campaign Intelligence Engine (Project 3)  
**Database File:** `data/campaign.db` (SQLite 3.x)  
**Integrated Data:** 
- 3,000 Social Media Posts across Instagram, Facebook, TikTok, and YouTube
- 31,795 Comments total, including **2,600+ Real Scraped YouTube Comments** from the YouTube Sentiment Analyzer (Project 2)
- Multi-Channel Ad Budget Optimization models and benchmarks (Project 1)

---

## 📋 Table of Contents
1. [Relational Normalization Architecture (1NF, 2NF, 3NF)](#1-relational-normalization-architecture-1nf-2nf-3nf)
2. [Complete Schema DDL (All 13 Entities & 2 Views)](#2-complete-schema-ddl-all-13-entities--2-views)
3. [Data Retrieval Queries (SELECT & Analytics)](#3-data-retrieval-queries-select--analytics)
   - [Basic Entity Retrievals](#basic-entity-retrievals)
   - [Multi-Table Normalized Joins](#multi-table-normalized-joins)
   - [YouTube Sentiment Analyzer Specific Queries (2,600+ Comments)](#youtube-sentiment-analyzer-specific-queries-2600-comments)
   - [Aggregated Marketing KPI & Engagement Queries](#aggregated-marketing-kpi--engagement-queries)
   - [Audience Segmentation & Anomaly Queries](#audience-segmentation--anomaly-queries)
4. [Data Mutation & Management Queries (INSERT, UPDATE, DELETE)](#4-data-mutation--management-queries-insert-update-delete)
   - [Lookup & Provenance Insertion](#lookup--provenance-insertion)
   - [Importing Real YouTube Sentiment Comments](#importing-real-youtube-sentiment-comments)
   - [Updating Sentiments, Engagement & Metrics](#updating-sentiments-engagement--metrics)
   - [Pruning, Archiving & Cascade Deletions](#pruning-archiving--cascade-deletions)
5. [Integrity Constraints & Indexing Strategy](#5-integrity-constraints--indexing-strategy)

---

## 1. Relational Normalization Architecture (1NF, 2NF, 3NF)

The schema has been designed under strict relational theory rules to eliminate data redundancy, prevent insertion/update/deletion anomalies, and guarantee referential integrity:

### 1NF (First Normal Form)
- **Atomicity:** Every attribute in every table stores a single, indivisible scalar value.
- **No Repeating Groups:** Instead of storing multiple comments, tags, or topics inside a single post row (e.g. as comma-separated strings or arrays), comments are extracted into their own dedicated child table (`comment`).
- **Primary Keys:** Every single entity possesses an explicit Primary Key (`post_id`, `comment_id`, `brand_id`, etc.).

### 2NF (Second Normal Form)
- **Full Functional Dependency on Primary Key:** Every non-key column is fully functionally dependent on the *entire* primary key, eliminating partial dependencies.
- In composite relationships, such as a brand operating on a platform:
  - Account followers depend on both `(brand_id, platform_id)`. Rather than storing `followers` redundantly in each `post`, it is isolated in the `account` entity (`account_id` PK with a `UNIQUE(brand_id, platform_id)` constraint).
  - Every attribute in `post` (`likes`, `comments_count`, `shares`) depends solely on `post_id`.

### 3NF (Third Normal Form)
- **No Transitive Functional Dependencies:** Non-key attributes must never depend on other non-key attributes ($X \rightarrow Y \rightarrow Z$).
- In raw spreadsheets, a comment row typically includes the platform name, brand name, topic category, language name, and sentiment label. Storing these text strings directly in the comment table creates transitive dependencies: `comment_id -> post_id -> account_id -> platform_name`.
- In this 3NF schema, all categorical dimensions are normalized into dedicated lookup tables (`brand`, `platform`, `campaign`, `content_type`, `product_category`, `language_type`, `sentiment`, `purchase_intent`, `topic`). The `comment` and `post` tables hold solely foreign key integer IDs.
- **No Persisted Derived Numbers:** Metrics such as `engagement_rate`, `comment_rate`, and `er_index` are **not** stored as physical table columns. They are calculated dynamically using SQL views (`v_post_flat`, `v_comment_flat`) to prevent synchronization anomalies.

---

## 2. Complete Schema DDL (All 13 Entities & 2 Views)

```sql
PRAGMA foreign_keys = ON;

-- 1. Dimension & Lookup Entities
CREATE TABLE brand (
    brand_id        INTEGER PRIMARY KEY,
    brand_name      TEXT NOT NULL UNIQUE
);

CREATE TABLE platform (
    platform_id     INTEGER PRIMARY KEY,
    platform_name   TEXT NOT NULL UNIQUE
);

CREATE TABLE campaign (
    campaign_id     INTEGER PRIMARY KEY,
    campaign_name   TEXT NOT NULL UNIQUE
);

CREATE TABLE content_type (
    content_type_id INTEGER PRIMARY KEY,
    content_type_name TEXT NOT NULL UNIQUE
);

CREATE TABLE product_category (
    category_id     INTEGER PRIMARY KEY,
    category_name   TEXT NOT NULL UNIQUE
);

CREATE TABLE language_type (
    language_id     INTEGER PRIMARY KEY,
    language_name   TEXT NOT NULL UNIQUE
);

CREATE TABLE sentiment (
    sentiment_id    INTEGER PRIMARY KEY,
    sentiment_label TEXT NOT NULL UNIQUE
);

CREATE TABLE purchase_intent (
    intent_id       INTEGER PRIMARY KEY,
    intent_label    TEXT NOT NULL UNIQUE
);

CREATE TABLE topic (
    topic_id        INTEGER PRIMARY KEY,
    topic_name      TEXT NOT NULL UNIQUE,
    theme           TEXT NOT NULL
);

-- 2. Data Provenance Entity
CREATE TABLE data_source (
    source_id        INTEGER PRIMARY KEY,
    source_name      TEXT NOT NULL UNIQUE,
    provenance       TEXT NOT NULL CHECK (provenance IN ('observed', 'simulated')),
    source_url       TEXT,
    collected_on     TEXT NOT NULL,
    reuse_permission TEXT,
    include_in_analysis INTEGER NOT NULL DEFAULT 1 CHECK (include_in_analysis IN (0, 1))
);

-- 3. Brand Account Entity (2NF Resolution)
CREATE TABLE account (
    account_id  INTEGER PRIMARY KEY,
    brand_id    INTEGER NOT NULL REFERENCES brand(brand_id),
    platform_id INTEGER NOT NULL REFERENCES platform(platform_id),
    followers   INTEGER CHECK (followers IS NULL OR followers >= 0),
    UNIQUE (brand_id, platform_id)
);

-- 4. Table A: Social Media Posts Entity
CREATE TABLE post (
    post_id         TEXT PRIMARY KEY,
    account_id      INTEGER NOT NULL REFERENCES account(account_id),
    campaign_id     INTEGER NOT NULL REFERENCES campaign(campaign_id),
    content_type_id INTEGER NOT NULL REFERENCES content_type(content_type_id),
    category_id     INTEGER NOT NULL REFERENCES product_category(category_id),
    source_id       INTEGER NOT NULL REFERENCES data_source(source_id),
    likes           INTEGER CHECK (likes IS NULL OR likes >= 0),
    comments_count  INTEGER NOT NULL CHECK (comments_count >= 0),
    shares          INTEGER CHECK (shares IS NULL OR shares >= 0),
    views           INTEGER CHECK (views  IS NULL OR views  >= 0),
    days_since_post INTEGER CHECK (days_since_post IS NULL OR days_since_post >= 0)
);

-- 5. Audience Segments Entity (Clusters)
CREATE TABLE segment (
    segment_id       INTEGER PRIMARY KEY,
    segment_name     TEXT NOT NULL,
    description      TEXT NOT NULL,
    suggested_action TEXT NOT NULL,
    top_terms        TEXT NOT NULL
);

-- 6. Commenters Entity
CREATE TABLE commenter (
    commenter_id INTEGER PRIMARY KEY,
    display_name TEXT NOT NULL UNIQUE
);

-- 7. Table B: Comments Entity
CREATE TABLE comment (
    comment_id           INTEGER PRIMARY KEY,
    post_id              TEXT    NOT NULL REFERENCES post(post_id) ON DELETE CASCADE,
    external_id          TEXT    UNIQUE,
    commenter_id         INTEGER REFERENCES commenter(commenter_id),
    comment_text         TEXT    NOT NULL,
    published_at         TEXT,
    like_count           INTEGER CHECK (like_count  IS NULL OR like_count  >= 0),
    reply_count          INTEGER CHECK (reply_count IS NULL OR reply_count >= 0),
    language_id          INTEGER NOT NULL REFERENCES language_type(language_id),
    topic_id             INTEGER NOT NULL REFERENCES topic(topic_id),
    sentiment_id         INTEGER NOT NULL REFERENCES sentiment(sentiment_id),
    sentiment_score      REAL    CHECK (sentiment_score IS NULL OR sentiment_score BETWEEN -1 AND 1),
    sentiment_confidence REAL    CHECK (sentiment_confidence IS NULL OR sentiment_confidence BETWEEN 0 AND 1),
    intent_id            INTEGER NOT NULL REFERENCES purchase_intent(intent_id),
    segment_id           INTEGER REFERENCES segment(segment_id)
);

-- 8. Post Anomalies Entity
CREATE TABLE post_anomaly (
    post_id       TEXT PRIMARY KEY REFERENCES post(post_id) ON DELETE CASCADE,
    anomaly_score REAL NOT NULL,
    anomaly_type  TEXT NOT NULL,
    reason        TEXT NOT NULL
);

-- 9. Strategic Recommendations Entity
CREATE TABLE recommendation (
    rec_id     INTEGER PRIMARY KEY,
    area       TEXT NOT NULL CHECK (area IN ('Content','Promotions','Customer service','Campaign testing')),
    priority   TEXT NOT NULL CHECK (priority IN ('High','Medium','Low')),
    title      TEXT NOT NULL,
    evidence   TEXT NOT NULL,
    action     TEXT NOT NULL,
    segment_id INTEGER REFERENCES segment(segment_id)
);

-- Indexes for Query Acceleration
CREATE INDEX ix_post_account  ON post(account_id);
CREATE INDEX ix_post_campaign ON post(campaign_id);
CREATE INDEX ix_comment_post  ON comment(post_id);
CREATE INDEX ix_comment_topic ON comment(topic_id);
CREATE INDEX ix_comment_seg   ON comment(segment_id);
CREATE INDEX ix_comment_pub   ON comment(published_at);

-- 10. Relational Views (De-normalized Read Models)
CREATE VIEW v_post_flat AS
SELECT p.post_id, b.brand_name AS brand, pl.platform_name AS platform,
       c.campaign_name AS campaign, ct.content_type_name AS content_type,
       pc.category_name AS product_category, a.followers,
       p.likes, p.comments_count, p.shares, p.views, p.days_since_post,
       ds.source_name, ds.provenance, ds.include_in_analysis
FROM post p
JOIN account a          ON a.account_id = p.account_id
JOIN brand b            ON b.brand_id = a.brand_id
JOIN platform pl        ON pl.platform_id = a.platform_id
JOIN campaign c         ON c.campaign_id = p.campaign_id
JOIN content_type ct    ON ct.content_type_id = p.content_type_id
JOIN product_category pc ON pc.category_id = p.category_id
JOIN data_source ds     ON ds.source_id = p.source_id;

CREATE VIEW v_comment_flat AS
SELECT cm.comment_id, cm.post_id, cm.external_id, cm.comment_text, cu.display_name AS commenter,
       cm.published_at, cm.like_count, cm.reply_count, cm.sentiment_score, cm.sentiment_confidence,
       l.language_name AS language_type, t.topic_name AS topic, t.theme,
       s.sentiment_label AS sentiment, i.intent_label AS purchase_intent,
       cm.segment_id, sg.segment_name AS segment
FROM comment cm
JOIN language_type l   ON l.language_id = cm.language_id
JOIN topic t           ON t.topic_id = cm.topic_id
JOIN sentiment s       ON s.sentiment_id = cm.sentiment_id
JOIN purchase_intent i ON i.intent_id = cm.intent_id
LEFT JOIN segment sg   ON sg.segment_id = cm.segment_id
LEFT JOIN commenter cu ON cu.commenter_id = cm.commenter_id;
```

---

## 3. Data Retrieval Queries (SELECT & Analytics)

### Basic Entity Retrievals
```sql
-- Retrieve total record count per table
SELECT 'post' AS entity, COUNT(*) AS total_rows FROM post
UNION ALL
SELECT 'comment', COUNT(*) FROM comment
UNION ALL
SELECT 'commenter', COUNT(*) FROM commenter
UNION ALL
SELECT 'brand', COUNT(*) FROM brand
UNION ALL
SELECT 'account', COUNT(*) FROM account;
```

### Multi-Table Normalized Joins
```sql
-- 4-Table Join: Posts with Account, Brand, and Platform Details
SELECT p.post_id, b.brand_name, pl.platform_name, p.comments_count, p.likes, a.followers
FROM post p
JOIN account a ON a.account_id = p.account_id
JOIN brand b ON b.brand_id = a.brand_id
JOIN platform pl ON pl.platform_id = a.platform_id
ORDER BY p.comments_count DESC
LIMIT 15;
```

### YouTube Sentiment Analyzer Specific Queries (2,600+ Comments)
```sql
-- 1. Retrieve all 2,600 scraped YouTube comments with author and polarity
SELECT c.comment_id, c.external_id AS yt_comment_id, cu.display_name AS author,
       c.comment_text, s.sentiment_label, c.sentiment_score, c.like_count, c.published_at
FROM comment c
JOIN commenter cu ON cu.commenter_id = c.commenter_id
JOIN sentiment s ON s.sentiment_id = c.sentiment_id
WHERE c.post_id LIKE 'YT-%'
ORDER BY c.like_count DESC
LIMIT 20;

-- 2. Sentiment distribution across YouTube comments
SELECT s.sentiment_label,
       COUNT(*) AS comment_count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM comment WHERE post_id LIKE 'YT-%'), 1) AS pct_share,
       SUM(c.like_count) AS total_likes,
       ROUND(AVG(c.like_count), 1) AS avg_likes_per_comment
FROM comment c
JOIN sentiment s ON s.sentiment_id = c.sentiment_id
WHERE c.post_id LIKE 'YT-%'
GROUP BY s.sentiment_label
ORDER BY comment_count DESC;

-- 3. Top negative high-consensus pushback comments
SELECT cu.display_name AS author, c.comment_text, c.sentiment_score, c.like_count
FROM comment c
JOIN commenter cu ON cu.commenter_id = c.commenter_id
JOIN sentiment s ON s.sentiment_id = c.sentiment_id
WHERE c.post_id LIKE 'YT-%' AND s.sentiment_label = 'Negative'
ORDER BY c.like_count DESC
LIMIT 10;
```

### Aggregated Marketing KPI & Engagement Queries
```sql
-- Compute Dynamic Engagement Rate per Content Format and Platform
SELECT content_type, platform,
       COUNT(*) AS total_posts,
       ROUND(AVG(likes + comments_count + COALESCE(shares, 0)) * 100.0 / AVG(followers), 2) AS calculated_er_pct
FROM v_post_flat
WHERE followers > 0
GROUP BY content_type, platform
ORDER BY calculated_er_pct DESC;

-- Topic volume and sentiment breakdown per brand
SELECT p.brand, c.topic,
       COUNT(*) AS total_comments,
       ROUND(AVG(c.sentiment_score), 2) AS avg_polarity,
       SUM(CASE WHEN c.sentiment = 'Positive' THEN 1 ELSE 0 END) AS positive_cnt,
       SUM(CASE WHEN c.sentiment = 'Negative' THEN 1 ELSE 0 END) AS negative_cnt
FROM v_comment_flat c
JOIN v_post_flat p ON p.post_id = c.post_id
GROUP BY p.brand, c.topic
ORDER BY total_comments DESC
LIMIT 20;
```

### Audience Segmentation & Anomaly Queries
```sql
-- Retrieve Audience Segment Sizes and Strategic Suggested Actions
SELECT s.segment_id, s.segment_name, COUNT(c.comment_id) AS total_audience,
       s.top_terms, s.suggested_action
FROM segment s
LEFT JOIN comment c ON c.segment_id = s.segment_id
GROUP BY s.segment_id
ORDER BY total_audience DESC;

-- Flagged Viral Spikes and Engagement Anomalies
SELECT a.post_id, p.brand, p.platform, a.anomaly_type,
       ROUND(a.anomaly_score, 3) AS anomaly_score, a.reason
FROM post_anomaly a
JOIN v_post_flat p ON p.post_id = a.post_id
ORDER BY a.anomaly_score DESC;
```

---

## 4. Data Mutation & Management Queries (INSERT, UPDATE, DELETE)

### Lookup & Provenance Insertion
```sql
-- Insert a new advertising platform if not exists
INSERT OR IGNORE INTO platform (platform_name) VALUES ('Snapchat');

-- Register a new data source
INSERT INTO data_source (source_name, provenance, source_url, collected_on, reuse_permission, include_in_analysis)
VALUES ('TikTok Campaign Ads Export', 'observed', 'https://ads.tiktok.com', '2026-11-16', 'Authorized internal analytics use', 1);
```

### Importing Real YouTube Sentiment Comments
```sql
-- Step 1: Insert Parent Post for the YouTube Video
INSERT OR IGNORE INTO post (post_id, account_id, campaign_id, content_type_id, category_id, source_id, likes, comments_count)
VALUES (
    'YT-UYaY2Kb_PKI',
    (SELECT account_id FROM account WHERE brand_id = 5 AND platform_id = 4),
    (SELECT campaign_id FROM campaign WHERE campaign_name = 'Gillette ad (YouTube)'),
    (SELECT content_type_id FROM content_type WHERE content_type_name = 'Video ad'),
    (SELECT category_id FROM product_category WHERE category_name = 'Advertisement (non-fashion)'),
    2,
    NULL,
    2600
);

-- Step 2: Insert or Get Commenter
INSERT OR IGNORE INTO commenter (display_name) VALUES ('JohnDoe_Reviewer');

-- Step 3: Insert Analyzed Comment
INSERT OR IGNORE INTO comment (
    post_id, external_id, commenter_id, comment_text, published_at, like_count, reply_count,
    language_id, topic_id, sentiment_id, sentiment_score, sentiment_confidence, intent_id
) VALUES (
    'YT-UYaY2Kb_PKI',
    'UgxXJ-SampleID123',
    (SELECT commenter_id FROM commenter WHERE display_name = 'JohnDoe_Reviewer'),
    'Great razor but price is too high compared to local alternatives.',
    '2024-03-12T14:32:00Z',
    14,
    2,
    (SELECT language_id FROM language_type WHERE language_name = 'English'),
    (SELECT topic_id FROM topic WHERE topic_name = 'Price / value'),
    (SELECT sentiment_id FROM sentiment WHERE sentiment_label = 'Neutral'),
    -0.05,
    0.89,
    (SELECT intent_id FROM purchase_intent WHERE intent_label = 'Low')
);
```

### Updating Sentiments, Engagement & Metrics
```sql
-- Update sentiment score after manual model review
UPDATE comment
SET sentiment_id = (SELECT sentiment_id FROM sentiment WHERE sentiment_label = 'Negative'),
    sentiment_score = -0.75,
    sentiment_confidence = 0.98
WHERE comment_id = 42;

-- Synchronize post comment count from actual stored rows
UPDATE post
SET comments_count = (
    SELECT COUNT(*) FROM comment c WHERE c.post_id = post.post_id
)
WHERE post_id LIKE 'YT-%';

-- Re-assign audience segment based on updated clustering
UPDATE comment
SET segment_id = 3
WHERE topic_id IN (SELECT topic_id FROM topic WHERE theme = 'Pricing & Offers');
```

### Pruning, Archiving & Cascade Deletions
```sql
-- Remove spam or test comments
DELETE FROM comment
WHERE comment_text LIKE '%subscribe to my channel%'
   OR comment_text LIKE '%free crypto%';

-- Cascade deletion: deleting a post automatically removes all related comments and anomalies
DELETE FROM post WHERE post_id = 'P_TEMP_TEST_01';
```

---

## 5. Integrity Constraints & Indexing Strategy

1. **Foreign Key Enforcement:** Enabled via `PRAGMA foreign_keys = ON`. Deleting a post cascades to all its associated comments via `ON DELETE CASCADE`.
2. **Domain Integrity Checks:**
   - `sentiment_score BETWEEN -1 AND 1`
   - `sentiment_confidence BETWEEN 0 AND 1`
   - `likes >= 0`, `comments_count >= 0`, `followers >= 0`
   - `provenance IN ('observed', 'simulated')`
3. **Compound Indexes:**
   - `ix_post_account`: Accelerates joins across `post` and `account`.
   - `ix_comment_post`: Ensures sub-millisecond retrieval of all comments belonging to a specific post or YouTube video.
   - `ix_comment_published`: Optimizes temporal time-series queries and monthly aggregation charts.

