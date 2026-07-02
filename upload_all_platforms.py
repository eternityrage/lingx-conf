import os, sys, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

upload_dir = Path(__file__).parent / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))

upload_to_facebook = None
upload_to_instagram = None
upload_to_youtube = None

try:
    from upload_facebook import upload_to_facebook as fb_upload
    upload_to_facebook = fb_upload
except ImportError:
    pass
try:
    from upload_instagram import upload_to_instagram as ig_upload
    upload_to_instagram = ig_upload
except ImportError:
    pass
try:
    from upload_to_youtube import upload_to_youtube as yt_upload
    upload_to_youtube = yt_upload
except ImportError:
    pass

CHANNEL_NAME = "Lingexa Confused"

def get_latest_reel():
    video_dir = Path("output/video")
    if not video_dir.exists():
        return None
    reels = list(video_dir.glob("*/final_reel.mp4"))
    if not reels:
        return None
    latest = max(reels, key=lambda p: p.stat().st_mtime)
    metadata_file = latest.parent / "metadata.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    pairs_data = metadata.get("pairs", [])
    all_pairs = [p.get("pair", "") for p in pairs_data]
    return {"video_path": str(latest), "metadata": metadata, "pairs": pairs_data, "word": all_pairs[0] if all_pairs else "Confused"}

def generate_caption(reel_data, platform="facebook"):
    pairs = reel_data.get("pairs", [])
    if not pairs:
        return f"Master confusing words with {CHANNEL_NAME}! #LingexaConfused"
    if platform == "facebook":
        lines = [f"🤔 Stop Confusing These Words! with {CHANNEL_NAME}", f""]
        for i, m in enumerate(pairs, 1):
            lines.append(f"{i}. {m['pair']}")
            lines.append(f"   WRONG: \"{m['wrong']}\"")
            lines.append(f"   RIGHT: \"{m['right']}\"")
            lines.append(f"   Tip: {m.get('tip', '')}")
            lines.append(f"")
        lines.extend([f"💡 Save this to remember!", f"🔔 Follow {CHANNEL_NAME}!", f"", f"#LingexaConfused #English #Grammar #LearnEnglish #CommonMistakes #ESL #WritingTips #LanguageLearning"])
    else:
        lines = [f"🤔 Stop Confusing These Words!", f""]
        for i, m in enumerate(pairs[:3], 1):
            lines.append(f"{i}. {m['pair']} - {m.get('tip', '')}")
        lines.extend([f"", f"#LingexaConfused #English #Grammar"])
    return "\n".join(lines)

def upload_to_all_platforms(video_path, caption, word, reel_data=None):
    results = {"timestamp": datetime.now().isoformat(), "word": word, "video": video_path, "uploads": {}, "platforms_attempted": [], "platforms_successful": [], "platforms_skipped": [], "platforms_failed": []}
    print(f"\n{'='*80}\n{CHANNEL_NAME.upper()} - MULTI-PLATFORM UPLOAD\n{'='*80}")
    if not Path(video_path).exists():
        return results
    platforms = [("facebook", upload_to_facebook, "Facebook"), ("instagram", upload_to_instagram, "Instagram"), ("youtube", upload_to_youtube, "YouTube")]
    for platform_name, upload_func, display_name in platforms:
        print(f"\n{display_name} UPLOAD...")
        results["platforms_attempted"].append(platform_name)
        if upload_func:
            try:
                if platform_name == "facebook":
                    upload_result = upload_func(video_path=video_path, description=caption, title=f"Confused Words: {word}")
                elif platform_name == "instagram":
                    upload_result = upload_func(video_path=video_path, caption=caption, is_story=False)
                elif platform_name == "youtube":
                    from upload_to_youtube import generate_video_metadata
                    yt_title, yt_description, yt_tags = generate_video_metadata(reel_data.get("pairs", []), reel_data)
                    upload_result = upload_func(video_path=video_path, title=yt_title, description=yt_description, tags=yt_tags, category_id='27')
                if upload_result:
                    results["uploads"][platform_name] = upload_result
                    results["platforms_successful"].append(platform_name)
                else:
                    results["platforms_failed"].append(platform_name)
            except Exception as e:
                results["uploads"][platform_name] = {"status": "failed", "error": str(e)}
                results["platforms_failed"].append(platform_name)
        else:
            results["platforms_skipped"].append(platform_name)
    print(f"\nSuccessful: {len(results['platforms_successful'])}, Failed: {len(results['platforms_failed'])}, Skipped: {len(results['platforms_skipped'])}")
    return results

def main():
    reel = get_latest_reel()
    if not reel:
        print("No reel found! Run lingexa_confused_bot.py first.")
        sys.exit(1)
    caption = generate_caption(reel, platform="facebook")
    print(f"Caption ({len(caption)} chars)")
    print(caption[:500])
    upload_to_all_platforms(reel['video_path'], caption, reel['word'], reel)

if __name__ == "__main__":
    main()
