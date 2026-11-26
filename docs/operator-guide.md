# OSINT IG — Operator Guide

**OSINT IG** (*Instagram Intelligence & Investigation Platform*)  
Developed by **Mohsin Khawaja** — **CSIB (Cyber Solutions & Information Board)**

---

## Architecture Overview

```
osint_ig/
├── cli/commands.py & __main__.py  # CLI entry point (`python -m osint_ig`)
├── config/settings.py             # Runtime defaults & environment overrides
├── logging/logger.py              # Structured application logging
├── utils/text.py                  # Unicode sanitization, masking & handle normalization
├── core/exceptions.py             # Domain errors (TargetNotFoundError, ProviderError, etc.)
├── instagram/                     # Auth, InstagramProvider client & payload normalizer
├── engine/                        # InvestigationRunner & 27 intelligence module bindings
├── database/                      # SQLite RequestCache & HistoryStore
├── evidence/                      # Saved cases, CDN media fetcher & executive report exporter
├── processing/estimator.py        # Request cost & pagination estimator
├── ai/gemini_analyzer.py          # Optional Google Gemini post-collection analysis
└── api/                           # Modular FastAPI app, schemas & domain routers
frontend/                          # Standalone Light/Dark forensic UI (`styles/`, `js/`)
```

---

## Intelligence Modules (27 commands)

### Profile Intelligence
- **Profile Information** (`get_user_info`): Bio, follower/following/post counts, verified/private flags, category, and public contact fields.
- **Profile Picture** (`get_user_propic`): Full-resolution profile picture URL with clickable preview.

### Network Intelligence
- **Followers** (`get_followers`): List target followers (`limit` (200)).
- **Following** (`get_followings`): List accounts the target follows.
- **Mutual Connections** (`compare_with`): Compare followers/following against another username.
- **Tagged By Others** (`get_people_who_tagged`): Accounts that tagged the target.
- **Tagged Users** (`get_people_tagged_by_user`): Accounts tagged by the target in posts.
- **Frequent Commenters** (`get_people_who_commented`): Top commenters across collected posts.

### Content Intelligence
- **Hashtags** (`get_hashtags`): Ranked hashtag frequency chart and table.
- **Captions** (`get_captions`): Extracted post captions.
- **Comments** (`get_comment_data`): Comments across target posts.
- **Total Comments** (`get_total_comments`): Aggregate comment count.
- **Likes Statistics** (`get_total_likes`): Total and per-post like metrics.
- **Posting Activity** (`get_posting_times`): Weekday & UTC hour posting distribution.
- **Post Comments** (`get_post_comments`): Comments for a specific post or reel URL/shortcode.

### Media Intelligence
- **Media Breakdown** (`get_media_type`): Distribution of photos, videos/reels, and carousels.
- **Photos & Videos** (`get_user_photos`): Media grid with clickable previews and batch ZIP download.
- **Stories** (`get_user_stories`): Active stories and previews.
- **Highlights** (`get_highlights`): Saved story highlights.
- **Media Alt Metadata** (`get_photo_descriptions`): Accessibility/alt descriptions.

### Location & Discovery Intelligence
- **Geotagged Locations** (`get_addrs`): Interactive Leaflet map (Street, Light, Satellite) and address table.
- **Place Search** (`search_location`): Search Instagram locations by keyword.
- **Hashtag Search** (`search_hashtag`): Search Instagram hashtags by keyword.

### Public Contact Intelligence
- **Followers Public Emails** (`get_followers_email`): Public business emails exposed on follower profiles.
- **Following Public Emails** (`get_followings_email`): Public business emails exposed on followed profiles.
- **Followers Public Phones** (`get_followers_phone`): Public phone numbers exposed on follower profiles.
- **Following Public Phones** (`get_followings_phone`): Public phone numbers exposed on followed profiles.

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `INSTAGRAM_BACKEND` / `OSINT_IG_BACKEND` | `instagrapi` | Active Instagram data provider |
| `INSTAGRAM_USERNAME` / `OSINT_IG_USERNAME` | `""` | Optional Instagram username override |
| `INSTAGRAM_PASSWORD` / `OSINT_IG_PASSWORD` | `""` | Optional Instagram password override |
| `INSTAGRAPI_SESSION_FILE` / `OSINT_IG_SESSION_PATH` | `config/instagrapi_session.json` | Path to persisted `instagrapi` session JSON |
| `OSINT_IG_CACHE_PATH` | `cache/requests.sqlite3` | SQLite request cache file (set `""` to disable) |
| `OSINT_IG_CACHE_TTL` | `300` | Default cache lifetime in seconds |
| `OSINT_IG_DOSSIER_DIR` | `dossier` | Directory for saved investigation dossiers |
| `OSINT_IG_CONTACT_MAX_CHECKS` | `100` | Safety cap for public contact scanning |
| `OSINT_IG_RETRY_ATTEMPTS` | `3` | Retry count for transient network/429 responses |
| `OSINT_IG_RETRY_DELAY` | `0.6` | Base exponential backoff delay in seconds |
| `GEMINI_API_KEY` | `""` | Optional Google Gemini API key (locks UI input when set) |
| `GEMINI_MODEL` | `gemini-4-hydrogen` | Default Google Gemini model |
| `OSINT_IG_GEMINI_CONFIG` | `config/gemini.json` | Path to persisted Gemini AI configuration |
