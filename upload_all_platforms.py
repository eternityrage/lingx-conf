"""
Lingexa Confused - Upload Script
"""
import os, sys, json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path: sys.path.insert(0, str(upload_dir))
CHANNEL_NAME = "Lingexa Confused"
def get_latest():
    vd = Path("output/video")
    if not vd.exists(): return None
    reels = list(vd.glob("*/final_reel.mp4"))
    if not reels: return None
    latest = max(reels, key=lambda p: p.stat().st_mtime)
    mf = latest.parent / "metadata.json"; meta = {}
    if mf.exists():
        with open(mf, "r", encoding="utf-8") as f: meta = json.load(f)
    items = meta.get("pairs", [])
    return {"video_path": str(latest), "metadata": meta, "pairs": items, "word": items[0].get("pair", "Confused") if items else "Confused"}
def gen_caption(data, platform="facebook"):
    ms = data.get("pairs", [])
    if not ms: return f"Master confusing words with {CHANNEL_NAME}! #LingexaConfused"
    lines = [f"🤔 Stop Confusing These Words! with {CHANNEL_NAME}", f""]
    for i, m in enumerate(ms, 1):
        lines.append(f"{i}. {m['pair']}")
        lines.append(f"   WRONG: \"{m['wrong']}\"")
        lines.append(f"   RIGHT: \"{m['right']}\"")
        lines.append(f"   Tip: {m.get('tip', '')}")
        lines.append(f"")
    lines.extend([f"💡 Save this to remember!", f"🔔 Follow {CHANNEL_NAME}!", f"", f"#LingexaConfused #English #Grammar #LearnEnglish #CommonMistakes #ESL #WritingTips #LanguageLearning"])
    return "\n".join(lines)
def main():
    d = get_latest()
    if not d: print("No reel!"); sys.exit(1)
    print(gen_caption(d, "facebook")[:500])
if __name__ == "__main__": main()
