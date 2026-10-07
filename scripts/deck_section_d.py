"""
deck_section_d.py
Contains builders for Slides 46 through 56:
- Slide 46: Detailed Work Breakdown Structure (WBS) & Task-Level Effort Justification
- Slide 47: Day-Wise Role Execution Plan (30 Working Days / 6 Weeks Execution Schedule)
- Slide 48: Operational Health Check KPIs, Synthetic Probes & Automated Remediation
- Slide 49: Health Check Technical Architecture & Developer Implementation Guide
- Slide 50: State Management Engine, Finite State Machine (FSM) & Transitions
- Slide 51: Native Azure Services Deep-Dive: Configs, Code Snippets & Cautions
- Slide 52: Reusable Enterprise Assets & Cross-Industry Accelerators
- Slide 53: Comprehensive Bill of Materials (BOM) & Azure Cloud Sizing Model
- Slide 54: Technical Specifications & Agentic Code Prompts for AntiGravity / Claude Code
- Slide 55: Cost-Optimal Architectural Alternatives vs Best Solution (TCO Trade-Off)
- Slide 56: Estimation Dependencies, Prerequisites, Labor Baseline ($30/hr) & Acceptance Criteria
"""

import os
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

from build_deck_helpers import (
    create_base_slide, add_card, add_table, add_kpi_metric, add_image_slide,
    BG_LIGHT, CARD_BG, CARD_BORDER, TEXT_DARK, TEXT_SUB, TEXT_MUTED,
    BLUE_PRIMARY, EMERALD_SUCCESS, AMBER_WARN, PURPLE_ACCENT, RED_ALERT
)

