# OSINT IG

> **Instagram OSINT tool to collect publicly available details of any public Instagram account.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Local%20Web%20UI-009688.svg)](https://fastapi.tiangolo.com/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)
[![Local-First](https://img.shields.io/badge/Mode-Local--First-8b5cf6.svg)](#-installation--setup)

**OSINT IG** is a local-first Instagram OSINT web platform with **Light & Dark themes**. It collects, structures, maps, and exports public profile, network, content, media, and location details using your authorized `instagrapi` session — with **optional** Google Gemini AI post-collection analysis.

![OSINT IG Investigation Workspace](docs/assets/osint-ig-ui.png)

---

## Key Capabilities

| Capability | Description |
|---|---|
| **Investigation Dashboard** | Live stats for saved investigations, exports, recent targets, Instagram session status, and workflow guide |
| **27 Intelligence Modules** | Modular lookups across profile, network, content, media, geolocation, and public contacts |
| **Live Terminal Logs** | Real-time backend request streaming with an expandable full-screen log modal |
| **Interactive Maps & Previews** | Leaflet geotag map (**Street**, **Light**, **Satellite** layers) plus clickable media grids and ZIP downloads |
| **Saved Dossiers & Diffs** | Reopen saved investigations from disk without re-querying Instagram and compare two runs side by side |
| **Light & Dark Theme** | Instant theme switcher in the top bar or **Settings → Storage & General** |
| **Optional Gemini AI** | Post-collection summaries, hashtag/engagement/posting-pattern analysis, and Q&A *(all OSINT tools work without an AI key)* |

---

## 27 Intelligence Modules

| Category | Modules |
|---|---|
| **Profile** | `Profile Information`, `Profile Picture` |
| **Network** | `Followers`, `Following`, `Mutual Connections`, `Tagged By Others`, `Tagged Users`, `Frequent Commenters` |
| **Content** | `Hashtags`, `Captions`, `Comments`, `Total Comments`, `Likes Statistics`, `Posting Activity`, `Post Comments` |
| **Media** | `Media Breakdown`, `Photos & Videos` *(previews + ZIP)*, `Stories`, `Highlights`, `Media Alt Metadata` |
| **Location & Discovery** | `Geotagged Locations` *(Leaflet map)*, `Place Search`, `Hashtag Search` |
| **Public Contacts** | `Followers Public Emails`, `Following Public Emails`, `Followers Public Phone Numbers`, `Following Public Phone Numbers` |

---

## Exports & Case Artifacts

| Export Type | Output Contents |
|---|---|
| **Full Case ZIP** | `report.html`, `report.json`, `report.csv`, `manifest.json`, `ai_analysis.md`, `raw_evidence/*.json`, `lists/` *(emails, phones, followers, following, hashtags, locations, captions)*, and `media/` |
| **Single-File Exports** | **JSON**, **CSV**, **HTML**, and **Print-to-PDF** |

---

## Installation & Setup

### Prerequisites
- **Python 3.10+** *(recommended: 3.11 or 3.12)*
- **Git**

### Windows (PowerShell)

```powershell
git clone https://github.com/csibmohsin/OSINT-IG.git
cd OSINT-IG

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

uvicorn osint_ig.api.app:app --host 127.0.0.1 --port 8000
# or:
python -m osint_ig serve
```

> [!TIP]
> If PowerShell blocks script activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` or launch directly with `.\.venv\Scripts\python.exe -m osint_ig serve`.

### Linux & macOS (Bash / Zsh)

```bash
git clone https://github.com/csibmohsin/OSINT-IG.git
cd OSINT-IG

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn osint_ig.api.app:app --host 127.0.0.1 --port 8000
# or:
python -m osint_ig serve
```

> [!NOTE]
> On Debian/Ubuntu, if `python3 -m venv` is unavailable, install it first: `sudo apt update && sudo apt install -y python3-venv python3-pip`.

### Docker

```bash
git clone https://github.com/csibmohsin/OSINT-IG.git
cd OSINT-IG

docker compose up --build
```

Open **http://127.0.0.1:8000** in your browser.

---

## Instagram Authentication & Configuration

Open **http://127.0.0.1:8000 → Settings → Instagram Connection** and choose one method:

| Method | How to Configure | Best For |
|---|---|---|
| **Direct Login** | Enter username & password → **Login & Save Credentials** → **Verify Connection** | Standard local login |
| **Browser `sessionid`** | Paste your `sessionid` cookie from a logged-in browser → **Save Session ID** | Avoiding IP/login challenges |
| **CLI Helper** | Run `python -m osint_ig auth` or `python -m osint_ig auth --sessionid <cookie>` | Terminal-first setup |

- **Private Accounts:** Works fully if your logged-in account already follows the private target; otherwise only basic public metadata is accessible.
- **Optional Gemini AI:** Add your Google Gemini API key under **Settings → AI Configuration** for post-collection analysis *(strictly separates **Observed Facts**, **Derived Statistics**, **AI Interpretations**, and **Unknowns**)*.

See [docs/operator-guide.md](docs/operator-guide.md) and [NOTICE.md](NOTICE.md) for architecture and GPL-3.0 attribution details.

---

## Development & Tests

| Platform | Commands |
|---|---|
| **Windows (PowerShell)** | `.\.venv\Scripts\pip.exe install -r requirements-dev.txt` <br> `.\.venv\Scripts\python.exe -m pytest` |
| **Linux / macOS (Bash)** | `pip install -r requirements-dev.txt` <br> `pytest` |

---

## Terms & Conditions

> [!WARNING]
> **Use at Your Own Risk.** **OSINT IG** is intended strictly for Open Source Intelligence (OSINT), authorized security research, digital forensics, and educational purposes.

- **Sole Responsibility:** You are solely responsible for complying with applicable laws and platform Terms of Service.
- **No Liability:** The author assumes no liability for misuse or unauthorized activity.

---

Developed by **Mohsin Khawaja** — **CSIB (Cyber Solutions & Information Board)**
