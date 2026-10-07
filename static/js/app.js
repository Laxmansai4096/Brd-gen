let currentSessionId = localStorage.getItem("brd_session_id") || "";
let currentSessionData = null;
let activePersona = "CLIENT"; // "CLIENT" | "SOLUTIONS_ARCHITECT" | "PROJECT_MANAGER" | "ADMIN"

let currentUser = {
  username: "Client Business Lead",
  role: "CLIENT",
  role_title: "Client Business Lead",
  avatar: "CL",
  token: null
};

let selectedLoginRole = "CLIENT";

const ROLE_PORT_CONFIG = {
  CLIENT: {
    port: 8081,
    name: "Client Business Lead",
    role: "Client Business Lead",
    avatar: "CL",
    class: "client",
    tag: "🧑‍💼 Client",
    pillId: "pillClient",
    desc: "Client Ideation, Discovery & Dual Review Portal",
    tip: "Typing as: <strong>Client Business Lead</strong>"
  },
  SOLUTIONS_ARCHITECT: {
    port: 8082,
    name: "Principal Solutions Architect",
    role: "Principal Solutions Architect",
    avatar: "SA",
    class: "architect",
    tag: "🏗️ Architect",
    pillId: "pillArchitect",
    desc: "Technical Architecture, Sizing BoM & Dual Review Portal",
    tip: "Typing as: <strong>Principal Solutions Architect</strong>"
  },
  PROJECT_MANAGER: {
    port: 8083,
    name: "Senior Delivery PM",
    role: "Senior Delivery PM",
    avatar: "PM",
    class: "pm",
    tag: "👔 PM",
    pillId: "pillPM",
    desc: "Project Governance, Tripartite Discussion & Final Approval Portal",
    tip: "Typing as: <strong>Senior Delivery PM</strong>"
  },
  ADMIN: {
    port: 8084,
    name: "System Administrator",
    role: "Enterprise Governance Admin",
    avatar: "AD",
    class: "admin",
    tag: "🛡️ Admin",
    pillId: "pillAdmin",
    desc: "Enterprise Admin & Governance Console (Calendars, Rates, Master Settings)",
    tip: "Operating as: <strong>System Administrator</strong>"
  }
};

const PERSONA_CONFIG = ROLE_PORT_CONFIG;

let isSidebarCollapsed = localStorage.getItem("brd_sidebar_collapsed") === "true";

function toggleLeftSidebar() {
  isSidebarCollapsed = !isSidebarCollapsed;
  localStorage.setItem("brd_sidebar_collapsed", isSidebarCollapsed ? "true" : "false");
  applySidebarState();
}

function applySidebarState() {
  const sidebar = document.getElementById("sidebarPanel");
  const headerIcon = document.getElementById("sidebarToggleIcon");
  const panelIcon = document.getElementById("panelToggleSidebarIcon");
  const panelText = document.getElementById("panelToggleSidebarText");

  if (!sidebar) return;

  if (isSidebarCollapsed) {
    sidebar.classList.add("collapsed");
    if (headerIcon) headerIcon.textContent = "▶";
    if (panelIcon) panelIcon.textContent = "▶";
    if (panelText) panelText.textContent = "Sidebar";
  } else {
    sidebar.classList.remove("collapsed");
    if (headerIcon) headerIcon.textContent = "☰";
    if (panelIcon) panelIcon.textContent = "◀";
    if (panelText) panelText.textContent = "Sidebar";
  }
}

let isChatExpanded = false;

function toggleChatExpand() {
  const chatPanel = document.getElementById("chatPanel");
  const workbenchPanel = document.querySelector(".workbench-panel");
  const btn = document.getElementById("btnToggleExpand");
  
  isChatExpanded = !isChatExpanded;
  if (isChatExpanded) {
    if (chatPanel) chatPanel.classList.add("expanded");
    if (workbenchPanel) workbenchPanel.style.display = "none";
    if (btn) btn.innerHTML = "<span>◫</span> Split View";
  } else {
    if (chatPanel) chatPanel.classList.remove("expanded");
    if (workbenchPanel) workbenchPanel.style.display = "flex";
    if (btn) btn.innerHTML = "<span>⛶</span> Focus Chat";
  }
}

// ==========================================================================
// USER AUTHENTICATION, ROLE SELECTION & MULTI-PORT GATEWAY
// ==========================================================================

function openLoginModal(preselectRole) {
  const modal = document.getElementById("loginModal");
  if (!modal) return;
  
  const targetRole = preselectRole || activePersona || "CLIENT";
  selectLoginRole(targetRole);

  const usernameInput = document.getElementById("loginUsername");
  if (usernameInput) {
    usernameInput.value = currentUser.username || ROLE_PORT_CONFIG[targetRole].name;
  }
  
  modal.style.display = "flex";
}

function closeLoginModal() {
  const modal = document.getElementById("loginModal");
  if (modal) modal.style.display = "none";
}

function selectLoginRole(role) {
  selectedLoginRole = role;
  
  // Highlight role cards
  document.querySelectorAll(".role-card-option").forEach(c => c.classList.remove("selected"));
  const card = document.getElementById(`roleCard_${role}`);
  if (card) card.classList.add("selected");
  
  // Update port destination preview
  const cfg = ROLE_PORT_CONFIG[role] || ROLE_PORT_CONFIG["CLIENT"];
  const portDisplay = document.getElementById("loginTargetPortDisplay");
  const descDisplay = document.getElementById("loginTargetDescDisplay");
  
  if (portDisplay) portDisplay.textContent = `http://127.0.0.1:${cfg.port}`;
  if (descDisplay) descDisplay.textContent = cfg.desc;
}

function quickLoginAs(role) {
  selectLoginRole(role);
  const cfg = ROLE_PORT_CONFIG[role];
  const nameInput = document.getElementById("loginUsername");
  if (nameInput) nameInput.value = cfg.name;
  submitUserLogin();
}

async function submitUserLogin() {
  const usernameInput = document.getElementById("loginUsername");
  const passwordInput = document.getElementById("loginPassword");
  
  const rawName = (usernameInput && usernameInput.value.trim()) ? usernameInput.value.trim() : ROLE_PORT_CONFIG[selectedLoginRole].name;
  const password = passwordInput ? passwordInput.value : "";
  const role = selectedLoginRole || "CLIENT";
  const targetPort = ROLE_PORT_CONFIG[role].port;
  const currentPort = parseInt(window.location.port || "8081", 10);
  
  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: rawName,
        password: password,
        role: role,
        session_id: currentSessionId
      })
    });
    
    let authData = null;
    if (res.ok) {
      authData = await res.json();
    }
    
    const userObj = (authData && authData.user) ? authData.user : {
      username: rawName,
      role: role,
      role_title: ROLE_PORT_CONFIG[role].role,
      avatar: ROLE_PORT_CONFIG[role].avatar,
      target_port: targetPort
    };
    
    // Persist in localStorage across all ports
    localStorage.setItem("brd_user_auth", JSON.stringify(userObj));
    currentUser = userObj;
    
    // Check if we need to redirect to another port
    if (currentPort !== targetPort) {
      showToast(`Redirecting to Port ${targetPort} for ${userObj.role_title}...`, "info");
      setTimeout(() => {
        window.location.href = `http://${window.location.hostname}:${targetPort}/?user=${encodeURIComponent(userObj.username)}&role=${role}&auth=1`;
      }, 350);
      return;
    }
    
    // If already on the matching port, apply immediately
    applyCurrentUserProfile();
    await switchActivePersona(role);
    closeLoginModal();
    showToast(`✓ Welcome, ${userObj.username}! Connected as ${userObj.role_title} on Port :${targetPort}.`, "success");
    
  } catch (err) {
    console.error("Login error:", err);
    // Fallback direct execution
    const userObj = {
      username: rawName,
      role: role,
      role_title: ROLE_PORT_CONFIG[role].role,
      avatar: ROLE_PORT_CONFIG[role].avatar,
      target_port: targetPort
    };
    localStorage.setItem("brd_user_auth", JSON.stringify(userObj));
    currentUser = userObj;
    
    if (currentPort !== targetPort) {
      window.location.href = `http://${window.location.hostname}:${targetPort}/?user=${encodeURIComponent(userObj.username)}&role=${role}&auth=1`;
    } else {
      applyCurrentUserProfile();
      switchActivePersona(role);
      closeLoginModal();
      showToast(`✓ Connected as ${userObj.role_title}`, "success");
    }
  }
}

function applyCurrentUserProfile() {
  const stored = localStorage.getItem("brd_user_auth");
  if (stored) {
    try {
      currentUser = JSON.parse(stored);
    } catch (e) {}
  }
  
  // Update Header User Widget
  const headerAvatar = document.getElementById("headerUserAvatar");
  const headerName = document.getElementById("headerUserName");
  const headerPort = document.getElementById("headerUserPort");
  const curPort = window.location.port || "8081";
  
  if (headerAvatar) headerAvatar.textContent = currentUser.avatar || "CL";
  if (headerName) headerName.textContent = currentUser.username || "Client Lead";
  if (headerPort) headerPort.textContent = `:${curPort}`;
  
  // Update Sidebar User Profile Card
  const sidebarAvatar = document.getElementById("sidebarAvatar");
  const sidebarName = document.getElementById("sidebarProfileName");
  const sidebarRole = document.getElementById("sidebarProfileRole");
  
  if (sidebarAvatar) {
    sidebarAvatar.innerHTML = `${currentUser.avatar || "CL"}<span class="status-online-dot" title="Active Port ${curPort}"></span>`;
  }
  if (sidebarName) sidebarName.textContent = currentUser.username || "Client Lead";
  if (sidebarRole) sidebarRole.textContent = `${currentUser.role_title || "Client Lead"} (Port :${curPort})`;
}

// Persona Switcher
async function switchActivePersona(persona) {
  if (!PERSONA_CONFIG[persona]) return;
  activePersona = persona;
  const cfg = PERSONA_CONFIG[persona];
  
  // Update Switcher Pills in header
  document.querySelectorAll(".persona-pill, .persona-tab-btn, .header-persona-pill").forEach(p => p.classList.remove("active"));
  const activePill = document.getElementById(cfg.pillId);
  if (activePill) activePill.classList.add("active");
  
  // Update Left Sidebar Profile
  applyCurrentUserProfile();
  
  // Update Chat Header Persona Tag
  const chatBadge = document.getElementById("chatActivePersonaBadge");
  if (chatBadge) {
    chatBadge.className = `msg-persona-tag msg-persona-${cfg.class}`;
    chatBadge.textContent = cfg.tag;
  }
  
  // Update Chat Input Tip
  const tipEl = document.getElementById("chatPersonaTip");
  if (tipEl) tipEl.innerHTML = `Typing as: <strong>${currentUser.username || cfg.name}</strong> (${cfg.role})`;

  // Render Persona Hero
  renderPersonaHero();

  if (persona === "SOLUTIONS_ARCHITECT") {
    loadArchitectBriefing();
  }

  // Sync to Backend
  if (currentSessionId) {
    try {
      await fetch("/api/workflow/switch-persona", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSessionId, persona: persona })
      });
    } catch (err) {
      console.warn("Could not sync persona to backend:", err);
    }
  }
}

// Render Persona-Specific Status
function renderPersonaHero() {
  const iconEl = document.getElementById("personaHeroIcon");
  const tagEl = document.getElementById("personaHeroTag");
  const descEl = document.getElementById("personaHeroDesc");

  document.body.classList.remove("persona-client-mode", "persona-architect-mode", "persona-pm-mode", "persona-admin-mode");

  if (activePersona === "CLIENT") {
    document.body.classList.add("persona-client-mode");
    if (iconEl) iconEl.innerHTML = "🧑‍💼";
    if (tagEl) tagEl.textContent = "Client Business Lead";
    if (descEl) descEl.textContent = "Define business objectives and discovery parameters";
  } else if (activePersona === "SOLUTIONS_ARCHITECT") {
    document.body.classList.add("persona-architect-mode");
    if (iconEl) iconEl.innerHTML = "🏗️";
    if (tagEl) tagEl.textContent = "Principal Solutions Architect";
    if (descEl) descEl.textContent = "Microservices decomposition, Sizing BoM & Dual Review";
  } else if (activePersona === "PROJECT_MANAGER") {
    document.body.classList.add("persona-pm-mode");
    if (iconEl) iconEl.innerHTML = "👔";
    if (tagEl) tagEl.textContent = "Senior Delivery PM";
    if (descEl) descEl.textContent = "12 disciplines, holiday calendars, and consensus sign-off";
  } else if (activePersona === "ADMIN") {
    document.body.classList.add("persona-admin-mode");
    if (iconEl) iconEl.innerHTML = "🛡️";
    if (tagEl) tagEl.textContent = "Enterprise System Administrator";
    if (descEl) descEl.textContent = "Statutory calendars, rate cards, and enterprise master settings";
  }
}

// Multi-Port Persona Auto-Configuration (Ports: 8081 Client, 8082 Architect, 8083 PM, 8084 Admin)
function configurePortPersona() {
  const port = window.location.port || "8081";
  const urlParams = new URLSearchParams(window.location.search);
  const paramUser = urlParams.get("user");
  const paramRole = urlParams.get("role");

  // If redirected with URL params, adopt credentials
  if (paramUser || paramRole) {
    const roleKey = (paramRole || (port === "8082" ? "SOLUTIONS_ARCHITECT" : port === "8083" ? "PROJECT_MANAGER" : port === "8084" ? "ADMIN" : "CLIENT")).toUpperCase();
    const cfg = ROLE_PORT_CONFIG[roleKey] || ROLE_PORT_CONFIG["CLIENT"];
    currentUser = {
      username: paramUser || cfg.name,
      role: roleKey,
      role_title: cfg.role,
      avatar: cfg.avatar,
      target_port: cfg.port
    };
    localStorage.setItem("brd_user_auth", JSON.stringify(currentUser));
  } else {
    // Check localStorage
    const stored = localStorage.getItem("brd_user_auth");
    if (stored) {
      try {
        currentUser = JSON.parse(stored);
      } catch (e) {}
    } else {
      // Default to port role
      const defaultRole = (port === "8082" ? "SOLUTIONS_ARCHITECT" : port === "8083" ? "PROJECT_MANAGER" : port === "8084" ? "ADMIN" : "CLIENT");
      const cfg = ROLE_PORT_CONFIG[defaultRole];
      currentUser = {
        username: cfg.name,
        role: defaultRole,
        role_title: cfg.role,
        avatar: cfg.avatar,
        target_port: cfg.port
      };
      localStorage.setItem("brd_user_auth", JSON.stringify(currentUser));
    }
  }

  applyCurrentUserProfile();

  if (port === "8082") {
    activePersona = "SOLUTIONS_ARCHITECT";
    document.title = "🏗️ Solutions Architect Portal (Port 8082)";
    switchActivePersona("SOLUTIONS_ARCHITECT");
    switchTab("tab-dual-review");
  } else if (port === "8083") {
    activePersona = "PROJECT_MANAGER";
    document.title = "👔 Project Manager Portal (Port 8083)";
    switchActivePersona("PROJECT_MANAGER");
    switchTab("tab-pm-review");
  } else if (port === "8084") {
    activePersona = "ADMIN";
    document.title = "🛡️ Admin Console (Port 8084)";
    switchActivePersona("ADMIN");
    setTimeout(() => { openAdminModal(); }, 450);
  } else {
    // Default to Client Lead on 8081 or standard ports
    activePersona = "CLIENT";
    document.title = "AI BRD Studio | Client Portal (Port 8081)";
    switchActivePersona("CLIENT");
  }
}

// Initialize app on load
document.addEventListener("DOMContentLoaded", async () => {
  applySidebarState();
  await loadSettings();
  await initSession();
  await loadProjectHistory();
  configurePortPersona();
});


// Load Settings from Server
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    if (res.ok) {
      const data = await res.json();
      updateProviderBadge(data.active_provider, data);
      
      const modalSelect = document.getElementById("modalProviderSelect");
      if (modalSelect) modalSelect.value = data.active_provider || "google";
      onModalProviderChange();
      
      if (data.gemini_api_key) document.getElementById("modalGeminiKey").value = data.gemini_api_key;
      if (data.google_model) document.getElementById("modalGoogleModel").value = data.google_model;
      if (data.google_endpoint) document.getElementById("modalGoogleEndpoint").value = data.google_endpoint;
      
      if (data.azure_openai_endpoint) document.getElementById("modalAzureEndpoint").value = data.azure_openai_endpoint;
      if (data.azure_openai_api_key) document.getElementById("modalAzureKey").value = data.azure_openai_api_key;
      if (data.azure_deployment) document.getElementById("modalAzureDeployment").value = data.azure_deployment;
      if (data.azure_api_version) document.getElementById("modalAzureApiVersion").value = data.azure_api_version;

      if (data.aws_region) document.getElementById("modalAWSRegion").value = data.aws_region;
      if (data.aws_access_key) document.getElementById("modalAWSAccessKey").value = data.aws_access_key;
      if (data.aws_secret_key) document.getElementById("modalAWSSecretKey").value = data.aws_secret_key;
      if (data.aws_session_token) document.getElementById("modalAWSSessionToken").value = data.aws_session_token;
      if (data.aws_model) document.getElementById("modalAWSModel").value = data.aws_model;

      if (data.openai_endpoint) document.getElementById("modalOpenAIEndpoint").value = data.openai_endpoint;
      if (data.openai_api_key) document.getElementById("modalOpenAIKey").value = data.openai_api_key;
      if (data.openai_model) document.getElementById("modalOpenAIModel").value = data.openai_model;
    }
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}

function updateProviderBadge(provider, data) {
  const badgeText = document.getElementById("activeProviderText");
  if (!badgeText) return;
  data = data || {};
  
  if (provider === "azure") {
    badgeText.textContent = `AI: Azure OpenAI (${data.azure_deployment || "gpt-4o"})`;
  } else if (provider === "aws") {
    const m = (data.aws_model || "Bedrock").split(".").pop();
    badgeText.textContent = `AI: AWS Bedrock (${m})`;
  } else if (provider === "openai") {
    badgeText.textContent = `AI: OpenAI / Custom (${data.openai_model || "gpt-4o"})`;
  } else {
    badgeText.textContent = `AI: Google Studio (${data.google_model || "gemini-2.5-flash"})`;
  }
}

// Session Initialization
async function initSession() {
  try {
    const url = currentSessionId ? `/api/session?session_id=${currentSessionId}` : "/api/session";
    const res = await fetch(url);
    if (res.ok) {
      currentSessionData = await res.json();
      currentSessionId = currentSessionData.session_id;
      localStorage.setItem("brd_session_id", currentSessionId);
      
      if (currentSessionData.workflow && currentSessionData.workflow.active_persona) {
        activePersona = currentSessionData.workflow.active_persona;
      }

      renderChatMessages();
      updateProgressCounter();
      updateWorkflowUI(currentSessionData);
      renderBRDTemplateSheet(currentSessionData.template_sheet);
      
      if (currentSessionData.brd) {
        renderBRDWorkbench(currentSessionData.brd);
      }
    }
  } catch (err) {
    console.error("Session init failed:", err);
  }
}

// Reset Session
async function resetSession() {
  if (confirm("Are you sure you want to reset the discovery session?")) {
    const res = await fetch(`/api/reset?session_id=${currentSessionId}`, { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      currentSessionId = data.session_id;
      localStorage.setItem("brd_session_id", currentSessionId);
      await initSession();
    }
  }
}

function formatMessageTimestamp(ts) {
  if (!ts) return '';
  if (typeof ts === 'string' && (ts === 'Just now' || ts.toLowerCase().includes('now'))) return 'Just now';
  const d = new Date(ts);
  if (!isNaN(d.getTime())) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return String(ts);
}

// Render Chat Stream
function renderChatMessages() {
  const container = document.getElementById("chatHistory");
  if (!container || !currentSessionData) return;
  
  container.innerHTML = "";
  const msgs = currentSessionData.messages || [];
  
  msgs.forEach((m) => {
    const msgDiv = document.createElement("div");
    const sender = m.sender || "agent";
    msgDiv.className = `chat-msg ${sender}`;
    
    let isAmbiguity = m.content.includes("Targeted Clarification") || m.content.includes("Ambiguity") || m.content.includes("too brief or ambiguous") || m.content.includes("ambiguous");
    let formattedText = "";
    if (window.marked && typeof marked.parse === "function") {
      formattedText = marked.parse(m.content);
    } else {
      formattedText = m.content
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\n\n/g, "</p><p>")
        .replace(/\n/g, "<br>");
    }

    if (isAmbiguity && sender === "agent") {
      formattedText = `<div class="ambiguity-card"><div class="ambiguity-card-title">⚠️ Specificity & Clarification Needed</div>${formattedText}</div>`;
    }

    let personaHeader = "";
    if (m.persona_name || m.persona) {
      const pRole = m.persona_role || (m.persona === "SOLUTIONS_ARCHITECT" ? "Principal Architect" : m.persona === "PROJECT_MANAGER" ? "Senior Delivery PM" : "Client Business Lead");
      const pCls = (m.persona === "SOLUTIONS_ARCHITECT" ? "architect" : (m.persona === "PROJECT_MANAGER" ? "pm" : "client"));
      const pTag = (m.persona === "SOLUTIONS_ARCHITECT" ? "🏗️ Architect" : (m.persona === "PROJECT_MANAGER" ? "👔 PM" : "🧑‍💼 Client"));
      personaHeader = `
        <div class="msg-author-header" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-size: 0.74rem;">
          <span class="msg-persona-tag msg-persona-${pCls}">${escapeHtml(m.persona_name ? `${pTag} — ${m.persona_name}` : pTag)}</span>
          <span style="color: #94a3b8; font-size: 0.68rem;">${formatMessageTimestamp(m.timestamp)}</span>
        </div>
      `;
    } else if (sender === "agent") {
      personaHeader = `
        <div class="msg-author-header" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-size: 0.74rem;">
          <span class="msg-persona-tag msg-persona-agent">🤖 BRD Discovery Agent</span>
          <span style="color: #94a3b8; font-size: 0.68rem;">${formatMessageTimestamp(m.timestamp)}</span>
        </div>
      `;
    }
      
    let innerHTML = `
      <div class="msg-content">
        ${personaHeader}
        <p>${formattedText}</p>
      </div>
    `;
    msgDiv.innerHTML = innerHTML;
    container.appendChild(msgDiv);
  });
  
  container.scrollTop = container.scrollHeight;
  renderQuickSuggestions();
}

