# Licensing & Attribution Notice

**OSINT IG** (*Instagram Intelligence & Investigation Platform*)  
Copyright (C) 2026 **Mohsin Khawaja** — **CSIB (Cyber Solutions & Information Board)**

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.  
See the full license text in [LICENSE](LICENSE).

## Derivative Work & Upstream Attribution

The core Instagram data collection logic in `osint_ig/core/collector.py` and `osint_ig/core/instagram_provider.py` includes adapted components derived from **Datalux/Osintgram**, which is distributed under the **GNU General Public License v3.0**. In full compliance with GPL-3.0:

- The GPL-3.0 license is preserved verbatim in `LICENSE`.
- All modified and restructured components remain licensed under GPL-3.0.
- The independent architecture, `osint_ig` package layout, FastAPI server, web forensic interface, Light/Dark theme, Case ZIP & multi-format report builder, and optional Google Gemini post-collection analysis were designed and implemented by **Mohsin Khawaja (CSIB)**.

## Third-Party Dependencies

- **FastAPI** (MIT License) & **Uvicorn** (BSD-3-Clause)
- **instagrapi** (MIT License)
- **google-genai** (Apache-2.0 License)
- **geopy** (MIT License) & **httpx** (BSD-3-Clause)
- **Leaflet** (BSD-2-Clause) & **Lucide Icons** (ISC License)