def build_slides_46_to_56(prs):
    print("Building Slides 46 to 56 (Section D)...")

    # =========================================================================
    # SLIDE 46 (Topic 32): Work Breakdown Structure (WBS) & Effort Justification
    # =========================================================================
    s46 = create_base_slide(
        prs, 46, "Work Breakdown Structure (WBS) & Effort Justification (Topic 32)",
        "Granular task-level effort allocation across all engineering roles; labor calculated at $30/hr blended baseline",
        "Section 30: Project Work Breakdown",
        {
            "logic": "Provides transparent engineering justification for the 162 person-day / $38,880 PoC baseline estimate.",
            "designs": "Tabular work breakdown structure detailing WBS Task, Assigned Role, Days, Total Hours, Labor Cost, and Justification.",
            "highlights": "Every task is bound to a single specialized engineering role; hourly labor cost strictly fixed at $30.00/hr ($240/day).",
            "details": "Covers Ingestion, AI Prompting, Machine Learning, Backend Services, Frontend UI, Cloud Infra, and Responsible AI."
        }
    )
    add_table(s46, 0.8, 1.5, 11.7, 5.1,
        ["WBS ID", "WBS Task Description", "Assigned Role", "Days", "Hours", "Labor Cost ($30/hr)", "Effort Justification & Complexity Driver"],
        [
            ["WBS-01", "Azure Landing Zone & Key Vault Setup", "Cloud Engineer", "12 d", "96 h", "$2,880", "VNet, Managed Identity, Event Grid, and subscription isolation."],
            ["WBS-02", "Doc Intelligence Ingestion & Chunking", "Data Engineer", "14 d", "112 h", "$3,360", "Prebuilt layout parsing, 72-DPI coordinate recovery, clause chunking."],
            ["WBS-03", "Hybrid Vector Indexing & Schema Tuning", "Data Engineer", "12 d", "96 h", "$2,880", "Azure AI Search index schema, 1536d embeddings, BM25 tuning."],
            ["WBS-04", "Prompt-Based Classification Pipeline", "AI Engineer", "10 d", "80 h", "$2,400", "Few-shot prompt calibration, temperature 0.0, category routing."],
            ["WBS-05", "Multi-Pass Clause Extraction Engine", "AI Engineer", "22 d", "176 h", "$5,280", "Pass 1 broad extraction + Pass 2/3 targeted ambiguity resolver."],
            ["WBS-06", "Benchmark Curation & Accuracy Evals", "ML Engineer", "14 d", "112 h", "$3,360", "Gold-standard test set scoring, precision/recall metric harness."],
            ["WBS-07", "FastAPI Orchestrator & State Engine", "Fullstack Developer", "16 d", "128 h", "$3,840", "Service Bus queue listener, multi-pass loop, SQL persistence."],
            ["WBS-08", "Excel Register Export Engine", "Fullstack Developer", "12 d", "96 h", "$2,880", "OpenPyXL generator preserving legacy spreadsheet columns."],
            ["WBS-09", "Risk Visibility React Cockpit UI", "UI Developer", "22 d", "176 h", "$5,280", "Interactive PDF.js side-by-side coordinate overlay cockpit."],
            ["WBS-10", "Responsible AI & Groundedness Checks", "RAI Specialist", "16 d", "128 h", "$3,840", "Content Safety, hallucination prevention, legal review gates."],
            ["WBS-11", "Observability, Telemetry & Canaries", "Cloud Engineer", "12 d", "96 h", "$2,880", "App Insights, token tracking, synthetic hourly canary probes."],
            ["TOTAL", "Phase 1 (PoC Baseline) Delivery", "7 Engineering Roles", "162 d", "1,296 h", "$38,880", "Comprehensive 6-week delivery across all 42 requirements."]
        ],
        col_widths=[0.8, 2.7, 1.6, 0.6, 0.7, 1.4, 3.9]
    )

    # =========================================================================
    # SLIDE 47 (Topic 33): Day-Wise Role Execution Plan (30 Working Days)
    # =========================================================================
    s47 = create_base_slide(
        prs, 47, "Day-Wise Role Execution Plan Across 30 Working Days / 6 Weeks (Topic 33)",
        "Daily task roadmap detailing what each engineering role executes across the 6-week project schedule",
        "Section 31: Project Schedule",
        {
            "logic": "Provides program managers and technical leads with a day-by-day operational execution roadmap for each engineering role.",
            "designs": "Tabular week-by-week and day-by-day activity grid mapping all 7 specialized engineering roles to their deliverables.",
            "highlights": "Structured into 3 two-week sprints: Foundation (W1-2), Core Build (W3-4), and Hardening/Sign-off (W5-6).",
            "details": "Ensures no role idle time; manages critical path dependencies between Data, AI, Backend, and Frontend teams."
        }
    )
    add_table(s47, 0.8, 1.5, 11.7, 5.1,
        ["Timeline / Sprint", "Cloud Engineer", "Data Engineer", "AI Engineer", "ML Engineer", "Fullstack Dev", "UI Developer", "RAI Specialist"],
        [
            ["Week 1 (Days 1–5)\nPlatform & Intake", "Provision Landing Zone, Key Vault, and Blob containers", "Establish Blob intake, inspect sample PDF layouts", "Review clause lists, draft classification prompts", "Define evaluation metrics and baseline criteria", "Design FastAPI API contracts & schemas", "Build UI skeleton and React design tokens", "Draft RAI policy and Groundedness metrics"],
            ["Week 2 (Days 6–10)\nParsing & Indexing", "Configure Managed ID, Event Grid, & Service Bus", "Deploy Doc Intel Layout parser, build chunking logic", "Test prompt classification across 6 categories", "Curate 60-document ground truth benchmark", "Implement Service Bus ingestion queue consumer", "Develop portfolio risk overview mockups", "Define content safety and PII masking rules"],
            ["Week 3 (Days 11–15)\nPass 1 Reasoning", "Scale Container Apps & configure VNet integration", "Build Azure AI Search index & 1536d vector pipeline", "Deploy Pass 1 broad clause extraction agent", "Execute baseline Pass 1 benchmark scoring", "Implement relational Azure SQL findings schema", "Build split-screen PDF.js viewer with coords", "Implement hallucination refusal policies"],
            ["Week 4 (Days 16–20)\nMulti-Pass & Rules", "Configure OpenAI TPM throttling alerts & jitter", "Tune hybrid retrieval (BM25 + Semantic rerank)", "Deploy Pass 2/3 targeted ambiguity resolver", "Measure Pass 2 recall gains (+12.4% uplift)", "Build state management FSM & pass scheduler", "Implement coordinate bounding box highlights", "Audit rationale groundedness (≥90% bar)"],
            ["Week 5 (Days 21–25)\nUI Integration & HITL", "Configure App Service SSL & Entra ID SSO", "Validate end-to-end data pipeline integrity", "Calibrate Principle Assessment rule engine", "Perform end-to-end ground truth validation", "Build Excel risk register export engine", "Wire HITL review actions (Approve, Override)", "Verify human review audit logging & trail"],
            ["Week 6 (Days 26–30)\nCanaries & Sign-off", "Deploy synthetic canaries & App Insights alerts", "Run final 600-contract historical batch intake", "Finalize prompts & freeze configuration", "Publish formal Benchmark Accuracy Report", "Conduct end-to-end integration regression", "Final polish on demonstration dashboard", "Deliver RAI compliance sign-off report"]
        ],
        col_widths=[1.5, 1.4, 1.5, 1.5, 1.4, 1.5, 1.5, 1.4]
    )

    # =========================================================================
    # SLIDE 48 (Topic 34): Operational Health Check KPIs & Synthetic Probes
    # =========================================================================
    s48 = create_base_slide(
        prs, 48, "Operational Health Check KPIs & Synthetic Probes (Topic 34)",
        "Real-time operational monitoring metrics, automated canary probes, and self-healing cloud incident triggers",
        "Section 32: System Health",
        {
            "logic": "Enterprise production solutions require continuous autonomous health monitoring to guarantee 99.9% availability and accuracy.",
            "designs": "Four operational health cards covering Health KPI Metrics, Synthetic Canary Probes, Incident Triggers, and Self-Healing Rules.",
            "highlights": "Executes hourly synthetic contract runs to detect prompt drift or OpenAI service degradation before users notice.",
            "details": "Includes circuit breakers, exponential retry with jitter, and automated failover between India Central and India South."
        }
    )
    add_card(s48, 0.8, 1.5, 2.75, 5.1, "1. Core Health KPIs", [
        "• API Uptime: ≥ 99.9% availability across all microservices.",
        "• P95 End-to-End Latency: < 48 seconds per 50-page contract.",
        "• Azure OpenAI TPM Utilization: Maintained between 40% and 75%.",
        "• HTTP 429 Throttle Rate: < 0.5% of total API calls.",
        "• Doc Intelligence Success: ≥ 99.5% successful layout extractions.",
        "• SQL Connection Pool: < 40% active DTU utilization."
    ], header_color=BLUE_PRIMARY)

    add_card(s48, 3.8, 1.5, 2.75, 5.1, "2. Synthetic Canary Probes", [
        "• Hourly Synthetic Contract Run: Azure Functions injects a calibrated dummy contract every 60 minutes.",
        "• Ground Truth Verification: Verifies that classification and extracted clauses match expected gold values 100%.",
        "• Latency Benchmark: Flags probe if execution takes > 60 seconds.",
        "• Silent Failure Detection: Catches hidden token format changes or model API deprecations instantly.",
        "• Automated Alerting: Dispatches instant P1 incident to Ops on failure."
    ], header_color=EMERALD_SUCCESS)

    add_card(s48, 6.8, 1.5, 2.75, 5.1, "3. Automated Incident Triggers", [
        "• Trigger A (Groundedness Drift): If canary groundedness drops below 92%, freeze auto-exports and alert Legal Ops.",
        "• Trigger B (OpenAI 429 Surge): If throttling exceeds 3 errors/min, activate queue backoff and throttle batch intake.",
        "• Trigger C (OCR Degradation): If OCR confidence drops < 70% on >5 consecutive docs, switch to secondary endpoint.",
        "• Trigger D (Dead-Letter Surge): If Service Bus dead-letters > 10 messages, trigger alert to on-call Cloud Engineer."
    ], header_color=AMBER_WARN)

    add_card(s48, 9.8, 1.5, 2.75, 5.1, "4. Self-Healing Runbooks", [
        "• Circuit Breaker Pattern: Temporarily trips queue consumption on downstream 500 errors to allow recovery.",
        "• Exponential Jitter Retry: Retries failed calls at 1s, 2s, 4s, 8s intervals with randomized millisecond jitter.",
        "• Dynamic Replicas: Container Apps autoscale from 1 to 5 instances when Service Bus queue backlog exceeds 50 messages.",
        "• Database Auto-Failover: Azure SQL geo-replica in India South initiates auto-failover on unresolvable primary outage."
    ], header_color=PURPLE_ACCENT)

    # =========================================================================
    # SLIDE 49 (Topic 35): Health Check Technical Architecture & Implementation
    # =========================================================================
    s49 = create_base_slide(
        prs, 49, "Health Check Technical Architecture & Developer Implementation (Topic 35)",
        "Granular developer blueprint for building health check probes, App Insights telemetry, and alert webhooks",
        "Section 32: System Health",
        {
            "logic": "Provides developers with concrete code snippets, endpoint definitions, and App Insights queries to build the health system.",
            "designs": "Three developer implementation cards covering Health Endpoints (/health), Telemetry Instrumentation, and Alert Webhooks.",
            "highlights": "Distinguishes liveness probes (/health/live) from deep dependency readiness probes (/health/ready).",
            "details": "Includes Kusto Query Language (KQL) queries for monitoring Azure OpenAI token consumption and P95 latency."
        }
    )
    add_card(s49, 0.8, 1.5, 3.7, 5.1, "1. Health Endpoints Implementation", [
        "• Liveness Probe: GET /api/v1/health/liveness -> Returns HTTP 200 OK if Container App process is alive.",
        "• Readiness Probe: GET /api/v1/health/readiness -> Performs live ping to Azure SQL, AI Search, and Key Vault.",
        "• Canary Trigger: POST /api/v1/health/canary/run -> Executes end-to-end evaluation contract and validates scores.",
        "• Code Pattern (FastAPI):",
        "  @app.get('/health/ready')\n  async def readiness():\n      db_ok = check_sql_connection()\n      search_ok = check_search_index()\n      if not (db_ok and search_ok):\n          raise HTTPException(status_code=503)"
    ], header_color=BLUE_PRIMARY)

    add_card(s49, 4.8, 1.5, 3.7, 5.1, "2. App Insights & KQL Monitoring", [
        "• Telemetry SDK: azure-monitor-opentelemetry Python package.",
        "• Custom Dimensions: DocId, Category, ExtractionPass, TokensConsumed, GroundednessScore, LatencyMs.",
        "• KQL Query - OpenAI TPM Consumption:",
        "  customEvents\n  | where name == 'OpenAICall'\n  | summarize TotalTokens = sum(todouble(customDimensions.TotalTokens))\n    by bin(timestamp, 1m)\n  | render timechart",
        "• KQL Query - High Latency Contracts (>60s):\n  requests\n  | where duration > 60000 and success == true\n  | project timestamp, id, duration, customDimensions.DocId"
    ], header_color=PURPLE_ACCENT)

    add_card(s49, 8.8, 1.5, 3.7, 5.1, "3. Alert Rules & Webhook Routing", [
        "• Action Groups: ag-contract-ops-p1 (SMS, PagerDuty, Slack, Teams).",
        "• Alert Metric 1: Http429Rate > 1% in 5 min window -> Severity 2 (Warning).",
        "• Alert Metric 2: CanaryGroundingScore < 0.90 -> Severity 1 (Critical).",
        "• Alert Metric 3: DeadLetterCount > 5 in Service Bus -> Severity 2 (Warning).",
        "• Automated Webhook Payload: Sends JSON event with DocId, stack trace, and Azure Portal runbook link directly to Ops channel."
    ], header_color=AMBER_WARN)

    # =========================================================================
    # SLIDE 50 (Topic 36): State Management Engine & FSM Transitions
    # =========================================================================
    s50 = create_base_slide(
        prs, 50, "State Management Engine: Finite State Machine (FSM) & Transitions (Topic 36)",
        "Formal lifecycle state machine defining contract business states, technical handlers, and rollback rules",
        "Section 33: State Management",
        {
            "logic": "Complex multi-pass batch pipelines require deterministic state management so interrupted batches resume without re-work.",
            "designs": "Full-width editable table detailing State Name, Business Function, Responsible Component, Trigger, and Rollback Policy.",
            "highlights": "Nine distinct states from INGESTED to REVIEWED; idempotent retries ensure zero duplicate billing or re-extraction.",
            "details": "State transitions persisted transactionally in Azure SQL Contracts table with optimistic concurrency control."
        }
    )
    add_table(s50, 0.8, 1.5, 11.7, 5.1,
        ["State Name", "Business Function", "Technical Component", "Entry Trigger", "Exit Condition", "Rollback / Error Policy"],
        [
            ["01. INGESTED", "Raw PDF landing in storage", "Azure Blob Storage", "User/Batch upload completes", "BlobCreated event emitted", "Purge corrupt blob on checksum mismatch"],
            ["02. PARSED", "Layout & table coordinate recovery", "Azure AI Doc Intelligence", "Dispatcher consumes message", "Layout JSON stored in blob", "Retry up to 3 times; else route to EXCEPTIONS"],
            ["03. INDEXED", "Semantic chunking & vector embed", "Azure AI Search", "Parsing completes", "Vectors indexed in AI Search", "Re-index chunk batch on network failure"],
            ["04. CLASSIFIED", "Assigning 1 of 6 contract domains", "Classification Agent (GPT-4o)", "Chunks indexed", "Category tag & conf emitted", "If conf < 0.85 -> UNCLASSIFIED_TRIAGE"],
            ["05. EXTRACTED_P1", "Broad baseline clause extraction", "Extraction Agent (Pass 1)", "Category schema bound", "Standard clauses validated", "Retry schema failure with repaired prompt"],
            ["06. EXTRACTED_MULTI", "Targeted ambiguity deep-dive", "Orchestrator + OpenAI (P2/P3)", "Pass 1 leaves terms empty", "All terms resolved or max 3 passes", "If pass_count >= 3 -> FLAG_UNRESOLVED"],
            ["07. ASSESSED", "Contracting principle evaluation", "Assessment Agent (GPT-4o)", "Clauses extracted", "Agree/Warn/Reject synthesized", "Mark unsupported if rationale lacks citation"],
            ["08. COMMITTED", "Risk register persistence", "Azure SQL Database", "Assessment completes", "Rows written to ContractFindings", "Database rollback on transaction abort"],
            ["09. REVIEWED", "Legal counsel approval sign-off", "App Service (Cockpit UI)", "Legal counsel clicks Confirm", "Audit log record committed", "Can re-open review with written justification"]
        ],
        col_widths=[1.6, 2.0, 2.0, 1.7, 2.2, 2.2]
    )

    # =========================================================================
    # SLIDE 51 (Topic 37): Native Azure Services Deep-Dive
    # =========================================================================
    s51 = create_base_slide(
        prs, 51, "Native Azure Services Deep-Dive: Configurations & Best Practices (Topic 37)",
        "Why native Azure services were selected, configuration blueprints, IAM permissions, and key operational cautions",
        "Section 34: Cloud Services",
        {
            "logic": "Provides enterprise architecture governance with clear justifications, IAM scopes, and cautions for each Azure PaaS service.",
            "designs": "Four structured service deep-dive cards covering Azure Blob, Doc Intelligence, Azure AI Search, and Azure OpenAI.",
            "highlights": "Focuses on private networking, zero-trust Managed Identity, and avoiding vendor lock-in traps.",
            "details": "Includes critical cautions such as regional TPM quota limits, document page size caps, and index replica sizing."
        }
    )
    add_card(s51, 0.8, 1.5, 2.75, 5.1, "1. Azure Blob Storage", [
        "• Why This Service: 99.999999999% durability, native WORM immutability, sub-100ms latency.",
        "• Configuration: Hot Tier, Hierarchical Namespace, Soft Delete 14 days, TLS 1.3 enforced.",
        "• IAM Role: Storage Blob Data Contributor assigned to Container App Managed Identity.",
        "• Code Pattern: DefaultAzureCredential() without hardcoded storage keys.",
        "• Key Caution: Disable public network access; enforce Private Endpoints to prevent accidental exposure."
    ], header_color=BLUE_PRIMARY)

    add_card(s51, 3.8, 1.5, 2.75, 5.1, "2. Azure AI Doc Intelligence", [
        "• Why This Service: Prebuilt Layout API recovers tables and exact bounding boxes deterministically.",
        "• Configuration: Standard S0 tier, prebuilt-layout v2024-02-29-preview, India Central.",
        "• IAM Role: Cognitive Services User role on resource group.",
        "• Code Pattern: poller.result().paragraphs[i].bounding_regions.",
        "• Key Caution: Max document size 500MB / 2,000 pages; split massive contract bundles if necessary."
    ], header_color=PURPLE_ACCENT)

    add_card(s51, 6.8, 1.5, 2.75, 5.1, "3. Azure AI Search", [
        "• Why This Service: Native hybrid retrieval combining BM25 keyword matching and vector search.",
        "• Configuration: Standard S1 tier (1 partition, 2 replicas for HA in UAT/Prod).",
        "• IAM Role: Search Index Data Contributor assigned to Orchestrator.",
        "• Code Pattern: Hybrid query with Semantic Reranker priority.",
        "• Key Caution: Basic tier lacks semantic reranking; use Standard S1 minimum for legal RAG accuracy."
    ], header_color=AMBER_WARN)

    add_card(s51, 9.8, 1.5, 2.75, 5.1, "4. Azure OpenAI Service", [
        "• Why This Service: Enterprise sovereign hosting of GPT-4o with zero model training on customer data.",
        "• Configuration: Pay-As-You-Go with TPM quota reserve in India Central region.",
        "• IAM Role: Cognitive Services OpenAI User role.",
        "• Code Pattern: client.beta.chat.completions.parse(response_format=PydanticModel).",
        "• Key Caution: Non-prod TPM quotas can be constrained; enforce exponential backoff with jitter."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 52 (Topic 38): Reusable Enterprise Assets & Cross-Industry Components
    # =========================================================================
    s52 = create_base_slide(
        prs, 52, "Reusable Enterprise Assets & Cross-Industry Accelerators (Topic 38)",
        "Modular components designed as reusable IP to accelerate future use cases and client engagements",
        "Section 35: Reusable Assets",
        {
            "logic": "Demonstrates forward-looking architectural value by creating modular IP that can be reused across banking, healthcare, and retail.",
            "designs": "Four reusable asset cards covering Ingestion Framework, Multi-Pass Prompt Engine, Principle Rule Engine, and PDF Viewer.",
            "highlights": "Reduces future document intelligence project build times by 40-50% through pre-built modular components.",
            "details": "Packaged as reusable Python libraries, React npm packages, and Terraform infrastructure-as-code modules."
        }
    )
    add_card(s52, 0.8, 1.5, 2.75, 5.1, "1. Ingestion Accelerator", [
        "• Asset: Layout-Aware Chunking & Coordinate Mapper (Python library).",
        "• Reusability: Parses any complex PDF document (insurance policies, loan agreements, clinical trials) into 512-token chunks with bounding boxes.",
        "• Value: Saves 3 weeks engineering effort on any document AI engagement.",
        "• Packaging: Modular Python wheel ready for PyPI or internal enterprise artifact repo."
    ], header_color=BLUE_PRIMARY)

    add_card(s52, 3.8, 1.5, 2.75, 5.1, "2. Multi-Pass Prompt Engine", [
        "• Asset: Pass-Aware Orchestration Engine (FastAPI microservice).",
        "• Reusability: Handles ambiguous, open-textured entity extraction across regulatory filings, ESG reports, and procurement RFP bids.",
        "• Value: Solves single-pass hallucination limits across all structured document extraction projects.",
        "• Packaging: Docker container image deployable to Azure Container Apps or AWS ECS."
    ], header_color=PURPLE_ACCENT)

    add_card(s52, 6.8, 1.5, 2.75, 5.1, "3. Principle Assessment Framework", [
        "• Asset: Declarative Policy & Principle Rule Engine (Python + SQL).",
        "• Reusability: Decouples business compliance rules from AI model logic; allows non-technical legal/compliance teams to edit rules in SQL.",
        "• Value: Eliminates code deployments for risk threshold changes across banking, retail, and insurance.",
        "• Packaging: Standalone policy evaluation microservice with REST API."
    ], header_color=AMBER_WARN)

    add_card(s52, 9.8, 1.5, 2.75, 5.1, "4. Coordinate PDF Viewer UI", [
        "• Asset: Side-by-Side Highlight Cockpit (React UI Component).",
        "• Reusability: Plugs into any React web application to render instant bounding-box highlight overlays on PDF documents via normalized coordinates.",
        "• Value: Saves 4 weeks frontend engineering; provides instant audit credibility.",
        "• Packaging: Reusable npm package with customizable color themes."
    ], header_color=EMERALD_SUCCESS)

    # =========================================================================
    # SLIDE 53 (Topic 39): Comprehensive Bill of Materials (BOM) & Cloud Sizing
    # =========================================================================
    s53 = create_base_slide(
        prs, 53, "Bill of Materials (BOM) & Azure Cloud Operating Sizing Model (Topic 39)",
        "Itemized cloud infrastructure, PaaS services, and model token costs across Phase 1 PoC and Enterprise Production",
        "Section 36: Sizing & Cost",
        {
            "logic": "Provides procurement and finance with an itemized, formula-driven Bill of Materials for both Phase 1 and Live Production.",
            "designs": "Tabular BOM matrix detailing Service Name, SKU Tier, Quantity, PoC Monthly Cost, and Production Monthly Cost.",
            "highlights": "Phase 1 cloud spend estimated at $1,420/month; Full Production operating cost sized at $4,850/month for 50,000 contracts.",
            "details": "Azure OpenAI sized at $0.005/1k prompt tokens and $0.015/1k completion tokens based on India Central commercial rate card."
        }
    )
    add_table(s53, 0.8, 1.5, 11.7, 5.1,
        ["Azure Service Component", "Selected SKU Tier", "Unit Sizing / Drivers", "PoC Monthly Cost", "Prod Monthly Cost", "Cost Optimization Notes"],
        [
            ["Azure Blob Storage", "Standard Hot LRS / ZRS", "50 GB (PoC) / 1.0 TB (Prod)", "$15.00", "$48.00", "Lifecycle tiering moves aged contracts to Cool/Archive tier after 90 days."],
            ["Azure AI Doc Intelligence", "Standard S0 (Layout API)", "600 docs (PoC) / 5,000 docs/mo (Prod)", "$60.00", "$450.00", "Billed at $10.00 per 1,000 pages parsed; highly cost-effective OCR."],
            ["Azure OpenAI Service", "GPT-4o & GPT-4o mini", "2,000 req/day; avg 2.5k tokens", "$480.00", "$1,650.00", "Multi-pass caching and prompt compression save 35% token overhead."],
            ["Azure AI Search", "Standard S1 / Standard S2", "1 Replica (PoC) / 3 Replicas Multi-AZ", "$245.00", "$980.00", "Indexes 24,000 chunks; Standard tier required for semantic reranker."],
            ["Azure Container Apps", "Consumption / Dedicated", "0-2 vCPU (PoC) / 4-10 vCPU (Prod)", "$85.00", "$320.00", "Scales to zero replicas when idle; eliminates paying for unused VM compute."],
            ["Azure SQL Database", "Serverless / General Purpose", "2 vCores (PoC) / 4 vCores HA (Prod)", "$120.00", "$480.00", "Auto-pause enabled in Dev/SIT; Reserved Capacity saves 38% in Prod."],
            ["Azure App Service (UI)", "Linux B1 / Standard S1", "1 Instance (PoC) / 2 Instances (Prod)", "$55.00", "$140.00", "Hosts React frontend behind Entra ID SSO and Azure Front Door."],
            ["Azure Key Vault & Monitor", "Standard / App Insights", "Logs + Secrets + Telemetry", "$65.00", "$180.00", "30-day log retention in Dev; 90-day retention with cold archive in Prod."],
            ["Azure Virtual Network / NAT", "Standard NAT Gateway", "Private Endpoints + Egress", "$45.00", "$145.00", "Guarantees zero public internet exposure for internal microservices."],
            ["Network Egress & Bandwidth", "Standard Data Transfer", "PDF streaming & UI downloads", "$20.00", "$65.00", "Intra-region data transfer is free; egress applies to external user views."],
            ["TOTAL MONTHLY AZURE OPEX", "All Native Azure Services", "Full 6-Category Platform Footprint", "$1,190.00", "$4,458.00", "Excludes labor; provides 30% headroom for annual volume growth."]
        ],
        col_widths=[2.4, 2.1, 2.4, 1.3, 1.4, 2.1]
    )

    # =========================================================================
    # SLIDE 54 (Topic 40): Technical Specifications & Agentic Code Prompts
    # =========================================================================
    s54 = create_base_slide(
        prs, 54, "Technical Specifications & Agentic Prompts for Developers & AntiGravity (Topic 40)",
        "Production prompt templates, system instructions, and JSON schemas for developers and AI coding agents",
        "Section 37: Technical Specifications",
        {
            "logic": "Provides developers and automated AI tools (AntiGravity / Claude Code) with exact system prompts and Pydantic models.",
            "designs": "Three structured prompt specification cards covering Classification Prompt, Multi-Pass Extraction, and Principle Evaluator.",
            "highlights": "Includes complete system prompts, few-shot examples, JSON schema constraints, and temperature settings.",
            "details": "Ready for direct copy-paste into Azure AI Foundry prompt playgrounds or FastAPI codebases."
        }
    )
    add_card(s54, 0.8, 1.5, 3.7, 5.1, "1. Classification System Prompt", [
        "• System Instruction:\n  'You are an expert contract taxonomist. Classify the contract into exactly ONE of the following 6 categories:\n  - COMMERCIAL_LEASE\n  - EQUIPMENT_VENDOR\n  - PROFESSIONAL_SERVICES\n  - FACILITIES_AMC\n  - TECHNOLOGY_SOFTWARE\n  - MARKETING_CONCESSION\n  Return JSON conforming to ContractCategorySchema.'",
        "• Output Model:\n  {\n    \"category\": \"COMMERCIAL_LEASE\",\n    \"confidence\": 0.98,\n    \"justification\": \"Parties identified as Landlord and Tenant; preamble references commercial multiplex retail lease premises.\"\n  }",
        "• Parameter Settings: Model: gpt-4o-mini; Temperature: 0.0; MaxTokens: 300."
    ], header_color=BLUE_PRIMARY)

    add_card(s54, 4.8, 1.5, 3.7, 5.1, "2. Pass 2 Targeted Prompt", [
        "• Context Injection: Injects top-k candidate chunks + target clause name + definition.",
        "• System Instruction:\n  'You are a specialized legal clause extractor. Locate and extract the target clause: \"Revenue Share Escalator Cap\". If ambiguous, analyze annexures. Return exact verbatim text and normalized numerical cap percentage. Do NOT invent values. If absent, set is_found=false.'",
        "• Pydantic Output:\n  {\n    \"clause_name\": \"Revenue Share Escalator Cap\",\n    \"is_found\": true,\n    \"verbatim_text\": \"...escalation clause shall be strictly capped at 4.5%...\",\n    \"normalized_value\": \"4.5%\",\n    \"page_number\": 14,\n    \"extraction_pass\": 2\n  }"
    ], header_color=PURPLE_ACCENT)

    add_card(s54, 8.8, 1.5, 3.7, 5.1, "3. Principle Evaluator Prompt", [
        "• System Instruction:\n  'Compare extracted clause against contracting rule PR-LSE-03: Minimum 7.0% escalator required. Cap < 4.0% is Strictly Rejected; Cap 4.0%-6.9% requires CFO Approval. Evaluate compliance status and provide concise rationale citing source text.'",
        "• Model Output:\n  {\n    \"principle_id\": \"PR-LSE-03\",\n    \"status\": \"AGREE_WITH_MANAGEMENT_APPROVAL\",\n    \"severity\": \"MODERATE\",\n    \"escalation_role\": \"CHIEF_FINANCIAL_OFFICER\",\n    \"rationale\": \"Cap of 4.5% falls below 7.0% baseline standard but exceeds critical 4.0% rejection floor. Requires CFO waiver.\"\n  }"
    ], header_color=AMBER_WARN)

    # =========================================================================
    # SLIDE 55 (Topic 41): Cost-Optimal Architectural Alternatives vs Best Solution
    # =========================================================================
    s55 = create_base_slide(
        prs, 55, "Cost-Optimal Architectural Alternatives vs Best Solution (Topic 41)",
        "Comparative architectural analysis evaluating best-in-class performance vs cost-optimized options and trade-offs",
        "Section 38: Architectural Trade-Offs",
        {
            "logic": "Enables executive leadership and enterprise architects to evaluate trade-offs between performance and cloud spend.",
            "designs": "Comprehensive tabular trade-off matrix detailing Architecture Tier, Best-in-Class Option, Cost-Optimal Alternative, Savings, and Limitations.",
            "highlights": "Cost-optimal architecture saves up to 42% cloud spend ($1,850/mo reduction) with minor acceptable trade-offs in edge latency.",
            "details": "Details decisions regarding GPT-4o vs mini, Container Apps vs AKS, Serverless SQL vs Business Critical, and AI Search tiers."
        }
    )
    add_table(s55, 0.8, 1.5, 11.7, 5.1,
        ["Architecture Tier", "Best-in-Class Production Solution", "Cost-Optimal Technical Alternative", "Potential Monthly Savings", "Trade-off & Technical Limitations"],
        [
            ["LLM Inference Engine", "Azure OpenAI GPT-4o for all extraction & evaluation passes", "GPT-4o mini for Pass 1 + GPT-4o strictly for Pass 2/3 and evals", "Save $650 / month (-40% LLM cost)", "Acceptable: Mini handles 80% standard clauses; full GPT-4o reserved for difficult edge cases."],
            ["Vector & Search Tier", "Azure AI Search Standard S2 (Multi-AZ, 3 replicas, high QPS)", "Azure AI Search Standard S1 (1 replica with auto-scaling)", "Save $520 / month (-53% search cost)", "Limitation: 99.9% SLA vs 99.95%; slightly higher P95 query latency under peak concurrent batch load."],
            ["Relational Database", "Azure SQL Business Critical (Active Geo-Replication in South)", "Azure SQL General Purpose Serverless (Auto-Pause enabled)", "Save $360 / month (-60% DB cost)", "Limitation: 30-second cold start delay after 1 hr idle time; manual failover to secondary region."],
            ["Microservices Compute", "Azure Kubernetes Service (AKS) Multi-AZ Cluster", "Azure Container Apps (Serverless Consumption 0-5 replicas)", "Save $450 / month (-65% compute cost)", "Trade-off: Minimal. Container Apps is simpler to manage and scales to zero when no batches are running."],
            ["Document OCR Engine", "Dedicated Azure AI Doc Intelligence S0 with Private Link", "Multi-tenant shared Doc Intelligence endpoint with HTTPS", "Save $120 / month (-25% OCR cost)", "Limitation: Relies on public IP filtering rather than full Private Endpoint VNet isolation."],
            ["OVERALL COMPARISON", "Best Enterprise Solution: $4,458 / month\n(Maximum HA, Zero Cold Starts, Sub-30s Latency)", "Cost-Optimal Architecture: $2,580 / month\n(42% Net Monthly Cloud Cost Reduction)", "Total Savings: $1,878 / month\n($22,536 / year)", "Recommendation: Deploy Cost-Optimal architecture for Phase 1 & 2; uplift to Best Solution for enterprise scale."]
        ],
        col_widths=[1.8, 2.6, 2.7, 1.8, 2.8]
    )

    # =========================================================================
    # SLIDE 56 (Topic 42): Estimation Dependencies, Prerequisites & Labor Baseline
    # =========================================================================
    s56 = create_base_slide(
        prs, 56, "Estimation Dependencies, Prerequisites & $30/hr Labor Baseline (Topic 42)",
        "Definitive governance assumptions, acceptance gates, and formula-driven labor calculations for program commitment",
        "Section 39: Program Commitment",
        {
            "logic": "Provides clear commercial and operational boundary conditions under which the estimates and delivery commitments are valid.",
            "designs": "Three comprehensive governance cards covering Labor Costing Baseline ($30/hr), Critical Prerequisites, and Gate Criteria.",
            "highlights": "Every labor hour is audited against the $30/hr blended baseline; ties project completion directly to measurable acceptance criteria.",
            "details": "Customer attestation of prerequisites required prior to Sprint 1 kick-off to ensure project velocity."
        }
    )
    add_card(s56, 0.8, 1.5, 3.7, 5.1, "1. Labor Costing Baseline ($30/hr)", [
        "• Blended Hourly Rate: Exactly $30.00 / hour across all engineering roles (AI, ML, Cloud, Fullstack, UI, Data, RAI).",
        "• Daily Rate Standard: 8 working hours/day = $240.00 / person-day.",
        "• Phase 1 PoC Commitment: 162 person-days = 1,296 hours = $38,880 total labor.",
        "• Full Production Delivery: 561 person-days = 4,488 hours = $134,640 total labor.",
        "• Role Demarcation: AI Engineer builds prompts/agents; ML Engineer handles benchmark evals; Fullstack/UI build apps; Cloud Engineer manages Azure."
    ], header_color=BLUE_PRIMARY)

    add_card(s56, 4.8, 1.5, 3.7, 5.1, "2. Program Dependencies & Blockers", [
        "• Prerequisite 1: Azure non-production subscription provisioned with minimum 100k TPM OpenAI quota headroom before Day 1.",
        "• Prerequisite 2: Representative sample of 600 executed contracts deposited in agreed Azure Blob Storage container.",
        "• Prerequisite 3: Legal & Procurement leads available for 8 hrs/week in Weeks 1-2 to freeze contracting ontologies.",
        "• Prerequisite 4: Single Point of Contact (Jitender Verma) authorized to resolve functional ambiguities within 24 hours.",
        "• Prerequisite 5: Corporate Entra ID tenant accessible for SSO configuration and security group role binding."
    ], header_color=PURPLE_ACCENT)

    add_card(s56, 8.8, 1.5, 3.7, 5.1, "3. Decision Gate Acceptance Criteria", [
        "• Metric Gate 1: Contract Classification Accuracy ≥ 95.0% across all 6 in-scope contract categories.",
        "• Metric Gate 2: Clause Extraction Accuracy ≥ 95.0% measured against legal ground truth benchmark.",
        "• Metric Gate 3: 100% Traceability between risk ratings and source document page coordinates.",
        "• Delivery Gate 4: Working interactive demonstration cockpit and Excel risk register export delivered.",
        "• Formal Authorization: Executive Sponsor (Nithin Arora) signs off acceptance before triggering Phase 2 Pilot."
    ], header_color=EMERALD_SUCCESS)

    prs.save("exports/PVR_INOX_TCS_Contract_Intelligence_Master_Deck.pptx")
    print("Checkpoint: Slides 46-56 successfully compiled.")
    return prs