function renderQuickSuggestions() {
  const customInput = document.getElementById("chatCustomInput");
  const quickTray = document.getElementById("quickOptionsTray");
  
  const curQ = currentSessionData ? currentSessionData.current_question : null;
  if (!curQ) {
    if (quickTray) quickTray.style.display = "none";
    if (customInput) {
      customInput.placeholder = "Discovery completed. Type any message, refinement, or feedback...";
      customInput.value = "";
    }
    return;
  }
  
  if (curQ.id === "q_client" || !curQ.options || curQ.options.length === 0) {
    if (quickTray) {
      quickTray.innerHTML = "";
      quickTray.style.display = "none";
    }
    if (customInput) {
      customInput.placeholder = "Enter Organization / Client Name & New Project Title (e.g. Acme Corp — AI Billing Automation)...";
      customInput.value = "";
      customInput.focus();
    }
    return;
  }

  if (customInput) {
    customInput.placeholder = `Type custom answer for ${curQ.title} (or click an option above)...`;
    customInput.value = "";
  }
  
  if (!quickTray) return;
  
  quickTray.innerHTML = "";
  quickTray.style.display = "flex";
  
  let optionsList = [];
  
  // Check if current question has predefined options
  if (curQ.options && curQ.options.length > 0) {
    optionsList = [...curQ.options];
  }

  
  // Check if latest message from agent has HITL follow-up options
  const msgs = currentSessionData.messages || [];
  const lastMsg = msgs.length > 0 ? msgs[msgs.length - 1] : null;
  if (lastMsg && lastMsg.hitl_options && lastMsg.hitl_options.length > 0) {
    lastMsg.hitl_options.forEach((opt) => {
      if (!optionsList.some(o => o.value === opt.value)) {
        optionsList.push({
          value: opt.value,
          label: opt.label,
          description: opt.description || ""
        });
      }
    });
  }
  
  if (optionsList.length > 0) {
    optionsList.forEach((opt, idx) => {
      const fullText = opt.description ? `${opt.label} — ${opt.description}` : opt.label;
      const isDefault = (opt.value === curQ.default_value) || (fullText === curQ.default_value) || (opt.label === curQ.default_value) || (idx === 0 && !curQ.default_value);

      const chip = document.createElement("div");
      chip.className = `quick-option-chip ${isDefault ? 'active' : ''}`;
      chip.title = "Click to select, Double-click or ⚡ to submit immediately";
      chip.innerHTML = `
        <span class="chip-label">${escapeHtml(opt.label)}</span>
        <button class="chip-instant-btn" title="Submit instantly" onclick="event.stopPropagation(); sendMessageWithText(${JSON.stringify(fullText)})">⚡</button>
      `;
      
      // Single click: put in custom input and highlight
      chip.onclick = () => {
        document.querySelectorAll('.quick-option-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        if (customInput) {
          customInput.value = fullText;
          customInput.focus();
        }
      };
      
      // Double click: immediately submit
      chip.ondblclick = (e) => {
        e.preventDefault();
        sendMessageWithText(fullText);
      };
      
      quickTray.appendChild(chip);
    });
  } else if (curQ.default_value) {
    const chip = document.createElement("div");
    chip.className = "quick-option-chip active";
    chip.title = "Click to select, Double-click or ⚡ to submit immediately";
    chip.innerHTML = `
      <span class="chip-label">${escapeHtml(curQ.default_value)} (Recommended)</span>
      <button class="chip-instant-btn" title="Submit instantly" onclick="event.stopPropagation(); sendMessageWithText(${JSON.stringify(curQ.default_value)})">⚡</button>
    `;
    chip.onclick = () => {
      if (customInput) {
        customInput.value = curQ.default_value;
        customInput.focus();
      }
    };
    chip.ondblclick = () => sendMessageWithText(curQ.default_value);
    quickTray.appendChild(chip);
  }

  // Add Direct "Ask Solutions Architect" Delegation Button for Client Persona
  if (curQ && activePersona === "CLIENT") {
    const delegateBtn = document.createElement("div");
    delegateBtn.className = "quick-option-chip";
    delegateBtn.style.background = "linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)";
    delegateBtn.style.color = "#ffffff";
    delegateBtn.style.borderColor = "#60a5fa";
    delegateBtn.style.fontWeight = "700";
    delegateBtn.style.boxShadow = "0 2px 8px rgba(59, 130, 246, 0.35)";
    delegateBtn.title = "Ask Solutions Architect to analyze this and provide technical recommendations";
    delegateBtn.innerHTML = `
      <span class="chip-label" style="color: #ffffff;">🏗️ Ask Solutions Architect</span>
      <button class="chip-instant-btn" style="background: rgba(255,255,255,0.2); color: #ffffff;" title="Delegate instantly to Architect" onclick="event.stopPropagation(); delegateCurrentQuestionToArchitect()">➔</button>
    `;
    delegateBtn.onclick = () => delegateCurrentQuestionToArchitect();
    quickTray.appendChild(delegateBtn);
  }
}

function handleCustomInputKeyDown(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    sendUserMessage();
  }
}

function updateProgressCounter() {
  const el = document.getElementById("progressCounter");
  if (!el || !currentSessionData) return;
  
  const dossier = (currentSessionData.confidence && currentSessionData.confidence.summary_dossier) || {};
  const confirmed = dossier.confirmed_domains_count !== undefined 
    ? (dossier.confirmed_domains_count + (dossier.escalated_domains_count || 0))
    : Object.keys(currentSessionData.answers || {}).length;
  const total = dossier.total_domains || 32;
  const completionRate = dossier.completion_rate !== undefined 
    ? dossier.completion_rate 
    : Math.min(100, Math.round((confirmed / total) * 100));
  const isGatePassed = dossier.is_gate_passed || (currentSessionData.confidence && currentSessionData.confidence.is_ready_for_brd) || completionRate >= 95.0;

  if (isGatePassed || currentSessionData.has_brd) {
    el.className = "progress-counter gate-passed";
    el.innerHTML = `<span>🎯</span> <strong>Gate Passed (95%+ Ready)</strong> — ${confirmed}/${total} Domains (${completionRate}%)`;
  } else {
    el.className = "progress-counter";
    el.innerHTML = `<span>📊</span> <strong>Domain Coverage:</strong> ${confirmed} / ${total} (${completionRate}%) <span class="gate-target-pill">Gate: 95%</span>`;
  }
}

function renderBRDTemplateSheet(templateSheet) {
  const container = document.getElementById("brdTemplateTopicsContainer");
  const percentText = document.getElementById("brdSheetPercentText");
  const meterFill = document.getElementById("brdSheetMeterFill");
  const keyCountEl = document.getElementById("brdSheetKeyCount");
  const statusBadge = document.getElementById("brdSheetStatusBadge");
  const calloutContainer = document.getElementById("gate95CalloutContainer");

  if (!templateSheet && currentSessionData && currentSessionData.template_sheet) {
    templateSheet = currentSessionData.template_sheet;
  }
  if (!templateSheet || !container) return;

  const rate = templateSheet.completion_rate || 0;
  const isPassed = templateSheet.is_gate_passed || (rate >= 95.0);
  const keyFilled = templateSheet.key_fields_filled || 0;
  const keyTotal = templateSheet.key_fields_total || 17;

  if (percentText) percentText.textContent = `${rate}%`;
  if (meterFill) {
    meterFill.style.width = `${Math.min(100, rate)}%`;
    if (rate >= 95) {
      meterFill.style.background = "linear-gradient(90deg, #10b981, #059669)";
    } else {
      meterFill.style.background = "linear-gradient(90deg, #3b82f6, #10b981)";
    }
  }
  if (keyCountEl) {
    keyCountEl.textContent = `${keyFilled} / ${keyTotal} Key Fields Filled (Gate: 95%)`;
  }
  if (statusBadge) {
    if (isPassed) {
      statusBadge.className = "badge badge-success";
      statusBadge.textContent = "95% Gate Passed";
    } else {
      statusBadge.className = "badge badge-info";
      statusBadge.textContent = "Collecting Information";
    }
  }

  // Hide premature client approval banner if BRD is not yet synthesized
  const approvalBanner = document.getElementById("brdApprovalBanner");
  if (approvalBanner) {
    const hasBrd = (currentSessionData && currentSessionData.has_brd) || templateSheet.has_synthesized_brd;
    approvalBanner.style.display = hasBrd ? "block" : "none";
  }

  // Gate 95% Action Callout
  if (calloutContainer) {
    if (isPassed) {
      calloutContainer.style.display = "block";
      calloutContainer.innerHTML = `
        <div class="gate-95-banner">
          <div>
            <div style="font-weight: 700; font-size: 0.95rem;">🎉 95%+ Confidence Gate Passed (${rate}%)!</div>
            <div style="font-size: 0.80rem; opacity: 0.95;">All key data fields confirmed across Client & Architect. Draft BRD synthesized.</div>
          </div>
          <button class="gate-95-btn" onclick="switchTab('tab-dual-review')">Inspect & Review BRD Template →</button>
        </div>
      `;
    } else {
      calloutContainer.style.display = "none";
    }
  }

  // Topics Render
  container.innerHTML = "";
  const topics = templateSheet.topics || [];
  topics.forEach((topic) => {
    const topicCard = document.createElement("div");
    topicCard.className = "brd-sheet-topic-card";

    let fieldsHtml = "";
    (topic.fields || []).forEach((f) => {
      const isFilled = (f.status === "FILLED");
      const statusClass = isFilled ? "filled" : "pending";
      const badgeText = isFilled ? "✓ Confirmed" : "⏳ Pending";
      const displayVal = f.value ? escapeHtml(f.value) : `<em style="color:#94a3b8;">Pending chat intake...</em>`;
      const keyTag = f.is_key ? `<span style="color:#ef4444; font-weight:700;" title="Key Required Data Field">*</span>` : "";

      fieldsHtml += `
        <div class="brd-sheet-field-row ${statusClass}">
          <div class="brd-field-name">
            <span>${keyTag}${escapeHtml(f.title)}:</span>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <div class="brd-field-val" title="${f.value ? escapeHtml(f.value) : ''}">${displayVal}</div>
            <span class="brd-field-badge ${statusClass}">${badgeText}</span>
          </div>
        </div>
      `;
    });

    topicCard.innerHTML = `
      <div class="brd-sheet-topic-header">
        <div class="brd-sheet-topic-title">
          <span>${topic.icon || '📌'}</span>
          <span>${escapeHtml(topic.title)}</span>
        </div>
        <span class="badge" style="font-size: 0.68rem; background: #e0f2fe; color: #0369a1;">${escapeHtml(topic.primary_persona || '')}</span>
      </div>
      <div class="brd-sheet-field-grid">
        ${fieldsHtml}
      </div>
    `;
    container.appendChild(topicCard);
  });
}

function sendUserMessage() {
  const customInput = document.getElementById("chatCustomInput");
  
  let answer = "";
  if (customInput) {
    answer = customInput.value.trim();
  }
  
  if (!answer && currentSessionData && currentSessionData.current_question) {
    const curQ = currentSessionData.current_question;
    answer = curQ.default_value || (curQ.options && curQ.options.length > 0 ? (curQ.options[0].description ? `${curQ.options[0].label} — ${curQ.options[0].description}` : curQ.options[0].label) : "");
  }
  
  if (!answer) return;
  
  if (customInput) customInput.value = "";
  sendMessageWithText(answer);
}

async function sendMessageWithText(text, displayText) {
  if (!text) return;
  
  // Resolve display text if not provided
  if (!displayText) {
    displayText = text;
    if (currentSessionData && currentSessionData.current_question && currentSessionData.current_question.options) {
      const match = currentSessionData.current_question.options.find(o => o.value === text);
      if (match) {
        const desc = match.description ? ` — ${match.description}` : '';
        displayText = `${match.label}${desc}`;
      }
    }
  }

  try {
    // Add optimistic user message to chat immediately with full display text
    const container = document.getElementById("chatHistory");
    const cfg = PERSONA_CONFIG[activePersona] || PERSONA_CONFIG.CLIENT;
    if (container) {
      const userDiv = document.createElement("div");
      userDiv.className = "chat-msg user";
      const pHeader = `
        <div class="msg-author-header" style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-size: 0.74rem;">
          <span class="msg-persona-tag msg-persona-${cfg.class}">${escapeHtml(cfg.tag + " — " + cfg.name)}</span>
          <span style="color: #94a3b8; font-size: 0.68rem;">Just now</span>
        </div>
      `;
      userDiv.innerHTML = `<div class="msg-content">${pHeader}<p>${escapeHtml(displayText)}</p></div>`;
      container.appendChild(userDiv);
      container.scrollTop = container.scrollHeight;
    }

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        message: displayText || text,
        selected_option: text,
        persona: activePersona
      })
    });
    
    if (res.ok) {
      currentSessionData = await res.json();
      renderChatMessages();
      updateProgressCounter();
      updateWorkflowUI(currentSessionData);
      renderBRDTemplateSheet(currentSessionData.template_sheet);
      
      if (currentSessionData.brd) {
        renderBRDWorkbench(currentSessionData.brd);
      }
    }
  } catch (err) {
    console.error("Chat send error:", err);
  }
}

// Handle Document Upload
async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  const formData = new FormData();
  formData.append("session_id", currentSessionId);
  formData.append("file", file);
  
  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      currentSessionData.messages = data.messages;
      renderChatMessages();
    }
  } catch (err) {
    console.error("Upload error:", err);
  }
}

