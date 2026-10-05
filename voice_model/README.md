# KaushalSetu AI — Standalone Voice Model & Chatbot Package

Welcome to the **KaushalSetu AI Voice Model** standalone distribution. This package provides a self-contained, zero-dependency, executable voice and conversational career counsellor for vocational education, ITI trades, admission prerequisites, fee subsidies (PMKVY 4.0), and career progression.

---

## 📦 What's Inside This Folder

| File Name | Type | Description |
| :--- | :--- | :--- |
| **`kaushalsetu_voice_chatbot.html`** | Single-File Executable UI | Standalone frontend containing all HTML, CSS, JavaScript, Web Speech Recognition (STT), Speech Synthesis (TTS), and offline fallback logic in **one single file**. |
| **`voice_model_server.py`** | Standalone Python Server | High-performance HTTP API server built with **100% Python standard library** (Zero `pip install` required). Provides `/api/counsellor/chat`, `/health`, and serves the UI with full CORS. |
| **`run_voice_chatbot.bat`** | Windows 1-Click Launcher | Automatically launches the Voice Model server on port 8000 and opens the chatbot in your default web browser with microphone access allowed. |
| **`run_voice_server.bat`** | Windows 1-Click Server | Starts the backend API server on `http://127.0.0.1:8000`. |
| **`voice_model_cli.py`** | Terminal Voice CLI | Interactive terminal-based counsellor supporting English and Hindi questions directly from the command line. |

---

## 🚀 Quick Start (Running in 3 Seconds)

### Method 1: The 1-Click Windows Launcher (Recommended)
1. Double-click **`run_voice_chatbot.bat`**.
2. It will start the local server on `http://127.0.0.1:8000` and automatically open **`kaushalsetu_voice_chatbot.html`** in your default browser.
3. Click the **Microphone** button or type your question in English or Hindi!

### Method 2: Direct Command Line Launch
Run using standard Python (any version 3.8+):
```bash
python voice_model_server.py --port 8000 --open-browser
```

### Method 3: Offline / No Python Required
If you do not have Python installed, you can simply **double-click `kaushalsetu_voice_chatbot.html`** directly. The chatbot has a built-in offline knowledge engine and will answer questions directly inside your browser!

---

## 🌐 Integration into an Existing Website

If your friend is developing a separate website for KaushalSetu and wants to add the Voice Chatbot, they have three simple options:

### Option A: Embed via `<iframe>` (Easiest — 1 Line of Code)
Place `kaushalsetu_voice_chatbot.html` in the public/static folder of the website and embed it anywhere:

```html
<!-- KaushalSetu AI Floating or Embedded Voice Chatbot -->
<iframe 
  src="/kaushalsetu_voice_chatbot.html" 
  width="460" 
  height="680" 
  style="border: none; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.15);"
  allow="microphone"
  title="KaushalSetu AI Voice Counsellor">
</iframe>
```
*Note: Make sure to include `allow="microphone"` so the browser permits speech recognition inside the iframe.*

### Option B: Call the Voice Model API from JavaScript
If your friend wants to use their own custom UI, they can call the Voice Model server's endpoint:

```javascript
// Example POST request to KaushalSetu Voice Model Server
const response = await fetch('http://127.0.0.1:8000/api/counsellor/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "What are the eligibility requirements for Stainless Steel Fabricator?",
    language: "English" // or "Hindi"
  })
});

const data = await response.json();
console.log(data.answer); // Verified counsellor answer
console.log(data.retrieved_evidence_summary); // Fact-checked citations
```

### Option C: Floating Chat Widget Modal
Add a button to your website that opens `kaushalsetu_voice_chatbot.html` in a popup or modal window:
```html
<button onclick="window.open('/kaushalsetu_voice_chatbot.html', 'KaushalSetuVoice', 'width=500,height=750')">
  🎙️ Open Voice Counsellor
</button>
```

---

## 🎙️ Voice & Speech Features

1. **Speech-to-Text (STT)**:
   - Uses the browser's native Web Speech Recognition API (`webkitSpeechRecognition`).
   - Supports **English (`en-IN`)** and **Hindi (`hi-IN`)**.
   - Live visual pulsing audio wave indicators during active listening.
2. **Text-to-Speech (TTS)**:
   - Uses the browser's native `window.speechSynthesis`.
   - Toggleable mute/unmute button in the top header.
   - Cleans markdown symbols before vocalization for natural, human-like narration.
3. **Microphone Permissions Note**:
   - Modern browsers (Chrome, Edge) require either `http://localhost` or `https://` to permit continuous microphone capture. Running via `run_voice_chatbot.bat` ensures `localhost` origin so microphone access works seamlessly without security warnings.

---

## 📚 Grounded Knowledge Base Included
The model is pre-grounded with verified NCVET and Directorate General of Training (DGT) data:
- **Trades Covered**: Stainless Steel Fabricator (NSQF Level 4), Welder (NSQF Level 3), CNC Operator / Machining Technician (NSQF Level 4), Electrician, and Solar Panel Technician.
- **Topics**: Minimum education eligibility, ITI NTC certificate rules, apprenticeship duration, PMKVY 4.0 zero-fee subsidies, and career salary growth paths.
- **Safety / Fact-Checking**: Automatically refuses to hallucinate unverified eligibility criteria or unapproved courses.
