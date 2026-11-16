from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "campaign.db"
MODEL_PATH = DATA_DIR / "segment_model.joblib"
TRUTH_PATH = DATA_DIR / "generator_ground_truth.csv"

COLLECTION_DATE = "2026-11-15"   # date the (simulated) data was "collected"
SEED = 42
N_POSTS = 3000                   # spec: ~2,000-5,000 post records
_yt_nested = DATA_DIR / "youtube" / "youtube_classified_comments.csv"
_yt_flat = DATA_DIR / "classified_comments.csv"
YOUTUBE_CSV = _yt_nested if _yt_nested.exists() else _yt_flat   # output of the YouTube sentiment analyzer (Project 2)
