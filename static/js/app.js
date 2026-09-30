let currentSessionId = localStorage.getItem("brd_session_id") || "";
let currentSessionData = null;

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

// Initialize app on load
document.addEventListener("DOMContentLoaded", async () => {
  await loadSettings();
  await initSession();
  await loadProjectHistory();
});

// Load Settings from Server
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    if (res.ok) {
      const data = await res.json();
      updateProviderBadge(data.active_provider, data);
      
      const modalSelect = document.getElementById("modalProviderSelect");
      if (modalSelect) modalSelect.value = data.active_provider;
      onModalProviderChange();
      
      if (data.gemini_api_key) document.getElementById("modalGeminiKey").value = data.gemini_api_key;
      if (data.azure_openai_endpoint) document.getElementById("modalAzureEndpoint").value = data.azure_openai_endpoint;
      if (data.azure_openai_api_key) document.getElementById("modalAzureKey").value = data.azure_openai_api_key;
      if (data.aws_region) document.getElementById("modalAWSRegion").value = data.aws_region;
      if (data.aws_access_key) document.getElementById("modalAWSAccessKey").value = data.aws_access_key;
    }
  } catch (err) {
    console.error("Failed to load settings:", err);
  }
}

function updateProviderBadge(provider, data) {
  const badgeText = document.getElementById("activeProviderText");
  if (!badgeText) return;
  
  if (provider === "azure") {
    badgeText.textContent = `AI: Azure OpenAI (GPT-4o/5)`;
  } else if (provider === "aws") {
    badgeText.textContent = `AI: AWS Bedrock (Claude 3.5)`;
  } else {
    badgeText.textContent = `AI: Google Studio (Gemini 2.5)`;
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
      
      renderChatMessages();
      updateProgressCounter();
      
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

// Render Chat Stream
function renderChatMessages() {
  const container = document.getElementById("chatHistory");
  if (!container || !currentSessionData) return;
  
  container.innerHTML = "";
  const msgs = currentSessionData.messages || [];
  
  msgs.forEach((m) => {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-msg ${m.sender}`;
    
    let avatarIcon = "🤖";
    if (m.sender === "user") avatarIcon = "👤";
    if (m.sender === "system") avatarIcon = "⚙️";
    
    let formattedText = m.content
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\n\n/g, "</p><p>")
      .replace(/\n/g, "<br>");
      
    let innerHTML = `
      <div class="msg-avatar">${avatarIcon}</div>
      <div class="msg-content">
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
  const dropdownSelect = document.getElementById("chatDropdownSelect");
  const customWrapper = document.getElementById("customInputWrapper");
  const customInput = document.getElementById("chatCustomInput");
  
  if (!dropdownSelect) return;
  
  const curQ = currentSessionData ? currentSessionData.current_question : null;
  if (!curQ) {
    dropdownSelect.style.display = "none";
    if (customWrapper) customWrapper.style.display = "none";
    return;
  }
  
  // Reset visibility
  dropdownSelect.style.display = "block";
  if (customWrapper) customWrapper.style.display = "none";
  if (customInput) customInput.value = "";
  
  dropdownSelect.innerHTML = "";
  
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
    optionsList.forEach((opt) => {
      const op = document.createElement("option");
      op.value = opt.value;
      const desc = opt.description ? ` — ${opt.description}` : '';
      op.textContent = `${opt.label}${desc}`;
      if (opt.value === curQ.default_value) {
        op.selected = true;
      }
      dropdownSelect.appendChild(op);
    });
  } else {
    // If no explicit options, add the default value as an option
    const defOp = document.createElement("option");
    defOp.value = curQ.default_value || "";
    defOp.textContent = `${curQ.default_value || "Recommended Default"} (Default)`;
    defOp.selected = true;
    dropdownSelect.appendChild(defOp);
  }
  
  // ALWAYS ADD THE FINAL OPTION: Custom Input (Anti-Gravity / User custom answer)
  const customOp = document.createElement("option");
  customOp.value = "__CUSTOM__";
  customOp.textContent = `✏️ Custom Input (Type your own answer / anti gravity)...`;
  customOp.style.color = "var(--primary)";
  customOp.style.fontWeight = "600";
  dropdownSelect.appendChild(customOp);
  
  dropdownSelect.focus();
}

function handleDropdownChange() {
  const dropdownSelect = document.getElementById("chatDropdownSelect");
  const customWrapper = document.getElementById("customInputWrapper");
  const customInput = document.getElementById("chatCustomInput");
  
  if (!dropdownSelect) return;
  
  if (dropdownSelect.value === "__CUSTOM__") {
    dropdownSelect.style.display = "none";
    if (customWrapper) customWrapper.style.display = "flex";
    if (customInput) {
      const curQ = currentSessionData ? currentSessionData.current_question : null;
      customInput.placeholder = curQ ? `Type custom answer for ${curQ.title}...` : "Type your custom answer...";
      customInput.value = "";
      customInput.focus();
    }
  }
}

function cancelCustomInput() {
  const dropdownSelect = document.getElementById("chatDropdownSelect");
  const customWrapper = document.getElementById("customInputWrapper");
  
  if (customWrapper) customWrapper.style.display = "none";
  if (dropdownSelect) {
    dropdownSelect.style.display = "block";
    dropdownSelect.selectedIndex = 0;
    dropdownSelect.focus();
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
  const cur = (currentSessionData.current_question_index || 0) + 1;
  const total = currentSessionData.total_questions || 22;
  el.textContent = cur <= total ? `Question ${cur} of ${total}` : `Discovery Complete (${total}/${total})`;
}

function handleDropdownKeyDown(e) {
  if (e.key === "Enter") {
    e.preventDefault();
    sendUserMessage();
  }
}

function sendUserMessage() {
  const dropdownSelect = document.getElementById("chatDropdownSelect");
  const customWrapper = document.getElementById("customInputWrapper");
  const customInput = document.getElementById("chatCustomInput");
  
  let answer = "";
  
  if (customWrapper && customWrapper.style.display !== "none") {
    answer = customInput.value.trim();
    if (!answer && currentSessionData && currentSessionData.current_question) {
      answer = currentSessionData.current_question.default_value;
    }
  } else if (dropdownSelect && dropdownSelect.style.display !== "none") {
    if (dropdownSelect.value === "__CUSTOM__") {
      answer = customInput ? customInput.value.trim() : "";
      if (!answer && currentSessionData && currentSessionData.current_question) {
        answer = currentSessionData.current_question.default_value;
      }
    } else {
      answer = dropdownSelect.value;
    }
  }
  
  if (!answer && currentSessionData && currentSessionData.current_question) {
    answer = currentSessionData.current_question.default_value;
  }
  
  if (!answer) return;
  
  if (customInput) customInput.value = "";
  sendMessageWithText(answer);
}

async function sendMessageWithText(text) {
  if (!text) return;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSessionId,
        message: text,
        selected_option: text
      })
    });
    
    if (res.ok) {
      currentSessionData = await res.json();
      renderChatMessages();
      updateProgressCounter();
      
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
  document.getElementById("brdExecSummary").textContent = brd.executive_summary;
  document.getElementById("brdProblemText").textContent = brd.problem_statement;
  document.getElementById("brdSixSentences").textContent = brd.solution_summary_six_sentences;
  
  const impactsList = document.getElementById("brdImpactsList");
  impactsList.innerHTML = (brd.business_impacts || []).map(imp => `<li>${imp}</li>`).join("");
  
  const inScopeList = document.getElementById("brdInScopeList");
  inScopeList.innerHTML = (brd.in_scope || []).map(s => `<li>${s}</li>`).join("");
  
  const outScopeList = document.getElementById("brdOutScopeList");
  outScopeList.innerHTML = (brd.out_of_scope || []).map(s => `<li>${s}</li>`).join("");
  
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
          <td><strong style="color: #fff;">${(r.total_assigned_fte || r.peak_fte || 0).toFixed(2)} FTE</strong></td>
        </tr>
      `;
    }).join("") + `
      <tr style="background: rgba(56, 189, 248, 0.1); font-weight: bold;">
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
          <td style="font-size: 0.8rem; color: #cbd5e1;">${b.purpose}</td>
        </tr>
      `).join("");
    }
  }

  const tasksTbody = document.getElementById("tasksTableBody");
  if (tasksTbody) {
    tasksTbody.innerHTML = (brd.task_estimates || []).map(t => `
      <tr>
        <td><span style="font-weight: 600; color: var(--primary);">${t.phase_code}</span></td>
        <td style="font-size: 0.82rem;">${t.task_name}</td>
        <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.72rem;">${t.primary_role}</span></td>
        <td>${t.base_days.toFixed(1)}</td>
        <td>${t.phase_factor.toFixed(3)}</td>
        <td>${t.scale_factor.toFixed(3)}</td>
        <td>${t.uplift_tag !== "NONE" ? `<span style="color: #f59e0b; font-weight: 600;">${t.uplift_tag} (${t.uplift_mult.toFixed(2)})</span>` : "1.00"}</td>
        <td style="font-weight: 600; color: #fff;">${t.effort_days.toFixed(2)} d</td>
      </tr>
    `).join("");
  }

  // Tab 3: 18-Phase Roadmap & Feasibility
  const feas = brd.schedule_feasibility;
  const feasCard = document.getElementById("feasibilityCard");
  if (feasCard && feas) {
    feasCard.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px;">
        <div>
          <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Reference Duration</div>
          <div style="font-size: 1.1rem; font-weight: 700; color: #fff;">${feas.reference_duration_weeks.toFixed(1)} Weeks (${feas.working_days} working days)</div>
        </div>
        <div>
          <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Resolved Duration</div>
          <div style="font-size: 1.1rem; font-weight: 700; color: ${feas.schedule_stretched ? '#f87171' : 'var(--success)'};">${feas.resolved_duration_weeks.toFixed(1)} Weeks</div>
        </div>
        <div>
          <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Peak Role FTE</div>
          <div style="font-size: 1.1rem; font-weight: 700; color: #fff;">${feas.peak_fte_observed.toFixed(2)} / ${feas.max_fte_limit.toFixed(0)} max</div>
        </div>
        <div>
          <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Binding Constraint</div>
          <div style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted);">${feas.binding_constraint}</div>
        </div>
      </div>
    `;
  }

  const phasesList = document.getElementById("phasesList");
  if (phasesList) {
    phasesList.innerHTML = (brd.project_phases || []).map(p => `
      <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div>
          <div style="font-weight: 600; color: #fff; font-size: 0.9rem;">${p.phase_name}</div>
          <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 2px;">
            Deliverables: ${p.key_deliverables.join(" • ")}
          </div>
        </div>
        <div style="text-align: right;">
          <span style="font-weight: 700; color: var(--primary); font-size: 0.95rem;">${p.weeks.toFixed(1)} wks</span>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${p.effort_days.toFixed(1)} Person-Days</div>
        </div>
      </div>
    `).join("");
  }

  // Tab 4: Technical Components (6)
  const compList = document.getElementById("componentsList");
  if (compList) {
    compList.innerHTML = (brd.technical_components || []).map(c => `
      <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-color); border-radius: 8px; padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <h4 style="color: var(--primary); font-size: 0.95rem;">${c.id}: ${c.name}</h4>
          <span class="badge-ai" style="font-size: 0.75rem;">${c.technology_choice}</span>
        </div>
        <p style="font-size: 0.84rem; color: #cbd5e1; margin-bottom: 10px;"><strong>Purpose:</strong> ${c.purpose}</p>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.8rem; color: var(--text-muted);">
          <div><strong>Key Decisions:</strong> ${c.key_design_decisions}</div>
          <div><strong>Interfaces:</strong> ${c.interfaces_in_out}</div>
          <div><strong>Scalability & Limits:</strong> ${c.scalability_performance}</div>
          <div><strong>Security & Guardrails:</strong> ${c.security_rai_controls}</div>
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
        <td style="font-size: 0.82rem; color: #cbd5e1;">${c.requirement}</td>
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
        <td style="font-size: 0.82rem; color: #cbd5e1;">${a.statement}</td>
        <td style="font-size: 0.8rem; color: #f87171;">${a.impact_if_wrong}</td>
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
      statusBadge = `<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b; font-size: 0.72rem;">${d.holiday_name || "Statutory Holiday"}</span>`;
      rowBg = "background: rgba(245, 158, 11, 0.05);";
      roleText = "N/A";
      hoursText = "0h";
      taskText = `<span style="color: #f59e0b; font-style: italic;">Statutory Holiday observed — Non-working calendar day</span>`;
    } else if (!d.is_working_day) {
      statusBadge = `<span class="badge" style="background: rgba(148, 163, 184, 0.15); color: #94a3b8; font-size: 0.72rem;">Weekend Off</span>`;
      rowBg = "background: rgba(15, 23, 42, 0.4); opacity: 0.8;";
      roleText = "N/A";
      hoursText = "0h";
      taskText = `<span style="color: var(--text-dim); font-style: italic;">Non-working weekend period</span>`;
    } else {
      const taskList = d.tasks_allocated || [];
      if (taskList.length > 0) {
        taskText = taskList.map(t => `<div style="margin-bottom: 3px;">• <strong>${t.task_name}</strong></div>`).join("");
        roleText = taskList.map(t => t.primary_role).filter(Boolean).join(", ") || "Engineering Team";
      } else {
        taskText = `Deliverable sprint execution for ${d.phase_name}`;
      }
    }

    return `
      <tr style="${rowBg}">
        <td><strong>#${d.day_number}</strong></td>
        <td>
          <div style="font-weight: 600; color: #fff;">${d.date}</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${d.day_name}</div>
        </td>
        <td>
          <span class="badge-ai" style="padding: 2px 6px; font-size: 0.72rem;">${d.phase_code}</span>
          <div style="font-size: 0.78rem; color: #cbd5e1; margin-top: 2px;">${d.phase_name}</div>
        </td>
        <td style="font-size: 0.82rem; color: #cbd5e1;">${taskText}</td>
        <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.72rem;">${roleText}</span></td>
        <td style="font-weight: 600; color: ${d.is_working_day ? 'var(--primary)' : 'var(--text-dim)'};">${hoursText}</td>
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

// Tab Switching
function switchTab(tabId) {
  document.querySelectorAll(".workbench-tabs .tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-pane").forEach(p => p.style.display = "none");
  
  const targetPane = document.getElementById(tabId);
  if (targetPane) targetPane.style.display = "block";
  
  const activeBtn = Array.from(document.querySelectorAll(".workbench-tabs .tab-btn"))
    .find(b => b.getAttribute("onclick").includes(tabId));
  if (activeBtn) activeBtn.classList.add("active");
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
}

async function saveSettingsFromModal() {
  const prov = document.getElementById("modalProviderSelect").value;
  const payload = {
    provider: prov,
    gemini_api_key: document.getElementById("modalGeminiKey").value,
    azure_openai_endpoint: document.getElementById("modalAzureEndpoint").value,
    azure_openai_api_key: document.getElementById("modalAzureKey").value,
    aws_region: document.getElementById("modalAWSRegion").value,
    aws_access_key: document.getElementById("modalAWSAccessKey").value,
    aws_secret_key: document.getElementById("modalAWSSecretKey").value
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

// Admin Console Functions
let cachedAdminCalendars = {};
let isAdminEditMode = false;

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
      banner.innerHTML = "🛡️ <strong>Admin Edit Mode:</strong> You have full administrative privileges to edit location working hours, add statutory holidays, upload holiday sheets, and adjust global rates.";
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
    const rate = cal.hourly_rate || 30.0;
    const hCount = (cal.holidays || []).length;
    return `
      <tr>
        <td><strong>${code}</strong></td>
        <td>${cal.country_name}</td>
        <td>
          <div style="display: flex; align-items: center; gap: 4px;">
            <span style="font-size: 0.8rem; color: var(--text-muted);">$</span>
            <input type="number" step="1.0" id="rate_${code}" class="form-control admin-field" style="width: 75px; padding: 4px 6px; font-size: 0.82rem;" value="${rate}" ${isAdminEditMode ? '' : 'disabled'} onchange="saveLocationCalendar('${code}')">
            <span style="font-size: 0.74rem; color: var(--text-dim);">/hr</span>
          </div>
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 4px;">
            <input type="number" step="0.5" id="hours_${code}" class="form-control admin-field" style="width: 70px; padding: 4px 6px; font-size: 0.82rem;" value="${hours}" ${isAdminEditMode ? '' : 'disabled'} onchange="saveLocationCalendar('${code}')">
            <span style="font-size: 0.74rem; color: var(--text-dim);">hrs</span>
          </div>
        </td>
        <td>${cal.working_days_per_week || 5} d/wk</td>
        <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.75rem;">${hCount} Holidays</span></td>
        <td>
          <button class="btn-header admin-field" style="padding: 3px 8px; font-size: 0.75rem;" ${isAdminEditMode ? '' : 'disabled'} onclick="saveLocationCalendar('${code}')">Save</button>
        </td>
      </tr>
    `;
  }).join("");
}

async function saveLocationCalendar(countryCode) {
  const cal = cachedAdminCalendars[countryCode];
  if (!cal) return;

  const hoursEl = document.getElementById(`hours_${countryCode}`);
  const rateEl = document.getElementById(`rate_${countryCode}`);
  
  const hours = hoursEl ? parseFloat(hoursEl.value) || 8.0 : (cal.daily_working_hours || 8.0);
  const rate = rateEl ? parseFloat(rateEl.value) || 30.0 : (cal.hourly_rate || 30.0);

  try {
    const res = await fetch("/api/admin/calendars", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country_code: countryCode,
        country_name: cal.country_name,
        working_days_per_week: cal.working_days_per_week || 5,
        daily_working_hours: hours,
        hourly_rate: rate,
        annual_holiday_allowance: cal.annual_holiday_allowance || 12
      })
    });
    if (res.ok) {
      cal.daily_working_hours = hours;
      cal.hourly_rate = rate;
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

async function loadProjectHistory() {
  try {
    const res = await fetch("/api/projects/history");
    if (res.ok) {
      const data = await res.json();
      cachedProjectList = data.projects || [];
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

  if (projects.length === 0) {
    container.innerHTML = `<div style="font-size: 0.76rem; color: var(--text-dim); text-align: center; padding: 10px;">No project workspaces found.</div>`;
    return;
  }

  container.innerHTML = projects.map((p, idx) => {
    const isActive = (p.id === currentSessionId || (idx === 0 && !currentSessionId));
    return `
      <div class="project-folder-card ${isActive ? 'active' : ''}" id="folder_card_${p.id}">
        <div class="project-folder-header" onclick="toggleProjectFolder('${p.id}')">
          <div class="project-folder-info">
            <span style="font-size: 0.95rem;">📁</span>
            <div style="min-width: 0;">
              <div class="folder-title-text" title="${p.name}">${p.name}</div>
              <div class="folder-meta">
                <span class="badge-ai" style="padding: 0 4px; font-size: 0.65rem; display: inline-block;">${p.tier}</span>
                <span>• ${p.updated_at}</span>
              </div>
            </div>
          </div>
          <span style="font-size: 0.75rem; color: var(--text-dim); transition: transform 0.2s;" id="chevron_${p.id}">▼</span>
        </div>

        <div class="project-subfiles" id="subfiles_${p.id}" style="${isActive ? 'display: flex;' : 'display: none;'}">
          <div class="project-subfile-link" onclick="loadProjectWorkspace('${p.id}')" title="Load active discovery interview & chat">
            <span>💬 Discovery Chat & Q&A</span>
            <span class="file-type-tag" style="background: rgba(56, 189, 248, 0.15); color: var(--primary);">${p.answers_count} Ans</span>
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
  }).join("");
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
    p.name.toLowerCase().includes(q) ||
    p.client.toLowerCase().includes(q) ||
    p.tier.toLowerCase().includes(q) ||
    p.cloud_platform.toLowerCase().includes(q)
  );
  renderProjectFolders(filtered);
}
