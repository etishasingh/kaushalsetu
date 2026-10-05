(() => {
  const params = new URLSearchParams(location.search);
  const API_BASE_URL = (
    params.get("api") ||
    window.API_BASE_URL ||
    (location.protocol === "file:" ? "http://127.0.0.1:8000" : "")
  ).replace(/\/+$/, "");

  const $ = (id) => document.getElementById(id);
  const screens = ["homeScreen","intakeScreen","resultsScreen","detailScreen","chatScreen"].map($);
  let profilePayload = null;
  let recommendations = [];
  let selectedCareer = null;
  let previousScreen = "resultsScreen";
  let lastChatQuestion = "";
  let careerVideos = {};
  let activeVideoCategory = "all";
  let speechRecognition = null;

  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));

  function showScreen(id) {
    screens.forEach(s => s.classList.toggle("active", s.id === id));
    window.scrollTo({top:0, behavior:"instant"});
  }

  function toast(message) {
    const el = $("toast");
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => el.classList.remove("show"), 2800);
  }

  function openModal(id) {
    $(id)?.classList.remove("hidden");
  }
  function closeModals() {
    document.querySelectorAll(".modal").forEach(m => m.classList.add("hidden"));
  }

  async function api(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {"Content-Type":"application/json", ...(options.headers || {})}
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
    return data;
  }

  function statusClass(status) {
    if (status === "ELIGIBLE") return "eligible";
    if (status === "INELIGIBLE") return "ineligible";
    return "unknown";
  }

  function parseMarkdown(text) {
    let html = esc(text || "");
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/`(.+?)`/g, "<code>$1</code>");
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1 ↗</a>');
    html = html.replace(/^- (.+)$/gm, "<div>• $1</div>");
    html = html.replace(/\n\n/g, "<br><br>").replace(/\n/g, "<br>");
    return html;
  }

  function profileFromForm() {
    const interests = $("interests").value.split(",").map(s => s.trim()).filter(Boolean);
    const activities = $("preferredActivities").value.split(",").map(s => s.trim()).filter(Boolean);
    const maxDuration = parseFloat($("maxDuration").value);
    const maxBudget = parseFloat($("maxBudget").value);
    return {
      interests,
      preferred_activities: activities,
      existing_qualification: $("education").value || null,
      prior_experience_years: parseFloat($("experience").value) || 0,
      current_district: $("district").value.trim() || null,
      current_state: $("state").value.trim() || null,
      willingness_to_relocate: $("relocation").value,
      max_duration_hours: Number.isFinite(maxDuration) ? maxDuration : null,
      max_budget_inr: Number.isFinite(maxBudget) ? maxBudget : null,
      language_preference: $("languagePref").value,
      exclude_ineligible: $("excludeIneligible").checked,
      exclude_unknown_location: $("excludeUnknownLocation").checked,
      exclude_unknown_fees: $("excludeUnknownFees").checked,
      top_k: 5
    };
  }

  function renderRecommendations(cards) {
    const row = $("recommendationRow");
    row.innerHTML = "";
    $("resultCount").innerHTML = `${String(cards.length).padStart(2,"0")}<br><span>OPTIONS</span>`;

    cards.forEach((card, index) => {
      const score = Math.round((card.hybrid_score || 0) * 100);
      const prov = card.training_provider_evidence || {};
      const el = document.createElement("article");
      el.className = "rec-card";
      el.innerHTML = `
        <span class="rec-rank">0${index + 1} / PATH</span>
        <h3>${esc(card.display_title || card.qualification_title)}</h3>
        <p class="rec-role">${esc(card.job_role || card.sector)}</p>
        <div class="rec-score"><b>${score}%</b><span>match</span></div>
        <div class="rec-meta">
          ${esc(card.nsqf_level)}<br>
          ${esc(card.duration_hours)} hours<br>
          ${esc(card.awarding_body)}
        </div>
        <span class="status-pill ${statusClass(card.eligibility_status)}">${esc(card.eligibility_status)}</span>
        <button class="outline-button detail-button" data-id="${esc(card.qualification_id)}">View in detail →</button>
      `;
      row.appendChild(el);
    });
    row.querySelectorAll(".detail-button").forEach(btn => {
      btn.addEventListener("click", () => openCareerDetail(btn.dataset.id));
    });
  }

  async function generateRecommendations() {
    $("resultsContent").classList.add("hidden");
    $("resultsError").classList.add("hidden");
    $("resultsLoading").classList.remove("hidden");
    showScreen("resultsScreen");

    try {
      if (!profilePayload) profilePayload = profileFromForm();
      const data = await api("/api/recommendations", {
        method:"POST",
        body:JSON.stringify(profilePayload)
      });
      recommendations = data.recommendations || [];
      if (!recommendations.length) throw new Error("No recommendations matched the current filters. Try widening your duration, location or evidence filters.");
      renderRecommendations(recommendations);
      $("resultsLoading").classList.add("hidden");
      $("resultsContent").classList.remove("hidden");
    } catch (err) {
      $("resultsLoading").classList.add("hidden");
      $("resultsError").classList.remove("hidden");
      $("resultsErrorText").textContent = err.message;
    }
  }

  function setText(id, value) {
    $(id).textContent = value ?? "";
  }

  function renderCareerDetail(card) {
    selectedCareer = card;
    setText("detailSector", (card.sector || "CAREER").toUpperCase());
    setText("detailTitle", card.display_title || card.qualification_title);
    setText("detailRole", card.job_role || "Career pathway");
    setText("detailScore", `${Math.round((card.hybrid_score || 0) * 100)}%`);

    const tags = [
      card.nsqf_level,
      card.awarding_body,
      `${card.duration_hours} hours`
    ].filter(Boolean);
    $("detailTags").innerHTML = tags.map(t => `<span class="detail-tag">${esc(t)}</span>`).join("");

    $("detailExplanation").innerHTML = parseMarkdown(
      profilePayload?.language_preference === "Hindi" ? card.explanation_hindi : card.explanation_english
    );

    const sb = card.score_breakdown || {};
    const labels = [
      ["Text relevance","text_relevance"],["Skills overlap","skills_overlap"],
      ["Preference match","preference_match"],["Eligibility","eligibility_score"],
      ["Evidence","evidence_completeness"]
    ];
    $("scoreBreakdown").innerHTML = labels.map(([label,key]) => {
      const value = Math.round((Number(sb[key]) || 0) * 100);
      return `<div><div class="score-bar-label"><span>${label}</span><b>${value}%</b></div><div class="score-bar"><i style="width:${value}%"></i></div></div>`;
    }).join("");

    setText("eligibilityTitle", card.eligibility_status || "UNKNOWN");
    $("eligibilityTitle").className = `status-pill ${statusClass(card.eligibility_status)}`;
    setText("eligibilityReason", card.eligibility_reason);

    $("courseFacts").innerHTML = [
      ["Qualification",card.qualification_title],
      ["Sector",card.sector],
      ["NSQF level",card.nsqf_level],
      ["Duration",`${card.duration_hours} hours`],
      ["Awarding body",card.awarding_body],
      ["Location status",`${card.location_status || "UNKNOWN"} — ${card.location_reason || ""}`],
      ["Fee status",`${card.fee_status || "UNKNOWN"} — ${card.fee_reason || ""}`]
    ].map(([a,b]) => `<div><dt>${esc(a)}</dt><dd>${esc(b)}</dd></div>`).join("");

    const p = card.training_provider_evidence || {};
    $("providerFacts").innerHTML = `
      <p><strong>${esc(p.provider_name || "Unspecified / search required")}</strong><br>${esc(p.location || "Location not linked")}</p>
      <p><strong>Fee:</strong> ${esc(p.fee_details)}<br><strong>Affiliation:</strong> ${esc(p.affiliation_status)}</p>
      <p><strong>Placement claim:</strong> ${esc(p.placement_claims || "None on record")}<br><strong>Audit evidence:</strong> ${esc(p.placement_audit_evidence || "Not linked")}</p>
      ${p.source_sidh_url ? `<a href="${esc(p.source_sidh_url)}" target="_blank" rel="noopener">View linked SIDH record ↗</a>` : ""}
    `;

    const e = card.employment_evidence || {};
    $("employmentFacts").innerHTML = `
      <p><strong>Live NCS evidence</strong><br>${esc(e.live_ncs_job || "No direct active vacancy in sample")}</p>
      <p><strong>Contextual benchmark</strong><br>${esc(e.macro_benchmark || "General sector benchmark")}</p>
      <p class="modal-footnote">Benchmark figures are contextual and are not a guaranteed individual salary.</p>
    `;

    const missing = card.missing_information || [];
    $("missingFacts").innerHTML = missing.length
      ? missing.map(x => `<li>${esc(x)}</li>`).join("")
      : "<li>No missing-information flags were returned for this record.</li>";

    const questions = card.trade_offs_and_investigation_questions || [];
    $("questionsList").innerHTML = questions.map(x => `<li>${esc(x)}</li>`).join("");

    const url = card.source_nqr_url || "https://nqr.gov.in";
    $("nqrLink").href = url;
    setText("sourceMeta", `National Qualifications Register • Last verified ${card.last_verified || "not specified"}`);
  }

  async function openCareerDetail(id) {
    previousScreen = "resultsScreen";
    showScreen("detailScreen");
    $("detailContent").classList.add("hidden");
    $("detailLoading").classList.remove("hidden");
    try {
      const card = await api(`/api/careers/${encodeURIComponent(id)}`);
      const ranked = recommendations.find(r => r.qualification_id === id);
      // Direct lookup has complete evidence; preserve the ranked score/explanation when available.
      renderCareerDetail(ranked ? {...card, ...ranked} : card);
      loadCareerVideos(false);
      $("detailLoading").classList.add("hidden");
      $("detailContent").classList.remove("hidden");
    } catch (err) {
      $("detailLoading").classList.add("hidden");
      toast(err.message);
      showScreen("resultsScreen");
    }
  }

  function renderCareerVideos(data) {
    careerVideos = data?.categories || {};
    const tabs = $("videoCategoryTabs");
    const grid = $("careerVideoGrid");
    const notice = $("videoJourneyNotice");
    const labels = data?.category_labels || {};
    const entries = Object.entries(careerVideos);
    activeVideoCategory = "all";

    const total = Number(data?.total_videos || 0);
    notice.textContent = data?.message || (total ? `${total} career-journey videos available.` : "No verified videos are available for this career yet.");
    tabs.innerHTML = [
      `<button type="button" class="video-tab active" data-video-category="all">All <span>${total}</span></button>`,
      ...entries.map(([key, videos]) => `<button type="button" class="video-tab" data-video-category="${esc(key)}">${esc((labels[key] || key).replace(/\s*—\s*/g, " · "))} <span>${videos.length}</span></button>`)
    ].join("");

    const allVideos = entries.flatMap(([category, videos]) => videos.map(v => ({...v, _category: category})));
    const render = () => {
      const videos = activeVideoCategory === "all" ? allVideos : allVideos.filter(v => v._category === activeVideoCategory);
      grid.innerHTML = videos.length ? videos.map(v => `
        <article class="career-video-card">
          <a class="video-thumb" href="${esc(v.video_url)}" target="_blank" rel="noopener noreferrer">
            <img src="${esc(v.thumbnail_url || "")}" alt="" loading="lazy" onerror="this.style.display='none'">
            <span class="video-play">▶</span>
          </a>
          <div class="video-card-body">
            <span class="video-category-label">${esc(labels[v._category] || v._category)}</span>
            <h4>${esc(v.video_title)}</h4>
            <p class="video-channel">${esc(v.channel_title)} · ${esc(v.language)}</p>
            <p>${esc(v.description)}</p>
            <div class="video-score"><span>Relevance</span><b>${Math.round(Number(v.relevance_score || 0) * 100)}%</b></div>
            <a class="watch-link" href="${esc(v.video_url)}" target="_blank" rel="noopener noreferrer">Watch on YouTube ↗</a>
          </div>
        </article>`).join("") : `<div class="video-empty">No videos in this category.</div>`;
    };
    render();
    tabs.querySelectorAll("[data-video-category]").forEach(btn => btn.addEventListener("click", () => {
      activeVideoCategory = btn.dataset.videoCategory;
      tabs.querySelectorAll(".video-tab").forEach(x => x.classList.toggle("active", x === btn));
      render();
    }));
  }

  async function loadCareerVideos(forceRefresh = false) {
    if (!selectedCareer?.qualification_id) return;
    $("videoJourneyNotice").textContent = "Loading verified career-journey videos…";
    try {
      const language = $("videoLanguageSelect").value;
      const q = new URLSearchParams({language});
      if (forceRefresh) q.set("force_refresh", "true");
      const data = await api(`/api/careers/${encodeURIComponent(selectedCareer.qualification_id)}/videos?${q.toString()}`);
      renderCareerVideos(data);
    } catch (err) {
      $("videoJourneyNotice").textContent = `Video explorer unavailable: ${err.message}`;
      $("careerVideoGrid").innerHTML = "";
    }
  }

  function setupVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const btn = $("chatMicBtn");
    if (!SpeechRecognition) {
      btn.disabled = true;
      btn.title = "Speech recognition is not supported by this browser";
      return;
    }
    speechRecognition = new SpeechRecognition();
    speechRecognition.continuous = false;
    speechRecognition.interimResults = false;
    speechRecognition.onstart = () => { btn.classList.add("listening"); $("voiceStatus").classList.remove("hidden"); };
    speechRecognition.onresult = event => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      if (transcript) $("chatInput").value = transcript;
    };
    speechRecognition.onerror = event => {
      toast(event.error === "not-allowed" ? "Microphone permission was blocked." : "I couldn't hear that. Please try again.");
    };
    speechRecognition.onend = () => { btn.classList.remove("listening"); $("voiceStatus").classList.add("hidden"); };
    btn.addEventListener("click", () => {
      speechRecognition.lang = (profilePayload?.language_preference || $("videoLanguageSelect")?.value || "English") === "Hindi" ? "hi-IN" : "en-IN";
      try { speechRecognition.start(); } catch (_) {}
    });
  }

  function speakLastAnswer() {
    const bubbles = document.querySelectorAll(".chat-bubble.bot");
    const latest = bubbles[bubbles.length - 1];
    if (!latest || !window.speechSynthesis) return;
    const text = latest.innerText.replace(/^KAUSHALSETU COUNSELLOR/i, "").trim();
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = (profilePayload?.language_preference || "English") === "Hindi" ? "hi-IN" : "en-IN";
    window.speechSynthesis.speak(utterance);
  }

  function openChat(career = null) {
    previousScreen = career ? "detailScreen" : "resultsScreen";
    if (career) {
      selectedCareer = career;
      setText("chatContextTitle", career.display_title || career.qualification_title);
      setText("chatContextMeta", `${career.nsqf_level || ""} • ${career.sector || ""}`);
    } else {
      selectedCareer = null;
      setText("chatContextTitle", "General career guidance");
      setText("chatContextMeta", "Ask about the recommendation set.");
    }
    showScreen("chatScreen");
    $("chatInput").focus();
  }

  function appendChat(role, text, evidence = [], sources = []) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;
    if (role === "user") {
      bubble.innerHTML = `<div class="bubble-label">YOU</div><div>${esc(text)}</div>`;
    } else {
      bubble.innerHTML = `
        <div class="bubble-label">KAUSHALSETU COUNSELLOR</div>
        <div>${parseMarkdown(text)}</div>
        <button class="speak-answer" type="button" title="Read this answer aloud">🔊 Read aloud</button>
        ${evidence.length ? `<div class="chat-evidence">${evidence.map(x => `<span>${esc(x)}</span>`).join("")}</div>` : ""}
        ${sources.length ? `<div style="font-size:9px;margin-top:9px;color:#747d73">Official reference: ${sources.map(x => esc(x)).join(" • ")}</div>` : ""}
      `;
    }
    $("chatMessages").appendChild(bubble);
    bubble.querySelector(".speak-answer")?.addEventListener("click", () => {
      const textToSpeak = (bubble.innerText || "").replace(/^KAUSHALSETU COUNSELLOR\s*/i, "").replace(/Read aloud/g, "").trim();
      if (window.speechSynthesis && textToSpeak) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(textToSpeak);
        u.lang = (profilePayload?.language_preference || "English") === "Hindi" ? "hi-IN" : "en-IN";
        window.speechSynthesis.speak(u);
      }
    });
    $("chatMessages").scrollTop = $("chatMessages").scrollHeight;
  }

  async function sendChat(questionOverride = null) {
    const input = $("chatInput");
    const query = (questionOverride || input.value).trim();
    if (!query) return;
    input.value = "";
    lastChatQuestion = query;
    appendChat("user", query);
    $("chatLoading").classList.remove("hidden");
    $("chatSendBtn").disabled = true;

    try {
      const payload = {
        message: query,
        language: profilePayload?.language_preference || "English",
        selected_qualification_id: selectedCareer?.qualification_id || null,
        profile_context: profilePayload || null
      };
      const data = await api("/api/counsellor/chat", {method:"POST",body:JSON.stringify(payload)});
      appendChat("bot", data.answer, data.retrieved_evidence_summary || [], data.official_sources_recommended || []);
    } catch (err) {
      appendChat("bot", `I couldn't connect to the counselling service. ${err.message}`);
    } finally {
      $("chatLoading").classList.add("hidden");
      $("chatSendBtn").disabled = false;
      input.focus();
    }
  }

  // Navigation
  document.querySelectorAll("[data-home]").forEach(btn => btn.addEventListener("click", () => showScreen("homeScreen")));
  document.querySelectorAll("[data-go]").forEach(btn => btn.addEventListener("click", () => showScreen(btn.dataset.go)));
  $("startBtn").addEventListener("click", () => showScreen("intakeScreen"));
  $("editProfileBtn").addEventListener("click", () => showScreen("intakeScreen"));
  $("backToResults").addEventListener("click", () => showScreen("resultsScreen"));
  $("backFromChat").addEventListener("click", () => showScreen(previousScreen));
  $("resultsChatBtn").addEventListener("click", () => openChat());
  $("detailChatBtn").addEventListener("click", () => openChat(selectedCareer));
  $("refreshVideosBtn").addEventListener("click", () => loadCareerVideos(true));
  $("videoLanguageSelect").addEventListener("change", () => loadCareerVideos(false));
  setupVoiceInput();

  $("learnerProfileForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    profilePayload = profileFromForm();
    await generateRecommendations();
  });
  $("retryResults").addEventListener("click", generateRecommendations);

  $("advancedToggle").addEventListener("click", () => {
    const panel = $("advancedFields");
    const hidden = panel.classList.toggle("hidden");
    $("advancedToggle").lastElementChild.textContent = hidden ? "＋" : "−";
  });

  document.querySelectorAll("[data-modal]").forEach(btn => btn.addEventListener("click", () => openModal(btn.dataset.modal)));
  document.querySelectorAll("[data-close-modal]").forEach(btn => btn.addEventListener("click", closeModals));
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeModals(); });

  $("counsellorChatForm").addEventListener("submit", e => { e.preventDefault(); sendChat(); });
  document.querySelectorAll(".chat-suggestions button").forEach(btn => btn.addEventListener("click", () => sendChat(btn.dataset.query)));

  // Small connectivity check without blocking the landing page.
  fetch(`${API_BASE_URL}/health`).then(r => r.ok ? r.json() : Promise.reject()).then(data => {
    console.info(`[KaushalSetu] API online — ${data.total_qualifications} qualifications loaded.`);
  }).catch(() => {
    console.warn(`[KaushalSetu] Backend not reachable at ${API_BASE_URL}. It will be checked when recommendations are requested.`);
  });
})();