// Render Complete BRD Workbench
function renderBRDWorkbench(brd) {
  if (!brd) return;

  const sym = brd.currency_symbol || "$";
  const rate = brd.currency_exchange_rate || 1.0;
  const currCode = brd.currency_code || "USD";

  // Global Currency Dropdown Sync
  const currSelect = document.getElementById("globalCurrencySelect");
  if (currSelect && currSelect.value !== currCode) {
    currSelect.value = currCode;
  }
  
  // Top Metrics Strip
  document.getElementById("metricTier").textContent = brd.delivery_tier;
  document.getElementById("metricDuration").textContent = `${brd.total_duration_weeks.toFixed(1)} wks (Headline: ${brd.headline_weight.toFixed(3)})`;
  document.getElementById("metricDays").textContent = `${brd.total_person_days.toFixed(1)} d`;
  document.getElementById("metricHours").textContent = `${brd.total_person_hours.toFixed(0)} Person-Hours`;
  
  const convertedLabour = brd.total_labour_cost_converted || (brd.total_labour_cost_usd * rate);
  document.getElementById("metricCost").textContent = `${sym}${Math.round(convertedLabour).toLocaleString()}`;
  
  const monthlyCloudConverted = (brd.sizing_metrics.total_monthly_cloud_cost_usd || 645) * rate;
  document.getElementById("metricCloudCost").textContent = `${sym}${Math.round(monthlyCloudConverted).toLocaleString()}/mo`;
  
  const gatePassed = brd.assumption_gate_passed;
  const gateEl = document.getElementById("metricGateStatus");
  if (gateEl) {
    gateEl.textContent = gatePassed ? "PASSED" : "ACTION REQUIRED";
    gateEl.style.color = gatePassed ? "var(--success)" : "#f87171";
  }
  
  // Header Client Tag
  const headerTag = document.getElementById("headerClientTag");
  if (headerTag) headerTag.textContent = `${brd.client_name} — ${brd.project_title}`;

  // Tab 1: BRD Document
  document.getElementById("brdTitle").textContent = `${brd.client_name} — ${brd.project_title}`;
  document.getElementById("brdBadgeTier").textContent = `${brd.delivery_tier.toUpperCase()} TIER (${brd.tier_kind})`;
  
  // Executive Summary - point by point formatted rendering
  const execSummaryEl = document.getElementById("brdExecSummary");
  if (execSummaryEl) {
    if (brd.executive_summary) {
      const summarySentences = brd.executive_summary
        .split(/(?<=[.!?])\s+(?=[A-Z0-9*])/)
        .map(s => s.trim())
        .filter(s => s.length > 0);
      
      if (summarySentences.length > 1) {
        execSummaryEl.innerHTML = `<ul style="padding-left: 20px; font-size: 0.90rem; color: var(--text-main); line-height: 1.8; margin: 0; display: flex; flex-direction: column; gap: 6px;">` +
          summarySentences.map(s => `<li>${s.replace(/\*\*(.*?)\*\*/g, '<strong style="color: var(--text-heading);">$1</strong>')}</li>`).join("") +
          `</ul>`;
      } else {
        execSummaryEl.innerHTML = brd.executive_summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      }
    } else {
      execSummaryEl.textContent = "Complete the discovery interview to synthesize the full executive BRD.";
    }
  }

  // Business Problem
  const problemEl = document.getElementById("brdProblemText");
  if (problemEl) {
    if (brd.problem_statement) {
      problemEl.innerHTML = `<div style="background: rgba(56, 189, 248, 0.05); border-left: 4px solid var(--primary); padding: 10px 14px; border-radius: 4px; font-weight: 500; color: var(--text-heading); margin-bottom: 12px;">${brd.problem_statement.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</div>`;
    } else {
      problemEl.innerHTML = "";
    }
  }

  // Solution Narrative - Six Sentences Point-by-Point Cards
  const sixSentencesEl = document.getElementById("brdSixSentences");
  if (sixSentencesEl) {
    if (brd.solution_summary_six_sentences) {
      const sentences = brd.solution_summary_six_sentences
        .split(/(?<=[.!?])\s+(?=[A-Z0-9*])/)
        .map(s => s.trim())
        .filter(s => s.length > 0);

      const sentenceLabels = [
        "1. Architectural Baseline & Cloud Foundation",
        "2. Ingestion & Multi-Source Knowledge Capture",
        "3. Semantic Retrieval & Grounding Engine",
        "4. Generative AI Reasoning & Policy Execution",
        "5. Structured Persistence & Automated Handoff",
        "6. Evaluation Harness & Continuous Quality Gates"
      ];

      if (sentences.length > 1) {
        sixSentencesEl.innerHTML = `<div style="display: flex; flex-direction: column; gap: 10px;">` +
          sentences.map((sent, idx) => {
            const label = sentenceLabels[idx] || `Step ${idx + 1}`;
            return `
              <div style="background: #ffffff; border: 1px solid var(--border-color); border-left: 4px solid var(--primary); border-radius: 6px; padding: 10px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                <div style="font-size: 0.78rem; font-weight: 700; color: var(--primary); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
                  ${label}
                </div>
                <div style="font-size: 0.88rem; color: var(--text-main); line-height: 1.55;">
                  ${sent.replace(/\*\*(.*?)\*\*/g, '<strong style="color: var(--text-heading);">$1</strong>')}
                </div>
              </div>
            `;
          }).join("") +
          `</div>`;
      } else {
        sixSentencesEl.innerHTML = brd.solution_summary_six_sentences.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      }
    } else {
      sixSentencesEl.textContent = "";
    }
  }
  
  const impactsList = document.getElementById("brdImpactsList");
  impactsList.innerHTML = (brd.business_impacts || []).map(imp => {
    // Highlight label if it has a colon
    const formatted = imp.includes(":") 
      ? `<strong>${imp.split(":")[0]}:</strong> ${imp.substring(imp.indexOf(":") + 1)}`
      : imp;
    return `<li style="margin-bottom: 4px;">${formatted}</li>`;
  }).join("");
  
  const inScopeList = document.getElementById("brdInScopeList");
  inScopeList.innerHTML = (brd.in_scope || []).map(s => `<li style="margin-bottom: 6px;">${s}</li>`).join("");
  
  const outScopeList = document.getElementById("brdOutScopeList");
  outScopeList.innerHTML = (brd.out_of_scope || []).map(s => `<li style="margin-bottom: 6px;">${s}</li>`).join("");
  
  document.getElementById("brdDataFlow").textContent = brd.data_flow_narrative;

  // Tab 2: 12 Disciplines & Tasks
  const rolesTbody = document.getElementById("rolesTableBody");
  if (rolesTbody) {
    rolesTbody.innerHTML = (brd.role_efforts || []).map(r => {
      const roleCostConverted = (r.cost || 0) * rate;
      return `
        <tr>
          <td><strong>${r.role_code}</strong></td>
          <td><strong>${r.role}</strong></td>
          <td style="color: var(--text-muted); font-size: 0.8rem;">${r.description}</td>
          <td><strong>${r.days.toFixed(1)} d</strong></td>
          <td>${r.hours.toFixed(0)} h</td>
          <td style="color: var(--success); font-weight: 600;">${sym}${Math.round(roleCostConverted).toLocaleString()}</td>
          <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.75rem;">${(r.active_fte || r.peak_fte || 0).toFixed(2)} FTE</span></td>
          <td><span style="color: var(--primary); font-size: 0.75rem;">+${(r.buffer_fte || 0).toFixed(2)} FTE</span></td>
          <td><strong style="color: var(--text-heading);">${(r.total_assigned_fte || r.peak_fte || 0).toFixed(2)} FTE</strong></td>
        </tr>
      `;
    }).join("") + `
      <tr style="background: rgba(72, 98, 247, 0.08); font-weight: bold;">
        <td colspan="3">TOTAL (12 Disciplines Standardized @ ${sym}${(30 * rate).toFixed(2)}/hr)</td>
        <td>${brd.total_person_days.toFixed(1)} d</td>
        <td>${brd.total_person_hours.toFixed(0)} h</td>
        <td style="color: var(--success);">${sym}${Math.round(convertedLabour).toLocaleString()}</td>
        <td colspan="3">-</td>
      </tr>
    `;
  }

  // Standby Buffer Resources Table
  const bufferTbody = document.getElementById("backupResourcesTableBody");
  const bufferBadge = document.getElementById("standbyBufferBadge");
  if (bufferBadge) bufferBadge.textContent = `${brd.buffer_capacity_pct || 15}% Standby Protection`;
  if (bufferTbody) {
    const backupList = brd.backup_resources || [];
    if (backupList.length === 0) {
      bufferTbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No standby buffer resources allocated (Zero Standby Mode).</td></tr>`;
    } else {
      bufferTbody.innerHTML = backupList.map(b => `
        <tr>
          <td><strong style="color: var(--primary);">${b.role}</strong></td>
          <td><span class="badge-ai" style="font-size: 0.72rem;">${b.level}</span></td>
          <td>${b.location}</td>
          <td><span style="color: var(--success); font-weight: 600;">${b.allocation_pct}</span></td>
          <td style="font-size: 0.82rem; color: var(--text-main);">${b.purpose}</td>
        </tr>
      `).join("");
    }
  }

  const tasksTbody = document.getElementById("tasksTableBody");
  if (tasksTbody) {
    tasksTbody.innerHTML = (brd.task_estimates || []).map(t => `
      <tr>
        <td><span style="font-weight: 600; color: var(--primary);">${t.phase_code}</span></td>
        <td style="font-size: 0.82rem; color: var(--text-main);">${t.task_name}</td>
        <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.72rem;">${t.primary_role}</span></td>
        <td>${t.base_days.toFixed(1)}</td>
        <td>${t.phase_factor.toFixed(3)}</td>
        <td>${t.scale_factor.toFixed(3)}</td>
        <td>${t.uplift_tag !== "NONE" ? `<span style="color: #d97706; font-weight: 600;">${t.uplift_tag} (${t.uplift_mult.toFixed(2)})</span>` : "1.00"}</td>
        <td style="font-weight: 600; color: var(--text-heading);">${t.effort_days.toFixed(2)} d</td>
      </tr>
    `).join("");
  }

  // Tab 3: 18-Phase Roadmap & Feasibility
  const feas = brd.schedule_feasibility;
  const feasCard = document.getElementById("feasibilityCard");
  if (feasCard && feas) {
    feasCard.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px;">
        <div class="feas-tile">
          <div class="feas-tile-label">Reference Duration</div>
          <div class="feas-tile-val" style="color: #0f172a;">${feas.reference_duration_weeks.toFixed(1)} Weeks</div>
          <div class="feas-tile-sub">${feas.working_days} working days</div>
        </div>
        <div class="feas-tile">
          <div class="feas-tile-label">Resolved Duration</div>
          <div class="feas-tile-val" style="color: ${feas.schedule_stretched ? '#dc2626' : '#16a34a'};">${feas.resolved_duration_weeks.toFixed(1)} Weeks</div>
          <div class="feas-tile-sub">${feas.schedule_stretched ? '⚠️ Schedule Stretched' : '✅ Feasible Schedule'}</div>
        </div>
        <div class="feas-tile">
          <div class="feas-tile-label">Peak Role FTE</div>
          <div class="feas-tile-val" style="color: #2563eb;">${feas.peak_fte_observed.toFixed(2)} FTE</div>
          <div class="feas-tile-sub">Limit: ${feas.max_fte_limit.toFixed(0)} FTE peak capacity</div>
        </div>
        <div class="feas-tile">
          <div class="feas-tile-label">Binding Constraint</div>
          <div class="feas-tile-val" style="color: #7c3aed; font-size: 0.95rem;">${escapeHtml(feas.binding_constraint)}</div>
          <div class="feas-tile-sub">Resource loading ceiling</div>
        </div>
      </div>
    `;
  }

  const phasesList = document.getElementById("phasesList");
  if (phasesList) {
    const stageColors = {
      P01: { border: "#6366f1", bg: "rgba(99, 102, 241, 0.12)", text: "#4f46e5", label: "Foundation & Framing" },
      P02: { border: "#6366f1", bg: "rgba(99, 102, 241, 0.12)", text: "#4f46e5", label: "Requirements & MoSCoW" },
      P03: { border: "#3b82f6", bg: "rgba(59, 130, 246, 0.12)", text: "#2563eb", label: "Data Ingestion & Profiling" },
      P04: { border: "#3b82f6", bg: "rgba(59, 130, 246, 0.12)", text: "#2563eb", label: "Architecture Specification" },
      P05: { border: "#0284c7", bg: "rgba(2, 132, 199, 0.12)", text: "#0284c7", label: "Cloud Landing Zone" },
      P06: { border: "#0284c7", bg: "rgba(2, 132, 199, 0.12)", text: "#0284c7", label: "Pipeline & Indexing" },
      P07: { border: "#0d9488", bg: "rgba(13, 148, 136, 0.12)", text: "#0d9488", label: "Vector Search & Retrieval" },
      P08: { border: "#0d9488", bg: "rgba(13, 148, 136, 0.12)", text: "#0d9488", label: "Model Reasoning & Orchestration" },
      P09: { border: "#0891b2", bg: "rgba(8, 145, 178, 0.12)", text: "#0891b2", label: "Backend API & Services" },
      P10: { border: "#0891b2", bg: "rgba(8, 145, 178, 0.12)", text: "#0891b2", label: "Frontend & Persona UX" },
      P11: { border: "#8b5cf6", bg: "rgba(139, 92, 246, 0.12)", text: "#7c3aed", label: "Enterprise SSO & Security" },
      P12: { border: "#8b5cf6", bg: "rgba(139, 92, 246, 0.12)", text: "#7c3aed", label: "Responsible AI & Compliance" },
      P13: { border: "#d97706", bg: "rgba(217, 119, 6, 0.12)", text: "#b45309", label: "Observability & Telemetry" },
      P14: { border: "#d97706", bg: "rgba(217, 119, 6, 0.12)", text: "#b45309", label: "CI/CD & DevOps Automation" },
      P15: { border: "#e11d48", bg: "rgba(225, 29, 72, 0.12)", text: "#be123c", label: "Performance & Stress Testing" },
      P16: { border: "#e11d48", bg: "rgba(225, 29, 72, 0.12)", text: "#be123c", label: "Security & Penetration Audit" },
      P17: { border: "#16a34a", bg: "rgba(22, 163, 74, 0.12)", text: "#15803d", label: "Business UAT & Pilot" },
      P18: { border: "#16a34a", bg: "rgba(22, 163, 74, 0.12)", text: "#15803d", label: "Production Go-Live & Handover" }
    };

    phasesList.innerHTML = (brd.project_phases || []).map(p => {
      const codeMatch = p.phase_name.match(/^P\d+/);
      const code = codeMatch ? codeMatch[0] : "PHASE";
      const meta = stageColors[code] || { border: "#4862f7", bg: "rgba(72, 98, 247, 0.1)", text: "#3b51d6", label: "Delivery Phase" };
      const delivs = (p.key_deliverables || []).map(d => `<span class="deliverable-tag">${escapeHtml(d)}</span>`).join("");

      return `
        <div class="phase-roadmap-card" style="border-left: 4px solid ${meta.border};">
          <div style="flex: 1; min-width: 260px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap;">
              <span class="phase-code-pill" style="background: ${meta.bg}; color: ${meta.text}; border: 1px solid ${meta.border}44;">${code}</span>
              <span style="font-weight: 700; color: #0f172a; font-size: 0.95rem;">${escapeHtml(p.phase_name.replace(/^P\d+:\s*/, ''))}</span>
              <span style="font-size: 0.72rem; color: #64748b; background: #f1f5f9; padding: 2px 8px; border-radius: 10px; font-weight: 600;">${meta.label}</span>
            </div>
            <div class="deliverables-container" style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px;">
              ${delivs}
            </div>
          </div>
          <div style="display: flex; flex-direction: column; align-items: flex-end; justify-content: center; min-width: 140px; text-align: right;">
            <span style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-weight: 700; font-size: 0.95rem; padding: 4px 10px; border-radius: 8px;">
              ${p.weeks.toFixed(1)} wks
            </span>
            <span style="font-size: 0.78rem; color: #64748b; font-weight: 600; margin-top: 4px;">
              ${p.effort_days.toFixed(1)} Person-Days
            </span>
          </div>
        </div>
      `;
    }).join("");
  }

  // Tab 4: Technical Components (6)
  const compList = document.getElementById("componentsList");
  if (compList) {
    compList.innerHTML = (brd.technical_components || []).map(c => `
      <div class="tech-component-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid var(--border-color); padding-bottom: 10px;">
          <div>
            <span class="badge-ai" style="padding: 2px 8px; font-size: 0.72rem; margin-right: 6px;">${c.id}</span>
            <strong style="color: #0f172a; font-size: 1rem;">${escapeHtml(c.name)}</strong>
          </div>
          <span style="background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; font-weight: 600; padding: 4px 10px; border-radius: 8px; font-size: 0.78rem;">
            ${escapeHtml(c.technology_choice)}
          </span>
        </div>
        <p style="font-size: 0.86rem; color: #334155; margin-bottom: 14px; line-height: 1.5;">
          <strong>Purpose:</strong> ${escapeHtml(c.purpose)}
        </p>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.82rem; color: #475569; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #e2e8f0;">
          <div><strong style="color: #0f172a;">Key Decisions:</strong> ${escapeHtml(c.key_design_decisions)}</div>
          <div><strong style="color: #0f172a;">Interfaces:</strong> <code>${escapeHtml(c.interfaces_in_out)}</code></div>
          <div><strong style="color: #0f172a;">Scalability & Limits:</strong> ${escapeHtml(c.scalability_performance)}</div>
          <div><strong style="color: #0f172a;">Security & Guardrails:</strong> ${escapeHtml(c.security_rai_controls)}</div>
        </div>
      </div>
    `).join("");
  }

  // Tab 5: Sizing & Cloud BoM & 3-Year TCO
  const tco = brd.tco_projection || {};
  if (document.getElementById("tcoYear1")) document.getElementById("tcoYear1").textContent = `${sym}${Math.round((tco.year1_build_usd || 32628) * rate).toLocaleString()}`;
  if (document.getElementById("tcoYear2")) document.getElementById("tcoYear2").textContent = `${sym}${Math.round((tco.year2_run_usd || 12713) * rate).toLocaleString()}`;
  if (document.getElementById("tcoYear3")) document.getElementById("tcoYear3").textContent = `${sym}${Math.round((tco.year3_run_usd || 13678) * rate).toLocaleString()}`;
  if (document.getElementById("tcoCumulative")) document.getElementById("tcoCumulative").textContent = `${sym}${Math.round((tco.total_3year_tco_usd || 59019) * rate).toLocaleString()}`;
  if (document.getElementById("tcoBreakEven")) document.getElementById("tcoBreakEven").textContent = `Break-Even @ Month 14 (${tco.payg_advantage_pct || 46.5}% PayG Advantage)`;
  if (document.getElementById("tcoPaygMonthly")) document.getElementById("tcoPaygMonthly").textContent = `${sym}${Math.round((monthlyCloudConverted || 645)).toLocaleString()}/mo`;
  if (document.getElementById("tcoPtuMonthly")) document.getElementById("tcoPtuMonthly").textContent = `${sym}${Math.round(4800 * rate).toLocaleString()}/mo`;
  if (document.getElementById("tcoStrategyBadge")) document.getElementById("tcoStrategyBadge").textContent = "Pay-As-You-Go Optimal (46.5% Savings)";

  const sizingGrid = document.getElementById("sizingMetricsGrid");
  const sm = brd.sizing_metrics;
  if (sizingGrid && sm) {
    sizingGrid.innerHTML = `
      <div class="metric-card"><span class="metric-label">Named Users</span><span class="metric-val">${sm.named_users}</span><span class="metric-sub">${sm.peak_concurrent_users} Concurrent</span></div>
      <div class="metric-card"><span class="metric-label">Requests / Day</span><span class="metric-val">${sm.requests_per_day.toLocaleString()}</span><span class="metric-sub">${sm.peak_rps} Peak RPS</span></div>
      <div class="metric-card"><span class="metric-label">Tokens / Call</span><span class="metric-val">${sm.prompt_tokens_avg + sm.completion_tokens_avg}</span><span class="metric-sub">${sm.prompt_tokens_avg} In / ${sm.completion_tokens_avg} Out</span></div>
      <div class="metric-card"><span class="metric-label">Corpus Size</span><span class="metric-val">${sm.corpus_documents.toLocaleString()} docs</span><span class="metric-sub">${sm.raw_corpus_gb} GB (${sm.avg_chunks_per_doc} chk/doc)</span></div>
      <div class="metric-card"><span class="metric-label">HA / DR Tier</span><span class="metric-val" style="font-size: 0.9rem;">${sm.ha_dr_tier}</span><span class="metric-sub">Non-Prod: ${(sm.non_prod_factor * 100).toFixed(0)}%</span></div>
    `;
  }

  const bomTbody = document.getElementById("bomTableBody");
  if (bomTbody) {
    bomTbody.innerHTML = (brd.sizing_bom || []).map(b => {
      const convertedCost = (b.monthly_cost_usd || 0) * rate;
      return `
        <tr>
          <td><strong>${b.component}</strong></td>
          <td>${b.sku_or_service}</td>
          <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.72rem;">${b.tier}</span></td>
          <td>${b.quantity}</td>
          <td style="color: var(--success); font-weight: 600;">${sym}${Math.round(convertedCost).toLocaleString()}/mo</td>
          <td style="font-size: 0.8rem; color: var(--text-muted);">${b.justification}</td>
        </tr>
      `;
    }).join("");
  }
  const bomTotalBanner = document.getElementById("bomTotalBanner");
  if (bomTotalBanner && sm) bomTotalBanner.textContent = `${sym}${Math.round(monthlyCloudConverted).toLocaleString()} / month`;

  // Tab: EU AI Act & ISO 42001 Governance Matrix
  const aiAct = brd.ai_act_classification || {};
  if (document.getElementById("aiActRiskBadge")) document.getElementById("aiActRiskBadge").textContent = aiAct.risk_tier || "Specific Transparency Risk";
  if (document.getElementById("aiActClassificationTitle")) document.getElementById("aiActClassificationTitle").textContent = `${aiAct.risk_tier || "Specific Transparency"} Tier Assessment`;
  if (document.getElementById("aiActJustification")) document.getElementById("aiActJustification").textContent = aiAct.justification || "Classification established based on system autonomy and user touchpoints.";
  if (document.getElementById("aiActReq1")) document.getElementById("aiActReq1").textContent = (aiAct.mandatory_requirements || [])[0] || "AI Content Watermarking & Notice";
  if (document.getElementById("aiActReq2")) document.getElementById("aiActReq2").textContent = (aiAct.mandatory_requirements || [])[1] || "Human-in-the-Loop Review Controls";
  if (document.getElementById("aiActReq3")) document.getElementById("aiActReq3").textContent = (aiAct.mandatory_requirements || [])[2] || "Clause Coordinate Audit Trails";

  const isoTbody = document.getElementById("isoTableBody");
  if (isoTbody) {
    isoTbody.innerHTML = (brd.iso_42001_controls || []).map(c => `
      <tr>
        <td><strong>${c.control_id}</strong></td>
        <td style="color: var(--primary); font-weight: 600;">${c.domain}</td>
        <td style="font-size: 0.82rem; color: var(--text-main);">${c.requirement}</td>
        <td><span class="badge badge-success" style="font-size: 0.72rem;">${c.status || "Implemented"}</span></td>
      </tr>
    `).join("");
  }

  // Tab 6: Assumptions Gate
  const asmTbody = document.getElementById("assumptionsTableBody");
  if (asmTbody) {
    asmTbody.innerHTML = (brd.assumptions || []).map(a => `
      <tr>
        <td><strong>${a.id}</strong></td>
        <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.72rem;">${a.category}</span></td>
        <td style="font-size: 0.82rem; color: var(--text-main);">${a.statement}</td>
        <td style="font-size: 0.8rem; color: #dc2626; font-weight: 500;">${a.impact_if_wrong}</td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${a.owner_to_confirm}</td>
        <td>
          <select class="form-control" style="padding: 4px 8px; font-size: 0.8rem;" onchange="updateAssumptionStatus('${a.id}', this.value)">
            <option value="Approve" ${a.status === "Approve" ? "selected" : ""}>✅ Approve</option>
            <option value="Correct" ${a.status === "Correct" ? "selected" : ""}>✏️ Correct</option>
            <option value="Reject" ${a.status === "Reject" ? "selected" : ""}>❌ Reject</option>
          </select>
        </td>
        <td>
          <input type="text" class="form-control" style="padding: 4px 8px; font-size: 0.8rem;" placeholder="Enter reason..." value="${a.reason || ""}" onchange="updateAssumptionReason('${a.id}', this.value)">
        </td>
      </tr>
    `).join("");
  }

  // Render Day-Wise Schedule
  renderDayWiseSchedule(brd.day_wise_schedule || [], brd);

  // Render Canonical 17 Reqs, Capability Catalog, Data Flows & HITL Gates
  renderCanonicalModel(brd);

  // Render Deterministic Calculation Ledger & Impact Analysis
  renderCalculationLedger(brd);
}

// Global Schedule Cache for Filtering
let cachedDayWiseSchedule = [];

// Render Day-Wise Master Execution Schedule
function renderDayWiseSchedule(schedule, brd) {
  cachedDayWiseSchedule = schedule || [];
  
  const totalCalDays = schedule.length;
  const workingDays = schedule.filter(d => d.is_working_day).length;
  const holidaysCount = schedule.filter(d => d.is_holiday).length;
  const weekendCount = schedule.filter(d => !d.is_working_day && !d.is_holiday).length;
  
  const startDay = schedule.length > 0 ? schedule[0].date : "Day 1";
  const endDay = schedule.length > 0 ? schedule[schedule.length - 1].date : "Day N";
  
  const calEl = document.getElementById("daywiseTotalCalDays");
  if (calEl) calEl.textContent = `${totalCalDays} Days`;
  
  const rangeEl = document.getElementById("daywiseDateRange");
  if (rangeEl) rangeEl.textContent = `${startDay} to ${endDay}`;
  
  const workEl = document.getElementById("daywiseWorkingDays");
  if (workEl) workEl.textContent = `${workingDays} Days`;
  
  const geoAns = (currentSessionData && currentSessionData.answers && currentSessionData.answers.q_geography)
    ? currentSessionData.answers.q_geography.answer : "Standard";
  const dailyHours = brd ? (brd.daily_working_hours || 8.0) : 8.0;
  
  const hrsEl = document.getElementById("daywiseWorkingHoursDay");
  if (hrsEl) hrsEl.textContent = `@ ${dailyHours.toFixed(1)} hrs/day (${geoAns})`;
  
  const holEl = document.getElementById("daywiseHolidaysCount");
  if (holEl) holEl.textContent = `${holidaysCount} Days`;
  
  const locEl = document.getElementById("daywiseLocationName");
  if (locEl) locEl.textContent = `${geoAns} Statutory Calendar`;
  
  const wkEl = document.getElementById("daywiseWeekendCount");
  if (wkEl) wkEl.textContent = `${weekendCount} Days`;
  
  filterDayWiseSchedule('all');
}

// Filter Day-Wise Schedule
function filterDayWiseSchedule(filterType) {
  // Update button active state
  ['btnFilterAllDays', 'btnFilterWorkDays', 'btnFilterHolidays'].forEach(id => {
    const btn = document.getElementById(id);
    if (btn) btn.classList.remove('active');
  });
  
  if (filterType === 'working') {
    const b = document.getElementById('btnFilterWorkDays');
    if (b) b.classList.add('active');
  } else if (filterType === 'off') {
    const b = document.getElementById('btnFilterHolidays');
    if (b) b.classList.add('active');
  } else {
    const b = document.getElementById('btnFilterAllDays');
    if (b) b.classList.add('active');
  }

  const tbody = document.getElementById("dayWiseTableBody");
  if (!tbody) return;
  
  let list = cachedDayWiseSchedule;
  if (filterType === 'working') {
    list = cachedDayWiseSchedule.filter(d => d.is_working_day);
  } else if (filterType === 'off') {
    list = cachedDayWiseSchedule.filter(d => !d.is_working_day);
  }

  tbody.innerHTML = list.map(d => {
    let statusBadge = `<span class="badge badge-success" style="font-size: 0.72rem;">Working Day</span>`;
    let rowBg = "";
    let roleText = "Lead Team";
    let hoursText = `${d.total_hours_today.toFixed(1)}h`;
    let taskText = "";

    if (d.is_holiday) {
      statusBadge = `<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #d97706; border: 1px solid #f59e0b; font-size: 0.62rem; font-weight: 600; padding: 1px 4px;">${d.holiday_name || "Statutory Holiday"}</span>`;
      rowBg = "background: #fffbeb;";
      roleText = "N/A";
      hoursText = "0h";
      taskText = `<span style="color: #d97706; font-style: italic; font-size: 0.68rem;">Statutory Holiday observed — Non-working calendar day</span>`;
      statusBadge = `<span class="badge" style="background: rgba(148, 163, 184, 0.15); color: #64748b; font-size: 0.62rem; font-weight: 600; padding: 1px 4px;">Weekend Off</span>`;
      rowBg = "background: #f8fafc;";
      roleText = "N/A";
      hoursText = "0h";
      taskText = `<span style="color: var(--text-dim); font-style: italic; font-size: 0.68rem;">Non-working weekend period</span>`;
    } else {
      const taskList = d.tasks_allocated || [];
      if (taskList.length > 0) {
        taskText = taskList.map(t => `<div style="margin-bottom: 2px; font-size: 0.68rem; line-height: 1.35;">• <strong>${t.task_name}</strong></div>`).join("");
        roleText = taskList.map(t => t.primary_role).filter(Boolean).join(", ") || "Engineering Team";
      } else {
        taskText = `<span style="font-size: 0.68rem;">Deliverable sprint execution for ${d.phase_name}</span>`;
      }
    }

    return `
      <tr style="${rowBg}">
        <td><strong style="font-size: 0.70rem;">#${d.day_number}</strong></td>
        <td>
          <div style="font-weight: 700; color: var(--text-heading); font-size: 0.72rem;">${d.date}</div>
          <div style="font-size: 0.64rem; color: var(--text-muted);">${d.day_name}</div>
        </td>
        <td>
          <span class="badge-ai" style="padding: 1px 4px; font-size: 0.62rem;">${d.phase_code}</span>
          <div style="font-size: 0.65rem; color: var(--text-muted); margin-top: 1px;">${d.phase_name}</div>
        </td>
        <td style="font-size: 0.68rem; color: var(--text-main); line-height: 1.35;">${taskText}</td>
        <td><span class="badge-ai" style="padding: 1px 4px; font-size: 0.62rem;">${roleText}</span></td>
        <td style="font-weight: 600; font-size: 0.70rem; color: ${d.is_working_day ? 'var(--primary)' : 'var(--text-dim)'};">${hoursText}</td>
        <td>${statusBadge}</td>
      </tr>
    `;
  }).join("");
}

// Approve & Lock Plan
function approveAndLockPlan() {
  const badge = document.getElementById("clientApprovalStatusBadge");
  if (badge) {
    badge.className = "badge badge-success";
    badge.innerHTML = "✅ APPROVED & LOCKED";
  }
  alert("🎉 Success! Project Plan and BRD have been approved by client. Moving to Export & Deliverables.");
  switchTab("tab-export");
}

// Review & Edit Discovery Responses Drawer
function openEditResponsesModal() {
  if (!currentSessionData) return;
  const ans = currentSessionData.answers || {};
  
  const setVal = (id, ansKey, defVal = "") => {
    const el = document.getElementById(id);
    if (!el) return;
    if (ans[ansKey] && ans[ansKey].answer) {
      el.value = ans[ansKey].answer;
    } else if (defVal) {
      el.value = defVal;
    }
  };

  // 1. Project Timeline & Scheduling Factors
  setVal("edit_q_client", "q_client", "PVR INOX — Contract Intelligence & Risk Visibility Platform");
  setVal("edit_q_duration", "q_duration", "6.0");
  setVal("edit_q_start_date", "q_start_date", "2026-09-30");
  setVal("edit_q_geography", "q_geography", "India");
  setVal("edit_q_buffer_strategy", "q_buffer_strategy", "15% Shadow / Backup Capacity (Recommended)");
  setVal("edit_q_approval_gate", "q_approval_gate", "Strict (All assumptions must be Approved)");

  // 2. Delivery Effort & Sizing Multipliers
  setVal("edit_q_tier", "q_tier", "PoC");
  setVal("edit_q_complexity", "q_complexity", "Low");
  setVal("edit_q_compliance", "q_compliance", "Internal policy only");
  setVal("edit_q_security", "q_security", "Standard");
  setVal("edit_q_usecases", "q_usecases_count", "1");
  setVal("edit_q_personas", "q_personas_count", "4");
  setVal("edit_q_integrations", "q_integrations_count", "0");
  setVal("edit_q_datasources", "q_datasources_count", "2");
  setVal("edit_q_channels", "q_channels_count", "1");
  setVal("edit_q_envs", "q_envs_count", "3");
  setVal("edit_q_languages", "q_languages_count", "1");
  setVal("edit_q_components", "q_components_count", "6");

  // 3. Technology Stack, Cloud & Infrastructure Factors
  setVal("edit_q_cloud", "q_cloud", "Microsoft Azure");
  setVal("edit_q_hadr", "q_hadr", "None (single instance)");
  setVal("edit_q_onprem_footprint", "q_onprem_footprint", "Zero on-premises components permitted (No hybrid tunnels/VPN)");
  setVal("edit_q_subscription_isolation", "q_subscription_isolation", "Dedicated newly created non-production cloud subscription");

  // 4. AI Engine, RAG Pipeline & Model Sizing Factors
  setVal("edit_q_foundation_llm", "q_foundation_llm", "Azure OpenAI reasoning/thinking tier (GPT-5 Thinking/Reasoning parameters)");
  setVal("edit_q_grounding_mode", "q_grounding_mode", "Work (Tenant data only, disabling public web retrieval) using M365 Copilot / Azure AI Agent services");
  setVal("edit_q_named_users", "q_named_users", "200");
  setVal("edit_q_concurrent_users", "q_concurrent_users", "50");
  setVal("edit_q_daily_requests", "q_daily_requests", "2000");

  // 5. Data Governance, Security & Administrative Control Factors
  setVal("edit_q_identity_auth", "q_identity_auth", "Microsoft Entra ID enforces Single Sign-On (SSO) and Role-Based Access Control (RBAC)");
  setVal("edit_q_secrets_mgmt", "q_secrets_mgmt", "Azure Key Vault using platform-managed keys (CMEK and air-gapped excluded)");
  setVal("edit_q_component_auth", "q_component_auth", "HTTPS authenticated via Azure Managed Identities (zero hardcoded credentials)");
  setVal("edit_q_retention", "q_retention", "Mandatory 12-month data retention rule for logs and telemetry");

  // 6. Functional Scope, Ingestion & Parser Contract Factors
  setVal("edit_q_legal_categories", "q_legal_categories", "Lease, Vendor, Service, Facilities, Technology, Marketing");
  setVal("edit_q_multi_pass_policy", "q_multi_pass_policy", "Pass 1 extracts explicit standard clauses | Pass 2 evaluates ambiguous terms: Agree, Agree with Management Approval, Not Agree");
  setVal("edit_q_parser_delimiters", "q_parser_delimiters", "Block headers (<<<BEGIN:NAME>>>) and pipe (|), 30,000 char limit, 0.72 synonym confidence");
  setVal("edit_q_problem", "q_problem", "Automate business contract ingestion, risk classification, and clause extraction.");

  document.getElementById("editResponsesModal").classList.add("active");
}

function closeEditResponsesModal() {
  document.getElementById("editResponsesModal").classList.remove("active");
}

async function saveEditedResponsesAndReplan() {
  const getVal = (id) => {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
  };

  const overrides = {
    // 1. Timeline & Scheduling
    q_client: getVal("edit_q_client"),
    q_duration: getVal("edit_q_duration"),
    q_start_date: getVal("edit_q_start_date"),
    q_geography: getVal("edit_q_geography"),
    q_buffer_strategy: getVal("edit_q_buffer_strategy"),
    q_approval_gate: getVal("edit_q_approval_gate"),

    // 2. Effort & Sizing Multipliers
    q_tier: getVal("edit_q_tier"),
    q_complexity: getVal("edit_q_complexity"),
    q_compliance: getVal("edit_q_compliance"),
    q_security: getVal("edit_q_security"),
    q_usecases_count: getVal("edit_q_usecases"),
    q_personas_count: getVal("edit_q_personas"),
    q_integrations_count: getVal("edit_q_integrations"),
    q_datasources_count: getVal("edit_q_datasources"),
    q_channels_count: getVal("edit_q_channels"),
    q_envs_count: getVal("edit_q_envs"),
    q_languages_count: getVal("edit_q_languages"),
    q_components_count: getVal("edit_q_components"),

    // 3. Tech Stack & Cloud
    q_cloud: getVal("edit_q_cloud"),
    q_hadr: getVal("edit_q_hadr"),
    q_onprem_footprint: getVal("edit_q_onprem_footprint"),
    q_subscription_isolation: getVal("edit_q_subscription_isolation"),

    // 4. AI Engine & Sizing
    q_foundation_llm: getVal("edit_q_foundation_llm"),
    q_grounding_mode: getVal("edit_q_grounding_mode"),
    q_named_users: getVal("edit_q_named_users"),
    q_concurrent_users: getVal("edit_q_concurrent_users"),
    q_daily_requests: getVal("edit_q_daily_requests"),

    // 5. Governance & Security
    q_identity_auth: getVal("edit_q_identity_auth"),
    q_secrets_mgmt: getVal("edit_q_secrets_mgmt"),
    q_component_auth: getVal("edit_q_component_auth"),
    q_retention: getVal("edit_q_retention"),

    // 6. Functional Scope & Parser
    q_legal_categories: getVal("edit_q_legal_categories"),
    q_multi_pass_policy: getVal("edit_q_multi_pass_policy"),
    q_parser_delimiters: getVal("edit_q_parser_delimiters"),
    q_problem: getVal("edit_q_problem")
  };

  try {
    const res = await fetch("/api/replan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        overrides: overrides
      })
    });
    if (res.ok) {
      currentSessionData = await res.json();
      renderChatMessages();
      if (currentSessionData.brd) renderBRDWorkbench(currentSessionData.brd);
      closeEditResponsesModal();
      alert("✅ Plan and Day-Wise Schedule successfully updated and recalculated!");
    }
  } catch (err) {
    console.error("Replan error:", err);
  }
}

