"""
Lingexa Confused - Commonly Confused Words
Stop mixing up these tricky word pairs
"""

import os, sys, json, random, asyncio, subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import random
import re

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
AI_MODEL = os.getenv("AI_MODEL")
if not AI_MODEL:
    raise ValueError("AI_MODEL not set!")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
for d in [OUTPUT_DIR, VIDEO_DIR, HISTORY_DIR]:
    d.mkdir(exist_ok=True)

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
TTS_VOICE = "en-US-GuyNeural"
CHANNEL_NAME = "Lingexa Confused"
WORDS_PER_VIDEO = 2
HISTORY_FILE = HISTORY_DIR / "all_pairs.json"
FONTS_DIR = Path(__file__).parent / "fonts"

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pairs": [], "last_updated": None}

def save_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_core_pair(pair_str):
    """Extract the core (left_word, right_word) tuple for semantic dedup.
    Handles various formats like 'affect vs effect', 'affect vs. effect (as verb/noun)'
    """
    parts = re.split(r'\s+vs\.?\s+', pair_str.lower().strip(), maxsplit=1)
    if len(parts) < 2:
        return None
    left = parts[0].strip()
    right = parts[1].strip()
    left = re.sub(r'\(.*?\)', '', left).strip().rstrip('.,;:!?')
    right = re.sub(r'\(.*?\)', '', right).strip().rstrip('.,;:!?')
    left = re.split(r'\s+as\s+', left)[0].strip()
    right = re.split(r'\s+as\s+', right)[0].strip()
    lw = left.split()[0].strip('.,;:!?()[]{}')
    rw = right.split()[0].strip('.,;:!?()[]{}')
    if not lw or not rw:
        return None
    return (lw, rw)


def is_semantically_used(pair_str, history_pairs):
    """Check if a word pair is semantically already in history.
    Compares core left/right words rather than exact strings.
    """
    core = extract_core_pair(pair_str)
    if not core:
        return False
    lw, rw = core
    for h_pair in history_pairs:
        h_core = extract_core_pair(h_pair)
        if not h_core:
            continue
        hl, hr = h_core
        if lw == hl and rw == hr:
            return True
        if lw == hr and rw == hl:
            return True
    return False


def add_to_history(ids):
    h = load_history()
    existing_cores = set()
    for existing in h.get("pairs", []):
        c = extract_core_pair(existing)
        if c:
            existing_cores.add(c)
    for pid_str in ids:
        core = extract_core_pair(pid_str)
        if core and core not in existing_cores:
            h["pairs"].append(pid_str.strip().lower())
            existing_cores.add(core)
        elif not core:
            if pid_str.strip().lower() not in [x.lower().strip() for x in h.get("pairs", [])]:
                h["pairs"].append(pid_str.strip().lower())
    save_history(h)

