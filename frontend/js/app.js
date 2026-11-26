/* OSINT IG — Frontend Application
 * Developed by Mohsin Khawaja | CSIB — Cyber Solutions & Information Board
 */
(() => {
  "use strict";

  const MODULE_CATEGORIES = [
    {
      id: "profile",
      title: "Profile Intelligence",
      tools: ["get_user_info", "get_user_propic"],
    },
    {
      id: "network",
      title: "Network Intelligence",
      tools: [
        "get_followers",
        "get_followings",
        "compare_with",
        "get_people_who_tagged",
        "get_people_tagged_by_user",
        "get_people_who_commented",
      ],
    },
    {
      id: "content",
      title: "Content Intelligence",
      tools: [
        "get_hashtags",
        "get_captions",
        "get_comment_data",
        "get_total_comments",
        "get_total_likes",
        "get_posting_times",
        "get_post_comments",
      ],
    },
    {
      id: "media",
      title: "Media Intelligence",
      tools: [
        "get_media_type",
        "get_user_photos",
        "get_user_stories",
        "get_highlights",
        "get_photo_descriptions",
      ],
    },
    {
      id: "location",
      title: "Location & Discovery Intelligence",
      tools: ["get_addrs", "search_location", "search_hashtag"],
    },
    {
      id: "contacts",
      title: "Public Contact Intelligence",
      tools: [
        "get_followers_email",
        "get_followings_email",
        "get_followers_phone",
        "get_followings_phone",
      ],
    },
  ];

  const TOOL_LABELS = {
    get_user_info: "Profile Information",
    get_user_propic: "Profile Picture",
    get_followers: "Followers",
    get_followings: "Following",
    compare_with: "Mutual Connections",
    get_people_who_tagged: "Tagged By Others",
    get_people_tagged_by_user: "Tagged Users",
    get_people_who_commented: "Frequent Commenters",
    get_hashtags: "Hashtags",
    get_captions: "Captions",
    get_comment_data: "Comments",
    get_total_comments: "Total Comments",
    get_total_likes: "Likes Statistics",
    get_posting_times: "Posting Activity",
    get_post_comments: "Post Comments",
    get_media_type: "Media Breakdown",
    get_user_photos: "Photos & Videos",
    get_user_stories: "Stories",
    get_highlights: "Highlights",
    get_photo_descriptions: "Media Alt Metadata",
    get_addrs: "Geotagged Locations",
    search_location: "Place Search",
    search_hashtag: "Hashtag Search",
    get_followers_email: "Followers Public Emails",
    get_followings_email: "Following Public Emails",
    get_followers_phone: "Followers Public Phones",
    get_followings_phone: "Following Public Phones",
  };

  const AI_ANALYSIS_OPTIONS = [
    { id: "investigation_summary", label: "Investigation Summary" },
    { id: "profile_summary", label: "Profile Summary" },
    { id: "hashtag_analysis", label: "Hashtag Analysis" },
    { id: "engagement_analysis", label: "Public Engagement Analysis" },
    { id: "posting_pattern", label: "Posting Pattern Analysis" },
    { id: "content_categorization", label: "Content Categorization" },
    { id: "relationship_summary", label: "Relationship Summary" },
    { id: "evidence_report", label: "Evidence-Based Report" },
  ];

  const state = {
    view: "dashboard",
    moduleFilter: null,
    tools: [],
    selectedTools: new Set(["get_user_info"]),
    toolArgs: {},
    target: "",
    maxItems: "50",
    cacheTtl: "300",
    running: false,
    runId: null,
    progressLogs: [],
    apiCallsTotal: 0,
    currentRun: null,
    aiConfig: null,
    igStatus: null,
    about: null,
    dashboard: null,
    dossiers: [],
    targetHistory: [],
    tableState: {},
    aiOutput: null,
    aiLoading: false,
  };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function esc(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function fmtDate(ts) {
    if (!ts) return "—";
    return new Date(ts * 1000).toLocaleString();
  }

  function toast(msg, type = "info") {
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = msg;
    $("#toastContainer").appendChild(el);
    setTimeout(() => el.remove(), 3800);
  }

  async function api(url, opts = {}) {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
      ...opts,
    });
    const ct = res.headers.get("content-type") || "";
    const body = ct.includes("application/json") ? await res.json() : await res.text();
    if (!res.ok) {
      const detail = typeof body === "object" && body ? body.detail || JSON.stringify(body) : body;
      throw new Error(detail || `HTTP ${res.status}`);
    }
    return body;
  }

  function refreshIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
  }

  function maskUsername(name) {
    const clean = String(name || "").trim().replace(/^@/, "");
    if (!clean) return "";
    if (clean.length <= 2) return clean[0] + "*";
    if (clean.length <= 4) return clean[0] + "*".repeat(clean.length - 2) + clean.slice(-1);
    return clean.slice(0, 2) + "***" + clean.slice(-2);
  }

  function updateGlobalStatus() {
    const igEl = $("#globalIgStatus");
    if (state.igStatus) {
      if (state.igStatus.connected) {
        igEl.className = "status-chip status-ok";
        igEl.querySelector(".status-text").textContent =
          `IG Connected${state.igStatus.username ? ` (@${maskUsername(state.igStatus.username)})` : ""}`;
      } else {
        igEl.className = "status-chip status-warn";
        igEl.querySelector(".status-text").textContent = "IG Session Required";
      }
    }

    const aiEl = $("#globalAiStatus");
    if (state.aiConfig) {
      if (state.aiConfig.enabled) {
        aiEl.className = "status-chip status-info";
        aiEl.querySelector(".status-text").textContent = `Gemini: ${state.aiConfig.model}`;
      } else if (state.aiConfig.configured) {
        aiEl.className = "status-chip status-muted";
        aiEl.querySelector(".status-text").textContent = "Gemini Disabled";
      } else {
        aiEl.className = "status-chip status-muted";
        aiEl.querySelector(".status-text").textContent = "AI Optional";
      }
    }
  }

  async function loadInitialData() {
    try {
      const [tools, about, igStatus, aiConfig] = await Promise.all([
        api("/api/tools"),
        api("/api/about"),
        api("/api/settings/instagram"),
        api("/api/ai/config"),
      ]);
      state.tools = tools;
      state.about = about;
      state.igStatus = igStatus;
      state.aiConfig = aiConfig;
      if (about && about.version) {
        $("#versionBadge").textContent = `v${about.version}`;
      }
      updateGlobalStatus();
    } catch (e) {
      toast(`Initialization error: ${e.message}`, "err");
    }
  }

  function navigate(view) {
    state.moduleFilter = null;
    if (view.startsWith("module-")) {
      state.moduleFilter = view.replace("module-", "");
      state.view = "investigate";
    } else {
      state.view = view;
    }

    $$(".nav-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.nav === view);
    });

    render();
  }

  async function render() {
    const main = $("#mainContent");
    if (state.view === "dashboard") {
      await renderDashboard(main);
    } else if (state.view === "investigate") {
      await renderWorkspace(main);
    } else if (state.view === "results") {
      renderResultsView(main);
    } else if (state.view === "saved" || state.view === "history") {
      await renderHistoryOrSaved(main, state.view);
    } else if (state.view === "reports") {
      await renderReportsView(main);
    } else if (state.view === "settings") {
      await renderSettingsView(main);
    } else if (state.view === "about") {
      renderAboutView(main);
    }
    refreshIcons();
  }

  // ---- 1. DASHBOARD ----
  async function renderDashboard(main) {
    main.innerHTML = `<div class="card">Loading dashboard metrics...</div>`;
    try {
      state.dashboard = await api("/api/dashboard");
      state.igStatus = state.dashboard.instagram_status;
      updateGlobalStatus();
    } catch (e) {
      main.innerHTML = `<div class="notice notice-warn">Could not load dashboard: ${esc(e.message)}</div>`;
      return;
    }
    const d = state.dashboard;
    const s = d.stats;

    main.innerHTML = `
      <div class="page-header">
        <div class="page-title-wrap">
          <div class="page-icon"><i data-lucide="layout-dashboard"></i></div>
          <div>
            <h1 class="page-title">Investigation Dashboard</h1>
            <p class="page-subtitle">Real-time overview of OSINT IG operations, saved dossiers, and provider status.</p>
          </div>
        </div>
        <button class="btn btn-primary" id="dashNewInv"><i data-lucide="plus"></i> New Investigation</button>
      </div>

      <div class="grid-4">
        <div class="stat-card">
          <div class="stat-label">Total Investigations</div>
          <div class="stat-value">${s.total_investigations}</div>
          <div class="stat-meta">Saved in local dossier store</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Completed Investigations</div>
          <div class="stat-value">${s.completed_investigations}</div>
          <div class="stat-meta">Verified local runs</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Saved Reports</div>
          <div class="stat-value">${s.saved_reports}</div>
          <div class="stat-meta">Ready for JSON / CSV / HTML export</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Investigated Targets</div>
          <div class="stat-value">${s.recent_targets_count}</div>
          <div class="stat-meta">Unique target history entries</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title"><i data-lucide="zap"></i> Quick Access Modules</h2>
        </div>
        <div class="quick-actions">
          <button class="quick-btn" data-quick="profile"><i data-lucide="user-check"></i><span>Profile Info</span></button>
          <button class="quick-btn" data-quick="network"><i data-lucide="users"></i><span>Followers / Following</span></button>
          <button class="quick-btn" data-quick="content"><i data-lucide="hash"></i><span>Hashtags Analysis</span></button>
          <button class="quick-btn" data-quick="media"><i data-lucide="image"></i><span>Media Intelligence</span></button>
          <button class="quick-btn" data-quick="location"><i data-lucide="map-pin"></i><span>Location Clues</span></button>
        </div>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title"><i data-lucide="folder-archive"></i> Recent Investigations</h2>
            <button class="btn btn-ghost btn-sm" data-nav="saved">View all</button>
          </div>
          ${
            d.recent_investigations.length
              ? `<div class="table-wrap"><table>
                  <thead><tr><th>Target</th><th>Modules</th><th>Saved</th><th>Action</th></tr></thead>
                  <tbody>
                    ${d.recent_investigations
                      .map(
                        (item) => `<tr>
                          <td><strong>@${esc(item.target)}</strong></td>
                          <td>${(item.commands || []).length} modules</td>
                          <td>${esc(fmtDate(item.saved_at))}</td>
                          <td><button class="btn btn-sm open-dossier" data-target="${esc(item.target)}" data-id="${esc(item.id)}">Open</button></td>
                        </tr>`
                      )
                      .join("")}
                  </tbody>
                </table></div>`
              : `<div class="notice">No saved investigations yet. Start a new investigation to collect and save intelligence.</div>`
          }
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title"><i data-lucide="activity"></i> System &amp; Backend Status</h2>
            <button class="btn btn-ghost btn-sm" data-nav="settings">Configure</button>
          </div>
          <div style="display:grid;gap:10px;">
            <div class="notice">
              <strong>Instagram Data Provider:</strong> <code>instagrapi</code><br/>
              Status: ${
                d.instagram_status.connected
                  ? `<span class="badge badge-ok">Connected${d.instagram_status.username ? ` (@${esc(maskUsername(d.instagram_status.username))})` : ""}</span>`
                  : `<span class="badge badge-warn">Session Not Configured</span>`
              }
            </div>
            <div class="notice">
              <strong>Google Gemini AI Analysis (Optional):</strong><br/>
              Status: ${
                d.ai_status.enabled
                  ? `<span class="badge badge-info">Enabled (${esc(d.ai_status.model)})</span>`
                  : `<span class="badge">Not Active (Core OSINT works normally)</span>`
              }
            </div>
            <div class="notice">
              <strong>Local Storage:</strong> Request cache active · Dossiers stored locally in <code>dossier/</code>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title"><i data-lucide="compass"></i> Investigation Workflow</h2>
        </div>
        <div class="grid-4" style="margin-bottom:0;">
          <div class="notice">
            <strong>1. Target &amp; Modules</strong><br/>
            <span class="form-help">Go to <strong>New Investigation</strong>, enter a public Instagram username or URL, and select modules.</span>
          </div>
          <div class="notice">
            <strong>2. Live Collection</strong><br/>
            <span class="form-help">Track real-time backend requests, enforce result limits, and use local caching to avoid duplicate calls.</span>
          </div>
          <div class="notice">
            <strong>3. Structured Analysis</strong><br/>
            <span class="form-help">Inspect profile cards, searchable tables, hashtag charts, media grids, maps, and optional Gemini AI insights.</span>
          </div>
          <div class="notice">
            <strong>4. Save &amp; Export</strong><br/>
            <span class="form-help">Save dossiers to populate these dashboard metrics, compare runs over time, or export HTML, CSV, and JSON reports.</span>
          </div>
        </div>
      </div>

      <div class="notice notice-warn" style="margin-top:4px;">
        <strong>Terms &amp; Conditions:</strong> Use <strong>OSINT IG</strong> at your own risk. This platform is strictly for <strong>OSINT, cybersecurity research, and educational purposes only</strong>. You are solely responsible for your actions and any unlawful or unauthorized activity.
      </div>
    `;

    $("#dashNewInv").onclick = () => navigate("investigate");
    $$("[data-quick]", main).forEach((b) => {
      b.onclick = () => navigate(`module-${b.dataset.quick}`);
    });
    $$(".open-dossier", main).forEach((b) => {
      b.onclick = () => openSavedDossier(b.dataset.target, b.dataset.id);
    });
  }

  // ---- 2. NEW INVESTIGATION WORKSPACE ----
  async function renderWorkspace(main) {
    try {
      state.targetHistory = await api("/api/history/targets");
    } catch (_) {}

    const specMap = new Map(state.tools.map((t) => [t.name, t]));
    const categories = state.moduleFilter
      ? MODULE_CATEGORIES.filter((c) => c.id === state.moduleFilter)
      : MODULE_CATEGORIES;

    main.innerHTML = `
      <div class="page-header">
        <div class="page-title-wrap">
          <div class="page-icon"><i data-lucide="search"></i></div>
          <div>
            <h1 class="page-title">Instagram Investigation</h1>
            <p class="page-subtitle">Gather publicly available information from Instagram profiles, posts, and activity.</p>
          </div>
        </div>
        ${state.currentRun ? `<button class="btn" id="viewCurrentResultsBtn"><i data-lucide="layers"></i> View Latest Results</button>` : ""}
      </div>

      <div class="workspace-grid">
        <div>
          <div class="card">
            <div class="card-header">
              <h2 class="card-title"><i data-lucide="user"></i> Target Profile</h2>
            </div>
            <label class="form-label" for="targetInput">Instagram Username or Profile URL</label>
            <div class="input-group">
              <span class="input-prefix">@</span>
              <input id="targetInput" type="text" placeholder="e.g. instagram or https://instagram.com/instagram" value="${esc(state.target)}" />
            </div>
            <div class="form-help">Optional for hashtag, place, or direct post/reel URL lookups.</div>
            ${
              state.targetHistory.length
                ? `<div class="chip-list">
                    ${state.targetHistory
                      .slice(0, 8)
                      .map((h) => `<span class="chip target-chip" data-val="${esc(h.value)}">@${esc(h.value)}</span>`)
                      .join("")}
                  </div>`
                : ""
            }
          </div>

          <div class="card">
            <div class="card-header">
              <h2 class="card-title"><i data-lucide="sliders"></i> Investigation Modules</h2>
              <div style="display:flex;gap:8px;">
                ${state.moduleFilter ? `<button class="btn btn-sm" id="showAllModulesBtn">Show All Categories</button>` : ""}
                <button class="btn btn-sm" id="selectAllModulesBtn">Select All</button>
                <button class="btn btn-sm" id="clearModulesBtn">Clear</button>
              </div>
            </div>
            ${categories
              .map((cat) => {
                const avail = cat.tools.filter((name) => specMap.has(name));
                if (!avail.length) return "";
                return `
                  <div class="module-category">
                    <h3 class="module-category-title">${esc(cat.title)}</h3>
                    <div class="module-list">
                      ${avail
                        .map((name) => {
                          const spec = specMap.get(name);
                          const checked = state.selectedTools.has(name);
                          const label = TOOL_LABELS[name] || name;
                          const args = state.toolArgs[name] || {};
                          return `
                            <div class="module-item ${checked ? "selected" : ""}" data-tool="${esc(name)}">
                              <label class="module-head">
                                <input type="checkbox" class="tool-check" data-tool="${esc(name)}" ${checked ? "checked" : ""} />
                                <div>
                                  <div class="module-name">${esc(label)}</div>
                                  <div class="module-desc">${esc(spec.description)}</div>
                                </div>
                              </label>
                              ${
                                checked && spec.params && spec.params.length
                                  ? `<div class="module-params">
                                      ${spec.params
                                        .map((p) => {
                                          const val = args[p.name] !== undefined ? args[p.name] : (p.default ?? "");
                                          if (p.choices) {
                                            return `<div>
                                              <label class="form-label">${esc(p.name)}</label>
                                              <select class="form-control tool-param" data-tool="${esc(name)}" data-param="${esc(p.name)}">
                                                ${p.choices.map((c) => `<option value="${esc(c)}" ${c === val ? "selected" : ""}>${esc(c)}</option>`).join("")}
                                              </select>
                                            </div>`;
                                          }
                                          return `<div>
                                            <label class="form-label">${esc(p.name)}</label>
                                            <input class="form-control tool-param" type="${p.type === "integer" ? "number" : "text"}"
                                              data-tool="${esc(name)}" data-param="${esc(p.name)}"
                                              placeholder="${esc(p.description || p.name)}" value="${esc(val)}" />
                                          </div>`;
                                        })
                                        .join("")}
                                    </div>`
                                  : ""
                              }
                            </div>`;
                        })
                        .join("")}
                    </div>
                  </div>`;
              })
              .join("")}
          </div>
        </div>

        <!-- Run Controls -->
        <aside>
          <div class="card">
            <div class="card-header">
              <h2 class="card-title"><i data-lucide="play-circle"></i> Run Investigation</h2>
            </div>

            <div style="margin-bottom:12px;">
              <label class="form-label" for="resultLimitSelect">Result &amp; Request Limit</label>
              <select id="resultLimitSelect" class="form-control">
                <option value="" ${state.maxItems === "" ? "selected" : ""}>No Limit</option>
                <option value="10" ${state.maxItems === "10" ? "selected" : ""}>10</option>
                <option value="50" ${state.maxItems === "50" ? "selected" : ""}>50</option>
                <option value="100" ${state.maxItems === "100" ? "selected" : ""}>100</option>
                <option value="200" ${state.maxItems === "200" ? "selected" : ""}>200</option>
              </select>
            </div>

            <div style="margin-bottom:14px;">
              <label class="form-label" for="cacheTtlSelect">Cache Lifetime</label>
              <select id="cacheTtlSelect" class="form-control">
                <option value="0" ${state.cacheTtl === "0" ? "selected" : ""}>Off (Fresh requests)</option>
                <option value="300" ${state.cacheTtl === "300" ? "selected" : ""}>5 Minutes</option>
                <option value="3600" ${state.cacheTtl === "3600" ? "selected" : ""}>1 Hour</option>
                <option value="21600" ${state.cacheTtl === "21600" ? "selected" : ""}>6 Hours</option>
                <option value="86400" ${state.cacheTtl === "86400" ? "selected" : ""}>24 Hours</option>
              </select>
            </div>

            <div style="display:grid;gap:8px;">
              ${
                state.running
                  ? `<button class="btn btn-danger btn-block" id="cancelRunBtn"><i data-lucide="square"></i> Cancel Investigation</button>`
                  : `<button class="btn btn-primary btn-block" id="startRunBtn"><i data-lucide="play"></i> Start Investigation (${state.selectedTools.size})</button>`
              }
              <button class="btn btn-block" id="estimateBtn" ${state.running ? "disabled" : ""}><i data-lucide="calculator"></i> Estimate Requests</button>
              <button class="btn btn-block" id="clearCacheBtn" ${state.running ? "disabled" : ""}><i data-lucide="trash-2"></i> Clear Cache</button>
            </div>

            <div id="estimateBox" style="margin-top:12px;"></div>

            ${
              state.running || state.progressLogs.length
                ? `<div style="margin-top:14px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
                      <span class="form-label" style="margin:0;">Live Progress (<span id="progressCount">${state.apiCallsTotal}</span> backend requests)</span>
                      <button class="btn btn-sm" id="expandLogsBtn" title="Expand logs"><i data-lucide="maximize-2"></i> Expand</button>
                    </div>
                    <div class="progress-log" id="progressLog">${state.progressLogs.map((l) => `<div>${esc(l)}</div>`).join("")}</div>
                  </div>`
                : ""
            }
          </div>
        </aside>
      </div>
    `;

    $("#targetInput").oninput = (e) => {
      state.target = e.target.value;
    };
    $$(".target-chip", main).forEach((c) => {
      c.onclick = () => {
        state.target = c.dataset.val;
        $("#targetInput").value = state.target;
      };
    });
    $$(".tool-check", main).forEach((cb) => {
      cb.onchange = () => {
        if (cb.checked) state.selectedTools.add(cb.dataset.tool);
        else state.selectedTools.delete(cb.dataset.tool);
        renderWorkspace(main);
        refreshIcons();
      };
    });
    $$(".tool-param", main).forEach((inp) => {
      inp.oninput = inp.onchange = () => {
        const t = inp.dataset.tool;
        const p = inp.dataset.param;
        state.toolArgs[t] = state.toolArgs[t] || {};
        state.toolArgs[t][p] = inp.value;
      };
    });
    $("#resultLimitSelect").onchange = (e) => (state.maxItems = e.target.value);
    $("#cacheTtlSelect").onchange = (e) => (state.cacheTtl = e.target.value);

    if ($("#showAllModulesBtn")) $("#showAllModulesBtn").onclick = () => navigate("investigate");
    $("#selectAllModulesBtn").onclick = () => {
      categories.forEach((c) => c.tools.forEach((t) => specMap.has(t) && state.selectedTools.add(t)));
      renderWorkspace(main);
      refreshIcons();
    };
    $("#clearModulesBtn").onclick = () => {
      state.selectedTools.clear();
      renderWorkspace(main);
      refreshIcons();
    };
    if ($("#viewCurrentResultsBtn")) $("#viewCurrentResultsBtn").onclick = () => navigate("results");
    if ($("#startRunBtn")) $("#startRunBtn").onclick = startInvestigation;
    if ($("#cancelRunBtn")) $("#cancelRunBtn").onclick = cancelInvestigation;
    if ($("#expandLogsBtn")) $("#expandLogsBtn").onclick = openLogsModal;
    $("#estimateBtn").onclick = estimateRequests;
    $("#clearCacheBtn").onclick = clearCache;
  }

  function openLogsModal() {
    if ($("#logsModal")) return;
    const backdrop = document.createElement("div");
    backdrop.id = "logsModal";
    backdrop.className = "modal-backdrop";
    backdrop.innerHTML = `
      <div class="modal-box">
        <div class="card-header">
          <h2 class="card-title"><i data-lucide="terminal"></i> Live Investigation Logs (<span id="modalProgressCount">${state.apiCallsTotal}</span> backend requests)</h2>
          <button class="btn btn-sm" id="closeLogsModalBtn">Close</button>
        </div>
        <div class="modal-log-body" id="modalProgressLog">${state.progressLogs.map((l) => `<div>${esc(l)}</div>`).join("")}</div>
      </div>
    `;
    document.body.appendChild(backdrop);
    refreshIcons();
    const logEl = $("#modalProgressLog");
    if (logEl) logEl.scrollTop = logEl.scrollHeight;
    $("#closeLogsModalBtn").onclick = () => backdrop.remove();
    backdrop.onclick = (e) => { if (e.target === backdrop) backdrop.remove(); };
  }

  function buildCallsPayload() {
    const specMap = new Map(state.tools.map((t) => [t.name, t]));
    return Array.from(state.selectedTools).map((name) => {
      const spec = specMap.get(name);
      const raw = state.toolArgs[name] || {};
      const args = {};
      if (spec && spec.params) {
        spec.params.forEach((p) => {
          const val = raw[p.name];
          if (val !== undefined && val !== "") {
            args[p.name] = p.type === "integer" ? Number(val) : val;
          }
        });
      }
      return { name, args };
    });
  }

  async function estimateRequests() {
    const calls = buildCallsPayload();
    if (!calls.length) return toast("Select at least one module first.", "err");
    try {
      const res = await api("/api/estimate", {
        method: "POST",
        body: JSON.stringify({
          target: state.target || null,
          calls,
          max_items: state.maxItems ? Number(state.maxItems) : null,
          cache_ttl_seconds: Number(state.cacheTtl),
        }),
      });
      $("#estimateBox").innerHTML = `<div class="notice notice-info">
        Estimated backend requests: <strong>${res.total_low}–${res.total_high}</strong>
        (cached items cost 0).
      </div>`;
    } catch (e) {
      toast(e.message, "err");
    }
  }

  async function clearCache() {
    try {
      const res = await api("/api/cache", { method: "DELETE" });
      toast(`Cleared ${res.cleared} cached entries.`, "ok");
    } catch (e) {
      toast(e.message, "err");
    }
  }

  async function cancelInvestigation() {
    if (!state.runId) return;
    try {
      await api("/api/cancel", { method: "POST", body: JSON.stringify({ run_id: state.runId }) });
      toast("Cancellation requested.", "info");
    } catch (e) {
      toast(e.message, "err");
    }
  }

  async function startInvestigation() {
    const calls = buildCallsPayload();
    if (!calls.length) return toast("Select at least one module to run.", "err");

    state.running = true;
    state.runId = `run_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    state.progressLogs = ["Starting investigation..."];
    state.apiCallsTotal = 0;
    state.aiOutput = null;
    render();

    const collectedResults = [];
    let resolvedTarget = state.target;
    let targetId = null;
    let backend = "instagrapi";

    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target: state.target || null,
          calls,
          verbose: true,
          max_items: state.maxItems ? Number(state.maxItems) : null,
          cache_ttl_seconds: Number(state.cacheTtl),
          run_id: state.runId,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const ev = JSON.parse(line.slice(6));
          if (ev.type === "start") {
            resolvedTarget = ev.target || resolvedTarget;
            targetId = ev.target_id;
            backend = ev.backend;
            state.progressLogs.push(`Connected (${backend}) — Target: ${resolvedTarget || "Target-free"}`);
          } else if (ev.type === "tool_call") {
            state.progressLogs.push(`Running ${TOOL_LABELS[ev.name] || ev.name}...`);
          } else if (ev.type === "api_call") {
            state.apiCallsTotal = ev.total;
            if (ev.status !== "cached") {
              state.progressLogs.push(`  ↳ ${ev.method} (${ev.status})`);
            }
          } else if (ev.type === "tool_result") {
            state.apiCallsTotal = ev.api_calls_total;
            collectedResults.push(ev);
            state.progressLogs.push(
              `${ev.is_error ? "✗" : "✓"} ${TOOL_LABELS[ev.name] || ev.name} (${ev.elapsed_ms} ms)`
            );
          } else if (ev.type === "error") {
            throw new Error(ev.detail);
          }
          const countEl = $("#progressCount");
          if (countEl) countEl.textContent = String(state.apiCallsTotal);
          const modalCountEl = $("#modalProgressCount");
          if (modalCountEl) modalCountEl.textContent = String(state.apiCallsTotal);
          const logEl = $("#progressLog");
          if (logEl) {
            logEl.innerHTML = state.progressLogs.slice(-40).map((l) => `<div>${esc(l)}</div>`).join("");
            logEl.scrollTop = logEl.scrollHeight;
          }
          const modalLogEl = $("#modalProgressLog");
          if (modalLogEl) {
            modalLogEl.innerHTML = state.progressLogs.map((l) => `<div>${esc(l)}</div>`).join("");
            modalLogEl.scrollTop = modalLogEl.scrollHeight;
          }
        }
      }

      state.currentRun = {
        target: resolvedTarget || "target-free",
        target_id: targetId,
        backend,
        saved_at: Math.floor(Date.now() / 1000),
        api_calls_total: state.apiCallsTotal,
        results: collectedResults,
      };
      state.running = false;
      toast("Investigation completed.", "ok");
      navigate("results");
    } catch (e) {
      state.running = false;
      state.progressLogs.push(`Error: ${e.message}`);
      toast(e.message, "err");
      render();
    }
  }

  // ---- 3. STRUCTURED RESULTS INTERFACE + GEMINI ANALYSIS ----
  function renderResultsView(main) {
    const run = state.currentRun;
    if (!run) {
      main.innerHTML = `
        <div class="page-header">
          <div class="page-title-wrap">
            <div class="page-icon"><i data-lucide="layers"></i></div>
            <div>
              <h1 class="page-title">Investigation Results</h1>
              <p class="page-subtitle">No active investigation loaded.</p>
            </div>
          </div>
          <button class="btn btn-primary" id="goInvestigateBtn"><i data-lucide="search"></i> New Investigation</button>
        </div>
        <div class="card">Run an investigation or open a saved dossier from <strong>Saved Investigations</strong> to inspect structured findings.</div>
      `;
      $("#goInvestigateBtn").onclick = () => navigate("investigate");
      return;
    }

    main.innerHTML = `
      <div class="page-header">
        <div class="page-title-wrap">
          <div class="page-icon"><i data-lucide="layers"></i></div>
          <div>
            <h1 class="page-title">Results: @${esc(run.target)}</h1>
            <p class="page-subtitle">
              Provider: ${esc(run.backend || "instagrapi")} ·
              Backend requests: ${esc(run.api_calls_total ?? 0)} ·
              Modules: ${(run.results || []).length}
            </p>
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button class="btn" id="saveDossierBtn"><i data-lucide="save"></i> Save Investigation</button>
          <button class="btn btn-primary" id="exportZipBtn"><i data-lucide="archive"></i> Export Case ZIP</button>
          <button class="btn" id="exportHtmlBtn"><i data-lucide="file-text"></i> Export HTML</button>
          <button class="btn" id="exportCsvBtn"><i data-lucide="table"></i> Export CSV</button>
          <button class="btn" id="exportJsonBtn"><i data-lucide="code"></i> Export JSON</button>
        </div>
      </div>

      ${renderAiAnalysisCard(run)}

      <div id="resultsCards">
        ${(run.results || []).map((r, idx) => renderModuleResultCard(r, idx)).join("")}
      </div>
    `;

    $("#saveDossierBtn").onclick = saveCurrentDossier;
    $("#exportZipBtn").onclick = () => exportReport("zip");
    $("#exportHtmlBtn").onclick = () => exportReport("html");
    $("#exportCsvBtn").onclick = () => exportReport("csv");
    $("#exportJsonBtn").onclick = () => exportReport("json");

    wireAiPanelEvents(run);
    wireResultInteractions(run);
  }

  function renderAiAnalysisCard(run) {
    const ai = state.aiConfig;
    if (!ai || !ai.configured || !ai.enabled) {
      return `
        <div class="card">
          <div class="card-header">
            <h2 class="card-title"><i data-lucide="sparkles"></i> Gemini AI Analysis (Optional)</h2>
            <button class="btn btn-sm" data-nav="settings">Configure Gemini</button>
          </div>
          <div class="notice">
            AI analysis is optional and currently ${ai && ai.configured ? "disabled" : "not configured"}.
            All core OSINT modules and exports work normally without it. You can enable Google Gemini in <strong>Settings → AI Configuration</strong> to summarize or query collected records.
          </div>
        </div>
      `;
    }

    return `
      <div class="card">
        <div class="card-header">
          <h2 class="card-title"><i data-lucide="sparkles"></i> Gemini AI Post-Collection Analysis</h2>
          <span class="badge badge-info">${esc(ai.model)}</span>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
          ${AI_ANALYSIS_OPTIONS.map(
            (opt) => `<button class="btn btn-sm ai-run-btn" data-type="${esc(opt.id)}" ${state.aiLoading ? "disabled" : ""}>${esc(opt.label)}</button>`
          ).join("")}
        </div>
        <div style="display:flex;gap:8px;margin-bottom:10px;">
          <input id="aiQuestionInput" class="form-control" type="text" placeholder="Ask a natural-language question about the collected results..." />
          <button class="btn btn-primary btn-sm" id="aiAskBtn" ${state.aiLoading ? "disabled" : ""}>Ask</button>
        </div>
        ${
          state.aiLoading
            ? `<div class="notice notice-info">Analyzing collected records with ${esc(ai.model)}...</div>`
            : state.aiOutput
            ? `<div class="notice" style="background:#FFFFFF;">
                <div style="font-size:11px;color:var(--text-secondary);margin-bottom:6px;">
                  Model: ${esc(state.aiOutput.model)} · Analysis: ${esc(state.aiOutput.analysis_type)}
                </div>
                <div style="white-space:pre-wrap;font-size:13px;">${esc(state.aiOutput.analysis)}</div>
              </div>`
            : `<div class="form-help">Select an analysis type above or ask a question. Gemini only inspects already-collected records and separates Observed Facts, Derived Statistics, AI Interpretations, and Unknowns.</div>`
        }
      </div>
    `;
  }

  function wireAiPanelEvents(run) {
    $$(".ai-run-btn").forEach((b) => {
      b.onclick = () => runGeminiAnalysis(run, b.dataset.type);
    });
    const askBtn = $("#aiAskBtn");
    if (askBtn) {
      askBtn.onclick = () => {
        const q = ($("#aiQuestionInput").value || "").trim();
        runGeminiAnalysis(run, "qa", q);
      };
    }
  }

  async function runGeminiAnalysis(run, analysisType, question = null) {
    state.aiLoading = true;
    renderResultsView($("#mainContent"));
    refreshIcons();
    try {
      const res = await api("/api/ai/analyze", {
        method: "POST",
        body: JSON.stringify({
          target: run.target,
          results: run.results || [],
          analysis_type: analysisType,
          question,
        }),
      });
      state.aiOutput = res;
      run.ai_analysis = res.analysis;
    } catch (e) {
      toast(e.message, "err");
    } finally {
      state.aiLoading = false;
      renderResultsView($("#mainContent"));
      refreshIcons();
    }
  }

  function renderModuleResultCard(r, idx) {
    const label = TOOL_LABELS[r.name] || r.name;
    const badge = r.is_error
      ? `<span class="badge badge-err">Error</span>`
      : `<span class="badge badge-ok">Completed · ${esc(r.elapsed_ms ?? 0)} ms</span>`;

    let bodyHtml = "";
    if (r.is_error) {
      bodyHtml = `<div class="notice notice-warn">${esc(r.result?.error || JSON.stringify(r.result))}</div>`;
    } else {
      bodyHtml = renderStructuredResult(r.name, r.result, idx);
    }

    return `
      <div class="card">
        <div class="card-header">
          <h2 class="card-title"><i data-lucide="check-circle-2"></i> ${esc(label)}</h2>
          ${badge}
        </div>
        ${bodyHtml}
        <details style="margin-top:12px;">
          <summary style="cursor:pointer;font-size:12px;color:var(--text-secondary);font-weight:600;">Raw Evidence (JSON)</summary>
          <pre class="raw-json">${esc(JSON.stringify(r.result, null, 2))}</pre>
        </details>
      </div>
    `;
  }

  function formatCellValue(val) {
    if (val === null || val === undefined) return "—";
    if (typeof val === "object") return esc(JSON.stringify(val));
    const s = String(val);
    if (/^https?:\/\//i.test(s)) {
      return `<a href="${esc(s)}" target="_blank" rel="noopener" class="btn btn-sm">Open Link ↗</a>`;
    }
    return esc(s);
  }

  function renderStructuredResult(name, data, idx) {
    if (data == null) return `<div class="notice">No data returned.</div>`;

    if (name === "get_user_propic" && typeof data === "object" && data.url) {
      return `
        <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
          <img class="profile-avatar" src="${esc(data.url)}" alt="Profile Picture" style="width:88px;height:88px;" />
          <div>
            <div style="font-weight:600;margin-bottom:6px;">Full-Resolution Profile Picture</div>
            <a href="${esc(data.url)}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">Open Full-Size Image ↗</a>
          </div>
        </div>
      `;
    }

    if (name === "get_user_photos" && Array.isArray(data)) {
      if (!data.length) return `<div class="notice">No photos or videos found.</div>`;
      const urls = data.map((p) => p.url).filter(Boolean);
      return `
        ${urls.length ? `<div style="margin-bottom:10px;"><button class="btn btn-sm btn-primary download-photos-zip" data-idx="${idx}"><i data-lucide="download"></i> Download All Media ZIP (${urls.length})</button></div>` : ""}
        <div class="media-grid">
          ${data
            .slice(0, 48)
            .map(
              (p) => `<div class="media-card">
                ${p.url ? `<a href="${esc(p.url)}" target="_blank" rel="noopener"><img class="media-thumb" src="${esc(p.url)}" alt="Media ${esc(p.id || "")}" loading="lazy" /></a>` : `<div class="media-thumb"></div>`}
                <div class="media-meta" style="display:flex;justify-content:space-between;align-items:center;gap:6px;">
                  <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">ID: ${esc(p.id || "—")}</span>
                  ${p.url ? `<a href="${esc(p.url)}" target="_blank" rel="noopener" class="btn btn-sm">Open ↗</a>` : ""}
                </div>
              </div>`
            )
            .join("")}
        </div>
      `;
    }

    if (name === "get_user_info" && typeof data === "object" && !Array.isArray(data)) {
      return `
        <div class="profile-hero">
          ${data.profile_pic_url ? `<img class="profile-avatar" src="${esc(data.profile_pic_url)}" alt="Profile picture" />` : ""}
          <div style="flex:1;">
            <div style="font-size:16px;font-weight:700;">${esc(data.full_name || data.username)} <span style="color:var(--text-secondary);font-weight:500;">@${esc(data.username)}</span></div>
            <div style="margin:6px 0;">${esc(data.biography || "No biography")}</div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:13px;margin:8px 0;">
              <span><strong>${esc(data.follower_count ?? "—")}</strong> Followers</span>
              <span><strong>${esc(data.following_count ?? "—")}</strong> Following</span>
              <span><strong>${esc(data.media_count ?? "—")}</strong> Posts</span>
              <span>Private: <strong>${data.is_private ? "Yes" : "No"}</strong></span>
              <span>Verified: <strong>${data.is_verified ? "Yes" : "No"}</strong></span>
              ${data.category_name || data.category ? `<span>Category: <strong>${esc(data.category_name || data.category)}</strong></span>` : ""}
            </div>
            ${data.external_url ? `<div>External URL: <a href="${esc(data.external_url)}" target="_blank" rel="noopener">${esc(data.external_url)}</a></div>` : ""}
            ${data.public_email ? `<div>Public Email: <strong>${esc(data.public_email)}</strong></div>` : ""}
            ${data.contact_phone_number ? `<div>Public Phone: <strong>${esc(data.contact_phone_number)}</strong></div>` : ""}
          </div>
        </div>
      `;
    }

    if (name === "get_hashtags" && Array.isArray(data)) {
      if (!data.length) return `<div class="notice">No hashtags found.</div>`;
      const maxCount = Math.max(...data.map((d) => d.count || 0), 1);
      const total = data.reduce((a, b) => a + (b.count || 0), 0) || 1;
      return `
        <div>
          ${data
            .slice(0, 20)
            .map((h) => {
              const pct = ((h.count / total) * 100).toFixed(1);
              const w = Math.round((h.count / maxCount) * 100);
              return `<div class="bar-row">
                <div class="bar-label">#${esc(h.hashtag)}</div>
                <div class="bar-track"><div class="bar-fill" style="width:${w}%"></div></div>
                <div style="width:90px;text-align:right;">${h.count} (${pct}%)</div>
              </div>`;
            })
            .join("")}
        </div>
      `;
    }

    if (name === "get_posting_times" && typeof data === "object") {
      const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
      const byW = data.by_weekday || {};
      const byH = data.by_hour || {};
      return `
        <div style="margin-bottom:10px;font-size:13px;">
          Posts analyzed: <strong>${esc(data.posts ?? 0)}</strong> · Timezone: <strong>${esc(data.timezone || "UTC")}</strong>
          ${data.busiest_weekday ? `· Busiest day: <strong>${esc(data.busiest_weekday)}</strong>` : ""}
          ${data.busiest_hour_utc !== undefined ? `· Busiest hour: <strong>${esc(data.busiest_hour_utc)}:00 UTC</strong>` : ""}
        </div>
        <div class="grid-2">
          <div>
            <div class="form-label">By Weekday</div>
            ${days.map((d) => `<div class="bar-row"><div class="bar-label">${d}</div><div class="bar-track"><div class="bar-fill" style="width:${Math.min(100, (byW[d] || 0) * 10)}%"></div></div><div>${byW[d] || 0}</div></div>`).join("")}
          </div>
          <div>
            <div class="form-label">Peak Hours (UTC)</div>
            <div style="display:flex;flex-wrap:wrap;gap:4px;">
              ${Object.entries(byH).map(([hr, cnt]) => `<span class="badge ${cnt > 0 ? "badge-info" : ""}">${hr}h: ${cnt}</span>`).join("")}
            </div>
          </div>
        </div>
      `;
    }

    if (data.previews && Array.isArray(data.previews)) {
      const urls = data.previews.map((p) => p.media_url || p.thumbnail_url).filter(Boolean);
      return `
        ${urls.length ? `<div style="margin-bottom:10px;"><button class="btn btn-sm download-zip-btn" data-idx="${idx}" data-name="${esc(name)}"><i data-lucide="download"></i> Download Media ZIP (${urls.length})</button></div>` : ""}
        <div class="media-grid">
          ${data.previews
            .slice(0, 36)
            .map(
              (p) => `<div class="media-card">
                ${p.thumbnail_url || p.media_url ? `<img class="media-thumb" src="${esc(p.thumbnail_url || p.media_url)}" alt="Media" loading="lazy" />` : `<div class="media-thumb"></div>`}
                <div class="media-meta">
                  <div><strong>${esc(p.type || "post")}</strong> ${p.like_count !== undefined ? `· ♥ ${p.like_count}` : ""}</div>
                  ${p.caption ? `<div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(p.caption)}</div>` : ""}
                </div>
              </div>`
            )
            .join("")}
        </div>
      `;
    }

    if (name === "get_addrs" && Array.isArray(data)) {
      return `
        <div id="map_${idx}" class="map-box"></div>
        <div class="table-wrap" style="margin-top:10px;"><table>
          <thead><tr><th>Location</th><th>Address</th><th>Coordinates</th></tr></thead>
          <tbody>
            ${data
              .map(
                (a) => `<tr>
                  <td><strong>${esc(a.location_name || a.name || "—")}</strong></td>
                  <td>${esc(a.address || "—")}</td>
                  <td>${
                    a.lat !== undefined
                      ? `<a href="https://www.google.com/maps?q=${encodeURIComponent(a.lat)},${encodeURIComponent(a.lng)}" target="_blank" rel="noopener">${esc(a.lat)}, ${esc(a.lng)} ↗</a>`
                      : "—"
                  }</td>
                </tr>`
              )
              .join("")}
          </tbody>
        </table></div>
      `;
    }

    if (Array.isArray(data)) {
      if (!data.length) return `<div class="notice">No records found.</div>`;
      if (typeof data[0] === "object" && data[0] !== null) {
        return renderInteractiveTable(data, idx);
      }
      return `<ul>${data.slice(0, 100).map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`;
    }

    if (typeof data === "object") {
      const entries = Object.entries(data).filter(([k]) => k !== "previews" && k !== "timestamps");
      return `
        <div class="table-wrap"><table>
          <tbody>
            ${entries.map(([k, v]) => `<tr><th style="width:220px;">${esc(k)}</th><td>${esc(typeof v === "object" ? JSON.stringify(v) : v)}</td></tr>`).join("")}
          </tbody>
        </table></div>
      `;
    }

    return `<div class="notice">${esc(data)}</div>`;
  }

  function renderInteractiveTable(rows, idx) {
    const keys = Object.keys(rows[0]).filter((k) => k !== "profile_pic_url").slice(0, 6);
    state.tableState[idx] = state.tableState[idx] || { q: "", page: 1, sortKey: null, asc: true };
    const ts = state.tableState[idx];

    let filtered = rows;
    if (ts.q) {
      const q = ts.q.toLowerCase();
      filtered = rows.filter((r) => keys.some((k) => String(r[k] ?? "").toLowerCase().includes(q)));
    }
    if (ts.sortKey) {
      filtered = [...filtered].sort((a, b) => {
        const va = String(a[ts.sortKey] ?? "");
        const vb = String(b[ts.sortKey] ?? "");
        return ts.asc ? va.localeCompare(vb, undefined, { numeric: true }) : vb.localeCompare(va, undefined, { numeric: true });
      });
    }

    const perPage = 15;
    const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
    ts.page = Math.min(ts.page, totalPages);
    const pageRows = filtered.slice((ts.page - 1) * perPage, ts.page * perPage);

    return `
      <div class="table-container" data-idx="${idx}">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px;">
          <input class="form-control table-search" data-idx="${idx}" style="max-width:280px;" placeholder="Filter ${rows.length} records..." value="${esc(ts.q)}" />
          <div style="font-size:12px;color:var(--text-secondary);">Showing ${pageRows.length} of ${filtered.length} (Page ${ts.page}/${totalPages})</div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                ${keys.map((k) => `<th class="table-sort" data-idx="${idx}" data-key="${esc(k)}" style="cursor:pointer;">${esc(k)} ↕</th>`).join("")}
              </tr>
            </thead>
            <tbody>
              ${pageRows
                .map(
                  (r) => `<tr>${keys
                    .map((k) => `<td>${formatCellValue(r[k])}</td>`)
                    .join("")}</tr>`
                )
                .join("")}
            </tbody>
          </table>
        </div>
        ${
          totalPages > 1
            ? `<div style="display:flex;gap:6px;margin-top:8px;">
                <button class="btn btn-sm table-prev" data-idx="${idx}" ${ts.page <= 1 ? "disabled" : ""}>Previous</button>
                <button class="btn btn-sm table-next" data-idx="${idx}" ${ts.page >= totalPages ? "disabled" : ""}>Next</button>
              </div>`
            : ""
        }
      </div>
    `;
  }

  function wireResultInteractions(run) {
    $$(".download-zip-btn").forEach((btn) => {
      btn.onclick = async () => {
        const r = run.results[Number(btn.dataset.idx)];
        const urls = (r?.result?.previews || []).map((p) => p.media_url || p.thumbnail_url).filter(Boolean);
        try {
          const res = await fetch("/api/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ urls, name: `${run.target}_${btn.dataset.name}` }),
          });
          if (!res.ok) throw new Error("Download failed");
          const blob = await res.blob();
          triggerBlobDownload(blob, `osint_ig_${run.target}_${btn.dataset.name}.zip`);
        } catch (e) {
          toast(e.message, "err");
        }
      };
    });

    $$(".download-photos-zip").forEach((btn) => {
      btn.onclick = async () => {
        const r = run.results[Number(btn.dataset.idx)];
        const urls = (Array.isArray(r?.result) ? r.result : []).map((p) => p.url).filter(Boolean);
        try {
          const res = await fetch("/api/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ urls, name: `${run.target}_photos` }),
          });
          if (!res.ok) throw new Error("Download failed");
          const blob = await res.blob();
          triggerBlobDownload(blob, `osint_ig_${run.target}_photos.zip`);
        } catch (e) {
          toast(e.message, "err");
        }
      };
    });

    // Maps for get_addrs (ESRI World Street Map + CartoDB Light fallback)
    (run.results || []).forEach((r, idx) => {
      if (r.name === "get_addrs" && Array.isArray(r.result) && window.L) {
        const el = $(`#map_${idx}`);
        const pts = r.result.filter((a) => typeof a.lat === "number" && typeof a.lng === "number");
        if (el && pts.length) {
          const map = window.L.map(el).setView([pts[0].lat, pts[0].lng], 10);
          const esriStreets = window.L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            { attribution: "Tiles © Esri", maxZoom: 19 }
          );
          const cartoLight = window.L.tileLayer(
            "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            { attribution: "© OpenStreetMap © CARTO", subdomains: "abcd", maxZoom: 19 }
          );
          const esriSat = window.L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            { attribution: "Tiles © Esri", maxZoom: 19 }
          );
          esriStreets.addTo(map);
          window.L.control.layers({ "Street Map": esriStreets, "Light Map": cartoLight, "Satellite": esriSat }).addTo(map);
          const bounds = [];
          pts.forEach((p) => {
            bounds.push([p.lat, p.lng]);
            window.L.marker([p.lat, p.lng])
              .addTo(map)
              .bindPopup(`<strong>${esc(p.location_name || p.address || "Location")}</strong><br>${esc(p.lat)}, ${esc(p.lng)}`);
          });
          if (bounds.length > 1) map.fitBounds(bounds, { padding: [24, 24] });
          setTimeout(() => map.invalidateSize(), 150);
        }
      }
    });

    wireTableControls(run);
  }

  function wireTableControls(run) {
    $$(".table-search").forEach((inp) => {
      inp.oninput = () => {
        const idx = Number(inp.dataset.idx);
        state.tableState[idx].q = inp.value;
        state.tableState[idx].page = 1;
        rerenderTable(run, idx);
      };
    });
    $$(".table-sort").forEach((th) => {
      th.onclick = () => {
        const idx = Number(th.dataset.idx);
        const key = th.dataset.key;
        const ts = state.tableState[idx];
        ts.asc = ts.sortKey === key ? !ts.asc : true;
        ts.sortKey = key;
        rerenderTable(run, idx);
      };
    });
    $$(".table-prev").forEach((b) => {
      b.onclick = () => {
        const idx = Number(b.dataset.idx);
        state.tableState[idx].page--;
        rerenderTable(run, idx);
      };
    });
    $$(".table-next").forEach((b) => {
      b.onclick = () => {
        const idx = Number(b.dataset.idx);
        state.tableState[idx].page++;
        rerenderTable(run, idx);
      };
    });
  }

  function rerenderTable(run, idx) {
    const container = $(`.table-container[data-idx="${idx}"]`);
    if (!container) return;
    container.outerHTML = renderInteractiveTable(run.results[idx].result, idx);
    wireTableControls(run);
  }

  async function saveCurrentDossier() {
    if (!state.currentRun) return;
    try {
      const saved = await api("/api/dossier", { method: "POST", body: JSON.stringify(state.currentRun) });
      state.currentRun.id = saved.id;
      toast(`Saved investigation ${saved.id}`, "ok");
    } catch (e) {
      toast(e.message, "err");
    }
  }

  async function exportReport(format, runOverride = null) {
    const run = runOverride || state.currentRun;
    if (!run) return toast("No investigation loaded to export.", "err");
    try {
      const res = await fetch("/api/report/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run, format }),
      });
      if (!res.ok) throw new Error(`Export failed (${res.status})`);
      const blob = await res.blob();
      const prefix = format === "zip" ? "osint_ig_case_" : "osint_ig_report_";
      triggerBlobDownload(blob, `${prefix}${run.target || "investigation"}.${format}`);
      toast(`Exported ${format.toUpperCase()} report.`, "ok");
    } catch (e) {
      toast(e.message, "err");
    }
  }

  function triggerBlobDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  // ---- 4. SAVED INVESTIGATIONS & HISTORY ----
  async function renderHistoryOrSaved(main, mode) {
    main.innerHTML = `<div class="card">Loading records...</div>`;
    try {
      const [dossiers, targets] = await Promise.all([api("/api/dossier"), api("/api/history/targets")]);
      state.dossiers = dossiers;
      state.targetHistory = targets;
    } catch (e) {
      main.innerHTML = `<div class="notice notice-warn">${esc(e.message)}</div>`;
      return;
    }

    const isSaved = mode === "saved";
    main.innerHTML = `
      <div class="page-header">
        <div class="page-title-wrap">
          <div class="page-icon"><i data-lucide="${isSaved ? "folder-archive" : "history"}"></i></div>
          <div>
            <h1 class="page-title">${isSaved ? "Saved Investigations" : "Investigation History"}</h1>
            <p class="page-subtitle">Reopen saved dossiers without rerunning API requests, compare runs, or export reports.</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title"><i data-lucide="database"></i> Saved Dossiers (${state.dossiers.length})</h2>
        </div>
        ${
          state.dossiers.length
            ? `<div class="table-wrap"><table>
                <thead><tr><th>ID</th><th>Target</th><th>Date &amp; Time</th><th>Modules</th><th>Requests</th><th>Actions</th></tr></thead>
                <tbody>
                  ${state.dossiers
                    .map(
                      (d) => `<tr>
                        <td><code>${esc(d.id)}</code></td>
                        <td><strong>@${esc(d.target)}</strong></td>
                        <td>${esc(fmtDate(d.saved_at))}</td>
                        <td>${(d.commands || []).map((c) => esc(TOOL_LABELS[c] || c)).join(", ")}</td>
                        <td>${esc(d.api_calls ?? 0)}</td>
                        <td style="display:flex;gap:6px;flex-wrap:wrap;">
                          <button class="btn btn-sm btn-primary open-dossier" data-target="${esc(d.target)}" data-id="${esc(d.id)}">Open</button>
                          <button class="btn btn-sm del-dossier" data-target="${esc(d.target)}" data-id="${esc(d.id)}">Delete</button>
                        </td>
                      </tr>`
                    )
                    .join("")}
                </tbody>
              </table></div>`
            : `<div class="notice">No saved investigations found.</div>`
        }
      </div>

      ${
        !isSaved
          ? `<div class="card">
              <div class="card-header">
                <h2 class="card-title"><i data-lucide="clock"></i> Recent Target Lookups (${state.targetHistory.length})</h2>
              </div>
              ${
                state.targetHistory.length
                  ? `<div class="chip-list">
                      ${state.targetHistory
                        .map(
                          (h) => `<span class="chip">
                            <span class="hist-pick" data-val="${esc(h.value)}">@${esc(h.value)}</span>
                            <button class="btn-ghost hist-del" data-val="${esc(h.value)}" style="border:none;cursor:pointer;padding:0 3px;">×</button>
                          </span>`
                        )
                        .join("")}
                    </div>`
                  : `<div class="notice">No target history recorded yet.</div>`
              }
            </div>`
          : ""
      }
    `;

    $$(".open-dossier", main).forEach((b) => {
      b.onclick = () => openSavedDossier(b.dataset.target, b.dataset.id);
    });
    $$(".del-dossier", main).forEach((b) => {
      b.onclick = async () => {
        if (!confirm(`Delete saved investigation ${b.dataset.id}?`)) return;
        await api(`/api/dossier/${encodeURIComponent(b.dataset.target)}/${encodeURIComponent(b.dataset.id)}`, { method: "DELETE" });
        toast("Investigation deleted.", "ok");
        renderHistoryOrSaved(main, mode);
      };
    });
    $$(".hist-pick", main).forEach((el) => {
      el.onclick = () => {
        state.target = el.dataset.val;
        navigate("investigate");
      };
    });
    $$(".hist-del", main).forEach((b) => {
      b.onclick = async () => {
        await api(`/api/history/targets?value=${encodeURIComponent(b.dataset.val)}`, { method: "DELETE" });
        renderHistoryOrSaved(main, mode);
      };
    });
  }

  async function openSavedDossier(target, id) {
    try {
      const run = await api(`/api/dossier/${encodeURIComponent(target)}/${encodeURIComponent(id)}`);
      state.currentRun = run;
      state.aiOutput = run.ai_analysis ? { model: "saved", analysis_type: "saved", analysis: run.ai_analysis } : null;
      navigate("results");
    } catch (e) {
      toast(e.message, "err");
    }
  }

  // ---- 5. REPORTS & EXPORTS ----
  async function renderReportsView(main) {
    state.dossiers = await api("/api/dossier").catch(() => []);
    const active = state.currentRun;
    main.innerHTML = `
      <div class="page-header">
        <div class="page-title-wrap">
          <div class="page-icon"><i data-lucide="file-text"></i></div>
          <div>
            <h1 class="page-title">Reports &amp; Exports</h1>
            <p class="page-subtitle">Generate branded CSIB intelligence reports in JSON, CSV, HTML, or Print-to-PDF.</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title"><i data-lucide="file-check"></i> Current Active Investigation</h2>
          ${active ? `<span class="badge badge-info">@${esc(active.target || "target-free")}</span>` : ""}
        </div>
        ${
          active
            ? `<div class="grid-4" style="margin-bottom:14px;">
                 <div class="stat-card"><div class="stat-label">Target</div><div class="stat-value" style="font-size:16px;">@${esc(active.target || "—")}</div></div>
                 <div class="stat-card"><div class="stat-label">Modules</div><div class="stat-value" style="font-size:16px;">${(active.results || []).length}</div></div>
                 <div class="stat-card"><div class="stat-label">Requests</div><div class="stat-value" style="font-size:16px;">${esc(active.api_calls_total || 0)}</div></div>
                 <div class="stat-card"><div class="stat-label">AI Summary</div><div class="stat-value" style="font-size:16px;">${active.ai_analysis ? "Included" : "Optional"}</div></div>
               </div>
               <div class="grid-2" style="gap:12px;">
                 <div class="notice">
                   <strong>Full Case ZIP Package</strong><br/>
                   <span class="form-help">Includes HTML/JSON/CSV reports, extracted <code>lists/</code> (emails, phones, followers, hashtags), raw JSON, and downloaded <code>media/</code>.</span>
                   <div style="margin-top:10px;"><button class="btn btn-primary btn-sm" id="repZip"><i data-lucide="archive"></i> Download Case ZIP</button></div>
                 </div>
                 <div class="notice">
                   <strong>Executive HTML &amp; Print-to-PDF</strong><br/>
                   <span class="form-help">Structured forensic report with KPI summary, tables, clickable links, and collapsible raw JSON evidence.</span>
                   <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;">
                     <button class="btn btn-sm" id="repPreview"><i data-lucide="eye"></i> Preview Report</button>
                     <button class="btn btn-sm" id="repHtml"><i data-lucide="file-text"></i> Download HTML</button>
                     <button class="btn btn-sm" id="repPrint"><i data-lucide="printer"></i> Print / PDF</button>
                   </div>
                 </div>
               </div>
               <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;">
                 <button class="btn btn-sm" id="repCsv"><i data-lucide="table"></i> Download CSV</button>
                 <button class="btn btn-sm" id="repJson"><i data-lucide="code"></i> Download JSON</button>
               </div>`
            : `<div class="notice">No active investigation in memory. Run an investigation or open one from Saved Investigations.</div>`
        }
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title"><i data-lucide="folder-archive"></i> Export Saved Dossiers</h2>
        </div>
        ${
          state.dossiers.length
            ? `<div class="table-wrap"><table>
                <thead><tr><th>Target</th><th>ID</th><th>Collected</th><th>Export</th></tr></thead>
                <tbody>
                  ${state.dossiers
                    .map(
                      (d) => `<tr>
                        <td><strong>@${esc(d.target)}</strong></td>
                        <td><code>${esc(d.id)}</code></td>
                        <td>${esc(fmtDate(d.saved_at))}</td>
                        <td style="display:flex;gap:6px;">
                          <button class="btn btn-sm btn-primary exp-saved" data-fmt="zip" data-target="${esc(d.target)}" data-id="${esc(d.id)}">Case ZIP</button>
                          <button class="btn btn-sm exp-saved" data-fmt="html" data-target="${esc(d.target)}" data-id="${esc(d.id)}">HTML</button>
                          <button class="btn btn-sm exp-saved" data-fmt="csv" data-target="${esc(d.target)}" data-id="${esc(d.id)}">CSV</button>
                          <button class="btn btn-sm exp-saved" data-fmt="json" data-target="${esc(d.target)}" data-id="${esc(d.id)}">JSON</button>
                        </td>
                      </tr>`
                    )
                    .join("")}
                </tbody>
              </table></div>`
            : `<div class="notice">No saved dossiers available.</div>`
        }
      </div>
    `;

    if (active) {
      $("#repZip").onclick = () => exportReport("zip");
      $("#repHtml").onclick = () => exportReport("html");
      $("#repCsv").onclick = () => exportReport("csv");
      $("#repJson").onclick = () => exportReport("json");
      $("#repPrint").onclick = () => window.print();
      $("#repPreview").onclick = async () => {
        try {
          const res = await fetch("/api/report/export", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ run: active, format: "html" }),
          });
          if (!res.ok) throw new Error(await res.text());
          const htmlText = await res.text();
          const blob = new Blob([htmlText], { type: "text/html;charset=utf-8" });
          window.open(URL.createObjectURL(blob), "_blank", "noopener");
        } catch (e) {
          toast(e.message, "err");
        }
      };
    }
    $$(".exp-saved", main).forEach((b) => {
      b.onclick = async () => {
        const run = await api(`/api/dossier/${encodeURIComponent(b.dataset.target)}/${encodeURIComponent(b.dataset.id)}`);
        exportReport(b.dataset.fmt, run);
      };
    });
  }

  // ---- 6. SETTINGS ----
  async function renderSettingsView(main) {
    const [ig, ai] = await Promise.all([api("/api/settings/instagram"), api("/api/ai/config")]);
    state.igStatus = ig;
    state.aiConfig = ai;
    updateGlobalStatus();

    main.innerHTML = `
      <div class="page-header">
        <div class="page-title-wrap">
          <div class="page-icon"><i data-lucide="settings"></i></div>
          <div>
            <h1 class="page-title">Settings</h1>
            <p class="page-subtitle">Manage Instagram session connection, optional Gemini AI configuration, and local storage.</p>
          </div>
        </div>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <h2 class="card-title"><i data-lucide="shield-check"></i> Instagram Connection</h2>
            <span class="badge ${ig.connected ? "badge-ok" : "badge-warn"}">${ig.connected ? "Connected" : "Not Connected"}</span>
          </div>
          <div class="notice" style="margin-bottom:12px;">
            Provider: <code>instagrapi</code> · Credentials: <strong>${ig.credentials_configured ? "Saved" : "Not set"}</strong><br/>
            Session file: <code>config/instagrapi_session.json</code> (${ig.session_exists ? "Present" : "Missing"})<br/>
            Account: ${ig.username ? `<strong>@${esc(maskUsername(ig.username))}</strong>` : "Not configured"}
          </div>

          <div style="padding-bottom:14px;margin-bottom:14px;border-bottom:1px solid var(--border);">
            <div class="form-label" style="margin-bottom:8px;">Direct Login (Username &amp; Password)</div>
            <div class="grid-2" style="gap:8px;margin-bottom:8px;">
              <input id="igUsernameInput" class="form-control" type="text" placeholder="${ig.username ? `Current: @${esc(maskUsername(ig.username))}` : "Instagram username"}" autocomplete="username" />
              <input id="igPasswordInput" class="form-control" type="password" placeholder="Instagram password" autocomplete="current-password" />
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
              <button class="btn btn-primary" id="saveIgCredsBtn">Login &amp; Save Credentials</button>
              <button class="btn" id="verifyIgSessionBtn">Verify Connection</button>
            </div>
            <div class="form-help">Credentials are stored server-side in <code>config/credentials.ini</code> and never exposed in the browser.</div>
          </div>

          <label class="form-label" for="igSessionIdInput">Or Update via Browser Session ID (write-only)</label>
          <input id="igSessionIdInput" class="form-control" type="password" placeholder="Paste Instagram sessionid cookie..." />
          <div class="form-help">Recommended if Instagram challenges direct password login from your IP.</div>
          <div style="display:flex;gap:8px;margin-top:10px;">
            <button class="btn" id="saveIgSessionBtn">Save Session ID</button>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h2 class="card-title"><i data-lucide="sparkles"></i> AI Configuration (Google Gemini)</h2>
            <span class="badge ${ai.enabled ? "badge-info" : ""}">${ai.enabled ? "Enabled" : "Optional"}</span>
          </div>
          <div style="margin-bottom:10px;">
            <label class="form-label" for="geminiKeyInput">Gemini API Key ${ai.preview ? `(Current: ${esc(ai.preview)})` : ""}</label>
            <input id="geminiKeyInput" class="form-control" type="password" placeholder="${ai.locked ? "Locked by GEMINI_API_KEY env var" : "Paste Gemini API key (optional)"}" ${ai.locked ? "disabled" : ""} />
          </div>
          <div style="margin-bottom:10px;">
            <label class="form-label" for="geminiModelSelect">Model Selection</label>
            <select id="geminiModelSelect" class="form-control">
              ${(ai.supported_models || [])
                .map((m) => `<option value="${esc(m.id)}" ${m.id === ai.model ? "selected" : ""}>${esc(m.label)}</option>`)
                .join("")}
            </select>
          </div>
          <label style="display:flex;align-items:center;gap:8px;margin-bottom:12px;cursor:pointer;">
            <input id="geminiEnabledCheck" type="checkbox" ${ai.enabled ? "checked" : ""} />
            <span>Enable optional Gemini AI post-collection analysis</span>
          </label>
          <div style="display:flex;gap:8px;">
            <button class="btn btn-primary" id="saveGeminiBtn">Save Configuration</button>
            <button class="btn" id="verifyGeminiBtn">Verify Connection</button>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h2 class="card-title"><i data-lucide="hard-drive"></i> Storage &amp; General</h2>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;padding-bottom:12px;margin-bottom:12px;border-bottom:1px solid var(--border);">
          <div>
            <strong>Interface Theme</strong><br/>
            <span class="form-help">Switch between Light and Dark appearance.</span>
          </div>
          <select id="themeSelect" class="form-control" style="width:160px;">
            <option value="light" ${getTheme() === "light" ? "selected" : ""}>Light</option>
            <option value="dark" ${getTheme() === "dark" ? "selected" : ""}>Dark</option>
          </select>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
          <div>
            <strong>Local Request Cache</strong><br/>
            <span class="form-help">Caches raw backend responses locally in SQLite to reduce repeated Instagram requests.</span>
          </div>
          <button class="btn" id="settingsClearCacheBtn"><i data-lucide="trash-2"></i> Clear Cache</button>
        </div>
      </div>
    `;

    $("#saveIgCredsBtn").onclick = async () => {
      const username = ($("#igUsernameInput").value || "").trim();
      const password = $("#igPasswordInput").value || "";
      if (!username || !password) return toast("Enter both Instagram username and password.", "err");
      const btn = $("#saveIgCredsBtn");
      btn.disabled = true;
      btn.textContent = "Logging in...";
      try {
        const res = await api("/api/settings/instagram/credentials", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });
        toast(`Instagram logged in & saved (@${maskUsername(res.username || username)}).`, "ok");
        renderSettingsView(main);
      } catch (e) {
        toast(e.message, "err");
      } finally {
        btn.disabled = false;
        btn.textContent = "Login & Save Credentials";
      }
    };
    $("#saveIgSessionBtn").onclick = async () => {
      const sid = ($("#igSessionIdInput").value || "").trim();
      if (!sid) return toast("Paste a sessionid first.", "err");
      try {
        await api("/api/settings/instagram/session", { method: "POST", body: JSON.stringify({ sessionid: sid }) });
        toast("Instagram session saved.", "ok");
        renderSettingsView(main);
      } catch (e) {
        toast(e.message, "err");
      }
    };
    $("#verifyIgSessionBtn").onclick = async () => {
      try {
        const res = await api("/api/settings/instagram/verify", { method: "POST" });
        toast(`Session verified (@${maskUsername(res.username || "ok")}).`, "ok");
        renderSettingsView(main);
      } catch (e) {
        toast(e.message, "err");
      }
    };
    $("#saveGeminiBtn").onclick = async () => {
      const payload = {
        model: $("#geminiModelSelect").value,
        enabled: $("#geminiEnabledCheck").checked,
      };
      const key = ($("#geminiKeyInput").value || "").trim();
      if (key) payload.api_key = key;
      try {
        state.aiConfig = await api("/api/ai/config", { method: "POST", body: JSON.stringify(payload) });
        updateGlobalStatus();
        toast("Gemini configuration saved.", "ok");
        renderSettingsView(main);
      } catch (e) {
        toast(e.message, "err");
      }
    };
    $("#verifyGeminiBtn").onclick = async () => {
      const key = ($("#geminiKeyInput").value || "").trim() || null;
      const model = $("#geminiModelSelect").value;
      try {
        const res = await api("/api/ai/verify", { method: "POST", body: JSON.stringify({ api_key: key, model }) });
        toast(`Gemini connected (${res.model}).`, "ok");
      } catch (e) {
        toast(e.message, "err");
      }
    };
    $("#settingsClearCacheBtn").onclick = clearCache;
    $("#themeSelect").onchange = (e) => applyTheme(e.target.value);
  }

  // ---- 7. ABOUT ----
  function renderAboutView(main) {
    const ab = state.about || {};
    main.innerHTML = `
      <div class="page-header">
        <div class="page-title-wrap">
          <div class="page-icon"><i data-lucide="info"></i></div>
          <div>
            <h1 class="page-title">About OSINT IG</h1>
            <p class="page-subtitle">Instagram Intelligence &amp; Investigation Platform</p>
          </div>
        </div>
      </div>

      <div class="card">
        <h2 style="margin-top:0;">OSINT IG v${esc(ab.version || "1.0")}</h2>
        <p><strong>Developer:</strong> ${esc(ab.author || "Mohsin Khawaja")}</p>
        <p><strong>Organization:</strong> ${esc(ab.organization_full || "Cyber Solutions & Information Board (CSIB)")}</p>
        <p class="form-help">Designed for authorized OSINT investigations, digital forensics, and public-profile analysis. Runs 100% locally on 127.0.0.1.</p>
      </div>

      <div class="card">
        <div class="card-header"><h2 class="card-title"><i data-lucide="shield-alert"></i> Terms &amp; Conditions</h2></div>
        <div class="notice notice-warn">
          <p style="margin-top:0;"><strong>Use at Your Own Risk:</strong> By using <strong>OSINT IG</strong>, you acknowledge and agree that you use this software entirely at your own risk.</p>
          <p><strong>OSINT &amp; Research Purpose Only:</strong> This tool is developed strictly for Open Source Intelligence (OSINT), authorized security research, digital forensics, and educational purposes.</p>
          <p style="margin-bottom:0;"><strong>User Responsibility:</strong> You are solely responsible for your actions, compliance with applicable local/international laws and platform Terms of Service, and any unlawful or unauthorized activity conducted with this tool. The developer (Mohsin Khawaja) assumes no responsibility or liability for any misuse.</p>
        </div>
      </div>

      <div class="card">
        <div class="card-header"><h2 class="card-title"><i data-lucide="package"></i> Core Components</h2></div>
        <div class="table-wrap"><table>
          <thead><tr><th>Library</th><th>Role</th><th>Version</th><th>License</th></tr></thead>
          <tbody>
            ${(ab.libraries || [])
              .map(
                (l) => `<tr>
                  <td><a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.name)}</a></td>
                  <td>${esc(l.role)}</td>
                  <td>${esc(l.version || "—")}</td>
                  <td>${esc(l.license || "—")}</td>
                </tr>`
              )
              .join("")}
          </tbody>
        </table></div>
      </div>
    `;
  }

  function getTheme() {
    return localStorage.getItem("osint_ig_theme") === "dark" ? "dark" : "light";
  }

  function applyTheme(theme) {
    const t = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", t);
    localStorage.setItem("osint_ig_theme", t);
    const btn = $("#themeToggleBtn");
    if (btn) {
      btn.innerHTML = `<i data-lucide="${t === "dark" ? "sun" : "moon"}"></i>`;
      btn.title = t === "dark" ? "Switch to light theme" : "Switch to dark theme";
      if (window.lucide) window.lucide.createIcons();
    }
  }

  // ---- BOOT ----
  document.addEventListener("DOMContentLoaded", async () => {
    applyTheme(getTheme());
    $("#themeToggleBtn").onclick = () => applyTheme(getTheme() === "dark" ? "light" : "dark");
    $("#sidebarToggle").onclick = () => $("#sidebar").classList.toggle("collapsed");
    document.addEventListener("click", (e) => {
      const navTarget = e.target.closest("[data-nav]");
      if (navTarget) navigate(navTarget.dataset.nav);
    });
    await loadInitialData();
    render();
  });
})();