async function updateAssumptionStatus(aid, status) {
  try {
    const res = await fetch("/api/assumptions/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        assumption_id: aid,
        status: status
      })
    });
    if (res.ok) {
      const data = await res.json();
      currentSessionData.brd = data.brd;
      renderBRDWorkbench(data.brd);
    }
  } catch (err) {
    console.error("Failed to update assumption status:", err);
  }
}

async function updateAssumptionReason(aid, reason) {
  try {
    await fetch("/api/assumptions/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        assumption_id: aid,
        status: "Correct",
        reason: reason
      })
    });
  } catch (err) {
    console.error("Failed to update assumption reason:", err);
  }
}

// Re-Plan / Re-Calculate Trigger
async function triggerReplan() {
  try {
    const res = await fetch("/api/replan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        overrides: {}
      })
    });
    if (res.ok) {
      currentSessionData = await res.json();
      renderChatMessages();
      if (currentSessionData.brd) renderBRDWorkbench(currentSessionData.brd);
    }
  } catch (err) {
    console.error("Replan error:", err);
  }
}

// Tab Switching (6 Lifecycle Stages with Cohesive Sub-Navigation)
function switchTab(tabId) {
  // Map sub-tabs to their parent lifecycle stages for sidebar button highlighting
  let parentStageTab = tabId;
  if (["tab-components", "tab-sizing", "tab-assumptions", "tab-canonical"].includes(tabId)) {
    parentStageTab = "tab-brd";
  } else if (["tab-phases", "tab-daywise", "tab-roles", "tab-estimates"].includes(tabId)) {
    parentStageTab = "tab-estimates";
    if (tabId === "tab-estimates") {
      tabId = "tab-phases"; // default view for stage 4
    }
  }

  document.querySelectorAll(".sidebar-tab-btn, .tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => p.style.display = "none");
  
  const targetPane = document.getElementById(tabId);
  if (targetPane) {
    targetPane.style.display = "block";
  }
  
  // Highlight the corresponding sidebar button for the parent lifecycle stage
  const activeBtns = Array.from(document.querySelectorAll(".sidebar-tab-btn, .tab-btn"))
    .filter(b => {
      const onclickAttr = b.getAttribute("onclick") || "";
      return onclickAttr.includes(`'${parentStageTab}'`) || onclickAttr.includes(`"${parentStageTab}"`);
    });
  activeBtns.forEach(b => b.classList.add("active"));

  // Synchronize sub-navigation pill highlights
  document.querySelectorAll(".btn-subpill").forEach(p => {
    const pOnclick = p.getAttribute("onclick") || "";
    if (pOnclick.includes(`'${tabId}'`) || pOnclick.includes(`"${tabId}"`)) {
      p.classList.add("active");
    } else {
      p.classList.remove("active");
    }
  });
}

// 0-Click RFP Auto-Discovery Ingestion
async function handleRfpAutoDiscovery(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  const autoBtn = document.querySelector('button[onclick*="rfpUploadInput"]');
  if (autoBtn) autoBtn.innerHTML = `<span>⏳</span> Ingesting RFP...`;

  try {
    const res = await fetch(`/api/upload?session_id=${currentSessionId}`, {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      currentSessionData = data;
      renderChatMessages();
      if (data.brd) {
        renderBRDWorkbench(data.brd);
      }
      alert("⚡ 0-Click RFP Ingestion & Discovery Complete! BRD, FinOps Sizing, and Day-Wise Schedule synthesized.");
    } else {
      const err = await res.json();
      alert(`Auto-discovery failed: ${err.detail || "Server error"}`);
    }
  } catch (err) {
    console.error("Auto discovery error:", err);
    alert("Upload failed. Please check network connection.");
  } finally {
    if (autoBtn) autoBtn.innerHTML = `<span>⚡</span> 0-Click Auto-Discovery`;
    event.target.value = "";
  }
}

// Global Multi-Currency Switcher
async function changeGlobalCurrency(currencyCode) {
  try {
    const res = await fetch("/api/replan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        currency_code: currencyCode,
        overrides: {}
      })
    });
    if (res.ok) {
      currentSessionData = await res.json();
      if (currentSessionData.brd) renderBRDWorkbench(currentSessionData.brd);
    }
  } catch (err) {
    console.error("Currency switch error:", err);
  }
}

// Enterprise Export Suite Endpoints
function downloadWordBRD() {
  if (!currentSessionId) return;
  window.open(`/api/export/word?session_id=${currentSessionId}`, "_blank");
}

function downloadExcelModel() {
  if (!currentSessionId) return;
  window.open(`/api/export/excel?session_id=${currentSessionId}`, "_blank");
}

function downloadJiraCSV() {
  if (!currentSessionId) return;
  window.open(`/api/export/jira?session_id=${currentSessionId}`, "_blank");
}

function downloadPPTX() {
  if (!currentSessionId) return;
  window.open(`/api/export-pptx?session_id=${currentSessionId}`, "_blank");
}

function downloadPDFBRD() {
  if (!currentSessionId) return;
  window.open(`/api/export/pdf?session_id=${currentSessionId}`, "_blank");
}

function openBRDPreview() {
  if (!currentSessionId) return;
  window.open(`/api/export-brd?session_id=${currentSessionId}`, "_blank");
}

function downloadHandoffJSON() {
  if (!currentSessionData || !currentSessionData.handoff_data) {
    alert("Handoff data is generated upon completing discovery.");
    return;
  }
  const str = JSON.stringify(currentSessionData.handoff_data, null, 2);
  const blob = new Blob([str], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `handoff_${currentSessionId.substring(0, 8)}.json`;
  a.click();
}

// Revisions Modal & Snapshot Diff
async function openRevisionsModal() {
  try {
    const res = await fetch(`/api/revisions?session_id=${currentSessionId}`);
    if (res.ok) {
      const data = await res.json();
      renderRevisionsTable(data.revisions || []);
    }
  } catch (err) {
    console.error("Failed to load revisions:", err);
  }
  document.getElementById("revisionsModal").classList.add("active");
}

function closeRevisionsModal() {
  document.getElementById("revisionsModal").classList.remove("active");
}

function renderRevisionsTable(revisions) {
  const tbody = document.getElementById("revisionsTableBody");
  if (!tbody) return;

  if (revisions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 16px;">No revisions recorded yet. Complete discovery or adjust parameters to view snapshots.</td></tr>`;
    return;
  }

  tbody.innerHTML = revisions.map(r => `
    <tr>
      <td><strong>#${r.revision_number}</strong></td>
      <td style="font-size: 0.8rem; color: var(--text-muted);">${r.timestamp}</td>
      <td style="color: var(--primary); font-weight: 600; font-size: 0.82rem;">${r.trigger_reason}</td>
      <td>${r.total_duration_weeks.toFixed(1)} wks</td>
      <td><strong>${r.total_person_days.toFixed(1)} d</strong></td>
      <td style="color: var(--success); font-weight: 600;">${r.currency_symbol || "$"}${Math.round(r.total_labour_cost).toLocaleString()}</td>
      <td style="color: var(--text-muted);">${r.currency_symbol || "$"}${Math.round(r.monthly_cloud_cost).toLocaleString()}/mo</td>
    </tr>
  `).join("");
}

// Modal Functions
function openSettingsModal() {
  document.getElementById("settingsModal").classList.add("active");
}

function closeSettingsModal() {
  document.getElementById("settingsModal").classList.remove("active");
}

function onModalProviderChange() {
  const prov = document.getElementById("modalProviderSelect").value;
  document.getElementById("googleSettingsGroup").style.display = (prov === "google") ? "block" : "none";
  document.getElementById("azureSettingsGroup").style.display = (prov === "azure") ? "block" : "none";
  document.getElementById("awsSettingsGroup").style.display = (prov === "aws") ? "block" : "none";
  const openaiGroup = document.getElementById("openaiSettingsGroup");
  if (openaiGroup) openaiGroup.style.display = (prov === "openai") ? "block" : "none";
}

async function testProviderConnection() {
  const banner = document.getElementById("testConnStatusBanner");
  if (!banner) return;
  banner.style.display = "block";
  banner.style.background = "rgba(56, 189, 248, 0.15)";
  banner.style.borderColor = "rgba(56, 189, 248, 0.4)";
  banner.style.color = "var(--primary)";
  banner.innerHTML = "⏳ <strong>Testing live cloud AI provider connection...</strong> Pinging remote endpoint...";

  const prov = document.getElementById("modalProviderSelect").value;
  const payload = {
    active_provider: prov,
    gemini_api_key: (document.getElementById("modalGeminiKey")?.value || "").trim(),
    google_model: (document.getElementById("modalGoogleModel")?.value || "").trim(),
    google_endpoint: (document.getElementById("modalGoogleEndpoint")?.value || "").trim(),
    azure_openai_endpoint: (document.getElementById("modalAzureEndpoint")?.value || "").trim(),
    azure_openai_api_key: (document.getElementById("modalAzureKey")?.value || "").trim(),
    azure_deployment: (document.getElementById("modalAzureDeployment")?.value || "").trim(),
    azure_api_version: (document.getElementById("modalAzureApiVersion")?.value || "").trim(),
    aws_region: (document.getElementById("modalAWSRegion")?.value || "").trim(),
    aws_access_key: (document.getElementById("modalAWSAccessKey")?.value || "").trim(),
    aws_secret_key: (document.getElementById("modalAWSSecretKey")?.value || "").trim(),
    aws_session_token: (document.getElementById("modalAWSSessionToken")?.value || "").trim(),
    aws_model: (document.getElementById("modalAWSModel")?.value || "").trim(),
    openai_endpoint: (document.getElementById("modalOpenAIEndpoint")?.value || "").trim(),
    openai_api_key: (document.getElementById("modalOpenAIKey")?.value || "").trim(),
    openai_model: (document.getElementById("modalOpenAIModel")?.value || "").trim()
  };

  try {
    const res = await fetch("/api/settings/test-connection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      banner.style.background = "rgba(16, 185, 129, 0.15)";
      banner.style.borderColor = "rgba(16, 185, 129, 0.4)";
      banner.style.color = "var(--success)";
      banner.innerHTML = `✅ <strong>Connected Successfully!</strong> Provider: <code>${result.provider}</code> | Model: <code>${result.model}</code> | Latency: <strong>${result.latency_ms} ms</strong><br><small style="color:#cbd5e1;">${result.message}</small>`;
    } else {
      banner.style.background = "rgba(239, 68, 68, 0.15)";
      banner.style.borderColor = "rgba(239, 68, 68, 0.4)";
      banner.style.color = "#f87171";
      banner.innerHTML = `❌ <strong>Connection Failed:</strong> ${result.message}`;
    }
  } catch (err) {
    banner.style.background = "rgba(239, 68, 68, 0.15)";
    banner.style.borderColor = "rgba(239, 68, 68, 0.4)";
    banner.style.color = "#f87171";
    banner.innerHTML = `❌ <strong>Network / Gateway Error:</strong> ${err.message}`;
  }
}

async function saveSettingsFromModal() {
  const prov = document.getElementById("modalProviderSelect").value;
  const payload = {
    active_provider: prov,
    gemini_api_key: (document.getElementById("modalGeminiKey")?.value || "").trim(),
    google_model: (document.getElementById("modalGoogleModel")?.value || "").trim(),
    google_endpoint: (document.getElementById("modalGoogleEndpoint")?.value || "").trim(),
    azure_openai_endpoint: (document.getElementById("modalAzureEndpoint")?.value || "").trim(),
    azure_openai_api_key: (document.getElementById("modalAzureKey")?.value || "").trim(),
    azure_deployment: (document.getElementById("modalAzureDeployment")?.value || "").trim(),
    azure_api_version: (document.getElementById("modalAzureApiVersion")?.value || "").trim(),
    aws_region: (document.getElementById("modalAWSRegion")?.value || "").trim(),
    aws_access_key: (document.getElementById("modalAWSAccessKey")?.value || "").trim(),
    aws_secret_key: (document.getElementById("modalAWSSecretKey")?.value || "").trim(),
    aws_session_token: (document.getElementById("modalAWSSessionToken")?.value || "").trim(),
    aws_model: (document.getElementById("modalAWSModel")?.value || "").trim(),
    openai_endpoint: (document.getElementById("modalOpenAIEndpoint")?.value || "").trim(),
    openai_api_key: (document.getElementById("modalOpenAIKey")?.value || "").trim(),
    openai_model: (document.getElementById("modalOpenAIModel")?.value || "").trim()
  };
  
  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      updateProviderBadge(data.settings.active_provider, data.settings);
      closeSettingsModal();
    }
  } catch (err) {
    console.error("Save settings failed:", err);
  }
}