def generate_data(num=WORDS_PER_VIDEO):
    max_attempts = 60
    cats = [
        "homophones that sound identical but have different spellings and meanings",
        "verb tense confusions: present perfect vs past simple vs past continuous",
        "preposition mistakes that completely change meaning",
        "false friends between English and French/Spanish/Italian",
        "formal vs informal register in professional emails",
        "academic vocabulary that undergraduates commonly misuse",
        "business English words that professionals confuse in meetings",
        "regional differences between US, UK, Australian, and Indian English",
        "singular vs plural agreement errors with collective nouns",
        "adjective vs adverb positions and their effect on meaning",
        "countable vs uncountable noun confusions with quantifiers",
        "commonly misused idioms and their correct forms",
        "phrasal verb meanings that non-native speakers mix up",
        "silent-letter words that trick even native spellers",
        "word order errors in English questions and negations",
        "comparative and superlative form mistakes with irregular adjectives",
        "active vs passive voice misuse in scientific and technical writing",
        "modal verb shades of meaning: can/may, must/have to, shall/will, should/ought",
        "conditional sentence type confusions (zero, first, second, third)",
        "contractions vs full forms across formal and casual writing",
        "Latin and Greek pluralization rules that people get wrong",
        "technical jargon confusions across different academic disciplines",
        "near-synonyms with different emotional connotations",
        "words that look similar but have opposite or unrelated meanings",
        "double negative constructions in different English dialects",
        "reflexive and reciprocal pronoun errors",
        "relative clause punctuation: restrictive vs non-restrictive (that vs which)",
        "subjunctive mood usage in formal vs everyday English",
        "collocation errors: words that don't naturally go together",
        "slang vs standard English in workplace communication",
        "archaic vs modern word choices in contemporary writing",
        "borrowed foreign words with unexpected English pronunciation",
        "compound word hyphenation rules and common mistakes",
        "cliche confusions: commonly misquoted sayings and proverbs",
        "prefix and suffix errors that change word meaning entirely",
        "false singulars and false plurals in English",
        "gender-neutral language confusions in modern usage",
        "time and sequence adverb placement errors",
        "correlative conjunction pairings (either/or, neither/nor, not only/but also)",
        "article usage: zero article vs definite vs indefinite with abstract nouns",
        "linking verb vs action verb confusions (feel good vs feel well)",
        "gradable vs non-gradable adjective intensifier mistakes",
        "infinitive vs gerund after certain verbs (stop to do vs stop doing)",
        "direct vs indirect speech tense shift errors",
        "emigrate vs immigrate vs migrate: movement prepositions",
        "principal vs principle and other sound-alike legal terms",
        "every day vs everyday and other compound adjective confusions",
        "who vs whom in formal vs casual contexts",
        "bring vs take vs fetch: direction of motion verbs",
        "economic vs economical and other -ic/-ical adjective pairs",
    ]
    random.shuffle(cats)
    collected = []
    for attempt in range(max_attempts):
        try:
            import requests
            url = "https://gen.pollinations.ai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}", "Content-Type": "application/json"}
            cat = cats[attempt % len(cats)]
            remaining = num - len(collected)
            print(f"[api] Attempt {attempt + 1}: {cat} (need {remaining} more)")
            h = load_history()
            # Build used set from recent history (as core tuples for semantic dedup)
            recent_pairs = h.get("pairs", [])[-50:]
            used_set = set()
            for hp in recent_pairs:
                c = extract_core_pair(hp)
                if c:
                    used_set.add(c)
            used_str = ", ".join([p for p in recent_pairs]) if recent_pairs else "(none)"
            prompt = f"""Generate 15 commonly confused word pairs about: {cat}

NEVER repeat: {used_str}
Return ONLY JSON array.

Each item has a confused pair with wrong/right usage. Make these pairs that even native speakers mix up.

Format:
[{{"pair":"AFFECT vs EFFECT","wrong":"The weather will effect our plans.","right":"The weather will affect our plans.","meaning":"Affect is a verb meaning to influence. Effect is usually a noun meaning result.","tip":"Affect = Action (both start with A). Effect = End result (both start with E)."}}]

REQUIREMENTS:
- 'meaning' field: ONE clear sentence explaining the difference
- 'tip' field: ONE unforgettable memory trick
- Wrong/right examples should be REALISTIC sentences people actually write
- Pairs must be related to the topic {cat}
Return ONLY the JSON array.""" 
            payload = {"model": AI_MODEL, "messages": [{"role": "system", "content": "Return ONLY valid JSON arrays."}, {"role": "user", "content": prompt}], "temperature": 1.6}
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            items = json.loads(content)
            if not isinstance(items, list):
                raise ValueError("Not a list")
            fresh = []
            seen_this_run = set()
            for item in items:
                pair = item.get("pair", "").strip()
                if not pair:
                    continue
                core = extract_core_pair(pair)
                if core and core in seen_this_run:
                    continue
                if core and core in used_set:
                    continue
                h = load_history()
                if is_semantically_used(pair, h.get("pairs", [])):
                    continue
                if core:
                    seen_this_run.add(core)
                    used_set.add(core)
                fresh.append(item)
                if len(collected) + len(fresh) >= num:
                    break
            collected.extend(fresh)
            if len(collected) >= num:
                add_to_history([m["pair"] for m in collected[:num]])
                return collected[:num]
        except Exception as e:
            print(f"[api] Attempt {attempt + 1} FAILED: {e}")
    if collected:
        add_to_history([m["pair"] for m in collected])
        return collected
    raise RuntimeError("API failed")

