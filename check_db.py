from campaign_engine import database as db 

total = db.query("SELECT COUNT(*) AS n FROM comment")[0]["n"]
yt = db.query("SELECT COUNT(*) AS n FROM comment WHERE post_id LIKE 'YT-%'")[0]["n"]
sources = db.query("SELECT source_name, provenance, COUNT(p.post_id) AS posts FROM data_source ds LEFT JOIN post p USING(source_id) GROUP BY source_name")

print(f"Total comments in DB: {total:,}")
print(f"YouTube comments in DB: {yt:,}")
print(f"Data Sources: {sources}")   