// Helper: Escape HTML strings for safe inline attribute insertion
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Toast notification helper
function showToast(message, type = "info") {
  const container = document.getElementById("customToastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `custom-toast toast-${type}`;
  const icon = type === "success" ? "✅" : (type === "warning" ? "⚠️" : "ℹ️");
  toast.innerHTML = `<span style="font-size: 1.1rem;">${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    setTimeout(() => toast.remove(), 350);
  }, 3500);
}

// Canonical Model Filter States
let activeCanonicalMoSCoWFilter = "ALL";
let activeCanonicalSearchQuery = "";

// Canonical Model Rendering
function renderCanonicalModel(brd) {
  if (!brd) return;

  // Update MoSCoW distribution stats
  updateMoSCoWStats(brd.canonical_requirements || []);

  // Render 17 Canonical Requirements In-line Editable Table
  renderCanonicalTableRows();

  // Capability Catalog
  const capTbody = document.getElementById("capabilitiesTableBody");
  if (capTbody && brd.capabilities) {
    capTbody.innerHTML = brd.capabilities.map(c => {
      const isInScope = (c.scope_status === "IN_SCOPE" || c.in_scope);
      const comps = Array.isArray(c.components) ? c.components.join(", ") : (c.components || "");
      return `
        <tr style="${isInScope ? '' : 'opacity: 0.65;'}">
          <td><strong>${c.capability_id || c.code}</strong></td>
          <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.72rem;">${c.category || 'Core'}</span></td>
          <td style="font-weight: 500; color: #f1f5f9;">${c.name}</td>
          <td>
            <span class="badge ${isInScope ? 'badge-success' : 'badge-warning'}" style="font-size: 0.72rem;">
              ${c.scope_status || (isInScope ? 'IN_SCOPE' : 'OUT_OF_SCOPE')}
            </span>
          </td>
          <td style="font-size: 0.8rem; color: #94a3b8;">${c.description || ''}</td>
          <td style="font-size: 0.78rem; color: var(--primary);">${comps}</td>
        </tr>
      `;
    }).join("");
  }

  // Data Flows
  const dfTbody = document.getElementById("dataFlowsTableBody");
  if (dfTbody && brd.data_flows) {
    dfTbody.innerHTML = brd.data_flows.map(df => `
      <tr>
        <td><strong>${df.flow_id || df.id}</strong></td>
        <td style="font-weight: 500; color: #f1f5f9;">${df.name || df.flow_name}</td>
        <td><code>${df.source || df.source_system}</code></td>
        <td><code>${df.target || df.target_system}</code></td>
        <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.72rem;">${df.protocol}</span></td>
        <td style="font-size: 0.8rem; color: #cbd5e1;">${df.data_objects || df.data_payload}</td>
        <td style="font-size: 0.8rem; color: #f87171;">${df.failure_handling || df.security_control}</td>
      </tr>
    `).join("");
  }

  // HITL Gates
  if (brd.hitl_gates) {
    renderHITLGates(brd.hitl_gates);
  }
}

// MoSCoW Statistics Update
function updateMoSCoWStats(reqs) {
  let mustCount = 0, shouldCount = 0, couldCount = 0, wontCount = 0;
  reqs.forEach(r => {
    const p = (r.priority || "").toUpperCase();
    if (p === "MUST") mustCount++;
    else if (p === "SHOULD") shouldCount++;
    else if (p === "COULD") couldCount++;
    else if (p === "WONT" || p === "WON'T") wontCount++;
    else shouldCount++; // fallback
  });

  const elAll = document.getElementById("countAllReqs");
  const elMust = document.getElementById("countMustReqs");
  const elShould = document.getElementById("countShouldReqs");
  const elCould = document.getElementById("countCouldReqs");
  const elWont = document.getElementById("countWontReqs");

  if (elAll) elAll.textContent = reqs.length;
  if (elMust) elMust.textContent = mustCount;
  if (elShould) elShould.textContent = shouldCount;
  if (elCould) elCould.textContent = couldCount;
  if (elWont) elWont.textContent = wontCount;
}

// Filter Requirements by MoSCoW Priority
function filterCanonicalReqs(filter) {
  activeCanonicalMoSCoWFilter = filter;
  ["moscowChipAll", "moscowChipMust", "moscowChipShould", "moscowChipCould", "moscowChipWont"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active-filter");
  });
  const activeChipId = filter === "ALL" ? "moscowChipAll" :
                       filter === "MUST" ? "moscowChipMust" :
                       filter === "SHOULD" ? "moscowChipShould" :
                       filter === "COULD" ? "moscowChipCould" : "moscowChipWont";
  const activeChip = document.getElementById(activeChipId);
  if (activeChip) activeChip.classList.add("active-filter");
  renderCanonicalTableRows();
}

// Filter Requirements by Search Input
function onSearchCanonicalReqs(query) {
  activeCanonicalSearchQuery = (query || "").toLowerCase().trim();
  renderCanonicalTableRows();
}

// Render In-Line Editable Canonical Table Rows
function renderCanonicalTableRows() {
  const reqTbody = document.getElementById("canonicalReqsTableBody");
  if (!reqTbody || !currentSessionData || !currentSessionData.brd) return;

  const reqs = currentSessionData.brd.canonical_requirements || [];
  const query = activeCanonicalSearchQuery;
  const filter = activeCanonicalMoSCoWFilter;

  const filtered = reqs.filter(r => {
    const p = (r.priority || "SHOULD").toUpperCase();
    if (filter !== "ALL" && p !== filter) return false;
    if (query) {
      const id = (r.requirement_id || r.id || "").toLowerCase();
      const type = (r.type || r.category || "").toLowerCase();
      const stmt = (r.statement || r.description || "").toLowerCase();
      const actor = (r.actor || "").toLowerCase();
      const criteria = Array.isArray(r.acceptance_criteria) ? r.acceptance_criteria.join(" ").toLowerCase() : (r.acceptance_criteria || "").toLowerCase();
      if (!id.includes(query) && !type.includes(query) && !stmt.includes(query) && !actor.includes(query) && !criteria.includes(query)) {
        return false;
      }
    }
    return true;
  });

  if (filtered.length === 0) {
    reqTbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No requirements match current filter criteria.</td></tr>`;
    return;
  }

  const categoryOptions = [
    "FUNCTIONAL", "NON_FUNCTIONAL", "BUSINESS", "TECHNICAL", "DATA", "INTEGRATION",
    "SECURITY", "COMPLIANCE", "AI", "RESPONSIBLE_AI", "OPERATIONAL", "DEPLOYMENT",
    "REPORTING", "UX", "AVAILABILITY", "PERFORMANCE", "DR"
  ];

  const statusOptions = [
    "CLIENT_CONFIRMED", "PROJECT_OVERRIDE", "DEFAULT", "PENDING_CONFIRMATION", "RESOLVED", "REJECTED"
  ];

  reqTbody.innerHTML = filtered.map(r => {
    const reqId = r.requirement_id || r.id;
    const curPriority = (r.priority || "SHOULD").toUpperCase();
    const curType = (r.type || r.category || "FUNCTIONAL").toUpperCase();
    const curStatus = (r.status || "CLIENT_CONFIRMED").toUpperCase();
    const curActor = r.actor || "System";
    const curStatement = r.statement || r.description || r.title || "";
    const curCriteria = Array.isArray(r.acceptance_criteria) ? r.acceptance_criteria.join("\n") : (r.acceptance_criteria || "");

    const mClass = curPriority === "MUST" ? "must" :
                   curPriority === "SHOULD" ? "should" :
                   curPriority === "COULD" ? "could" : "wont";

    return `
      <tr id="row-req-${reqId}">
        <td><strong style="color: var(--primary);">${reqId}</strong></td>
        <td>
          <select class="category-select" data-req-id="${reqId}" onchange="updateCanonicalRequirement('${reqId}', 'type', this.value, this)">
            ${categoryOptions.map(cat => `<option value="${cat}" ${curType === cat ? 'selected' : ''}>${cat}</option>`).join("")}
          </select>
        </td>
        <td>
          <select class="moscow-select ${mClass}" data-req-id="${reqId}" onchange="updateCanonicalRequirement('${reqId}', 'priority', this.value, this)">
            <option value="MUST" ${curPriority === 'MUST' ? 'selected' : ''}>🔴 MUST</option>
            <option value="SHOULD" ${curPriority === 'SHOULD' ? 'selected' : ''}>🟡 SHOULD</option>
            <option value="COULD" ${curPriority === 'COULD' ? 'selected' : ''}>🔵 COULD</option>
            <option value="WONT" ${curPriority === 'WONT' ? 'selected' : ''}>⚪ WONT</option>
          </select>
        </td>
        <td>
          <select class="status-select" data-req-id="${reqId}" onchange="updateCanonicalRequirement('${reqId}', 'status', this.value, this)">
            ${statusOptions.map(st => `<option value="${st}" ${curStatus === st ? 'selected' : ''}>${st}</option>`).join("")}
          </select>
        </td>
        <td>
          <input type="text" class="inline-cell-input" value="${escapeHtml(curActor)}" data-prev="${escapeHtml(curActor)}" 
                 onblur="handleCellBlur(this, '${reqId}', 'actor')" 
                 onkeydown="if(event.key==='Enter') this.blur()">
        </td>
        <td>
          <textarea class="inline-cell-textarea" rows="2" data-prev="${escapeHtml(curStatement)}" 
                    onblur="handleCellBlur(this, '${reqId}', 'statement')"
                    onkeydown="if(event.key==='Enter' && !event.shiftKey){ event.preventDefault(); this.blur(); }">${escapeHtml(curStatement)}</textarea>
        </td>
        <td>
          <textarea class="inline-cell-textarea" rows="2" placeholder="Acceptance criteria..." data-prev="${escapeHtml(curCriteria)}" 
                    onblur="handleCellBlur(this, '${reqId}', 'acceptance_criteria')">${escapeHtml(curCriteria)}</textarea>
        </td>
        <td style="text-align: center;">
          <button class="btn-filter" style="padding: 4px 8px; font-size: 0.72rem;" title="Inspect in Calculation Ledger" onclick="jumpToLedgerForReq('${reqId}')">📑</button>
        </td>
      </tr>
    `;
  }).join("");
}

// In-Line Cell Blur Handler
function handleCellBlur(inputEl, reqId, field) {
  const newVal = inputEl.value.trim();
  const prevVal = inputEl.getAttribute("data-prev") || "";
  if (newVal !== prevVal) {
    inputEl.setAttribute("data-prev", newVal);
    updateCanonicalRequirement(reqId, field, newVal, inputEl);
  }
}

// Update Canonical Requirement with Immediate Ledger Tracking
async function updateCanonicalRequirement(reqId, field, newValue, triggerEl) {
  if (!currentSessionId) return;

  try {
    const res = await fetch("/api/canonical-requirements/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        requirement_id: reqId,
        field: field,
        new_value: newValue
      })
    });

    if (res.ok) {
      const data = await res.json();
      
      // Update local session data
      if (currentSessionData && currentSessionData.brd) {
        // Update requirement in array
        const reqs = currentSessionData.brd.canonical_requirements || [];
        const idx = reqs.findIndex(r => (r.requirement_id || r.id) === reqId);
        if (idx !== -1 && data.updated_requirement) {
          reqs[idx] = data.updated_requirement;
        }
        
        // Update calculation ledger
        if (data.calculation_ledger) {
          currentSessionData.brd.calculation_ledger = data.calculation_ledger;
          renderCalculationLedger(currentSessionData.brd, data.ledger_entry ? data.ledger_entry.calculation_id : null);
        }

        // Update MoSCoW distribution stats
        updateMoSCoWStats(reqs);
      }

      // Visual feedback on changed element
      if (triggerEl) {
        triggerEl.classList.add("cell-saved-pulse");
        setTimeout(() => triggerEl.classList.remove("cell-saved-pulse"), 1600);
        if (field === "priority") {
          triggerEl.className = `moscow-select ${newValue.toLowerCase()}`;
        }
      }

      const ledgerId = data.ledger_entry ? data.ledger_entry.calculation_id : "LEDGER";
      showToast(`Requirement <strong>${reqId}</strong> (${field}) updated & audited in ledger <strong>${ledgerId}</strong>`, "success");
    } else {
      showToast(`Failed to update ${reqId}`, "warning");
    }
  } catch (err) {
    console.error("Canonical req update failed:", err);
    showToast(`Network error updating ${reqId}`, "warning");
  }
}

// Jump to Calculation Ledger and Highlight Row
function jumpToLedgerForReq(reqId) {
  const impactTabBtn = document.querySelector(`[onclick*="tab-impact"]`);
  if (impactTabBtn) impactTabBtn.click();
  setTimeout(() => {
    const tbody = document.getElementById("calcLedgerTableBody");
    if (!tbody) return;
    const rows = tbody.querySelectorAll("tr");
    for (const r of rows) {
      if (r.textContent.includes(reqId)) {
        r.scrollIntoView({ behavior: "smooth", block: "center" });
        r.classList.add("ledger-row-new");
        setTimeout(() => r.classList.remove("ledger-row-new"), 3000);
        break;
      }
    }
  }, 200);
}

// 4 HITL Gates Rendering & Approval
function renderHITLGates(gates) {
  gates = gates || {};
  const g1 = !!(gates.gate1_requirements_approved || gates.gate_1_scope_confirmed);
  const g2 = !!(gates.gate2_solution_approved || gates.gate_2_feasibility_confirmed);
  const g3 = !!(gates.gate3_estimate_approved || gates.gate_3_commercial_confirmed);
  const g4 = !!(gates.gate4_brd_approved || gates.gate_4_executive_signoff);

  updateGateBadgeUI("gate1Badge", "btnApproveGate1", g1, gates.gate1_notes || gates.gate_1_notes);
  updateGateBadgeUI("gate2Badge", "btnApproveGate2", g2, gates.gate2_notes || gates.gate_2_notes);
  updateGateBadgeUI("gate3Badge", "btnApproveGate3", g3, gates.gate3_notes || gates.gate_3_notes);
  updateGateBadgeUI("gate4Badge", "btnApproveGate4", g4, gates.gate4_notes || gates.gate_4_notes);
}

function updateGateBadgeUI(badgeId, btnId, isPassed, notes) {
  const badge = document.getElementById(badgeId);
  const btn = document.getElementById(btnId);
  if (badge) {
    badge.textContent = isPassed ? "PASSED" : "PENDING";
    badge.style.background = isPassed ? "rgba(16, 185, 129, 0.2)" : "rgba(245, 158, 11, 0.2)";
    badge.style.color = isPassed ? "#10b981" : "#f59e0b";
  }
  if (btn) {
    if (isPassed) {
      btn.textContent = "✅ Approved";
      btn.disabled = true;
      btn.style.opacity = "0.7";
      btn.style.cursor = "default";
    } else {
      btn.textContent = "Approve Gate";
      btn.disabled = false;
      btn.style.opacity = "1";
      btn.style.cursor = "pointer";
    }
  }
}

async function approveHITLGate(gateId) {
  if (!currentSessionId) return;
  const promptText = `Enter sign-off notes for ${gateId.replace('_', ' ').toUpperCase()}:`;
  const notes = prompt(promptText, "Approved by Lead Architect per reference.txt guidelines.") || "Approved";
  try {
    const res = await fetch("/api/gates/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        gate: gateId,
        approved: true,
        notes: notes
      })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.hitl_gates) {
        if (currentSessionData.brd) {
          currentSessionData.brd.hitl_gates = data.hitl_gates;
        }
        renderHITLGates(data.hitl_gates);
        showToast(`Gate ${gateId.toUpperCase()} signed off!`, "success");
      }
    }
  } catch (err) {
    console.error("Gate approval failed:", err);
  }
}

// Calculation Ledger Rendering with Highlight Support
function renderCalculationLedger(brd, highlightCalcId = null) {
  const tbody = document.getElementById("calcLedgerTableBody");
  if (!tbody || !brd || !brd.calculation_ledger) return;

  tbody.innerHTML = brd.calculation_ledger.slice().reverse().map(item => {
    const calcId = item.calculation_id || item.step_id;
    const isNew = highlightCalcId && (calcId === highlightCalcId);
    const resSummary = typeof item.result === "object" ? JSON.stringify(item.result) : (item.result || item.output_value || "");
    const isScenarioCommit = (item.calculation_type === "SCENARIO_COMMIT");
    const isReqEdit = (item.calculation_type === "MOSCOW_PRIORITY_UPDATE" || item.calculation_type === "REQUIREMENT_MUTATION");

    let badgeClass = "badge-ai";
    if (isScenarioCommit) badgeClass = "badge-success";
    else if (isReqEdit) badgeClass = "badge-warning";

    return `
      <tr class="${isNew ? 'ledger-row-new' : ''}">
        <td><strong>${calcId}</strong></td>
        <td><span class="${badgeClass}" style="padding: 2px 6px; font-size: 0.72rem;">${item.calculation_type || item.component_or_multiplier}</span></td>
        <td style="font-family: monospace; font-size: 0.78rem; color: var(--primary);">${escapeHtml(item.formula || item.formula_applied)}</td>
        <td style="font-weight: 600; color: var(--success); font-size: 0.82rem;">${escapeHtml(resSummary)}</td>
        <td style="font-size: 0.76rem; color: #94a3b8;">${item.timestamp || ""}</td>
      </tr>
    `;
  }).join("");
}

// Global Cached Simulation State for Side-by-Side Diff & Commit
let lastSimulatedParam = null;
let lastSimulatedOldVal = null;
let lastSimulatedNewVal = null;
let lastSimulatedResult = null;

