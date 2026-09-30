let currentSessionId = localStorage.getItem("brd_session_id") || "";
let currentSessionData = null;

// Initialize app on load
document.addEventListener("DOMContentLoaded", async () => {
  await loadSettings();
  await initSession();
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
  const container = document.getElementById("quickSuggestions");
  const textInput = document.getElementById("chatInput");
  const numInput = document.getElementById("chatNumberInput");
  const dropdownSelect = document.getElementById("chatDropdownSelect");
  
  if (!container) return;
  container.innerHTML = "";
  
  const curQ = currentSessionData ? currentSessionData.current_question : null;
  if (!curQ) {
    if (textInput) textInput.style.display = "block";
    if (numInput) numInput.style.display = "none";
    if (dropdownSelect) dropdownSelect.style.display = "none";
    return;
  }
  
  if (curQ.type === "dropdown" && curQ.options && curQ.options.length > 0) {
    // Show dropdown selector directly in the input bar
    if (textInput) textInput.style.display = "none";
    if (numInput) numInput.style.display = "none";
    if (dropdownSelect) {
      dropdownSelect.style.display = "block";
      dropdownSelect.innerHTML = "";
      
      curQ.options.forEach((opt) => {
        const op = document.createElement("option");
        op.value = opt.value;
        op.textContent = `${opt.label} ${opt.description ? '— ' + opt.description : ''}`;
        if (opt.value === curQ.default_value) op.selected = true;
        dropdownSelect.appendChild(op);
      });
      dropdownSelect.focus();
    }
    // Redundant dynamic chips removed per user request
    
  } else if (curQ.type === "number") {
    // Show dedicated number input in the input bar
    if (textInput) textInput.style.display = "none";
    if (dropdownSelect) dropdownSelect.style.display = "none";
    if (numInput) {
      numInput.style.display = "block";
      numInput.value = curQ.default_value || "1";
      numInput.placeholder = `Enter number for ${curQ.title} (e.g. ${curQ.default_value})...`;
      numInput.focus();
    }
    
  } else if (curQ.type === "date") {
    // Show date input picker
    if (numInput) numInput.style.display = "none";
    if (dropdownSelect) dropdownSelect.style.display = "none";
    if (textInput) {
      textInput.style.display = "block";
      textInput.type = "date";
      textInput.value = curQ.default_value || "2026-10-05";
      textInput.focus();
    }
    
  } else {
    // Standard Text input
    if (numInput) numInput.style.display = "none";
    if (dropdownSelect) dropdownSelect.style.display = "none";
    if (textInput) {
      textInput.style.display = "block";
      textInput.type = "text";
      textInput.value = "";
      textInput.placeholder = `Type your answer for ${curQ.title}...`;
      textInput.focus();
    }
  }

  // Check if the latest message from agent has interactive follow-up / blueprint options
  const msgs = currentSessionData.messages || [];
  const lastMsg = msgs.length > 0 ? msgs[msgs.length - 1] : null;
  if (lastMsg && lastMsg.hitl_options && lastMsg.hitl_options.length > 0) {
    lastMsg.hitl_options.forEach((opt) => {
      const chip = document.createElement("button");
      chip.className = "suggestion-chip";
      chip.style.cssText = "margin: 4px 6px; padding: 8px 14px; font-size: 0.82rem; border-radius: 12px; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: #fff; cursor: pointer; text-align: left; display: block; width: 100%;";
      chip.innerHTML = `<strong>${opt.label}</strong><br><span style="font-size: 0.76rem; color: var(--text-muted);">${opt.value}</span>`;
      chip.onclick = () => {
        sendMessageWithText(opt.value);
      };
      container.appendChild(chip);
    });
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

function handleInputKeyDown(e) {
  if (e.key === "Enter") {
    sendUserMessage();
  }
}

function handleNumberInputKeyDown(e) {
  if (e.key === "Enter") {
    sendUserMessage();
  }
}

function sendUserMessage() {
  const textInput = document.getElementById("chatInput");
  const numInput = document.getElementById("chatNumberInput");
  const dropdownSelect = document.getElementById("chatDropdownSelect");
  
  let answer = "";
  
  if (dropdownSelect && dropdownSelect.style.display !== "none") {
    answer = dropdownSelect.value;
  } else if (numInput && numInput.style.display !== "none") {
    answer = numInput.value.trim();
  } else if (textInput && textInput.style.display !== "none") {
    answer = textInput.value.trim();
  }
  
  if (!answer && currentSessionData && currentSessionData.current_question) {
    answer = currentSessionData.current_question.default_value;
  }
  
  if (!answer) return;
  
  if (textInput) textInput.value = "";
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
  
  // Top Metrics Strip
  document.getElementById("metricTier").textContent = brd.delivery_tier;
  document.getElementById("metricDuration").textContent = `${brd.total_duration_weeks.toFixed(1)} wks (Headline: ${brd.headline_weight.toFixed(3)})`;
  document.getElementById("metricDays").textContent = `${brd.total_person_days.toFixed(1)} d`;
  document.getElementById("metricHours").textContent = `${brd.total_person_hours.toFixed(0)} Person-Hours`;
  document.getElementById("metricCost").textContent = `$${brd.total_labour_cost_usd.toLocaleString()}`;
  document.getElementById("metricCloudCost").textContent = `$${brd.sizing_metrics.total_monthly_cloud_cost_usd.toLocaleString()}/mo`;
  
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
    rolesTbody.innerHTML = (brd.role_efforts || []).map(r => `
      <tr>
        <td><strong>${r.role_code}</strong></td>
        <td><strong>${r.role}</strong></td>
        <td style="color: var(--text-muted); font-size: 0.8rem;">${r.description}</td>
        <td><strong>${r.days.toFixed(1)} d</strong></td>
        <td>${r.hours.toFixed(0)} h</td>
        <td style="color: var(--success); font-weight: 600;">$${r.cost.toLocaleString()}</td>
        <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.75rem;">${(r.active_fte || r.peak_fte || 0).toFixed(2)} FTE</span></td>
        <td><span style="color: var(--primary); font-size: 0.75rem;">+${(r.buffer_fte || 0).toFixed(2)} FTE</span></td>
        <td><strong style="color: #fff;">${(r.total_assigned_fte || r.peak_fte || 0).toFixed(2)} FTE</strong></td>
      </tr>
    `).join("") + `
      <tr style="background: rgba(56, 189, 248, 0.1); font-weight: bold;">
        <td colspan="3">TOTAL (12 Disciplines Standardized @ $30/hr)</td>
        <td>${brd.total_person_days.toFixed(1)} d</td>
        <td>${brd.total_person_hours.toFixed(0)} h</td>
        <td style="color: var(--success);">$${brd.total_labour_cost_usd.toLocaleString()}</td>
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

  // Tab 5: Sizing & Cloud BoM
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
    bomTbody.innerHTML = (brd.sizing_bom || []).map(b => `
      <tr>
        <td><strong>${b.component}</strong></td>
        <td>${b.sku_or_service}</td>
        <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.72rem;">${b.tier}</span></td>
        <td>${b.quantity}</td>
        <td style="color: var(--success); font-weight: 600;">$${b.monthly_cost_usd.toFixed(2)}</td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${b.justification}</td>
      </tr>
    `).join("");
  }
  const bomTotalBanner = document.getElementById("bomTotalBanner");
  if (bomTotalBanner && sm) bomTotalBanner.textContent = `$${sm.total_monthly_cloud_cost_usd.toFixed(2)} / month`;

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

  setVal("edit_q_client", "q_client", "PVR INOX — Contract Intelligence & Risk Visibility Platform");
  setVal("edit_q_tier", "q_tier", "PoC");
  setVal("edit_q_start_date", "q_start_date", "2026-10-05");
  setVal("edit_q_buffer_strategy", "q_buffer_strategy", "15% Shadow / Backup Capacity (Recommended)");
  setVal("edit_q_problem", "q_problem", "Automate business contract ingestion, risk classification, and clause extraction.");
  setVal("edit_q_duration", "q_duration", "6.0");
  setVal("edit_q_cloud", "q_cloud", "Microsoft Azure");
  setVal("edit_q_geography", "q_geography", "India");
  setVal("edit_q_usecases", "q_usecases", "1");
  setVal("edit_q_personas", "q_personas", "4");
  setVal("edit_q_integrations", "q_integrations", "0");
  setVal("edit_q_datasources", "q_datasources", "2");
  setVal("edit_q_channels", "q_channels", "1");
  setVal("edit_q_languages", "q_languages", "1");
  setVal("edit_q_envs", "q_envs", "3");
  setVal("edit_q_components", "q_components", "6");
  setVal("edit_q_complexity", "q_complexity", "Low");
  setVal("edit_q_compliance", "q_compliance", "Internal policy only");
  setVal("edit_q_security", "q_security", "Standard");
  setVal("edit_q_hadr", "q_hadr", "None (single instance)");
  setVal("edit_q_named_users", "q_named_users", "200");
  setVal("edit_q_concurrent_users", "q_concurrent_users", "50");
  setVal("edit_q_daily_requests", "q_daily_requests", "2000");

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
    q_client: getVal("edit_q_client"),
    q_tier: getVal("edit_q_tier"),
    q_start_date: getVal("edit_q_start_date"),
    q_buffer_strategy: getVal("edit_q_buffer_strategy"),
    q_problem: getVal("edit_q_problem"),
    q_duration: getVal("edit_q_duration"),
    q_cloud: getVal("edit_q_cloud"),
    q_geography: getVal("edit_q_geography"),
    q_usecases: getVal("edit_q_usecases"),
    q_personas: getVal("edit_q_personas"),
    q_integrations: getVal("edit_q_integrations"),
    q_datasources: getVal("edit_q_datasources"),
    q_channels: getVal("edit_q_channels"),
    q_languages: getVal("edit_q_languages"),
    q_envs: getVal("edit_q_envs"),
    q_components: getVal("edit_q_components"),
    q_complexity: getVal("edit_q_complexity"),
    q_compliance: getVal("edit_q_compliance"),
    q_security: getVal("edit_q_security"),
    q_hadr: getVal("edit_q_hadr"),
    q_named_users: getVal("edit_q_named_users"),
    q_concurrent_users: getVal("edit_q_concurrent_users"),
    q_daily_requests: getVal("edit_q_daily_requests")
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

// Export Endpoints
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
    const hCount = (cal.holidays || []).length;
    return `
      <tr>
        <td><strong>${code}</strong></td>
        <td>${cal.country_name}</td>
        <td>
          <input type="number" step="0.5" class="form-control admin-field" style="width: 80px; padding: 4px 8px; font-size: 0.8rem;" value="${hours}" ${isAdminEditMode ? '' : 'disabled'} onchange="saveLocationHours('${code}', this.value)">
        </td>
        <td>${cal.working_days_per_week || 5} d/wk</td>
        <td><span class="badge-ai" style="padding: 2px 6px; font-size: 0.75rem;">${hCount} Holidays</span></td>
        <td>
          <button class="btn-header admin-field" style="padding: 3px 8px; font-size: 0.75rem;" ${isAdminEditMode ? '' : 'disabled'} onclick="saveLocationHours('${code}')">Save</button>
        </td>
      </tr>
    `;
  }).join("");
}

async function saveLocationHours(countryCode, hoursVal) {
  const cal = cachedAdminCalendars[countryCode];
  if (!cal) return;
  const hours = parseFloat(hoursVal) || (cal.daily_working_hours || 8.0);

  try {
    await fetch("/api/admin/calendars", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country_code: countryCode,
        country_name: cal.country_name,
        working_days_per_week: cal.working_days_per_week || 5,
        daily_working_hours: hours,
        annual_holiday_allowance: cal.annual_holiday_allowance || 12
      })
    });
    cal.daily_working_hours = hours;
    await triggerReplan();
  } catch (err) {
    console.error("Failed to save location hours:", err);
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
