"""
YouTube Upload Script - Lingexa Vocabulary
Updated for 2025
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()


def get_authenticated_service():
    client_id = (os.getenv('YOUTUBE_CLIENT_ID') or os.getenv('YT_CLIENT_ID', '')).strip()
    client_secret = (os.getenv('YOUTUBE_CLIENT_SECRET') or os.getenv('YT_CLIENT_SECRET', '')).strip()
    refresh_token = (os.getenv('YOUTUBE_REFRESH_TOKEN') or os.getenv('YT_REFRESH_TOKEN', '')).strip()

    def mask(s): return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else "MISSING"
    print(f"[youtube] Client ID: {mask(client_id)}")
    print(f"[youtube] Client Secret: {mask(client_secret)}")
    print(f"[youtube] Refresh Token: {mask(refresh_token)}")

    if not all([client_id, client_secret, refresh_token]):
        raise ValueError(
            "Missing credentials! Set these environment variables:\n"
            "  - YOUTUBE_CLIENT_ID or YT_CLIENT_ID\n"
            "  - YOUTUBE_CLIENT_SECRET or YT_CLIENT_SECRET\n"
            "  - YOUTUBE_REFRESH_TOKEN or YT_REFRESH_TOKEN"
        )

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube"]
    )

    try:
        creds.refresh(Request())
    except Exception as e:
        if "invalid_grant" in str(e).lower():
            print("\n[youtube] AUTH ERROR: Refresh token has EXPIRED or been REVOKED.")
            print("SOLUTION: Generate a new refresh token.")
        raise

    return build('youtube', 'v3', credentials=creds)


def generate_video_metadata(words_data: list, reel_data: dict = None):
    """Generate YouTube title, description, and tags for vocabulary video with ALL 5 words"""
    
    if not words_data:
        return "English Vocabulary Lesson - Lingexa", "Learn English words with Lingexa!", ["vocabulary", "learn english", "lingexa"]
    
    # Get first 3 words for title
    first_words = [w.get("word", "") for w in words_data[:3]]
    words_count = len(words_data)
    
    title = f"Learn {words_count} English Words - {', '.join(first_words)} | Vocabulary Lesson"
    
    description_lines = [
        f"📚 Learn {words_count} new English words with Lingexa!",
        f"",
        f"=== TODAY'S VOCABULARY ===",
        f"",
    ]
    
    # Add all 5 words with details
    for i, w in enumerate(words_data, 1):
        word = w.get("word", "")
        pos = w.get("part_of_speech", "")
        definition = w.get("definition", "")
        example = w.get("example", "")
        synonyms = w.get("synonyms", [])
        fun_fact = w.get("fun_fact", "")
        level = w.get("level", "")
        
        description_lines.append(f"{i}. {word.upper()} ({pos}){f' - {level}' if level else ''}")
        description_lines.append(f"   Definition: {definition}")
        description_lines.append(f"   Example: {example}")
        if synonyms:
            description_lines.append(f"   Synonyms: {', '.join(synonyms)}")
        if fun_fact:
            description_lines.append(f"   💡 {fun_fact}")
        description_lines.append(f"")
    
    description_lines.extend([
        f"=== ABOUT LINGEXA ===",
        f"",
        f"Learn a new word every day with Lingexa!",
        f"🔔 Subscribe for daily English vocabulary lessons!",
        f"📱 Follow us on social media @lingexa",
        f"",
        f"=== HASHTAGS ===",
        f"#Lingexa #Vocabulary #LearnEnglish #WordOfTheDay #EnglishLearning #VocabularyBuilder #EnglishWords #StudyEnglish #DailyVocabulary #ESL #EnglishPractice #LanguageLearning #Shorts",
    ])
    
    description = "\n".join(description_lines)
    
    # Generate tags from all words
    all_words_lower = [w.get("word", "").lower() for w in words_data]
    tags = [
        "vocabulary",
        "learn english",
        "word of the day",
        "english vocabulary",
        "english learning",
        "vocabulary builder",
        "english words",
        "lingexa",
        "study english",
        "daily vocabulary",
        "english practice",
        "esl",
        "language learning",
    ] + all_words_lower[:5]
    
    return title, description, tags


def upload_to_youtube(video_path, title, description, tags=None, category_id='27'):
    if tags is None:
        tags = ['education', 'vocabulary', 'english learning', 'lingexa']
    youtube = get_authenticated_service()

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }

    if '#Shorts' not in body['snippet']['description']:
        body['snippet']['description'] += '\n\n#Shorts'

    media = MediaFileUpload(
        str(video_path),
        chunksize=-1,
        resumable=True,
        mimetype='video/mp4'
    )

    print(f"[youtube] Uploading: {title}")
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[youtube] Progress: {int(status.progress() * 100)}%")

    print(f"[youtube] Uploaded! Video ID: {response['id']}")
    print(f"[youtube] URL: https://youtube.com/shorts/{response['id']}")

    return response


def main():
    video_file = Path('final_video.mp4')

    if not video_file.exists():
        print("[youtube] No video found at final_video.mp4")
        return

    title = "Learn English Vocabulary Daily"
    description = "#shorts #vocabulary #learnenglish #lingexa"
    tags = ['vocabulary', 'english learning', 'lingexa']

    try:
        upload_to_youtube(
            video_path=video_file,
            title=title,
            description=description,
            tags=tags,
            category_id='27'
        )
    except Exception as e:
        print(f"[youtube] Upload failed: {e}")
        raise


if __name__ == '__main__':
    main()