// Impact Analysis Parameter Handler
function onImpactParamChange() {
  const sel = document.getElementById("impactParamSelect");
  const oldValInput = document.getElementById("impactOldVal");
  const newValInput = document.getElementById("impactNewVal");
  if (!sel || !oldValInput || !newValInput) return;

  const brd = currentSessionData ? currentSessionData.brd : null;
  const param = sel.value;

  if (param === "users") {
    const curUsers = (brd && brd.sizing_metrics) ? brd.sizing_metrics.target_users : 200;
    oldValInput.value = curUsers;
    newValInput.value = curUsers * 2.5;
  } else if (param === "tier") {
    const curTier = brd ? brd.delivery_tier : "PoC";
    oldValInput.value = curTier;
    newValInput.value = (curTier === "PoC" || curTier === "Starter") ? "MVP" : "Full Scale Enterprise";
  } else if (param === "duration") {
    const curWeeks = brd ? brd.total_duration_weeks : 6.0;
    oldValInput.value = `${curWeeks.toFixed(1)} wks`;
    newValInput.value = `${(curWeeks + 2.0).toFixed(1)} wks`;
  } else if (param === "rate") {
    const curRate = (brd && brd.blended_hourly_rate) ? brd.blended_hourly_rate : 30.0;
    oldValInput.value = `$${curRate}/hr`;
    newValInput.value = `$${curRate + 10}/hr`;
  }
}

// Interactive Impact Analysis Calculation
async function runInteractiveImpactAnalysis() {
  if (!currentSessionId) return;

  const sel = document.getElementById("impactParamSelect");
  const oldValInput = document.getElementById("impactOldVal");
  const newValInput = document.getElementById("impactNewVal");
  if (!sel || !oldValInput || !newValInput) return;

  const param = sel.value;
  const oldVal = oldValInput.value;
  const newVal = newValInput.value;

  try {
    const res = await fetch("/api/impact-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        parameter_changed: param,
        old_value: oldVal,
        new_value: newVal
      })
    });
    if (res.ok) {
      const result = await res.json();
      lastSimulatedParam = param;
      lastSimulatedOldVal = oldVal;
      lastSimulatedNewVal = newVal;
      lastSimulatedResult = result;
      renderImpactAnalysisResults(result);
    }
  } catch (err) {
    console.error("Impact analysis failed:", err);
    showToast("Impact analysis calculation error", "warning");
  }
}

// Render Side-by-Side Scenario Diff Results
function renderImpactAnalysisResults(result) {
  if (!result) return;
  const container = document.getElementById("impactResultsContainer");
  if (container) container.style.display = "block";

  const sym = (currentSessionData && currentSessionData.brd) ? (currentSessionData.brd.currency_symbol || "$") : "$";

  // Subtitle
  const subEl = document.getElementById("diffSubtitle");
  if (subEl) {
    subEl.textContent = `Parameter: ${result.parameter_changed.toUpperCase()} (${result.old_value} ➔ ${result.new_value}) | Evaluated across 18 WBS Phases`;
  }

  // Left Card: Current Baseline
  const cardBaseParam = document.getElementById("cardBaseParam");
  if (cardBaseParam) cardBaseParam.textContent = String(result.old_value);
  const cardBaseDuration = document.getElementById("cardBaseDuration");
  if (cardBaseDuration) cardBaseDuration.textContent = `${result.base_duration_weeks.toFixed(1)} wks`;
  const cardBaseDays = document.getElementById("cardBaseDays");
  if (cardBaseDays) cardBaseDays.textContent = `${result.base_person_days.toFixed(1)} d`;
  const cardBaseCost = document.getElementById("cardBaseCost");
  if (cardBaseCost) cardBaseCost.textContent = `${sym}${Math.round(result.base_cost_usd).toLocaleString()}`;
  const cardBaseFTE = document.getElementById("cardBaseFTE");
  if (cardBaseFTE) cardBaseFTE.textContent = `${result.base_fte.toFixed(2)} FTE`;
  const cardBaseCloud = document.getElementById("cardBaseCloud");
  if (cardBaseCloud) cardBaseCloud.textContent = `${sym}${Math.round(result.base_monthly_cloud_usd).toLocaleString()}/mo`;

  // Right Card: Simulated Target
  const cardSimParam = document.getElementById("cardSimParam");
  if (cardSimParam) cardSimParam.textContent = String(result.new_value);
  const cardSimDuration = document.getElementById("cardSimDuration");
  if (cardSimDuration) cardSimDuration.textContent = `${result.sim_duration_weeks.toFixed(1)} wks`;
  const cardSimDays = document.getElementById("cardSimDays");
  if (cardSimDays) cardSimDays.textContent = `${result.sim_person_days.toFixed(1)} d`;
  const cardSimCost = document.getElementById("cardSimCost");
  if (cardSimCost) cardSimCost.textContent = `${sym}${Math.round(result.sim_cost_usd).toLocaleString()}`;
  const cardSimFTE = document.getElementById("cardSimFTE");
  if (cardSimFTE) cardSimFTE.textContent = `${result.sim_fte.toFixed(2)} FTE`;
  const cardSimCloud = document.getElementById("cardSimCloud");
  if (cardSimCloud) cardSimCloud.textContent = `${sym}${Math.round(result.sim_monthly_cloud_usd).toLocaleString()}/mo`;

  // Comparative Diff Table Body
  const diffTbody = document.getElementById("scenarioDiffTableBody");
  if (diffTbody) {
    const deltaDaysSign = result.delta_days >= 0 ? "+" : "";
    const deltaDaysPct = result.base_person_days > 0 ? ((result.delta_days / result.base_person_days) * 100).toFixed(1) : "0.0";
    const deltaDaysClass = result.delta_days > 0 ? "positive-effort" : (result.delta_days < 0 ? "negative-effort" : "neutral");

    const deltaCostSign = result.delta_cost_usd >= 0 ? "+" : "";
    const deltaCostPct = result.base_cost_usd > 0 ? ((result.delta_cost_usd / result.base_cost_usd) * 100).toFixed(1) : "0.0";
    const deltaCostClass = result.delta_cost_usd > 0 ? "positive-effort" : (result.delta_cost_usd < 0 ? "negative-effort" : "neutral");

    const deltaDuration = result.sim_duration_weeks - result.base_duration_weeks;
    const deltaDurationSign = deltaDuration >= 0 ? "+" : "";
    const deltaDurationClass = deltaDuration > 0 ? "positive-effort" : (deltaDuration < 0 ? "negative-effort" : "neutral");

    const deltaFte = result.sim_fte - result.base_fte;
    const deltaFteSign = deltaFte >= 0 ? "+" : "";
    const deltaFteClass = deltaFte > 0 ? "positive-effort" : (deltaFte < 0 ? "negative-effort" : "neutral");

    const deltaCloud = result.sim_monthly_cloud_usd - result.base_monthly_cloud_usd;
    const deltaCloudSign = deltaCloud >= 0 ? "+" : "";
    const deltaCloudClass = deltaCloud > 0 ? "positive-effort" : (deltaCloud < 0 ? "negative-effort" : "neutral");

    diffTbody.innerHTML = `
      <tr>
        <td><strong>Tested Parameter</strong></td>
        <td><code>${escapeHtml(String(result.old_value))}</code></td>
        <td><code>${escapeHtml(String(result.new_value))}</code></td>
        <td><span class="diff-pill neutral">Active Simulation</span></td>
        <td style="color: #64748b; font-size: 0.8rem;">Independent driver variable adjusted in impact engine</td>
      </tr>
      <tr>
        <td><strong>Project Duration</strong></td>
        <td>${result.base_duration_weeks.toFixed(1)} weeks</td>
        <td>${result.sim_duration_weeks.toFixed(1)} weeks</td>
        <td><span class="diff-pill ${deltaDurationClass}">${deltaDurationSign}${deltaDuration.toFixed(1)} wks</span></td>
        <td style="color: #64748b; font-size: 0.8rem;">${deltaDuration !== 0 ? 'Calendar schedule duration shifted' : 'Fixed timeline duration maintained'}</td>
      </tr>
      <tr>
        <td><strong>Total Engineering Effort</strong></td>
        <td>${result.base_person_days.toFixed(1)} days</td>
        <td>${result.sim_person_days.toFixed(1)} days</td>
        <td><span class="diff-pill ${deltaDaysClass}">${deltaDaysSign}${result.delta_days.toFixed(1)} d (${deltaDaysSign}${deltaDaysPct}%)</span></td>
        <td style="color: #64748b; font-size: 0.8rem;">Task loading recalculated deterministically across 18 WBS phases</td>
      </tr>
      <tr>
        <td><strong>Labour Budget Cost</strong></td>
        <td>${sym}${Math.round(result.base_cost_usd).toLocaleString()}</td>
        <td>${sym}${Math.round(result.sim_cost_usd).toLocaleString()}</td>
        <td><span class="diff-pill ${deltaCostClass}">${deltaCostSign}${sym}${Math.round(result.delta_cost_usd).toLocaleString()} (${deltaCostSign}${deltaCostPct}%)</span></td>
        <td style="color: #64748b; font-size: 0.8rem;">12-role blended engineering rate applied to incremental person-hours</td>
      </tr>
      <tr>
        <td><strong>Staffing Team Loading</strong></td>
        <td>${result.base_fte.toFixed(2)} FTE</td>
        <td>${result.sim_fte.toFixed(2)} FTE</td>
        <td><span class="diff-pill ${deltaFteClass}">${deltaFteSign}${deltaFte.toFixed(2)} FTE</span></td>
        <td style="color: #64748b; font-size: 0.8rem;">Average weekly team concurrency required to achieve schedule target</td>
      </tr>
      <tr>
        <td><strong>Monthly Cloud Infrastructure</strong></td>
        <td>${sym}${Math.round(result.base_monthly_cloud_usd).toLocaleString()}/mo</td>
        <td>${sym}${Math.round(result.sim_monthly_cloud_usd).toLocaleString()}/mo</td>
        <td><span class="diff-pill ${deltaCloudClass}">${deltaCloudSign}${sym}${Math.round(deltaCloud).toLocaleString()}/mo</span></td>
        <td style="color: #64748b; font-size: 0.8rem;">App Services, Vector Search, and compute tier sizing scale</td>
      </tr>
    `;
  }

  // Narrative explanation
  const narrEl = document.getElementById("impactNarrative");
  if (narrEl) narrEl.textContent = result.narrative_explanation || "";

  // Affected / Protected Scope breakdown
  const detailsEl = document.getElementById("impactAffectedDetails");
  if (detailsEl) {
    let affectedHtml = "";
    if (result.affected_dimensions && Object.keys(result.affected_dimensions).length > 0) {
      affectedHtml += "<strong>Impacted Architectural Dimensions:</strong><ul style='margin: 4px 0 8px 18px;'>";
      for (const [dim, val] of Object.entries(result.affected_dimensions)) {
        affectedHtml += `<li><strong>${escapeHtml(dim)}</strong>: ${typeof val === 'object' ? escapeHtml(JSON.stringify(val)) : escapeHtml(val)}</li>`;
      }
      affectedHtml += "</ul>";
    }
    if (result.unaffected_dimensions && result.unaffected_dimensions.length > 0) {
      affectedHtml += `<div style="margin-top: 8px;"><strong>Protected Scope (Unaffected):</strong> <code style="color: #10b981;">${escapeHtml(result.unaffected_dimensions.join(', '))}</code></div>`;
    }
    detailsEl.innerHTML = affectedHtml;
  }

  // Reset commit buttons state
  document.querySelectorAll(".btn-commit-baseline").forEach(btn => {
    btn.disabled = false;
    btn.innerHTML = `<span>⚡</span> Commit Simulation to Baseline`;
  });
}

// Single Action: Commit Simulation Directly to Baseline
async function commitSimulationToBaseline() {
  if (!currentSessionId) return;

  if (!lastSimulatedParam || lastSimulatedNewVal === null) {
    showToast("Please calculate an impact simulation first before committing.", "warning");
    return;
  }

  const commitBtns = document.querySelectorAll(".btn-commit-baseline");
  commitBtns.forEach(btn => {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳</span> Committing Simulation to Baseline...`;
  });

  try {
    const res = await fetch("/api/impact-analysis/commit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        parameter_changed: lastSimulatedParam,
        new_value: lastSimulatedNewVal
      })
    });

    if (res.ok) {
      const data = await res.json();
      currentSessionData.brd = data.brd;

      // Re-render complete workbench (all 18 phases, metrics, financials, canonical reqs)
      renderBRDWorkbench(currentSessionData.brd);

      // Synchronize input fields
      const oldValInput = document.getElementById("impactOldVal");
      const newValInput = document.getElementById("impactNewVal");
      if (oldValInput) oldValInput.value = lastSimulatedNewVal;
      if (newValInput && lastSimulatedParam === "users") {
        newValInput.value = Math.round(Number(lastSimulatedNewVal) * 2.5);
      }

      // Update diff subtitle to show active baseline committed
      const subEl = document.getElementById("diffSubtitle");
      if (subEl) {
        subEl.textContent = `✅ Successfully Committed to Baseline: ${lastSimulatedParam.toUpperCase()} = ${lastSimulatedNewVal} (Active Baseline Synchronized)`;
      }

      // Update commit buttons
      commitBtns.forEach(btn => {
        btn.disabled = false;
        btn.innerHTML = `<span>✅</span> Simulation Committed to Baseline`;
        btn.style.background = "linear-gradient(135deg, #059669 0%, #047857 100%)";
      });

      // Find the SCENARIO_COMMIT ledger entry
      const ledgerEntries = data.calculation_ledger || [];
      const commitEntry = ledgerEntries.slice().reverse().find(e => e.calculation_type === "SCENARIO_COMMIT");
      const commitLedgerId = commitEntry ? commitEntry.calculation_id : "CALC-SCENARIO";

      showToast(`⚡ Simulation committed to baseline! All 18 phases updated & logged to Calculation Ledger (<strong>${commitLedgerId}</strong>).`, "success");

      // Re-render Calculation Ledger and scroll to the new entry
      renderCalculationLedger(currentSessionData.brd, commitLedgerId);
    } else {
      commitBtns.forEach(btn => {
        btn.disabled = false;
        btn.innerHTML = `<span>⚡</span> Commit Simulation to Baseline`;
      });
      showToast("Error committing simulation to baseline.", "warning");
    }
  } catch (err) {
    console.error("Failed to commit simulation:", err);
    commitBtns.forEach(btn => {
      btn.disabled = false;
      btn.innerHTML = `<span>⚡</span> Commit Simulation to Baseline`;
    });
    showToast("Network error while committing simulation.", "warning");
  }
}

// Admin Console Functions
let cachedAdminCalendars = {};
let isAdminEditMode = false;
let isAdminAuthenticated = false;

function requestAdminEditMode() {
  if (isAdminAuthenticated) {
    setAdminRoleMode(true);
  } else {
    openAdminPinModal();
  }
}

function openAdminPinModal() {
  const modal = document.getElementById("adminPinModal");
  const input = document.getElementById("adminPinInput");
  const err = document.getElementById("adminPinError");
  if (err) err.style.display = "none";
  if (input) input.value = "";
  if (modal) modal.classList.add("active");
  setTimeout(() => {
    if (input) input.focus();
  }, 100);
}

function closeAdminPinModal() {
  const modal = document.getElementById("adminPinModal");
  if (modal) modal.classList.remove("active");
  if (!isAdminEditMode) {
    setAdminRoleMode(false);
  }
}

async function submitAdminPin() {
  const input = document.getElementById("adminPinInput");
  const err = document.getElementById("adminPinError");
  const pin = input ? input.value.trim() : "";

  if (!pin) {
    if (err) {
      err.textContent = "❌ Please enter the 6-digit Admin PIN.";
      err.style.display = "block";
    }
    return;
  }

  // Check pin (supports "123456" directly and backend verification)
  if (pin === "123456") {
    isAdminAuthenticated = true;
    closeAdminPinModal();
    setAdminRoleMode(true);
    return;
  }

  try {
    const res = await fetch("/api/admin/verify-pin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin: pin })
    });
    if (res.ok) {
      isAdminAuthenticated = true;
      closeAdminPinModal();
      setAdminRoleMode(true);
    } else {
      if (err) {
        err.textContent = "❌ Invalid PIN. Please enter the correct Admin PIN.";
        err.style.display = "block";
      }
      if (input) input.select();
    }
  } catch (e) {
    if (err) {
      err.textContent = "❌ Invalid PIN. Please enter the correct Admin PIN.";
      err.style.display = "block";
    }
  }
}

function setAdminRoleMode(isAdmin) {
  isAdminEditMode = isAdmin;
  const btnViewer = document.getElementById("btnRoleViewer");
  const btnAdmin = document.getElementById("btnRoleAdmin");
  const banner = document.getElementById("adminModeBanner");
  const saveBtn = document.getElementById("btnSaveAdminDefaults");

  if (btnViewer) btnViewer.classList.toggle("active", !isAdmin);
  if (btnAdmin) btnAdmin.classList.toggle("active", isAdmin);

  if (banner) {
    if (isAdmin) {
      banner.style.background = "rgba(16, 185, 129, 0.15)";
      banner.style.borderColor = "rgba(16, 185, 129, 0.4)";
      banner.style.color = "var(--success)";
      banner.innerHTML = "🛡️ <strong>Admin Edit Mode (Authenticated):</strong> You have full administrative privileges to edit location working hours, add statutory holidays, upload holiday sheets, and adjust global rates.";
    } else {
      banner.style.background = "rgba(56, 189, 248, 0.1)";
      banner.style.borderColor = "rgba(56, 189, 248, 0.3)";
      banner.style.color = "var(--primary)";
      banner.innerHTML = "🔒 <strong>View-Only Mode:</strong> Regular users can inspect system default settings, location working hours, and holiday schedules. Switch to Admin Edit Mode to modify.";
    }
  }

  document.querySelectorAll(".admin-field").forEach(el => {
    el.disabled = !isAdmin;
  });
  if (saveBtn) saveBtn.disabled = !isAdmin;
}

async function openAdminModal() {
  document.getElementById("adminModal").classList.add("active");
  setAdminRoleMode(false); // Default to viewer
  await loadAdminDefaults();
  await loadAdminCalendars();
}

function closeAdminModal() {
  document.getElementById("adminModal").classList.remove("active");
}

async function loadAdminDefaults() {
  try {
    const res = await fetch("/api/admin/defaults");
    if (res.ok) {
      const data = await res.json();
      if (document.getElementById("adminHourlyRate")) document.getElementById("adminHourlyRate").value = data.blended_hourly_rate || 30.0;
      if (document.getElementById("adminHoursPerDay")) document.getElementById("adminHoursPerDay").value = data.hours_per_day || 8.0;
      if (document.getElementById("adminDaysPerWeek")) document.getElementById("adminDaysPerWeek").value = data.working_days_per_week || 5;
    }
  } catch (err) {
    console.error("Failed to load admin defaults:", err);
  }
}

async function loadAdminCalendars() {
  try {
    const res = await fetch("/api/admin/calendars");
    if (res.ok) {
      cachedAdminCalendars = await res.json();
      renderAdminCalendarsTable();
      renderAdminHolidaysList();
    }
  } catch (err) {
    console.error("Failed to load admin calendars:", err);
  }
}

function renderAdminCalendarsTable() {
  const tbody = document.getElementById("adminCalendarsTableBody");
  if (!tbody) return;

  tbody.innerHTML = Object.entries(cachedAdminCalendars).map(([code, cal]) => {
    const hours = cal.daily_working_hours || 8.0;
    const rateUsd = cal.hourly_rate || 30.0;
    const rateLocal = cal.hourly_rate_local || rateUsd;
    const sym = cal.currency_symbol || "$";
    const curr = cal.currency_code || "USD";
    const holidays = cal.holidays || [];
    const hCount = holidays.length;
    
    // Exact dates preview
    const topHolidays = holidays.slice(0, 2).map(h => `
      <span class="badge-ai" style="padding: 1px 5px; font-size: 0.66rem; margin: 1px; white-space: nowrap;" title="${h.date}: ${h.name}">
        📅 ${h.date.substring(5)}: ${h.name.substring(0, 10)}
      </span>
    `).join("");
    const moreLink = hCount > 2 
      ? `<button class="btn-header" style="padding: 1px 5px; font-size: 0.66rem; border: none; background: transparent; color: var(--primary); cursor: pointer;" onclick="selectAdminCountry('${code}')">+${hCount - 2} dates...</button>` 
      : (hCount === 0 ? `<span style="font-size: 0.7rem; color: var(--text-dim);">No holidays</span>` : '');

    return `
      <tr>
        <td><strong>${code}</strong></td>
        <td>
          <div style="font-weight: 600; font-size: 0.84rem;">${cal.country_name}</div>
          <div style="font-size: 0.72rem; color: var(--text-dim);">${curr} (${sym.trim()})</div>
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 4px;">
            <span style="font-size: 0.82rem; color: var(--primary); font-weight: 700;">${sym}</span>
            <input type="number" step="1.0" id="rate_local_${code}" class="form-control admin-field" style="width: 82px; padding: 4px 6px; font-size: 0.82rem; font-weight: 600;" value="${rateLocal}" ${isAdminEditMode ? '' : 'disabled'} onchange="saveLocationCalendar('${code}')">
            <span style="font-size: 0.72rem; color: var(--text-dim);">${curr}</span>
          </div>
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 4px;">
            <span style="font-size: 0.8rem; color: var(--text-muted);">$</span>
            <input type="number" step="1.0" id="rate_${code}" class="form-control admin-field" style="width: 70px; padding: 4px 6px; font-size: 0.82rem;" value="${rateUsd}" ${isAdminEditMode ? '' : 'disabled'} onchange="saveLocationCalendar('${code}')">
            <span style="font-size: 0.72rem; color: var(--text-dim);">/hr</span>
          </div>
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 4px;">
            <input type="number" step="0.5" id="hours_${code}" class="form-control admin-field" style="width: 65px; padding: 4px 6px; font-size: 0.82rem;" value="${hours}" ${isAdminEditMode ? '' : 'disabled'} onchange="saveLocationCalendar('${code}')">
            <span style="font-size: 0.72rem; color: var(--text-dim);">hrs</span>
          </div>
        </td>
        <td style="font-size: 0.82rem;">${cal.working_days_per_week || 5} d/wk</td>
        <td>
          <div style="display: flex; flex-direction: column; gap: 2px; max-width: 170px;">
            <div style="display: flex; flex-wrap: wrap; gap: 2px;">${topHolidays}</div>
            ${moreLink}
          </div>
        </td>
        <td>
          <button class="btn-header admin-field" style="padding: 3px 8px; font-size: 0.75rem;" ${isAdminEditMode ? '' : 'disabled'} onclick="saveLocationCalendar('${code}')">Save</button>
        </td>
      </tr>
    `;
  }).join("");
}

function selectAdminCountry(countryCode) {
  const sel = document.getElementById("adminSelectedCountry");
  if (sel) {
    sel.value = countryCode;
    renderAdminHolidaysList();
  }
}

async function saveLocationCalendar(countryCode) {
  const cal = cachedAdminCalendars[countryCode];
  if (!cal) return;

  const hoursEl = document.getElementById(`hours_${countryCode}`);
  const rateUsdEl = document.getElementById(`rate_${countryCode}`);
  const rateLocalEl = document.getElementById(`rate_local_${countryCode}`);
  
  const hours = hoursEl ? parseFloat(hoursEl.value) || 8.0 : (cal.daily_working_hours || 8.0);
  const rateUsd = rateUsdEl ? parseFloat(rateUsdEl.value) || 30.0 : (cal.hourly_rate || 30.0);
  const rateLocal = rateLocalEl ? parseFloat(rateLocalEl.value) || rateUsd : (cal.hourly_rate_local || rateUsd);

  try {
    const res = await fetch("/api/admin/calendars", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country_code: countryCode,
        country_name: cal.country_name,
        currency_code: cal.currency_code || "USD",
        currency_symbol: cal.currency_symbol || "$",
        working_days_per_week: cal.working_days_per_week || 5,
        daily_working_hours: hours,
        hourly_rate: rateUsd,
        hourly_rate_local: rateLocal,
        annual_holiday_allowance: cal.annual_holiday_allowance || 12
      })
    });
    if (res.ok) {
      cal.daily_working_hours = hours;
      cal.hourly_rate = rateUsd;
      cal.hourly_rate_local = rateLocal;
      await triggerReplan();
    }
  } catch (err) {
    console.error("Failed to save location calendar:", err);
  }
}

function renderAdminHolidaysList() {
  const sel = document.getElementById("adminSelectedCountry");
  const tbody = document.getElementById("adminHolidaysTableBody");
  if (!sel || !tbody) return;

  const code = sel.value;
  const cal = cachedAdminCalendars[code] || {};
  const holidays = cal.holidays || [];

  if (holidays.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No holidays configured for ${code}.</td></tr>`;
    return;
  }

  tbody.innerHTML = holidays.map((h, idx) => `
    <tr>
      <td>${h.date}</td>
      <td><strong>${h.name}</strong></td>
      <td><span class="badge-ai" style="padding: 1px 5px; font-size: 0.7rem;">${h.type || "Statutory"}</span></td>
      <td>
        <button class="btn-header admin-field" style="padding: 2px 6px; font-size: 0.7rem; color: #f87171;" ${isAdminEditMode ? '' : 'disabled'} onclick="deleteAdminHoliday('${code}', ${idx})">🗑️</button>
      </td>
    </tr>
  `).join("");
}

async function addAdminHolidayFromModal() {
  const sel = document.getElementById("adminSelectedCountry");
  const dInput = document.getElementById("newHolidayDate");
  const nInput = document.getElementById("newHolidayName");
  if (!sel || !dInput || !nInput) return;

  const code = sel.value;
  const dateVal = dInput.value.trim();
  const nameVal = nInput.value.trim();
  if (!dateVal || !nameVal) {
    alert("Please provide both Date and Holiday Name.");
    return;
  }

  try {
    const res = await fetch(`/api/admin/calendars/${code}/holidays`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        date: dateVal,
        name: nameVal,
        type: "Statutory"
      })
    });
    if (res.ok) {
      dInput.value = "";
      nInput.value = "";
      await loadAdminCalendars();
      await triggerReplan();
    }
  } catch (err) {
    console.error("Failed to add holiday:", err);
  }
}

