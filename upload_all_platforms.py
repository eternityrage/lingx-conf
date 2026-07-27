"""
VELOCITY LANGUAGE - Unified Social Media Upload Script
"""

import os, sys, json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

root = Path(__file__).parent
upload_dir = root / "upload"
if upload_dir.exists() and str(upload_dir) not in sys.path:
    sys.path.insert(0, str(upload_dir))
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

uploaders = {}
modules = [
    ("upload_facebook", "upload_to_facebook", "fb"),
    ("upload_instagram", "upload_to_instagram", "ig"),
    ("upload_to_youtube", "upload_to_youtube", "yt"),
    ("upload_vk", "upload_to_vk", "vk"),
    ("upload_telegram", "upload_to_telegram", "tg"),
    ("upload_twitter", "upload_to_twitter", "tw"),
    ("upload_threads", "upload_to_threads", "th"),
    ("upload_tiktok", "upload_to_tiktok", "tk"),
]
for mod_name, func_name, key in modules:
    for prefix in ["upload.", ""]:
        try:
            mod = __import__(prefix + mod_name, fromlist=[func_name])
            uploaders[key] = getattr(mod, func_name)
            break
        except ImportError:
            continue
    if not uploaders.get(key):
        print(f"[!] {mod_name} not available")


def get_latest_reel():
    fv = Path("output/final_video.mp4")
    if fv.exists():
        meta = {"story": "", "topic": ""}
        se = Path("output/story_en.txt")
        if se.exists():
            with open(se, encoding="utf-8") as f: meta["story"] = f.read()
        tp = Path("output/topic.txt")
        if tp.exists():
            with open(tp, encoding="utf-8") as f: meta["topic"] = f.read()
        return {"video_path": str(fv), "metadata": meta, "category": meta.get("topic", "Daily Story"), "phrases": [], "words": [], "lang_field": "native"}
    video_dir = Path("output/video")
    if not video_dir.exists(): return None
    reels = list(video_dir.glob("*/final_reel.mp4"))
    if not reels: return None
    latest = max(reels, key=lambda p: p.stat().st_mtime)
    meta = {}
    mf = latest.parent / "metadata.json"
    if mf.exists():
        with open(mf, encoding="utf-8") as f: meta = json.load(f)
    phrases = meta.get("phrases", [])
    words = meta.get("words", [])
    lang_field = None
    if phrases:
        for key in phrases[0]:
            if key not in ("english", "transliteration", "category"):
                lang_field = key
                break
    return {"video_path": str(latest), "metadata": meta, "category": meta.get("category_english", meta.get("channel", "Learning")), "phrases": phrases, "words": words, "lang_field": lang_field or "native"}


LANGUAGE_MAP = {
    "slovn": "Slovenian", "slovenian": "Slovenian",
    "heb": "Hebrew", "hebrew": "Hebrew",
    "dut": "Dutch", "dutch": "Dutch",
    "tam": "Tamil", "tamil": "Tamil",
    "kan": "Kannada", "kannada": "Kannada",
    "bos": "Bosnian", "bosnian": "Bosnian",
    "viet": "Vietnamese", "vietnamese": "Vietnamese",
    "fili": "Filipino", "filipino": "Filipino",
    "indo": "Indonesian", "indonesian": "Indonesian",
    "alb": "Albanian", "albanian": "Albanian",
    "slvk": "Slovak", "slovak": "Slovak",
    "ser": "Serbian", "serbian": "Serbian",
    "afr": "Afrikaans", "afrikaans": "Afrikaans",
    "catln": "Catalan", "catalan": "Catalan",
    "hung": "Hungarian", "hungarian": "Hungarian",
    "cze": "Czech", "czech": "Czech",
    "wel": "Welsh", "welsh": "Welsh",
    "rom": "Romanian", "romanian": "Romanian",
    "guj": "Gujarati", "gujarati": "Gujarati",
    "swah": "Swahili", "swahili": "Swahili",
    "ice": "Icelandic", "icelandic": "Icelandic",
    "tha": "Thai", "thai": "Thai",
    "tel": "Telugu", "telugu": "Telugu",
    "fny": "Fanny", "french": "French",
    "tur": "Turkish", "turkish": "Turkish",
    "ukr": "Ukrainian", "ukrainian": "Ukrainian",
    "pol": "Polish", "polish": "Polish",
    "gre": "Greek", "greek": "Greek",
    "hin": "Hindi", "hindi": "Hindi",
    "ben": "Bengali", "bengali": "Bengali",
    "urd": "Urdu", "urdu": "Urdu",
    "per": "Persian", "persian": "Persian",
    "mar": "Marathi", "marathi": "Marathi",
    "telu": "Telugu",
    "mal": "Malayalam", "malayalam": "Malayalam",
    "ukr": "Ukrainian", "ukrainian": "Ukrainian",
    "nor": "Norwegian", "norwegian": "Norwegian",
    "gre": "Greek", "greek": "Greek",
    "finn": "Finnish", "finnish": "Finnish",
    "dan": "Danish", "danish": "Danish",
    "ger": "German", "german": "German",
    "him": "Hindi", "hindi": "Hindi",
    "pol": "Polish", "polish": "Polish",
    "por": "Portuguese", "portuguese": "Portuguese",
    "ita": "Italian", "italian": "Italian",
    "Geo": "Georgian", "georgian": "Georgian", "geo": "Georgian",
}


