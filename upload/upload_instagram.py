"""
Instagram Reels Upload - VELOCITY HEBREW
Improved: compression, multi-host fallback, graph.facebook primary, auth error handling
"""
import os, subprocess, requests, tempfile, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TEMP_DIR = Path(tempfile.gettempdir()) / "ig_compress"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def compress_video(video_path):
    """Compress video to under 40MB for faster Instagram processing."""
    inp = Path(video_path)
    size_mb = inp.stat().st_size / (1024 * 1024)
    print(f"[instagram] Original size: {size_mb:.1f} MB")
    if size_mb < 40:
        print("[instagram] Under 40MB, skipping compression")
        return str(video_path)
    out = TEMP_DIR / f"compressed_{inp.stem}.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(inp), "-c:v", "libx264", "-crf", "28",
           "-preset", "fast", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out)]
    print("[instagram] Compressing video...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0 or not out.exists():
        print(f"[instagram] Compression failed, using original")
        return str(video_path)
    comp_mb = out.stat().st_size / (1024 * 1024)
    print(f"[instagram] Compressed: {size_mb:.1f}MB -> {comp_mb:.1f}MB")
    return str(out)


def upload_to_hosting(file_path):
    """Try multiple free hosting services, return direct URL."""
    services = [
        ("tmpfiles.org", lambda f: _upload_tmpfiles(f)),
        ("0x0.st", lambda f: _upload_0x0(f)),
        ("catbox.moe", lambda f: _upload_catbox(f)),
        ("uguu.se", lambda f: _upload_uguu(f)),
    ]
    last_err = None
    for name, fn in services:
        try:
            print(f"[instagram] Uploading via {name}...")
            url = fn(file_path)
            print(f"[instagram] Hosted at {url}")
            return url
        except Exception as e:
            print(f"[instagram] {name} failed: {e}")
            last_err = e
    raise Exception(f"All hosting services failed: {last_err}")


def _upload_tmpfiles(file_path):
    with open(file_path, 'rb') as f:
        r = requests.post('https://tmpfiles.org/api/v1/upload', files={'file': ('v.mp4', f, 'video/mp4')}, timeout=(15, 120))
    if r.status_code != 200: raise Exception(f"Status {r.status_code}")
    d = r.json()
    if d.get('status') != 'success': raise Exception(str(d))
    return d['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')


def _upload_0x0(file_path):
    with open(file_path, 'rb') as f:
        r = requests.post('https://0x0.st', files={'file': ('v.mp4', f, 'video/mp4')}, timeout=(15, 120))
    if r.status_code != 200: raise Exception(f"Status {r.status_code}")
    return r.text.strip()


def _upload_catbox(file_path):
    with open(file_path, 'rb') as f:
        r = requests.post('https://catbox.moe/user/api.php', data={'reqtype': 'fileupload'},
                          files={'fileToUpload': ('v.mp4', f, 'video/mp4')}, timeout=(15, 120))
    if r.status_code != 200: raise Exception(f"Status {r.status_code}")
    return r.text.strip()


def _upload_uguu(file_path):
    with open(file_path, 'rb') as f:
        r = requests.post('https://uguu.se/upload', files={'files[]': ('v.mp4', f, 'video/mp4')}, timeout=(15, 120))
    if r.status_code != 200: raise Exception(f"Status {r.status_code}")
    d = r.json()
    if not d.get('success'): raise Exception(str(d))
    return d['files'][0]['url']


def upload_to_instagram(video_path, caption, is_story=False):
    media_type = 'STORIES' if is_story else 'REELS'
    print("\n" + "=" * 60)
    print(f"INSTAGRAM {media_type} UPLOAD")
    print("=" * 60)

    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_ACCOUNT_ID') or os.getenv('IG_USER_ID')
    if not access_token: raise ValueError("INSTAGRAM_ACCESS_TOKEN not set")
    if not user_id: raise ValueError("INSTAGRAM_ACCOUNT_ID not set")

    inp = Path(video_path)
    if not inp.exists(): raise FileNotFoundError(f"Video not found: {video_path}")
    print(f"[instagram] Video: {inp.name} ({inp.stat().st_size/1024/1024:.1f} MB)")
    caption_limited = caption[:2200] if len(caption) > 2200 else caption

    compressed = None
    try:
        # Step 0: Compress if needed
        compressed = compress_video(video_path)
        upload_path = compressed

        # Step 1: Upload to temporary hosting
        print("[instagram] Step 1: Uploading to temporary hosting...")
        video_url = upload_to_hosting(upload_path)

        # Step 2: Create container (use graph.facebook as primary)
        print("[instagram] Step 2: Creating media container...")
        container_url = f"https://graph.facebook.com/v21.0/{user_id}/media"
        params = {'media_type': media_type, 'video_url': video_url, 'access_token': access_token}
        if not is_story:
            params['caption'] = caption_limited
            params['share_to_feed'] = 'false'
            params['thumb_offset'] = '5000'
        cont_resp = requests.post(container_url, params=params, timeout=60)
        if cont_resp.status_code != 200:
            print(f"[instagram] Facebook Graph failed, retrying Instagram API...")
            print(f"[instagram] Error: {cont_resp.text[:300]}")
            container_url = f"https://graph.instagram.com/v21.0/{user_id}/media"
            cont_resp = requests.post(container_url, params=params, timeout=60)
            if cont_resp.status_code != 200:
                raise Exception(f"Container creation failed: {cont_resp.text[:300]}")
        container_id = cont_resp.json().get('id')
        print(f"[instagram] Container ID: {container_id}")

        # Step 3: Wait for processing (up to 180s, then force publish)
        # Step 3: Wait for processing (no polling)
        print("[instagram] Step 3: Waiting 60 seconds for processing...")
        time.sleep(60)

        # Step 4: Publish
        print("[instagram] Step 4: Publishing...")
        publish_url = f"https://graph.facebook.com/v21.0/{user_id}/media_publish"
        publish_params = {
            "creation_id": container_id,
            "access_token": access_token
        }
        publish_response = requests.post(publish_url, params=publish_params, timeout=60)

        if publish_response.status_code != 200:
            print("[instagram] First publish failed, retrying after 30s...")
            time.sleep(30)
            publish_response = requests.post(publish_url, params=publish_params, timeout=60)

        if publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response and publish_response.text else {}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            print(f"[instagram] Publish failed: {error_msg}")
            raise Exception(f"Instagram Publish Error: {error_msg}")

        media_id = publish_response.json().get("id")
        print(f"[instagram] SUCCESS! Media ID: {media_id}")
        return {'id': media_id, 'platform': 'instagram', 'status': 'success'}
    except Exception as e:
        print(f"[instagram] ERROR: {e}")
        raise
    finally:
        if compressed and compressed != video_path:
            try: Path(compressed).unlink()
            except Exception: pass


if __name__ == '__main__':
    video_file = Path('final_video.mp4')
    if video_file.exists():
        try: upload_to_instagram(str(video_file), "Test")
        except Exception as e: print(f"Failed: {e}")