async function deleteAdminHoliday(countryCode, idx) {
  try {
    const res = await fetch(`/api/admin/calendars/${countryCode}/holidays/${idx}`, {
      method: "DELETE"
    });
    if (res.ok) {
      await loadAdminCalendars();
      await triggerReplan();
    }
  } catch (err) {
    console.error("Failed to delete holiday:", err);
  }
}

async function uploadAdminHolidaySheet() {
  const sel = document.getElementById("adminSelectedCountry");
  const fileInput = document.getElementById("adminHolidayFileInput");
  if (!sel || !fileInput || !fileInput.files[0]) {
    alert("Please select a file to upload.");
    return;
  }

  const code = sel.value;
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("country_code", code);
  formData.append("country_name", cachedAdminCalendars[code] ? cachedAdminCalendars[code].country_name : code);
  formData.append("file", file);

  try {
    const res = await fetch("/api/admin/calendars/upload", {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      fileInput.value = "";
      await loadAdminCalendars();
      await triggerReplan();
      alert(`Holidays uploaded successfully for ${code}!`);
    }
  } catch (err) {
    console.error("Failed to upload holidays sheet:", err);
  }
}

async function saveAdminDefaultsFromModal() {
  const rate = parseFloat(document.getElementById("adminHourlyRate").value) || 30.0;
  const hours = parseFloat(document.getElementById("adminHoursPerDay").value) || 8.0;
  const days = parseInt(document.getElementById("adminDaysPerWeek").value) || 5;
  
  try {
    await fetch("/api/admin/defaults", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        blended_hourly_rate: rate,
        hours_per_day: hours,
        working_days_per_week: days
      })
    });
    closeAdminModal();
    await triggerReplan();
    alert("Admin defaults saved successfully!");
  } catch (err) {
    console.error("Failed to save admin defaults:", err);
  }
}

// Project Workspaces & Folderwise BRD History
let cachedProjectList = [];

function getDeletedWorkspaceIds() {
  try {
    return JSON.parse(localStorage.getItem("brd_deleted_workspaces") || "[]");
  } catch (e) {
    return [];
  }
}

function saveDeletedWorkspaceId(id) {
  const list = getDeletedWorkspaceIds();
  if (!list.includes(id)) {
    list.push(id);
    localStorage.setItem("brd_deleted_workspaces", JSON.stringify(list));
  }
}

function initWorkspacesCollapseState() {
  const isCollapsed = localStorage.getItem("brd_workspaces_collapsed") === "true";
  const collapsibleArea = document.getElementById("workspacesCollapsibleArea");
  const chev = document.getElementById("workspacesCollapseIcon");
  const btn = document.getElementById("btnToggleWorkspaces");

  if (collapsibleArea) {
    if (isCollapsed) {
      collapsibleArea.classList.add("collapsed");
      if (chev) chev.style.transform = "rotate(-90deg)";
      if (btn) btn.textContent = "Show";
    } else {
      collapsibleArea.classList.remove("collapsed");
      if (chev) chev.style.transform = "rotate(0deg)";
      if (btn) btn.textContent = "Hide";
    }
  }
}

function toggleAllWorkspaces(forcedState) {
  const collapsibleArea = document.getElementById("workspacesCollapsibleArea");
  const chev = document.getElementById("workspacesCollapseIcon");
  const btn = document.getElementById("btnToggleWorkspaces");
  if (!collapsibleArea) return;

  let willCollapse;
  if (typeof forcedState === "boolean") {
    willCollapse = forcedState;
  } else {
    willCollapse = !collapsibleArea.classList.contains("collapsed");
  }

  if (willCollapse) {
    collapsibleArea.classList.add("collapsed");
    if (chev) chev.style.transform = "rotate(-90deg)";
    if (btn) btn.textContent = "Show";
    localStorage.setItem("brd_workspaces_collapsed", "true");
  } else {
    collapsibleArea.classList.remove("collapsed");
    if (chev) chev.style.transform = "rotate(0deg)";
    if (btn) btn.textContent = "Hide";
    localStorage.setItem("brd_workspaces_collapsed", "false");
  }
}

async function loadProjectHistory() {
  try {
    initWorkspacesCollapseState();
    const res = await fetch("/api/projects/history");
    if (res.ok) {
      const data = await res.json();
      const rawProjects = data.projects || [];
      const deletedIds = getDeletedWorkspaceIds();
      cachedProjectList = rawProjects.filter(p => !deletedIds.includes(p.id));
      renderProjectFolders(cachedProjectList);
    }
  } catch (err) {
    console.error("Failed to load project history:", err);
  }
}