def get_language_name(phrases, lang_field):
    try:
        import subprocess
        remote = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], stderr=subprocess.DEVNULL).decode().strip()
        import re
        m = re.search(r'(?:vel|Vel|vdl|vei|xn)_?([a-z0-9]+)', remote, re.IGNORECASE)
        if m:
            code = m.group(1).lower()
            if code in LANGUAGE_MAP:
                return LANGUAGE_MAP[code]
        m2 = re.search(r'/([^/]+)$', remote)
        if m2:
            repo = m2.group(1).replace(".git", "").lower()
            parts = re.split(r'[-_\s]', repo)
            if len(parts) > 1:
                code = parts[-1]
                if code in LANGUAGE_MAP:
                    return LANGUAGE_MAP[code]
    except Exception:
        pass
    if lang_field in LANGUAGE_MAP:
        return LANGUAGE_MAP[lang_field]
    if phrases and lang_field:
        sample = phrases[0].get(lang_field, "").lower()
        for code, name in LANGUAGE_MAP.items():
            if code in sample:
                return name
    return lang_field.capitalize()


def generate_caption(phrases, category, lang_field="native", words=None, metadata=None, platform="facebook"):
    if metadata and metadata.get("story"):
        story = metadata["story"]
        topic = metadata.get("topic", "History")
        tag = "ancienthistory"
        base = [f"Ancient History: {topic}", "", story.strip(), ""]
        base.extend(["Like & follow for daily history!", ""])
        base.extend(["#" + tag, "#history", "#ancienthistory", "#greekhistory", "#womenshistory"])
        return "\n".join(base)
    if words:
        channel = category
        tag = channel.lower().replace(" ", "")
        base = [f"{channel.upper()} - Unlock English Vocabulary!", "", f"Today's words:", ""]
        for i, w in enumerate(words[:3], 1):
            word = w.get("word", "")
            root = w.get("root", "")
            root_m = w.get("root_meaning", "")
            pos = w.get("part_of_speech", "")
            definition = w.get("definition", "")
            example = w.get("example", "")
            base.append(f"{i}. {word.upper()} ({pos})")
            base.append(f"   {definition}")
            if root and root_m:
                base.append(f"   Root: {root} = {root_m}")
            base.append(f"   \"{example}\"")
            base.append("")
        base.extend(["Like & follow for daily vocabulary!", ""])
        base.extend([f"#{tag}", f"#{tag}daily", "#vocabulary", "#englishlearning", "#wordroots", "#learnenglish"])
        return "\n".join(base)
    lang_name = get_language_name(phrases, lang_field)
    lang_tag = lang_name.lower().replace(" ", "")
    if platform == "instagram":
        base = [f"Learn {lang_name} with VELOCITY {lang_name.upper()}!", "", f"Category: {category}", ""]
        for i, p in enumerate(phrases[:3], 1):
            base.append(f"{i}. {p['english']}")
            base.append(f"   {p.get(lang_field, '')}")
            base.append("")
        base.extend(["Which phrase is your favorite? 👇", f"Follow for daily {lang_name} lessons!", ""])
        base.extend([f"#learn{lang_tag}", f"#{lang_tag}lessons", "#languagelearning", f"#velocity{lang_tag}", f"#daily{lang_tag}"])
        return "\n".join(base)
    base = [f"Learn {lang_name} with VELOCITY {lang_name.upper()}!", "", f"Category: {category}", "", f"Master {lang_name} one phrase at a time! Today's {category} lesson:", ""]
    for i, p in enumerate(phrases[:5], 1):
        base.append(f"{i}. {p['english']}")
        base.append(f"   {p.get(lang_field, '')}")
        base.append(f"   [{p.get('transliteration', '')}]")
        base.append("")
    base.extend(["Tip: Repeat each phrase out loud 3 times!", "Like this video if you learned something new!", "Comment your favorite phrase below!", "Follow for daily lessons!", ""])
    base.extend([f"#learn{lang_tag}", f"#{lang_tag}lessons", f"#{lang_tag}forbeginners", "#languagelearning", f"#{lang_tag}vocabulary", f"#velocity{lang_tag}", f"#daily{lang_tag}", f"#{lang_tag}", "#learnlanguages"])
    return "\n".join(base)


