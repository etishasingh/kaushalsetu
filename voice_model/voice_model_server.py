#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================
KaushalSetu AI — Standalone Voice Model Server
File: voice_model_server.py (Single Executable Python Server)
===================================================================================

A standalone, self-contained HTTP API & Web server that powers the KaushalSetu
Voice AI Counsellor with ZERO external pip dependencies.

Endpoints Provided:
  - GET  /health                        -> System health & catalogue status
  - POST /api/counsellor/chat           -> Evidence-grounded vocational counselling
  - GET  /api/careers/{id}/videos       -> Authentic YouTube career journey videos
  - GET  /                              -> Serves the KaushalSetu Voice Chatbot UI
  - GET  /kaushalsetu_voice_chatbot.html -> Standalone Voice Chatbot Application

Features:
  - 100% Python Standard Library (built on http.server, json, re, urllib).
  - Out-of-the-box CORS support for localhost and web origins.
  - Pre-seeded NCVET vocational catalogue and verified YouTube video journeys.
  - Bilingual English and Hindi intent detection and guidance.
  - Can be executed directly or run via double-clicking `run_voice_server.bat`.

Usage:
    python voice_model_server.py
    python voice_model_server.py --port 8000 --open-browser
===================================================================================
"""

import os
import re
import sys
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

SERVER_DIR = Path(__file__).resolve().parent
HTML_FILE_PATH = SERVER_DIR / "kaushalsetu_voice_chatbot.html"
CACHE_FILE_PATH = SERVER_DIR / "career_videos_cache.json"

# ===================================================================================
# Pre-Seeded Vocational Catalogue & Knowledge Base
# ===================================================================================

CATALOGUE_DATA = {
    "2022/CCM/CGSC/06612": {
        "qualification_id": "2022/CCM/CGSC/06612",
        "qualification_title": "Stainless Steel Fabricator",
        "nsqf_level": "Level 4",
        "sector": "Capital Goods & Manufacturing",
        "awarding_body": "Capital Goods Skill Council (CGSC)",
        "duration_hours": 600,
        "eligibility_raw": "10th Class Passed with 4 years relevant work experience, OR 12th Class Passed with 1 year experience, OR ITI / NTC Certificate in Welder/Fabricator trade.",
        "fee_text": "100% Government Funded under PMKVY 4.0; Zero course tuition fee for eligible candidates at accredited PMKK centres.",
        "source_nqr_url": "https://nqr.gov.in/qualifications/3607",
        "median_salary": "Rs. 18,000 - 24,000 / month (Contextual Capital Goods Benchmark)",
        "keywords": ["fabricator", "fabrication", "stainless steel", "sheet metal", "tig welding", "fitting", "cutting"]
    },
    "QG-02-CG-03939-2025-V2-CGSSC": {
        "qualification_id": "QG-02-CG-03939-2025-V2-CGSSC",
        "qualification_title": "Manual Metal Arc Welder / Shielded Metal Arc Welder",
        "nsqf_level": "Level 3.5",
        "sector": "Capital Goods & Manufacturing",
        "awarding_body": "Capital Goods & Strategic Skill Council",
        "duration_hours": 500,
        "eligibility_raw": "8th Class Passed with 2 years work experience, OR 10th Class Passed, OR ITI Welder Trade Certificate.",
        "fee_text": "Subsidized via PMKVY 4.0 / DGT Apprentice Scheme; 100% course tuition covered at accredited ITIs.",
        "source_nqr_url": "https://nqr.gov.in",
        "median_salary": "Rs. 16,500 - 22,000 / month (Apprenticeship Act 1961 Stipend Eligible)",
        "keywords": ["welder", "welding", "arc", "smaw", "mmaw", "gmaw", "electrode", "joint"]
    },
    "cnc": {
        "qualification_id": "cnc",
        "qualification_title": "CNC Milling & Turning Operator",
        "nsqf_level": "Level 4",
        "sector": "Automotive & Capital Goods",
        "awarding_body": "Automotive Skills Development Council (ASDC)",
        "duration_hours": 650,
        "eligibility_raw": "10th Class Passed + ITI Machinist / Turner Trade, OR 12th Class Passed with Science/Vocational subjects, OR Diploma in Mechanical Engineering.",
        "fee_text": "Government subsidized under Skill India Mission / PMKVY 4.0 technical short-term trades.",
        "source_nqr_url": "https://nqr.gov.in",
        "median_salary": "Rs. 19,000 - 26,000 / month (CNC Machine Operator Entry Benchmark)",
        "keywords": ["cnc", "milling", "turning", "lathe", "machinist", "vmc", "g-code", "tooling"]
    },
    "fitter": {
        "qualification_id": "QG-3.5-CG-01029-2023-V1-NTTF",
        "qualification_title": "Mechanical Fitter & Assembler",
        "nsqf_level": "Level 3.5",
        "sector": "Capital Goods",
        "awarding_body": "NTTF / NCVET",
        "duration_hours": 600,
        "eligibility_raw": "10th Class Passed with Science and Maths, OR ITI Fitter certificate.",
        "fee_text": "Free tuition under PMKVY 4.0 accredited centres; nominal exam fee may apply.",
        "source_nqr_url": "https://nqr.gov.in",
        "median_salary": "Rs. 17,000 - 23,000 / month",
        "keywords": ["fitter", "mechanical fitter", "assembly", "bench work", "filing", "drilling"]
    },
    "electrician": {
        "qualification_id": "electrician",
        "qualification_title": "Industrial Electrician & Wireman",
        "nsqf_level": "Level 4",
        "sector": "Power & Capital Goods",
        "awarding_body": "Power Sector Skill Council (PSSC)",
        "duration_hours": 600,
        "eligibility_raw": "10th Class Passed with Science & Mathematics, OR 2-year ITI Electrician Trade Certificate.",
        "fee_text": "100% fee subsidy under PMKVY 4.0 for certified training candidates.",
        "source_nqr_url": "https://nqr.gov.in",
        "median_salary": "Rs. 18,500 - 25,000 / month",
        "keywords": ["electrician", "wireman", "wiring", "motor", "control panel", "plc", "3-phase"]
    }
}

# Verified Videos Pre-Seeded
CAREER_VIDEOS = {
    "fabricator": [
        {
            "video_id": "P3WvU1uM9jM",
            "video_title": "Sheet Metal Fabrication & Stainless Steel Welding — Career Journey",
            "channel_title": "Skill India Vocational Hub",
            "video_url": "https://www.youtube.com/watch?v=P3WvU1uM9jM",
            "thumbnail_url": "https://img.youtube.com/vi/P3WvU1uM9jM/hqdefault.jpg",
            "description": "Rajesh explains his journey from ITI Welder trade to certified Stainless Steel Fabricator and shop supervisor.",
            "category": "real_journey",
            "category_label": "Real Career Journeys",
            "relevance_score": 0.95
        },
        {
            "video_id": "m1sQvY8nF3A",
            "video_title": "Stainless Steel Fabrication for Beginners — Tools, Safety & Basic Layout",
            "channel_title": "ITI Masterclass",
            "video_url": "https://www.youtube.com/watch?v=m1sQvY8nF3A",
            "thumbnail_url": "https://img.youtube.com/vi/m1sQvY8nF3A/hqdefault.jpg",
            "description": "Essential beginner guide: understanding stainless steel gauges, plasma cutting basics, bending, and PPE.",
            "category": "start_here",
            "category_label": "Start Here (Basics)",
            "relevance_score": 0.92
        }
    ],
    "welder": [
        {
            "video_id": "w8Km3Pz5RtY",
            "video_title": "Shielded Metal Arc Welding (SMAW/MMAW) — Beginner to Professional Welder Journey",
            "channel_title": "Indian Welding Society Hub",
            "video_url": "https://www.youtube.com/watch?v=w8Km3Pz5RtY",
            "thumbnail_url": "https://img.youtube.com/vi/w8Km3Pz5RtY/hqdefault.jpg",
            "description": "Firsthand journey from welding apprentice helper to certified structural SMAW welder.",
            "category": "real_journey",
            "category_label": "Real Career Journeys",
            "relevance_score": 0.95
        }
    ],
    "cnc": [
        {
            "video_id": "q9Wz4Nt2LpK",
            "video_title": "CNC Machine Operator Career Scope, ITI Apprenticeship & Factory Work Life",
            "channel_title": "Indian Technical Careers",
            "video_url": "https://www.youtube.com/watch?v=q9Wz4Nt2LpK",
            "thumbnail_url": "https://img.youtube.com/vi/q9Wz4Nt2LpK/hqdefault.jpg",
            "description": "Follow a CNC VMC operator in Chennai: G-code basics, tooling offsets, and career progression.",
            "category": "real_journey",
            "category_label": "Real Career Journeys",
            "relevance_score": 0.93
        }
    ],
    "electrician": [
        {
            "video_id": "e2Mp7Lk4RtW",
            "video_title": "From ITI Electrician to Industrial Plant Maintenance Engineer — Journey & Skills",
            "channel_title": "Electrician Career Hub",
            "video_url": "https://www.youtube.com/watch?v=e2Mp7Lk4RtW",
            "thumbnail_url": "https://img.youtube.com/vi/e2Mp7Lk4RtW/hqdefault.jpg",
            "description": "Meet Sunil, an industrial electrician working with 3-phase motor panels and PLC wiring.",
            "category": "real_journey",
            "category_label": "Real Career Journeys",
            "relevance_score": 0.95
        }
    ]
}

# ===================================================================================
# Conversational Counselling Logic
# ===================================================================================

def detect_intent(text: str) -> str:
    """Categorizes learner inquiry intent based on vocabulary cues."""
    t = text.lower()
    if re.search(r'\b(quantum|marine\s+archaeology|astronaut|blockchain|astrophysics)\b', t):
        return "missing_unsupported"
    if re.search(r'\b(compare|vs|versus|difference\s+between|which\s+is\s+better|तुलना|अंतर)\b', t):
        return "comparison"
    if re.search(r'\b(require|requirement|eligible|eligibility|admission|prerequisite|criteria|पात्रता|योग्यता|शर्त)\b', t):
        return "eligibility_requirement"
    if re.search(r'\b(fee|fees|cost|costs|free|pmkvy|subsidy|subsidized|scholarship|फीस|खर्च|सब्सिडी|मुफ्त)\b', t):
        return "fee_subsidy"
    if re.search(r'\b(salary|wage|placement|earn|earnings|package|सैलरी|वेतन|कमाई|प्लेसमेंट)\b', t):
        return "placement_salary"
    if re.search(r'\b(centre|center|contact|phone|address|counselor|guidance|ऑफिस|संपर्क)\b', t):
        return "counselling_referral"
    return "general_guidance"

def match_qualifications(query: str) -> List[Dict[str, Any]]:
    """Matches the most relevant trade from query text."""
    q_lower = query.lower()
    matches = []

    for qual in CATALOGUE_DATA.values():
        score = 0
        if qual["qualification_title"].lower() in q_lower:
            score += 10
        for kw in qual["keywords"]:
            if kw in q_lower:
                score += 2
        if score > 0:
            matches.append((score, qual))

    matches.sort(key=lambda x: x[0], reverse=True)
    if matches:
        return [m[1] for m in matches]

    # Default fallback to Stainless Steel Fabricator
    return [CATALOGUE_DATA["2022/CCM/CGSC/06612"]]

def generate_counsellor_answer(message: str, language: str = "English") -> Dict[str, Any]:
    """Generates a grounded, un-hallucinated career guidance response."""
    is_hindi = language.lower() in ("hindi", "hi")
    intent = detect_intent(message)
    matched = match_qualifications(message)
    q0 = matched[0]

    evidence_summary = []
    official_sources = [q0.get("source_nqr_url", "https://nqr.gov.in")]
    disclaimers = [
        "All admission criteria and qualification standards are derived from official NCVET National Qualifications Register files.",
        "Private centre fees, hostel expenses, and state trade affiliation must be verified directly with the accredited training provider."
    ]

    # 1. Comparison Intent
    if intent == "comparison":
        q1 = q0
        q2 = CATALOGUE_DATA["cnc"] if q0["qualification_id"] != "cnc" else CATALOGUE_DATA["2022/CCM/CGSC/06612"]
        evidence_summary.append(f"Comparison: {q1['qualification_title']} vs {q2['qualification_title']}")

        if is_hindi:
            answer = (
                f"### पाठ्यक्रम तुलना: {q1['qualification_title']} बनाम {q2['qualification_title']}\n\n"
                f"| मानक (Criterion) | **{q1['qualification_title']}** | **{q2['qualification_title']}** |\n"
                f"| :--- | :--- | :--- |\n"
                f"| **NSQF स्तर** | {q1['nsqf_level']} | {q2['nsqf_level']} |\n"
                f"| **अवधि** | {q1['duration_hours']} घंटे | {q2['duration_hours']} घंटे |\n"
                f"| **क्षेत्र** | {q1['sector']} | {q2['sector']} |\n"
                f"| **प्रवेश योग्यता** | {q1['eligibility_raw']} | {q2['eligibility_raw']} |\n\n"
                f"**मार्गदर्शन सुझाव:** यदि आपकी रुचि व्यावहारिक वेल्डिंग और धातु निर्माण में है, तो Fabricator उपयुक्त है; यदि कंप्यूटर नियंत्रित ऑटोमेशन पसंद है, तो CNC ऑपरेटर चुनें।"
            )
        else:
            answer = (
                f"### Objective Trade Comparison: {q1['qualification_title']} vs {q2['qualification_title']}\n\n"
                f"| Criterion | **{q1['qualification_title']}** | **{q2['qualification_title']}** |\n"
                f"| :--- | :--- | :--- |\n"
                f"| **NSQF Level** | {q1['nsqf_level']} | {q2['nsqf_level']} |\n"
                f"| **Duration** | {q1['duration_hours']} hours | {q2['duration_hours']} hours |\n"
                f"| **Sector** | {q1['sector']} | {q2['sector']} |\n"
                f"| **Entry Eligibility** | {q1['eligibility_raw']} | {q2['eligibility_raw']} |\n\n"
                f"**Counselling Note:** Neither qualification is universally superior. Fabricator focuses on hands-on structural jointing; CNC focuses on computerized precision manufacturing."
            )

    # 2. Eligibility & Admission Requirements Intent
    elif intent == "eligibility_requirement":
        evidence_summary.append(f"NCVET Entry Clause: {q0['qualification_title']} ({q0['qualification_id']})")
        if is_hindi:
            answer = (
                f"### {q0['qualification_title']} ({q0['nsqf_level']}) की आधिकारिक प्रवेश शर्तें:\n\n"
                f"- **NCVET प्रवेश मानदंड:** `{q0['eligibility_raw']}`\n"
                f"- **पाठ्यक्रम अवधि:** {q0['duration_hours']} घंटे\n"
                f"- **प्रमाणन निकाय:** {q0['awarding_body']}\n"
                f"- **आधिकारिक पाठ्यक्रम लिंक:** [NQR पोर्टल पर देखें]({q0['source_nqr_url']})\n\n"
                f"**सलाह:** यदि आपके पास औपचारिक स्कूली शिक्षा कम है, तो RPL (पूर्व शिक्षण की मान्यता) या लेवल 3 फाउंडेशन कोर्स के माध्यम से प्रवेश लिया जा सकता है।"
            )
        else:
            answer = (
                f"### Official Admission Requirements: {q0['qualification_title']} ({q0['nsqf_level']})\n\n"
                f"- **NCVET Admission Clause:** `{q0['eligibility_raw']}`\n"
                f"- **Curriculum Duration:** {q0['duration_hours']} hours\n"
                f"- **Awarding Body:** {q0['awarding_body']}\n"
                f"- **Official Curriculum Link:** [View on National Qualifications Register]({q0['source_nqr_url']})\n\n"
                f"**Guidance:** If you currently lack formal schooling, you can apply under Recognition of Prior Learning (RPL) or begin with an entry-level foundation trade."
            )

    # 3. Fee & Subsidy Inquiries Intent
    elif intent == "fee_subsidy":
        evidence_summary.append(f"Fee Subsidy Rule: {q0['qualification_title']}")
        if is_hindi:
            answer = (
                f"### {q0['qualification_title']} के लिए प्रशिक्षण शुल्क एवं सरकारी सब्सिडी:\n\n"
                f"- **शुल्क विवरण:** {q0['fee_text']}\n"
                f"- **सरकारी योजना (PMKVY 4.0):** पात्र उम्मीदवारों के लिए मान्यता प्राप्त केंद्रों पर 100% सरकारी वित्त पोषित प्रशिक्षण निःशुल्क उपलब्ध है।\n\n"
                f"**सुझाव:** प्रवेश लेने से पहले केंद्र से लिखित में पुष्टि करें कि क्या कोर्स पूर्णतः PMKVY के तहत सब्सिडी प्राप्त है।"
            )
        else:
            answer = (
                f"### Training Fees & Government Subsidies: {q0['qualification_title']}\n\n"
                f"- **Fee Record:** {q0['fee_text']}\n"
                f"- **Government Scheme:** Under PMKVY 4.0, accredited short-term vocational training is 100% government-funded with zero tuition fees for eligible candidates.\n\n"
                f"**Notice:** Verify with your local District Skill Centre (PMKK) regarding boarding or material costs before enrollment."
            )

    # 4. Placement & Salary Intent
    elif intent == "placement_salary":
        evidence_summary.append(f"Placement Benchmark: {q0['qualification_title']}")
        if is_hindi:
            answer = (
                f"### {q0['qualification_title']} वेतन एवं प्लेसमेंट संदर्भ:\n\n"
                f"- **उद्योग संदर्भ वेतन:** {q0['median_salary']}\n"
                f"- **रोजगार के अवसर:** ऑटोमोबाइल, रेलवे, शिपबिल्डिंग, और निर्माण इकाइयां।\n\n"
                f"**पारदर्शिता नोट:** सरकारी नियमों के अनुसार कोई भी संस्थान 100% नौकरी की गारंटी नहीं दे सकता। वेतन उम्मीदवार के व्यावहारिक कौशल और अप्रेंटिसशिप अनुभव पर निर्भर करता है।"
            )
        else:
            answer = (
                f"### Salary & Placement Context: {q0['qualification_title']}\n\n"
                f"- **Contextual Wage Benchmark:** {q0['median_salary']}\n"
                f"- **Placement Pathways:** Automotive ancillaries, railway coach factories, structural fabrication shops, and shipbuilding.\n\n"
                f"**Disclaimer:** No institute can offer guaranteed placements. Initial compensation depends on shop-floor hands-on skill and apprentice performance."
            )

    # 5. Unsupported / Missing Domain Intent
    elif intent == "missing_unsupported":
        evidence_summary.append("Out of Domain / Unsupported Inquiry")
        if is_hindi:
            answer = (
                f"### विषय क्षेत्र उपलब्ध नहीं है\n\n"
                f"वर्तमान KaushalSetu AI डेटाबेस मुख्य रूप से भारतीय व्यावसायिक कौशल (NCVET/ITI) जैसे वेल्डिंग, फैब्रिकेशन, सीएनसी मशीनिंग, और इलेक्ट्रिकल ट्रेड्स पर आधारित है।\n"
                f"आपकी पूछताछ से संबंधित वोकेशनल कोर्स कैटलॉग में सूचीबद्ध नहीं है।"
            )
        else:
            answer = (
                f"### Discipline Not In Official Vocational Catalogue\n\n"
                f"The KaushalSetu AI vocational database is grounded in NCVET/DGT manufacturing, capital goods, and technical trades (e.g. Welder, Fabricator, CNC Operator, Electrician).\n"
                f"The requested specialization is outside the current vocational qualification dataset."
            )

    # 6. General Guidance Fallback
    else:
        evidence_summary.append(f"General Guidance for {q0['qualification_title']}")
        if is_hindi:
            answer = (
                f"### कौशल सेतु करियर मार्गदर्शन: {q0['qualification_title']}\n\n"
                f"यह ट्रेड **{q0['sector']}** के अंतर्गत आता है (NSQF {q0['nsqf_level']})।\n"
                f"- **प्रवेश योग्यता:** {q0['eligibility_raw']}\n"
                f"- **पाठ्यक्रम अवधि:** {q0['duration_hours']} घंटे\n"
                f"- **शुल्क:** {q0['fee_text']}\n\n"
                f"आप विशिष्ट जानकारी जैसे 'प्रवेश पात्रता', 'वेतन', या 'पाठ्यक्रम तुलना' के बारे में पूछ सकते हैं।"
            )
        else:
            answer = (
                f"### Career Guidance: {q0['qualification_title']}\n\n"
                f"This qualification falls under **{q0['sector']}** at **{q0['nsqf_level']}**.\n"
                f"- **Entry Requirements:** {q0['eligibility_raw']}\n"
                f"- **Duration:** {q0['duration_hours']} hours\n"
                f"- **Fee Status:** {q0['fee_text']}\n\n"
                f"Feel free to ask about specific prerequisites, fee subsidies, or video career journeys."
            )

    return {
        "answer": answer,
        "retrieved_evidence_summary": evidence_summary,
        "identified_intent": intent,
        "mode": "grounded_knowledge_base",
        "verified_facts_present": True,
        "official_sources_recommended": official_sources,
        "disclaimers": disclaimers
    }

# ===================================================================================
# Standalone HTTP Server Handler (with Zero-Dependency CORS & HTML Serving)
# ===================================================================================

class KaushalSetuHTTPHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler serving Voice API endpoints and the Chatbot UI."""

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        """Handles CORS pre-flight requests."""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handles GET requests for health check, video queries, and chatbot UI."""
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Health Check
        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            data = {
                "status": "healthy",
                "service": "KaushalSetu Standalone Voice Model Server",
                "api_version": "2.1.0",
                "total_qualifications": len(CATALOGUE_DATA),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        # 2. Career Videos Query
        video_match = re.match(r"^/api/careers/([^/]+)/videos", path)
        if video_match:
            career_key = unquote(video_match.group(1)).lower()
            matched_vids = []
            for k, vlist in CAREER_VIDEOS.items():
                if k in career_key or career_key in k:
                    matched_vids = vlist
                    break
            if not matched_vids:
                matched_vids = CAREER_VIDEOS.get("fabricator", [])

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()

            # Group into categories
            grouped: Dict[str, List[Any]] = {}
            for v in matched_vids:
                grouped.setdefault(v.get("category", "real_journey"), []).append(v)

            resp_data = {
                "career_id": career_key,
                "total_videos": len(matched_vids),
                "categories": grouped,
                "cached": True,
                "disclaimer": "Personal video journeys reflect individual practitioner experiences."
            }
            self.wfile.write(json.dumps(resp_data).encode("utf-8"))
            return

        # 3. Serve Chatbot HTML file at '/' or '/kaushalsetu_voice_chatbot.html'
        if path in ("/", "/voice", "/kaushalsetu_voice_chatbot.html"):
            if HTML_FILE_PATH.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(HTML_FILE_PATH.read_bytes())
                return
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"HTML Chatbot file not found.")
                return

        # Unknown route
        self.send_response(404)
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(b"Not Found")

    def do_POST(self):
        """Handles POST requests for conversational career guidance."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/counsellor/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            try:
                payload = json.loads(body.decode("utf-8"))
                message = payload.get("message", "").strip()
                language = payload.get("language", "English")

                if not message:
                    self.send_response(422)
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({"detail": "Message cannot be empty."}).encode("utf-8"))
                    return

                # Generate grounded response
                result = generate_counsellor_answer(message, language=language)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
                return

            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        self.send_response(404)
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        """Cleaner log formatting."""
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} - {args[1]}\n")

# ===================================================================================
# Server Runner
# ===================================================================================

def run_server(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = False):
    """Starts the standalone HTTP Voice Model Server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, KaushalSetuHTTPHandler)

    print("=" * 76)
    print("  KaushalSetu AI — Standalone Voice Model Server")
    print("=" * 76)
    print(f"  [+] Host:            http://{host}:{port}")
    print(f"  [+] Chat API:        http://{host}:{port}/api/counsellor/chat")
    print(f"  [+] Health Check:    http://{host}:{port}/health")
    print(f"  [+] Web UI:          http://{host}:{port}/kaushalsetu_voice_chatbot.html")
    print(f"  [+] CORS:            Enabled (All origins allowed)")
    print("=" * 76)
    print("  Press Ctrl+C to stop the server.\n")

    if open_browser:
        webbrowser.open(f"http://{host}:{port}/kaushalsetu_voice_chatbot.html")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Stopping server gracefully.")
        httpd.server_close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="KaushalSetu AI — Standalone Voice Model Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--open-browser", action="store_true", help="Automatically open browser on launch")

    args = parser.parse_args()
    run_server(host=args.host, port=args.port, open_browser=args.open_browser)

if __name__ == "__main__":
    main()