def create_bg():
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        r = y / VIDEO_HEIGHT
        if r < 0.5:
            rgb = (250, 248, 252)
        else:
            rgb = (int(250+(245-250)*(r-0.5)*2), int(248+(245-248)*(r-0.5)*2), int(252+(248-252)*(r-0.5)*2))
        draw.rectangle([(0,y),(VIDEO_WIDTH,y+1)], fill=rgb)
    return img

async def ga(text, voice, path):
    try:
        import edge_tts; await edge_tts.Communicate(text, voice).save(path); return True
    except: return False

async def gar(text, voice, path, r=3):
    for a in range(1, r+1):
        ok = await ga(text, voice, path)
        if ok and Path(path).exists() and Path(path).stat().st_size > 100: return True
        await asyncio.sleep(2*a)
    return False

def gad(file):
    if not Path(file).exists(): return 2.0
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",file], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 2.0

def gen_audio(items, out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    af = []; total = 0.0
    for i, item in enumerate(items):
        pair = item.get("pair",""); wrong = item.get("wrong",""); right = item.get("right","")
        meaning = item.get("meaning",""); tip = item.get("tip","")
        text = f"Commonly confused: {pair}. The wrong way: {wrong}. The correct way: {right}. Why? {meaning}. Quick tip: {tip}"
        fp = out_dir / f"c_{i}.mp3"
        ok = asyncio.run(gar(text, TTS_VOICE, str(fp)))
        if not ok: subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=24000:cl=mono","-t","5",str(fp)], capture_output=True)
        dur = gad(str(fp)); af.append({"file":str(fp),"duration":dur}); total += dur+0.3
    print(f"[audio] {len(af)} pairs, {total:.1f}s")
    return af, total

def cfa(audio_files, out_file):
    od = Path(out_file).parent; parts = []
    for i, af in enumerate(audio_files):
        p = od/f"pd_{i}.mp3"
        subprocess.run(["ffmpeg","-y","-i",str(af["file"]),"-af","apad=pad_dur=0.3","-ar","24000","-ac","1","-c:a","libmp3lame",str(p)], capture_output=True)
        parts.append(p)
    cl = od/"cl.txt"
    with open(cl,"w") as f:
        for p in parts: f.write(f"file '{str(p.resolve()).replace(chr(92),chr(47))}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(cl),"-c:a","libmp3lame",str(out_file)], capture_output=True)
    for p in parts:
        if p.exists(): p.unlink()
    if cl.exists(): cl.unlink()
    return Path(out_file).exists() and Path(out_file).stat().st_size > 100

def wt(draw, text, font, mw):
    w = text.split(); l = []; c = []
    for word in w:
        t = ' '.join(c+[word])
        if draw.textbbox((0,0),t,font=font)[2] <= mw or not c: c.append(word)
        else: l.append(' '.join(c)); c = [word]
    if c: l.append(' '.join(c))
    return l

def gen_img(item, bg, out_path):
    from PIL import Image, ImageDraw, ImageFont
    img = bg.copy().convert('RGBA'); draw = ImageDraw.Draw(img)
    MX=90; CX=VIDEO_WIDTH//2; CW=VIDEO_WIDTH-MX*2
    FB=["/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf","C:/Windows/Fonts/arialbd.ttf","C:/Windows/Fonts/segoeuib.ttf"]
    FR=["/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf","/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf","C:/Windows/Fonts/arial.ttf","C:/Windows/Fonts/segoeui.ttf"]
    def lf(p,sz):
        for pp in p:
            try: f=ImageFont.truetype(pp,sz); return f
            except: continue
        return ImageFont.load_default()

    f_head=lf(FB,65); f_word=lf(FB,100); f_pos=lf(FB,50)
    f_dlab=lf(FB,42); f_def=lf(FR,58); f_exlab=lf(FB,42); f_ex=lf(FR,48)
    f_tlab=lf(FB,38); f_tip=lf(FR,44); f_foot=lf(FB,38)

    pair=item.get("pair","").upper()
    wrong=item.get("wrong",""); right=item.get("right","")
    meaning=item.get("meaning",""); tip=item.get("tip","")

    H=(45,35,65); L=(80,65,105); DB=(65,50,95); EB=(95,80,125)

    draw.rectangle([(0,0),(VIDEO_WIDTH,90)],fill=H)
    draw.text((CX,45),CHANNEL_NAME.upper(),fill=(255,255,255),font=f_head,anchor="mm")

    y=260
    mww=CW; wfs=100; wf=f_word; ww=draw.textbbox((0,0),pair,font=wf)[2]
    while ww>mww and wfs>40: wfs-=5; wf=lf(FB,wfs); ww=draw.textbbox((0,0),pair,font=wf)[2]
    wh=draw.textbbox((0,0),"Ay",font=wf)[3]-draw.textbbox((0,0),"Ay",font=wf)[1]
    draw.text((CX,y+wh//2),pair,fill=(25,20,45),font=wf,anchor="mm",stroke_width=max(1,wfs//40),stroke_fill=(220,215,220))
    y+=wh+50

    pt="COMMONLY CONFUSED"
    pb=draw.textbbox((0,0),pt,font=f_pos)
    pw=pb[2]-pb[0]; ph=pb[3]-pb[1]
    draw.rounded_rectangle([(CX-pw//2-18,y),(CX+pw//2+18,y+ph+18)],radius=10,fill=(75,55,115))
    draw.text((CX,y+ph//2+9),pt,fill=(255,245,140),font=f_pos,anchor="mm")
    y+=ph+65

    draw.text((MX,y),"MEANING",fill=L,font=f_dlab,anchor="lm"); y+=55
    dl=wt(draw,meaning,f_def,CW-70)
    while len(dl)>3 and f_def.size>36: f_def=lf(FR,f_def.size-4); dl=wt(draw,meaning,f_def,CW-70)
    lh=draw.textbbox((0,0),"A",font=f_def)[3]-draw.textbbox((0,0),"A",font=f_def)[1]
    ls=int(lh*1.5); th=(len(dl)-1)*ls+lh; pd=40; bh=th+pd*2
    box=Image.new('RGBA',(CW,bh),DB+(255,)); bd=ImageDraw.Draw(box)
    bd.rounded_rectangle([(0,0),(CW,bh)],radius=16,fill=DB+(255,))
    for i,line in enumerate(dl): bd.text((CW//2,pd+(i*ls)+lh//2),line,fill=(255,255,255),font=f_def,anchor="mm")
    img.paste(box,(MX,y),box); y+=bh+55

    draw.text((MX,y),"EXAMPLE",fill=L,font=f_exlab,anchor="lm"); y+=55
    ex_t=f"WRONG: {wrong}"
    if right: ex_t+=f"    RIGHT: {right}"
    el=wt(draw,ex_t,f_ex,CW-70)
    while len(el)>2 and f_ex.size>32: f_ex=lf(FR,f_ex.size-4); el=wt(draw,ex_t,f_ex,CW-70)
    elh=draw.textbbox((0,0),"A",font=f_ex)[3]-draw.textbbox((0,0),"A",font=f_ex)[1]
    els=int(elh*1.5); eth=(len(el)-1)*els+elh; epd=35; ebh=eth+epd*2
    ebox=Image.new('RGBA',(CW,ebh),EB+(220,)); ed=ImageDraw.Draw(ebox)
    ed.rounded_rectangle([(0,0),(CW,ebh)],radius=14,fill=EB+(220,))
    for i,line in enumerate(el): ed.text((CW//2,epd+(i*els)+elh//2),line,fill=(255,255,255),font=f_ex,anchor="mm")
    img.paste(ebox,(MX,y),ebox); y+=ebh+55

    if tip and y<VIDEO_HEIGHT-160:
        draw.text((MX,y),"TIP",fill=(110,75,55),font=f_tlab,anchor="lm"); y+=50
        tl=wt(draw,tip,f_tip,CW-70)
        while len(tl)>2 and f_tip.size>28: f_tip=lf(FR,f_tip.size-4); tl=wt(draw,tip,f_tip,CW-70)
        tlh=draw.textbbox((0,0),"A",font=f_tip)[3]-draw.textbbox((0,0),"A",font=f_tip)[1]
        tls=int(tlh*1.5); tth=(len(tl)-1)*tls+tlh; tpd=30; tbh=tth+tpd*2
        tbox=Image.new('RGBA',(CW,tbh),(255,210,160,200)); td=ImageDraw.Draw(tbox)
        td.rounded_rectangle([(0,0),(CW,tbh)],radius=12,fill=(255,210,160,200))
        for i,line in enumerate(tl): td.text((CW//2,tpd+(i*tls)+tlh//2),line,fill=(70,45,25),font=f_tip,anchor="mm")
        img.paste(tbox,(MX,y),tbox)

    draw.rectangle([(0,VIDEO_HEIGHT-65),(VIDEO_WIDTH,VIDEO_HEIGHT)],fill=H)
    draw.text((CX,VIDEO_HEIGHT-32),f"Master confusing words daily  |  {CHANNEL_NAME}",fill=(210,200,220),font=f_foot,anchor="mm")
    img=img.convert('RGB')
    Path(out_path).parent.mkdir(parents=True,exist_ok=True); img.save(out_path,quality=96,optimize=True)
    print(f"[image] {Path(out_path).name}")
    return out_path

def create_video(image_files, audio_files, out_file):
    print(f"[video] {len(image_files)} images...")
    clips=[]
    for i,(ip,ai) in enumerate(zip(image_files,audio_files)):
        tc=Path(out_file).parent/f"c_{i}.mp4"; d=ai["duration"]
        subprocess.run(["ffmpeg","-y","-loop","1","-i",str(ip),"-i",str(ai["file"]),
            "-vf",f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v","libx264","-preset","medium","-pix_fmt","yuv420p","-c:a","aac","-b:a","128k",
            "-t",f"{d}","-shortest",str(tc)],capture_output=True)
        ad=gad(str(tc)); print(f"  Clip {i+1}: {ad:.1f}s"); clips.append(tc)
    if not clips: return False
    cf=Path(out_file).parent/"cl.txt"
    with open(cf,"w") as f:
        for c in clips: f.write(f"file '{str(c.resolve()).replace(chr(92),chr(47))}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(cf),"-c","copy",str(out_file)],capture_output=True)
    for c in clips:
        if c.exists(): c.unlink()
    if cf.exists(): cf.unlink()
    print(f"[video] {Path(out_file).name}")
    return True

def gen_reel():
    print(f"\n{'='*80}\n  {CHANNEL_NAME.upper()}\n{'='*80}\n")
    ts=datetime.now().strftime("%Y%m%d_%H%M%S")
    rd=VIDEO_DIR/f"pairs_{ts}"; rd.mkdir()
    print("[1/3] Generating confused word pairs...")
    items=generate_data(WORDS_PER_VIDEO)
    for i,m in enumerate(items,1): print(f"  {i}. {m['pair']}")
    print("\n[2/3] Generating images...")
    bg=create_bg(); imgs=[]
    for i,m in enumerate(items): ip=rd/f"c_{i}.jpg"; gen_img(m,bg,str(ip)); imgs.append(str(ip))
    print("\n[3/3] Generating audio & video...")
    af,td=gen_audio(items,str(rd)); fa=rd/"narration.mp3"; cfa(af,str(fa))
    ov=rd/"final_reel.mp4"; create_video(imgs,af,str(ov))
    meta={"channel":CHANNEL_NAME,"pairs":items,"timestamp":ts,"video":str(ov),"duration":td}
    with open(rd/"metadata.json","w") as f: json.dump(meta,f,indent=2)
    print(f"\n{'='*80}\n  COMPLETE! {td:.1f}s\n{'='*80}\n")
    return meta

if __name__=="__main__":
    print(f"\n{'='*80}\n  {CHANNEL_NAME.upper()}\n{'='*80}\n"); gen_reel()