function renderProjectFolders(projects) {
  const container = document.getElementById("projectFoldersList");
  const countBadge = document.getElementById("projectCountBadge");
  if (!container) return;

  if (countBadge) countBadge.textContent = `${projects.length} Workspaces`;

  const deletedIds = getDeletedWorkspaceIds();
  const hasDeleted = deletedIds.length > 0;

  if (projects.length === 0) {
    container.innerHTML = `
      <div style="font-size: 0.76rem; color: var(--text-dim); text-align: center; padding: 14px 10px; background: rgba(15, 23, 42, 0.4); border-radius: var(--radius-sm); border: 1px dashed var(--bg-sidebar-border);">
        <div style="margin-bottom: 6px; color: #cbd5e1;">All workspaces hidden or removed</div>
        ${hasDeleted ? `<button class="folder-restore-btn" onclick="restoreDefaultWorkspaces()"><span>🔄</span> Restore Default Workspaces</button>` : ''}
      </div>
    `;
    return;
  }

  container.innerHTML = projects.map((p, idx) => {
    const isActive = (p.id === currentSessionId || (idx === 0 && !currentSessionId));
    const safeTitle = (p.name || '').replace(/'/g, "\\'");
    return `
      <div class="project-folder-card ${isActive ? 'active' : ''}" id="folder_card_${p.id}">
        <div class="project-folder-header" onclick="toggleProjectFolder('${p.id}')">
          <div class="project-folder-info">
            <span style="font-size: 0.95rem; flex-shrink: 0;">📁</span>
            <div style="min-width: 0;">
              <div class="folder-title-text" title="${p.name}">${p.name}</div>
              <div class="folder-meta">
                <span class="badge-ai" style="padding: 0 4px; font-size: 0.65rem; display: inline-block;">${p.tier}</span>
                <span>• ${p.updated_at}</span>
              </div>
            </div>
          </div>
          <div class="project-folder-actions">
            <button class="btn-folder-delete" onclick="event.stopPropagation(); removeProjectWorkspace('${p.id}', '${safeTitle}')" title="Remove workspace from sidebar">
              🗑️
            </button>
            <span style="font-size: 0.75rem; color: var(--text-dim); transition: transform 0.2s;" id="chevron_${p.id}">▼</span>
          </div>
        </div>

        <div class="project-subfiles" id="subfiles_${p.id}" style="${isActive ? 'display: flex;' : 'display: none;'}">
          <div class="project-subfile-link" onclick="loadProjectWorkspace('${p.id}')" title="Load active discovery interview & chat">
            <span>💬 Discovery Chat & Q&A</span>
            <span class="file-type-tag" style="background: rgba(56, 189, 248, 0.15); color: var(--primary);">${p.answers_count || 22} Ans</span>
          </div>
          <a class="project-subfile-link" href="${p.files.word_docx}" target="_blank" title="Download Formal Word BRD">
            <span>📄 Executive BRD Document</span>
            <span class="file-type-tag" style="background: rgba(43, 87, 154, 0.3); color: #93c5fd;">.docx</span>
          </a>
          <a class="project-subfile-link" href="${p.files.pptx_deck}" target="_blank" title="Download 16:9 PowerPoint Presentation Deck">
            <span>📊 PowerPoint Presentation</span>
            <span class="file-type-tag" style="background: rgba(210, 71, 38, 0.3); color: #fca5a5;">.pptx</span>
          </a>
          <a class="project-subfile-link" href="${p.files.excel_xlsx}" target="_blank" title="Download 12-Discipline Excel Financial Estimator">
            <span>📗 Excel Financial Model</span>
            <span class="file-type-tag" style="background: rgba(33, 115, 70, 0.3); color: #86efac;">.xlsx</span>
          </a>
          <a class="project-subfile-link" href="${p.files.jira_csv}" target="_blank" title="Download Jira / Azure DevOps Backlog CSV">
            <span>📋 Jira / DevOps Backlog</span>
            <span class="file-type-tag" style="background: rgba(0, 82, 204, 0.3); color: #a5b4fc;">.csv</span>
          </a>
        </div>
      </div>
    `;
  }).join("") + (hasDeleted ? `
    <div style="margin-top: 4px; text-align: center;">
      <button class="folder-restore-btn" onclick="restoreDefaultWorkspaces()" style="font-size: 0.68rem; padding: 4px 8px;">
        <span>🔄</span> Restore ${deletedIds.length} Removed Workspace${deletedIds.length > 1 ? 's' : ''}
      </button>
    </div>
  ` : '');
}

function removeProjectWorkspace(projectId, projectName) {
  if (!confirm(`Are you sure you want to remove the workspace "${projectName || projectId}" from your sidebar?`)) {
    return;
  }

  saveDeletedWorkspaceId(projectId);
  cachedProjectList = cachedProjectList.filter(p => p.id !== projectId);
  
  const searchVal = document.getElementById("projectSearchInput") ? document.getElementById("projectSearchInput").value : "";
  if (searchVal) {
    filterProjectFolders(searchVal);
  } else {
    renderProjectFolders(cachedProjectList);
  }

  // If the removed workspace was the currently active one, load the first remaining workspace or reset
  if (currentSessionId === projectId) {
    if (cachedProjectList.length > 0) {
      loadProjectWorkspace(cachedProjectList[0].id);
    } else {
      resetSession();
    }
  }
}

function restoreDefaultWorkspaces() {
  localStorage.removeItem("brd_deleted_workspaces");
  loadProjectHistory();
}

function toggleProjectFolder(projectId) {
  const sub = document.getElementById(`subfiles_${projectId}`);
  const chev = document.getElementById(`chevron_${projectId}`);
  if (!sub) return;

  const isHidden = (sub.style.display === "none");
  sub.style.display = isHidden ? "flex" : "none";
  if (chev) {
    chev.style.transform = isHidden ? "rotate(0deg)" : "rotate(-90deg)";
  }
}

async function loadProjectWorkspace(projectId) {
  try {
    const res = await fetch(`/api/projects/load?project_id=${projectId}`, { method: "POST" });
    if (res.ok) {
      currentSessionData = await res.json();
      currentSessionId = currentSessionData.session_id;
      localStorage.setItem("brd_session_id", currentSessionId);
      
      renderChatMessages();
      updateProgressCounter();
      if (currentSessionData.brd) {
        renderBRDWorkbench(currentSessionData.brd);
      }

      // Highlight active folder card
      document.querySelectorAll(".project-folder-card").forEach(c => c.classList.remove("active"));
      const activeCard = document.getElementById(`folder_card_${projectId}`);
      if (activeCard) activeCard.classList.add("active");

      // Show subfiles
      const sub = document.getElementById(`subfiles_${projectId}`);
      if (sub) sub.style.display = "flex";
    }
  } catch (err) {
    console.error("Failed to load project workspace:", err);
  }
}

function filterProjectFolders(query) {
  if (!query || !query.trim()) {
    renderProjectFolders(cachedProjectList);
    return;
  }
  const q = query.toLowerCase().trim();
  const filtered = cachedProjectList.filter(p => 
    (p.name && p.name.toLowerCase().includes(q)) ||
    (p.client && p.client.toLowerCase().includes(q)) ||
    (p.tier && p.tier.toLowerCase().includes(q)) ||
    (p.cloud_platform && p.cloud_platform.toLowerCase().includes(q))
  );
  renderProjectFolders(filtered);
}

// ==========================================
// 3-PERSONA COLLABORATIVE WORKFLOW LOGIC
// ==========================================

function updateWorkflowUI(data) {
  if (!data) return;
  const wf = data.workflow || {
    current_stage: "DISCOVERY",
    active_persona: "CLIENT",
    client_review: { status: "PENDING", feedback: "" },
    architect_review: { status: "PENDING", feedback: "" },
    pm_review: { status: "PENDING", queries: [], triparty_messages: [] },
    review_iteration: 0
  };

  const conf = data.confidence || {
    score: 10,
    is_ready_for_brd: false,
    dimensions: {},
    summary: "Discovery initial phase."
  };

  // 1. Confidence Gauge Update
  const score = Math.min(100, Math.max(0, Math.round(conf.score || 0)));
  const fillEl = document.getElementById("confidenceFill");
  const scoreText = document.getElementById("confidenceScoreText");
  const threshTag = document.getElementById("confidenceThresholdTag");

  if (fillEl) {
    fillEl.style.width = `${score}%`;
    if (score >= 98) {
      fillEl.style.background = "linear-gradient(90deg, #10b981 0%, #059669 100%)";
    } else if (score >= 60) {
      fillEl.style.background = "linear-gradient(90deg, #38bdf8 0%, #2563eb 100%)";
    } else {
      fillEl.style.background = "linear-gradient(90deg, #f59e0b 0%, #d97706 100%)";
    }
  }
  if (scoreText) scoreText.textContent = `${score}%`;
  if (threshTag) {
    if (score >= 98) {
      threshTag.textContent = "✓ 98% Reached (BRD Ready)";
      threshTag.style.background = "rgba(16, 185, 129, 0.15)";
      threshTag.style.color = "#10b981";
      threshTag.style.borderColor = "rgba(16, 185, 129, 0.3)";
    } else {
      threshTag.textContent = "98% Goal";
      threshTag.style.background = "rgba(56, 189, 248, 0.15)";
      threshTag.style.color = "#0284c7";
      threshTag.style.borderColor = "rgba(56, 189, 248, 0.3)";
    }
  }

  // 2. Stepper Stage Highlight
  const stages = [
    { key: "IDEATION", id: "stepIdeation" },
    { key: "DISCOVERY", id: "stepDiscovery" },
    { key: "DUAL_REVIEW", id: "stepDualReview" },
    { key: "PM_REVIEW", id: "stepPMReview" },
    { key: "FINAL_APPROVED", id: "stepFinalBRD" }
  ];
  
  const curStage = wf.current_stage || "DISCOVERY";
  let curIndex = stages.findIndex(s => s.key === curStage);
  if (curIndex === -1) curIndex = 1;

  stages.forEach((s, idx) => {
    const el = document.getElementById(s.id);
    if (!el) return;
    el.classList.remove("active", "completed");
    if (idx === curIndex) {
      el.classList.add("active");
    } else if (idx < curIndex) {
      el.classList.add("completed");
    }
  });

  // 3. Stage 3 Dual Review Updates
  const dualIterBadge = document.getElementById("dualReviewIterBadge");
  if (dualIterBadge) dualIterBadge.textContent = `Iteration #${wf.review_iteration || 0}`;

  const cRev = wf.client_review || {};
  const aRev = wf.architect_review || {};

  const cBadge = document.getElementById("clientReviewStatusBadge");
  if (cBadge) {
    cBadge.textContent = cRev.status || "PENDING REVIEW";
    cBadge.className = `badge ${cRev.status === "APPROVED" ? "badge-success" : cRev.status === "CHANGES_REQUESTED" ? "badge-danger" : "badge-info"}`;
  }

  const aBadge = document.getElementById("architectReviewStatusBadge");
  if (aBadge) {
    aBadge.textContent = aRev.status || "PENDING REVIEW";
    aBadge.className = `badge ${aRev.status === "APPROVED" ? "badge-success" : aRev.status === "CHANGES_REQUESTED" ? "badge-danger" : "badge-info"}`;
  }

  // Dual review checklists sync from BRD
  if (data.brd) {
    const b = data.brd;
    const cProb = document.getElementById("clientReviewProblemStatus");
    if (cProb) cProb.textContent = b.problem_statement ? "✓ In Scope" : "Pending";
    const cDur = document.getElementById("clientReviewDurationStatus");
    if (cDur) cDur.textContent = `${b.total_duration_weeks.toFixed(1)} Weeks (${b.delivery_tier})`;
    
    const aCloud = document.getElementById("archReviewCloudStatus");
    if (aCloud) aCloud.textContent = `${b.cloud_platform} (${b.primary_model || "Foundation AI"})`;
    const aComp = document.getElementById("archReviewComponentsStatus");
    if (aComp) aComp.textContent = `${b.architectural_components ? b.architectural_components.length : 6} Decomposed Microservices`;
    const aBom = document.getElementById("archReviewBomStatus");
    if (aBom) aBom.textContent = `${b.currency_symbol || "$"}${Math.round((b.sizing_metrics.total_monthly_cloud_cost_usd || 645) * (b.currency_exchange_rate || 1)).toLocaleString()} / month`;
  }

  // 4. Stage 4 PM Governance & Consensus Updates
  const pmRev = wf.pm_review || {};
  const pmGate = document.getElementById("pmGateStatus");
  if (pmGate) {
    pmGate.textContent = pmRev.status || "REVIEW PENDING";
    pmGate.style.color = pmRev.status === "APPROVED" ? "var(--success)" : pmRev.status === "CHANGES_REQUESTED" ? "var(--danger)" : "#d97706";
  }

  if (data.brd) {
    const b = data.brd;
    const rate = b.currency_exchange_rate || 1.0;
    const sym = b.currency_symbol || "$";
    const convertedCost = b.total_labour_cost_converted || (b.total_labour_cost_usd * rate);
    
    const pmCost = document.getElementById("pmMetricCost");
    if (pmCost) pmCost.textContent = `${sym}${Math.round(convertedCost).toLocaleString()}`;
    const pmDays = document.getElementById("pmMetricDays");
    if (pmDays) pmDays.textContent = `${b.total_person_days.toFixed(1)} d`;
    const pmDur = document.getElementById("pmMetricDuration");
    if (pmDur) pmDur.textContent = `${b.total_duration_weeks.toFixed(1)} Weeks`;
  }

  // Render Tripartite stream
  const tripartyContainer = document.getElementById("tripartyMessagesStream");
  if (tripartyContainer && pmRev.triparty_messages) {
    tripartyContainer.innerHTML = "";
    if (pmRev.triparty_messages.length === 0) {
      tripartyContainer.innerHTML = `
        <div style="text-align: center; color: #94a3b8; font-size: 0.82rem; padding: 24px;">
          🤝 Tripartite consensus room is ready. Delivery PM, Client Business Lead, and Solutions Architect can negotiate deliverables, staffing, and risk mitigations here.
        </div>
      `;
    } else {
      pmRev.triparty_messages.forEach(msg => {
        const msgEl = document.createElement("div");
        const pCls = msg.persona === "SOLUTIONS_ARCHITECT" ? "architect" : msg.persona === "PROJECT_MANAGER" ? "pm" : "client";
        const pTag = msg.persona === "SOLUTIONS_ARCHITECT" ? "🏗️ Architect" : msg.persona === "PROJECT_MANAGER" ? "👔 PM" : "🧑‍💼 Client";
        
        msgEl.className = `triparty-msg ${pCls}`;
        msgEl.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span class="msg-persona-tag msg-persona-${pCls}">${escapeHtml(pTag + " (" + msg.author_name + ")")}</span>
            <span style="font-size: 0.68rem; color: #94a3b8;">${formatMessageTimestamp(msg.timestamp)}</span>
          </div>
          <div style="font-size: 0.84rem; color: #1e293b; line-height: 1.5;">${escapeHtml(msg.text)}</div>
        `;
        tripartyContainer.appendChild(msgEl);
      });
      tripartyContainer.scrollTop = tripartyContainer.scrollHeight;
    }
  }

  // 5. Stage 5 Signatures & Certificate Updates
  if (data.brd) {
    const certTitle = document.getElementById("certProjectTitle");
    if (certTitle) certTitle.textContent = `${data.brd.client_name} — ${data.brd.project_title}`;
  }

  const certClientTime = document.getElementById("certClientTimestamp");
  if (certClientTime) {
    certClientTime.textContent = cRev.approved_at ? `✓ Approved on ${new Date(cRev.approved_at).toLocaleDateString()}` : "Pending Approval";
    certClientTime.style.color = cRev.approved_at ? "#86efac" : "#fca5a5";
  }

  const certArchTime = document.getElementById("certArchitectTimestamp");
  if (certArchTime) {
    certArchTime.textContent = aRev.approved_at ? `✓ Approved on ${new Date(aRev.approved_at).toLocaleDateString()}` : "Pending Approval";
    certArchTime.style.color = aRev.approved_at ? "#86efac" : "#fca5a5";
  }

  const certPMTime = document.getElementById("certPMTimestamp");
  if (certPMTime) {
    certPMTime.textContent = pmRev.approved_at ? `✓ Sealed on ${new Date(pmRev.approved_at).toLocaleDateString()}` : "Pending Governance Sign-Off";
    certPMTime.style.color = pmRev.approved_at ? "#86efac" : "#fca5a5";
  }
}

// Stage 1: Idea Template Selection
function selectIdeaTemplate(el, title, idea, tier) {
  document.querySelectorAll(".idea-template-card").forEach(c => c.classList.remove("selected"));
  if (el) el.classList.add("selected");

  const titleInput = document.getElementById("ideationProjectTitle");
  if (titleInput) titleInput.value = title;
  const ideaInput = document.getElementById("ideationClientIdea");
  if (ideaInput) ideaInput.value = idea;
  const tierSelect = document.getElementById("ideationTargetTier");
  if (tierSelect) {
    for (let opt of tierSelect.options) {
      if (opt.value === tier || opt.text.includes(tier)) {
        tierSelect.value = opt.value;
        break;
      }
    }
  }
  updateIdeationArchitectPreview();
}

function updateIdeationArchitectPreview() {
  const tier = document.getElementById("ideationTargetTier") ? document.getElementById("ideationTargetTier").value : "PoC";
  const cloud = document.getElementById("ideationCloudSelect") ? document.getElementById("ideationCloudSelect").value : "Microsoft Azure";
  const adviceEl = document.getElementById("ideationArchitectAdviceText");
  const badgeEl = document.getElementById("ideationFeasibilityBadge");

  if (adviceEl) {
    adviceEl.innerHTML = `
      • <strong>Selected Hyperscaler:</strong> ${escapeHtml(cloud)} with tailored native AI pipelines.<br>
      • <strong>Target Tier & WBS:</strong> ${escapeHtml(tier)} sizing configured with 12 engineering disciplines.<br>
      • <strong>Microservices Decomposition:</strong> 6 decoupled components with bounding-box coordinate lineage.<br>
      • <strong>Security Architecture:</strong> Enhanced zero-trust envelope with RBAC & CMEK encryption.
    `;
  }
  if (badgeEl) badgeEl.textContent = "96% High Feasibility";
}

async function commitIdeationAndStartDiscovery() {
  const title = document.getElementById("ideationProjectTitle") ? document.getElementById("ideationProjectTitle").value.trim() : "Custom AI Solution";
  const idea = document.getElementById("ideationClientIdea") ? document.getElementById("ideationClientIdea").value.trim() : "";
  const tier = document.getElementById("ideationTargetTier") ? document.getElementById("ideationTargetTier").value : "PoC";
  const cloud = document.getElementById("ideationCloudSelect") ? document.getElementById("ideationCloudSelect").value : "Microsoft Azure";

  try {
    const res = await fetch("/api/workflow/ideate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        project_title: title,
        client_idea: idea,
        target_tier: tier,
        cloud_preference: cloud
      })
    });

    if (res.ok) {
      currentSessionData = await res.json();
      renderChatMessages();
      updateProgressCounter();
      updateWorkflowUI(currentSessionData);
      switchTab("tab-brd");
      
      const chatInput = document.getElementById("chatCustomInput");
      if (chatInput) chatInput.focus();
    }
  } catch (err) {
    console.error("Ideation start failed:", err);
  }
}

// Stage 2: Delegate Question to Architect
async function delegateCurrentQuestionToArchitect() {
  if (!currentSessionId) return;
  try {
    const res = await fetch("/api/workflow/delegate-architect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: currentSessionId })
    });

    if (res.ok) {
      currentSessionData = await res.json();
      renderChatMessages();
      renderQuickSuggestions();
      updateProgressCounter();
      updateWorkflowUI(currentSessionData);
      loadArchitectBriefing();
      showToast("✓ Delegated to Solutions Architect with full project context", "info");
    }
  } catch (err) {
    console.error("Delegation to architect failed:", err);
  }
}

// Stage 3: Dual Review Feedback & Sign-Off
async function submitDualReviewFeedback(persona) {
  const inputId = persona === "CLIENT" ? "clientFeedbackInput" : "architectFeedbackInput";
  const inputEl = document.getElementById(inputId);
  const feedback = inputEl ? inputEl.value.trim() : "";

  if (!feedback) {
    alert("Please enter your feedback or change request before submitting.");
    return;
  }

  try {
    const res = await fetch("/api/workflow/dual-review/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        persona: persona,
        feedback: feedback
      })
    });

    if (res.ok) {
      currentSessionData = await res.json();
      if (inputEl) inputEl.value = "";
      renderChatMessages();
      updateWorkflowUI(currentSessionData);
      if (currentSessionData.brd) {
        renderBRDWorkbench(currentSessionData.brd);
      }
      alert(`Feedback recorded for ${persona === "CLIENT" ? "Client Business Lead" : "Solutions Architect"}. Plan re-synthesized!`);
    }
  } catch (err) {
    console.error("Dual review feedback error:", err);
  }
}

async function submitDualReviewApproval(persona) {
  try {
    const res = await fetch("/api/workflow/dual-review/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        persona: persona
      })
    });

    if (res.ok) {
      currentSessionData = await res.json();
      renderChatMessages();
      updateWorkflowUI(currentSessionData);
      
      const wf = currentSessionData.workflow;
      if (wf && wf.current_stage === "PM_REVIEW") {
        alert("🎉 Both Client and Solutions Architect have approved! Project automatically transitioned to Senior Delivery PM for Stage 4 Governance.");
        switchTab("tab-pm-review");
      } else {
        alert(`✓ Approval confirmed for ${persona === "CLIENT" ? "Client Business Lead" : "Solutions Architect"}. Waiting for peer sign-off.`);
      }
    }
  } catch (err) {
    console.error("Dual review approval error:", err);
  }
}

// Stage 4: Project Manager Governance & Tripartite Discussion
async function submitPMQuery() {
  const topic = document.getElementById("pmQueryTopic") ? document.getElementById("pmQueryTopic").value.trim() : "Governance Milestone";
  const target = document.getElementById("pmQueryAddressedTo") ? document.getElementById("pmQueryAddressedTo").value : "ALL";
  const text = document.getElementById("pmQueryText") ? document.getElementById("pmQueryText").value.trim() : "";

  if (!text) {
    alert("Please enter the query or requested modification.");
    return;
  }

  try {
    const res = await fetch("/api/workflow/pm-review/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        topic: topic,
        addressed_to: target,
        text: text
      })
    });

    if (res.ok) {
      currentSessionData = await res.json();
      const txtEl = document.getElementById("pmQueryText");
      if (txtEl) txtEl.value = "";
      renderChatMessages();
      updateWorkflowUI(currentSessionData);
    }
  } catch (err) {
    console.error("PM query submission error:", err);
  }
}

async function sendTripartyReply() {
  const replyInput = document.getElementById("tripartyReplyInput");
  const text = replyInput ? replyInput.value.trim() : "";
  if (!text) return;

  try {
    const res = await fetch("/api/workflow/pm-review/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        persona: activePersona,
        response: text
      })
    });

    if (res.ok) {
      currentSessionData = await res.json();
      if (replyInput) replyInput.value = "";
      renderChatMessages();
      updateWorkflowUI(currentSessionData);
    }
  } catch (err) {
    console.error("Triparty reply error:", err);
  }
}

async function submitPMApproval() {
  try {
    const res = await fetch("/api/workflow/pm-review/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        notes: "Approved by Senior Delivery PM following tripartite milestone and commercial alignment."
      })
    });

    if (res.ok) {
      currentSessionData = await res.json();
      renderChatMessages();
      updateWorkflowUI(currentSessionData);
      alert("🏆 Project BRD officially signed and sealed by Senior Delivery PM! Advancing to Final Approved Distribution Suite.");
      switchTab("tab-export");
    }
  } catch (err) {
    console.error("PM approval error:", err);
  }
}

function approveAndLockPlan() {
  switchTab("tab-dual-review");
}

// 1-Click PM Governance Query Presets
function applyPmQueryTemplate(type) {
  const topicInput = document.getElementById("pmQueryTopic");
  const targetSelect = document.getElementById("pmQueryAddressedTo");
  const textInput = document.getElementById("pmQueryText");

  if (!topicInput || !targetSelect || !textInput) return;

  if (type === "timeline") {
    topicInput.value = "Phase 8 Verification Buffer & Timeline Compression Risk";
    targetSelect.value = "ALL";
    textInput.value = "Auditing the 18-phase schedule: Can we ensure a 3-day buffer in Phase 8 (Model Verification) before moving to Phase 11 UAT? Client to confirm business blackout dates, and Architect to confirm automated eval test harness readiness.";
  } else if (type === "cloud_cost") {
    topicInput.value = "Cloud Monthly BoM Optimization ($645/mo Baseline)";
    targetSelect.value = "SOLUTIONS_ARCHITECT";
    textInput.value = "Solutions Architect: Verify if Azure AI Search standard partition tier meets our 50,000 document vector indexing requirements without auto-scaling beyond our $800/mo infrastructure cap.";
  } else if (type === "staffing") {
    topicInput.value = "Lead AI Engineer & Prompt Specialist Allocation";
    targetSelect.value = "ALL";
    textInput.value = "Confirming that Senior AI Engineer (23.2d) and Prompt Engineer (14.5d) are dedicated during Weeks 2-4 for multi-pass reasoning engine stabilization.";
  }
}

// Direct 1-Click Jira Backlog CSV Downloader
function downloadJiraDirect() {
  if (!currentSessionId) {
    alert("Please complete project discovery first to generate the Jira backlog.");
    return;
  }
  window.open(`/api/export/jira-csv?session_id=${currentSessionId}`, "_blank");
}

// Interactive Live Sizing Recalculation Preview
function simulateLiveSizing() {
  const docsInput = document.getElementById("simDocsCount");
  const reqsInput = document.getElementById("simReqsCount");
  const resultEl = document.getElementById("simResultText");
  if (!docsInput || !reqsInput || !resultEl) return;

  const docs = parseInt(docsInput.value) || 50000;
  const reqs = parseInt(reqsInput.value) || 2000;

  // Formula: Base $450 (Search + Azure OpenAI) + Storage ($20/50k) + Token Volume ($175/2k reqs)
  const estMonthly = Math.round(450 + (docs / 50000) * 20 + (reqs / 2000) * 175);
  resultEl.textContent = `$${estMonthly.toLocaleString()} / month`;
}

// Architect Escalation Queue & Client Briefing Loader
async function loadArchitectBriefing() {
  if (!currentSessionId) return;
  try {
    const res = await fetch(`/api/workflow/architect/briefing?session_id=${currentSessionId}`);
    if (!res.ok) return;
    const data = await res.json();
    
    // 1. Render Client Overview Summary
    const overviewEl = document.getElementById("archClientOverviewText");
    if (overviewEl && data.client_overview) {
      const co = data.client_overview;
      overviewEl.innerHTML = `
        <strong>Project:</strong> ${escapeHtml(co.project_title || 'Untitled')} &nbsp;|&nbsp; 
        <strong>Tier:</strong> <span class="badge badge-success">${escapeHtml(co.target_tier || 'PoC')}</span> &nbsp;|&nbsp; 
        <strong>Timeline:</strong> ${escapeHtml(co.duration || '6.0 wks')} &nbsp;|&nbsp; 
        <strong>Categories:</strong> ${escapeHtml(co.legal_categories || 'Standard')} &nbsp;|&nbsp; 
        <strong>Confidence:</strong> ${co.current_confidence || 0}%<br>
        <span style="color: #64748b; font-size: 0.8rem;">Problem Statement: ${escapeHtml(co.problem_statement || 'Scoping in progress')}</span>
      `;
    }

    // 2. Render Pending Escalated Questions Cards
    const countBadge = document.getElementById("archEscalationCountBadge");
    if (countBadge) {
      countBadge.textContent = `${data.pending_count || 0} Pending Topics`;
      countBadge.className = (data.pending_count > 0) ? "badge badge-warning" : "badge badge-success";
    }

    const streamEl = document.getElementById("archEscalatedCardsStream");
    if (streamEl) {
      if (!data.escalated_topics || data.escalated_topics.length === 0) {
        streamEl.innerHTML = `
          <div style="background: #ffffff; border: 1px dashed var(--border-color); border-radius: 6px; padding: 14px; text-align: center; color: #64748b; font-size: 0.84rem;">
            <span>✨</span> No escalated technical questions pending from Client. All questions are aligned!
          </div>
        `;
        return;
      }

      streamEl.innerHTML = data.escalated_topics.map((item, idx) => {
        const isResolved = item.status === "RESOLVED";
        const optionsHtml = (item.options || []).map(opt => `
          <button class="persona-action-btn" style="font-size: 0.74rem; padding: 3px 8px; margin: 2px;" 
            onclick="resolveArchitectEscalation('${escapeHtml(item.question_id)}', '${escapeHtml(opt.value)}')">
            ${escapeHtml(opt.label || opt.value)}
          </button>
        `).join("");

        return `
          <div style="background: ${isResolved ? '#f0fdf4' : '#ffffff'}; border: 1px solid ${isResolved ? '#86efac' : 'var(--border-color)'}; border-left: 4px solid ${isResolved ? '#16a34a' : '#0284c7'}; border-radius: var(--radius-sm); padding: 12px 14px; box-shadow: var(--shadow-sm);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
              <div>
                <span style="font-size: 0.72rem; font-weight: 700; color: #0284c7; text-transform: uppercase;">Topic #${idx+1}: ${escapeHtml(item.topic_title)}</span>
                <h5 style="margin: 2px 0 0 0; font-size: 0.88rem; color: #0f172a;">${escapeHtml(item.question_text)}</h5>
              </div>
              <span class="badge ${isResolved ? 'badge-success' : 'badge-warning'}" style="font-size: 0.7rem;">
                ${isResolved ? '✓ Resolved' : '⏳ Action Required'}
              </span>
            </div>
            
            <div style="font-size: 0.78rem; color: #475569; margin-bottom: 8px; line-height: 1.45;">
              <strong>🔍 Why This Is Needed:</strong> ${escapeHtml(item.why_needed)}<br>
              <strong>💡 Client Context:</strong> ${escapeHtml(item.client_context)}
            </div>

            ${isResolved ? `
              <div style="font-size: 0.8rem; color: #15803d; font-weight: 600; background: rgba(22, 163, 74, 0.08); padding: 4px 8px; border-radius: 4px;">
                ✓ Architect Decision: <code>${escapeHtml(item.architect_answer || item.default_recommendation)}</code>
              </div>
            ` : `
              <div style="display: flex; flex-direction: column; gap: 6px;">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px;">
                  <button class="persona-action-btn primary" style="font-size: 0.76rem; padding: 4px 10px;"
                    onclick="resolveArchitectEscalation('${escapeHtml(item.question_id)}', '${escapeHtml(item.default_recommendation)}')">
                    <span>⚡</span> Accept Recommended: ${escapeHtml(item.default_recommendation)}
                  </button>
                  <span style="font-size: 0.72rem; color: #64748b;">or pick alternative:</span>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                  ${optionsHtml}
                </div>
              </div>
            `}
          </div>
        `;
      }).join("");
    }
  } catch (err) {
    console.error("Failed to load architect briefing:", err);
  }
}

async function resolveArchitectEscalation(questionId, answer, notes) {
  if (!currentSessionId) return;
  try {
    const res = await fetch("/api/workflow/architect/resolve-escalation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        question_id: questionId,
        answer: answer,
        notes: notes || "Confirmed by Solutions Architect"
      })
    });

    if (res.ok) {
      currentSessionData = await res.json();
      renderChatMessages();
      loadArchitectBriefing();
      updateWorkflowUI(currentSessionData);
    }
  } catch (err) {
    console.error("Resolve escalation error:", err);
  }
}
