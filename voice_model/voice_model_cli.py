#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===================================================================================
KaushalSetu AI — Voice Model Terminal CLI
File: voice_model_cli.py (Single Executable Terminal Voice Interface)
===================================================================================

A terminal-based interface to the KaushalSetu Voice Counselling Model.
Allows interactive guidance conversations in English and Hindi directly from
the command line, with optional speech synthesis and voice capture.

Usage:
    python voice_model_cli.py
    python voice_model_cli.py --query "Prerequisites for Welder" --language "English"
    python voice_model_cli.py --query "वेल्डर बनने के लिए योग्यता क्या है?" --language "Hindi"
===================================================================================
"""

import sys
import os
import argparse
from pathlib import Path

# Windows console encoding safeguard
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import the core counselling engine from voice_model_server
try:
    from voice_model_server import generate_counsellor_answer, CATALOGUE_DATA, detect_intent
except ImportError:
    # If run from another directory, add module dir to sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from voice_model_server import generate_counsellor_answer, CATALOGUE_DATA, detect_intent

def speak_text(text: str, is_hindi: bool = False):
    """Speaks text using Windows SAPI Speech Synthesis if available."""
    if sys.platform == "win32":
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            clean_text = text.replace("#", "").replace("*", "").replace("`", "")
            clean_text = clean_text[:300]  # speak brief summary
            speaker.Speak(clean_text)
            return
        except Exception:
            pass

    # Optional pyttsx3 fallback
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text[:300])
        engine.runAndWait()
    except Exception:
        pass

def run_interactive_session():
    """Runs an interactive conversational session in the console."""
    print("=" * 76)
    print("  KaushalSetu AI — Conversational Voice & Text Counsellor Console")
    print("=" * 76)
    print("  Ask any career question about ITI trades, admission prerequisites,")
    print("  trade comparisons, or PMKVY fee subsidies in English or Hindi.")
    print("  Type 'exit' or 'quit' to end the session.")
    print("=" * 76)

    lang_choice = input("\nSelect Language: [1] English, [2] Hindi (Default: 1): ").strip()
    active_lang = "Hindi" if lang_choice == "2" else "English"

    print(f"\n[+] Active Language: {active_lang}")
    print("[*] Ready. Enter your question below:\n")

    while True:
        try:
            prompt = "\nआप: " if active_lang == "Hindi" else "\nYou: "
            query = input(prompt).strip()
            if not query:
                continue

            if query.lower() in ("exit", "quit", "q", "बाहर"):
                print("Session ended. Namaste!")
                break

            response = generate_counsellor_answer(query, language=active_lang)

            print("\n" + "-" * 76)
            print(f"KaushalSetu AI ({response['mode']}):")
            print("-" * 76)
            print(response["answer"])

            if response.get("retrieved_evidence_summary"):
                print("\n📌 Grounded Evidence Summary:")
                for ev in response["retrieved_evidence_summary"]:
                    print(f"  • {ev}")

            print("-" * 76)

            # Optional audio speech
            speak_text(response["answer"], is_hindi=(active_lang == "Hindi"))

        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Exiting.")
            break

def main():
    parser = argparse.ArgumentParser(description="KaushalSetu AI — Voice Model Terminal CLI")
    parser.add_argument("--query", "-q", type=str, help="Career question or guidance prompt")
    parser.add_argument("--language", "-l", type=str, default="English", help="Language: 'English' or 'Hindi'")
    parser.add_argument("--speak", action="store_true", help="Speak the response aloud via TTS")

    args = parser.parse_args()

    if args.query:
        resp = generate_counsellor_answer(args.query, language=args.language)
        print("\n" + "=" * 76)
        print(f"KaushalSetu AI ({args.language}):")
        print("=" * 76)
        print(resp["answer"])
        print("=" * 76)
        if args.speak:
            speak_text(resp["answer"], is_hindi=(args.language.lower() == "hindi"))
    else:
        run_interactive_session()

if __name__ == "__main__":
    main()