def upload_to_all_platforms(video_path, caption, category, phrases=None, lang_field="native"):
    lang_name = get_language_name(phrases or [], lang_field)
    results = {"timestamp": datetime.now().isoformat(), "category": category, "video": video_path, "uploads": {}, "platforms_attempted": [], "platforms_successful": [], "platforms_skipped": [], "platforms_failed": [], "timing": {}}
    print("\n" + "="*80)
    print(f"VELOCITY {lang_name.upper()} - MULTI-PLATFORM UPLOAD")
    print("="*80)
    if not Path(video_path).exists(): print(f"Video not found"); return results
    platforms = [("facebook", "fb", "Facebook"), ("instagram", "ig", "Instagram"), ("youtube", "yt", "YouTube"), ("vk", "vk", "VK"), ("telegram", "tg", "Telegram"), ("twitter", "tw", "Twitter"), ("threads", "th", "Threads"), ("tiktok", "tk", "TikTok")]
    for pname, key, dname in platforms:
        results["platforms_attempted"].append(pname)
        func = uploaders.get(key)
        if func:
            try:
                t_start = datetime.now()
                if pname == "youtube":
                    from upload_to_youtube import generate_video_metadata
                    yt_title, yt_desc, yt_tags = generate_video_metadata(category, len(phrases) if phrases else 5, phrases)
                    r = func(video_path=video_path, title=yt_title, description=yt_desc, tags=yt_tags, category_id='22')
                elif pname == "vk":
                    r = func(video_path=video_path, description=caption)
                elif pname == "telegram":
                    r = func(video_path=video_path, caption=caption)
                elif pname == "twitter":
                    r = func(video_path=video_path, caption=caption)
                elif pname == "threads":
                    r = func(video_path=video_path, text=caption)
                elif pname == "tiktok":
                    r = func(video_path=video_path, description=caption, title=caption[:100])
                elif pname == "facebook":
                    r = func(video_path=video_path, description=caption)
                elif pname == "instagram":
                    ig_cap = generate_caption(phrases, category, lang_field, words, metadata, platform="instagram")
                    r = func(video_path=video_path, caption=ig_cap, is_story=False)
                t_end = datetime.now()
                t_sec = round((t_end - t_start).total_seconds())
                results["timing"][pname] = f"{t_sec}s"
                if r:
                    results["uploads"][pname] = r
                    results["platforms_successful"].append(pname)
                else: results["platforms_failed"].append(pname)
            except Exception as e:
                results["uploads"][pname] = {"status": "failed", "error": str(e)}
                results["platforms_failed"].append(pname)
        else:
            results["uploads"][pname] = {"status": "skipped"}
            results["platforms_skipped"].append(pname)
    s = len(results["platforms_successful"]); f = len(results["platforms_failed"]); sk = len(results["platforms_skipped"])
    print(f"\nSUMMARY: {s} success, {f} failed, {sk} skipped")
    rf = Path("output") / f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    rf.parent.mkdir(exist_ok=True)
    with open(rf, "w", encoding="utf-8") as f: json.dump(results, f, indent=2, ensure_ascii=False)
    return results


def main():
    print("\n" + "="*80)
    print("VELOCITY LANGUAGE - AUTOMATED UPLOAD")
    print("="*80)
    reel = get_latest_reel()
    if not reel: print("No reel found"); sys.exit(1)
    caption = generate_caption(reel['phrases'], reel['category'], reel['lang_field'], reel.get('words'), reel.get('metadata'))
    upload_to_all_platforms(reel['video_path'], caption, reel['category'], reel['phrases'], reel['lang_field'])

if __name__ == "__main__": main()
