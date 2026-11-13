from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.bootstrap import bootstrap
from core.config_loader import load_all_channel_configs
from core.workflow import create_full_mvp_video

print("Running system test...")
bootstrap()
configs = load_all_channel_configs()
expected = {
    "reddit_stories", "english_learning", "psychology", "dark_history",
    "ai_tools_automation", "quiz", "facts", "sports_reviews"
}
missing = expected - set(configs)
if missing:
    raise SystemExit(f"Missing channel configs: {missing}")

for channel_id in expected:
    root = ROOT / "channels" / channel_id
    for sub in ["workspace", "output/final_clips", "output/thumbnails", "upload_packages", "prompts"]:
        (root / sub).mkdir(parents=True, exist_ok=True)

video_id, folder = create_full_mvp_video("quiz", "grammar_quiz", "System Test Quiz")
if not (folder / "script.txt").exists():
    raise SystemExit("script.txt missing")
if not (folder / "metadata.txt").exists():
    raise SystemExit("metadata.txt missing")
if not (folder / "safety_report.json").exists():
    raise SystemExit("safety_report.json missing")
print("System test passed.")
print(video_id)
