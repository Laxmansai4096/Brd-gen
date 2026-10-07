import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs('exports/assets/diagrams', exist_ok=True)

def get_font(size, bold=False):
    font_names = ['arialbd.ttf' if bold else 'arial.ttf', 'segoeuib.ttf' if bold else 'segoeui.ttf', 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf']
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            pass
    return ImageFont.load_default()

def paste_icon(canvas, icon_path, x, y, size=(50, 50)):
    if os.path.exists(icon_path):
        try:
            icon = Image.open(icon_path).convert('RGBA')
            icon = icon.resize(size, Image.Resampling.LANCZOS)
            canvas.paste(icon, (x, y), icon)
        except Exception as e:
            print(f"Error pasting {icon_path}: {e}")

# =========================================================================
# 1. Component Architecture Diagram (HD: 1920x1080)
# =========================================================================
w, h = 1920, 1080
img1 = Image.new('RGB', (w, h), (248, 250, 252))
d1 = ImageDraw.Draw(img1)

# Header
d1.rectangle([(0, 0), (w, 80)], fill=(15, 23, 42))
d1.text((40, 24), 'PRODUCTION-GRADE AZURE TECHNICAL COMPONENT ARCHITECTURE', fill=(255, 255, 255), font=get_font(24, True))
d1.text((1500, 30), 'Multi-Tier Cloud Blueprint', fill=(56, 189, 248), font=get_font(14, True))

# 4 Major Tiers (Horizontal columns)
tiers = [
    ("1. INTAKE & INGESTION TIER (Non-AI)", 40, 420, (238, 242, 255), (99, 102, 241)),
    ("2. ORCHESTRATION & EVENT BUS", 480, 420, (240, 253, 244), (34, 197, 94)),
    ("3. REASONING & EXTRACTION (Agentic AI)", 920, 520, (254, 243, 199), (245, 158, 11)),
    ("4. STORAGE & PRESENTATION TIER", 1460, 420, (245, 243, 255), (168, 85, 247))
]

for title, tx, tw, bg_col, b_col in tiers:
    d1.rounded_rectangle([(tx, 100), (tx + tw, 1000)], radius=12, fill=bg_col, outline=b_col, width=2)
    d1.rectangle([(tx, 100), (tx + tw, 150)], fill=b_col)
    d1.text((tx + 20, 115), title, fill=(255, 255, 255), font=get_font(15, True))

# Components in Tier 1
# Azure Blob
d1.rounded_rectangle([(60, 170), (440, 320)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_blob.png', 80, 190, (50, 50))
d1.text((150, 190), 'Azure Blob Storage', fill=(15, 23, 42), font=get_font(16, True))
d1.text((150, 215), 'Landing Zone: /contracts/raw', fill=(71, 85, 105), font=get_font(12, False))
d1.text((80, 250), 'Immutable contract intake, immutable audit archive, SSE-KMS 256-bit encryption.', fill=(51, 65, 85), font=get_font(11, False))

# Azure Document Intelligence
d1.rounded_rectangle([(60, 340), (440, 520)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_doc_intel.png', 80, 360, (50, 50))
d1.text((150, 360), 'Azure AI Doc Intelligence', fill=(15, 23, 42), font=get_font(16, True))
d1.text((150, 385), 'Prebuilt Layout & Read API', fill=(71, 85, 105), font=get_font(12, False))
d1.text((80, 420), 'Deterministic OCR extraction, table cell parsing, and exact pixel/normalized coordinate recovery.', fill=(51, 65, 85), font=get_font(11, False))
d1.text((80, 470), '[Deterministic Engine: Zero Hallucination]', fill=(16, 185, 129), font=get_font(11, True))

# Ingestion Worker (Functions)
d1.rounded_rectangle([(60, 540), (440, 710)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_functions.png', 80, 560, (50, 50))
d1.text((150, 560), 'Ingestion Event Dispatcher', fill=(15, 23, 42), font=get_font(16, True))
d1.text((150, 585), 'Azure Functions (FaaS: Serverless)', fill=(71, 85, 105), font=get_font(12, False))
d1.text((80, 620), 'BlobCreated event triggers chunking across section boundaries (512 tokens) and metadata tagging.', fill=(51, 65, 85), font=get_font(11, False))

# Components in Tier 2
# Event Grid / Service Bus
d1.rounded_rectangle([(500, 170), (880, 320)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_functions.png', 520, 190, (50, 50))
d1.text((590, 190), 'Azure Service Bus Queue', fill=(15, 23, 42), font=get_font(16, True))
d1.text((590, 215), 'Decoupled Queue & Dead-Letter', fill=(71, 85, 105), font=get_font(12, False))
d1.text((520, 250), 'Asynchronous batch buffering, exponential backoff with jitter on 429 throttling.', fill=(51, 65, 85), font=get_font(11, False))

# Pipeline Orchestrator (Container Apps)
d1.rounded_rectangle([(500, 340), (880, 560)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_container.png', 520, 360, (50, 50))
d1.text((590, 360), 'Multi-Pass Workflow Engine', fill=(15, 23, 42), font=get_font(16, True))
d1.text((590, 385), 'Azure Container Apps (FastAPI)', fill=(71, 85, 105), font=get_font(12, False))
d1.text((520, 420), 'Pass-aware finite state machine. Schedules Pass 1 (direct) and follow-up Pass 2+ for unresolved terms.', fill=(51, 65, 85), font=get_font(11, False))
d1.text((520, 480), 'Tracks provenance, execution passes, and exception routing.', fill=(51, 65, 85), font=get_font(11, False))

# Azure Key Vault & IAM
d1.rounded_rectangle([(500, 580), (880, 750)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_keyvault.png', 520, 600, (50, 50))
d1.text((590, 600), 'Azure Key Vault & Entra ID', fill=(15, 23, 42), font=get_font(16, True))
d1.text((590, 625), 'Managed Identity (Zero Keys)', fill=(71, 85, 105), font=get_font(12, False))
d1.text((520, 660), 'Workload identity federation, role assignments, secret-free service-to-service communication.', fill=(51, 65, 85), font=get_font(11, False))

# Components in Tier 3 (Agentic AI Tier)
# Azure AI Search
d1.rounded_rectangle([(940, 170), (1420, 350)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_search.png', 960, 190, (50, 50))
d1.text((1030, 190), 'Azure AI Search (Hybrid RAG)', fill=(15, 23, 42), font=get_font(16, True))
d1.text((1030, 215), 'Semantic + Vector (text-emb-3-large)', fill=(71, 85, 105), font=get_font(12, False))
d1.text((960, 250), 'Indexes 512-token chunks with 1536d embeddings. Hybrid BM25 keyword matching + vector similarity ensures precision for exact legal phrasing.', fill=(51, 65, 85), font=get_font(11, False))

# Classification Agent
d1.rounded_rectangle([(940, 370), (1420, 530)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_openai.png', 960, 390, (50, 50))
d1.text((1030, 390), 'Category Classification Agent', fill=(15, 23, 42), font=get_font(16, True))
d1.text((1030, 415), 'Azure OpenAI (GPT-4o mini)', fill=(71, 85, 105), font=get_font(12, False))
d1.text((960, 450), 'Evaluates preamble & structure to classify contracts into 6 categories (Lease, Vendor, Service, Facilities, Tech, Marketing).', fill=(51, 65, 85), font=get_font(11, False))

# Multi-Pass Clause Extraction & Principle Agent
d1.rounded_rectangle([(940, 550), (1420, 770)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_foundry.png', 960, 570, (50, 50))
d1.text((1030, 570), 'Multi-Pass Clause & Principle Agent', fill=(15, 23, 42), font=get_font(16, True))
d1.text((1030, 595), 'Azure AI Foundry / OpenAI GPT-4o', fill=(71, 85, 105), font=get_font(12, False))
d1.text((960, 630), 'Pass 1: Broad extraction of standardized clauses.', fill=(51, 65, 85), font=get_font(11, False))
d1.text((960, 655), 'Pass 2+: Targeted prompt iteration for ambiguous & negotiated terms.', fill=(51, 65, 85), font=get_font(11, False))
d1.text((960, 680), 'Principle Assessment: Evaluates extracted terms against category rule ontologies -> Agree / Agree w/ Mgmt Approval / Not Agree.', fill=(51, 65, 85), font=get_font(11, False))

# Components in Tier 4
# Azure SQL Database
d1.rounded_rectangle([(1480, 170), (1860, 340)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_vm.png', 1500, 190, (50, 50))
d1.text((1570, 190), 'Azure SQL Database', fill=(15, 23, 42), font=get_font(16, True))
d1.text((1570, 215), 'Relational Findings & Register Store', fill=(71, 85, 105), font=get_font(12, False))
d1.text((1500, 250), 'Holds master ontologies, frozen clause standards, extracted entities, pass records, and audit logs.', fill=(51, 65, 85), font=get_font(11, False))

# Risk Cockpit UI (App Service / Static Web Apps)
d1.rounded_rectangle([(1480, 360), (1860, 540)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_container.png', 1500, 380, (50, 50))
d1.text((1570, 380), 'Risk Visibility Cockpit', fill=(15, 23, 42), font=get_font(16, True))
d1.text((1570, 405), 'Azure App Service / React UI', fill=(71, 85, 105), font=get_font(12, False))
d1.text((1500, 440), 'Interactive demonstration dashboard with side-by-side PDF coordinate highlight viewer and one-click export.', fill=(51, 65, 85), font=get_font(11, False))

# Azure Monitor & App Insights
d1.rounded_rectangle([(1480, 560), (1860, 740)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
paste_icon(img1, 'exports/assets/azure_monitor.png', 1500, 580, (50, 50))
d1.text((1570, 580), 'Azure Monitor & Insights', fill=(15, 23, 42), font=get_font(16, True))
d1.text((1570, 605), 'E2E Observability & Evaluation', fill=(71, 85, 105), font=get_font(12, False))
d1.text((1500, 640), 'Token quota tracking, P95 latency alerts, groundedness drift detection, and synthetic canary probes.', fill=(51, 65, 85), font=get_font(11, False))

# Footer metadata banner
d1.rectangle([(40, 800), (w - 40, 980)], fill=(241, 245, 249), outline=(203, 213, 225))
d1.text((60, 815), 'CROSS-CUTTING GOVERNANCE & ARCHITECTURAL HIGHLIGHTS', fill=(30, 41, 59), font=get_font(14, True))
d1.text((60, 845), '• Boundary Separation: Deterministic parsing (Doc Intelligence) strictly decoupled from LLM inference (Azure OpenAI).', fill=(71, 85, 105), font=get_font(12, False))
d1.text((60, 875), '• 100% Coordinate Groundedness: Every LLM finding is bound to exact page coordinates (x, y, w, h) in Azure SQL.', fill=(71, 85, 105), font=get_font(12, False))
d1.text((60, 905), '• Multi-Pass Convergence: Unresolved open-textured terms queue targeted passes (Max 3 passes) before routing to exceptions queue.', fill=(71, 85, 105), font=get_font(12, False))
d1.text((60, 935), '• Security & Residency: India Central/South regions; Entra ID SSO; Zero shared keys; Platform-managed encryption.', fill=(71, 85, 105), font=get_font(12, False))

img1.save('exports/assets/diagrams/arch_component_diagram.png')
print('Component Architecture Diagram saved')

# =========================================================================
# 2. Deployment Architecture Diagram (Dev, SIT, UAT, Prod)
# =========================================================================
img2 = Image.new('RGB', (w, h), (248, 250, 252))
d2 = ImageDraw.Draw(img2)
d2.rectangle([(0, 0), (w, 80)], fill=(15, 23, 42))
d2.text((40, 24), 'MULTI-ENVIRONMENT DEPLOYMENT ARCHITECTURE (DEV, SIT, UAT, PROD)', fill=(255, 255, 255), font=get_font(24, True))
d2.text((1450, 30), 'Isolated Subscription Topology', fill=(56, 189, 248), font=get_font(14, True))

env_cols = [
    ("DEVELOPMENT (DEV)", 40, 440, "Non-Prod Subscription", [
        ("Azure Resource Group", "rg-contract-dev-001"),
        ("Storage Account", "stdl contractdev (LRS, Hot)"),
        ("Doc Intelligence", "Standard S0 (Shared Dev Key Vault)"),
        ("Azure OpenAI", "Pay-As-You-Go (TPM: 50k)"),
        ("Azure AI Search", "Basic Tier (1 Replica, 1 Partition)"),
        ("Compute Engine", "Container Apps (Consumption 0-2 Replicas)"),
        ("Database Tier", "Azure SQL Basic / Serverless 2 vCores"),
        ("Access Model", "Project Developers via Entra ID Group")
    ], (238, 242, 255), (99, 102, 241)),
    
    ("SYSTEM TESTING (SIT)", 510, 440, "Non-Prod Subscription", [
        ("Azure Resource Group", "rg-contract-sit-001"),
        ("Storage Account", "stdl contractsit (LRS, Soft Delete)"),
        ("Doc Intelligence", "Standard S0 (Automated Test Pipeline)"),
        ("Azure OpenAI", "Pay-As-You-Go (TPM: 100k)"),
        ("Azure AI Search", "Standard S1 (1 Replica, 1 Partition)"),
        ("Compute Engine", "Container Apps (Fixed 2 Replicas)"),
        ("Database Tier", "Azure SQL Standard S2 (50 DTUs)"),
        ("Access Model", "QA Engineers & Automated CI/CD Agent")
    ], (240, 253, 244), (34, 197, 94)),
    
    ("USER ACCEPTANCE (UAT)", 980, 440, "Non-Prod Subscription", [
        ("Azure Resource Group", "rg-contract-uat-001"),
        ("Storage Account", "stdl contractuat (GRS, WORM Compliant)"),
        ("Doc Intelligence", "Standard S0 (Production Parity)"),
        ("Azure OpenAI", "Pay-As-You-Go (TPM: 150k Reserved)"),
        ("Azure AI Search", "Standard S1 (2 Replicas, 1 Partition)"),
        ("Compute Engine", "Container Apps (Autoscale 2-5 Replicas)"),
        ("Database Tier", "Azure SQL General Purpose (4 vCores)"),
        ("Access Model", "Legal / Procurement SMEs & Sponsor Sign-off")
    ], (254, 243, 199), (245, 158, 11)),
    
    ("ENTERPRISE PROD", 1450, 430, "Production Subscription", [
        ("Azure Resource Group", "rg-contract-prod-001 (Locked)"),
        ("Storage Account", "stdl contractprod (ZRS, Immutable)"),
        ("Doc Intelligence", "Dedicated S0 Endpoint (Zone Redundant)"),
        ("Azure OpenAI", "Provisioned Throughput PTU / 300k TPM"),
        ("Azure AI Search", "Standard S2 (3 Replicas, 2 Partitions, HA)"),
        ("Compute Engine", "Container Apps / AKS (HA Multi-AZ)"),
        ("Database Tier", "Azure SQL Business Critical (Geo-Repl South)"),
        ("Access Model", "Entra ID PIM / JIT Access with MFA")
    ], (254, 242, 242), (239, 68, 68))
]

for title, ex, ew, subhead, services, c_bg, c_border in env_cols:
    d2.rounded_rectangle([(ex, 100), (ex + ew, 980)], radius=12, fill=c_bg, outline=c_border, width=2)
    d2.rectangle([(ex, 100), (ex + ew, 150)], fill=c_border)
    d2.text((ex + 16, 112), title, fill=(255, 255, 255), font=get_font(15, True))
    d2.text((ex + 16, 132), subhead, fill=(241, 245, 249), font=get_font(11, False))
    
    sy = 170
    for s_name, s_spec in services:
        d2.rounded_rectangle([(ex + 14, sy), (ex + ew - 14, sy + 88)], radius=6, fill=(255, 255, 255), outline=(226, 232, 240))
        d2.text((ex + 26, sy + 14), s_name, fill=(15, 23, 42), font=get_font(13, True))
        d2.text((ex + 26, sy + 42), s_spec, fill=(71, 85, 105), font=get_font(11, False))
        sy += 98

img2.save('exports/assets/diagrams/arch_deployment_diagram.png')
print('Deployment Architecture Diagram saved')

# =========================================================================
# 3. Contextual Solution Architecture Diagram
# =========================================================================
img3 = Image.new('RGB', (w, h), (248, 250, 252))
d3 = ImageDraw.Draw(img3)
d3.rectangle([(0, 0), (w, 80)], fill=(15, 23, 42))
d3.text((40, 24), 'CONTEXTUAL SOLUTION ARCHITECTURE & ENTERPRISE INTEGRATION LANDSCAPE', fill=(255, 255, 255), font=get_font(24, True))
d3.text((1500, 30), 'System Context & Boundary', fill=(56, 189, 248), font=get_font(14, True))

# Left Box: External Actors & Intake Sources
d3.rounded_rectangle([(40, 110), (480, 980)], radius=12, fill=(241, 245, 249), outline=(148, 163, 184), width=2)
d3.rectangle([(40, 110), (480, 160)], fill=(71, 85, 105))
d3.text((60, 125), 'EXTERNAL ACTORS & SOURCE SYSTEMS', fill=(255, 255, 255), font=get_font(16, True))

actors = [
    ("Corporate Legal Operations", "Uploads executed contracts & reviews flagged non-standard deviations in HITL cockpit.", (15, 23, 42)),
    ("Procurement & Category Leads", "Monitors commercial terms, escalator caps, liability thresholds across vendor contracts.", (15, 23, 42)),
    ("Executive Leadership / CFO", "Receives automated risk exposure digests and signs off on escalated Agree w/ Approval terms.", (15, 23, 42)),
    ("Phase 2 Enterprise Systems", "Contract Lifecycle Mgmt (CLM), SAP/Oracle ERP, SharePoint, Documentum repositories.", (100, 116, 139))
]
ay = 180
for aname, adesc, acol in actors:
    d3.rounded_rectangle([(60, ay), (460, ay + 170)], radius=8, fill=(255, 255, 255), outline=(226, 232, 240))
    d3.text((80, ay + 18), aname, fill=acol, font=get_font(14, True))
    d3.text((80, ay + 50), adesc, fill=(71, 85, 105), font=get_font(11, False))
    ay += 195

# Center Box: Solution Core (Azure Platform)
d3.rounded_rectangle([(520, 110), (1400, 980)], radius=12, fill=(238, 242, 255), outline=(99, 102, 241), width=2)
d3.rectangle([(520, 110), (1400, 160)], fill=(99, 102, 241))
d3.text((540, 125), 'CONTRACT INTELLIGENCE PLATFORM (AZURE SECURE BOUNDARY)', fill=(255, 255, 255), font=get_font(16, True))

sub_systems = [
    ("Ingestion & Layout Decomposition Engine", "Azure AI Doc Intelligence + Blob Storage. Converts messy PDFs into structured layout-aware JSON with (x, y, w, h) coordinates.", 550, 180, 820, 160),
    ("Multi-Pass Agentic Reasoning & Evaluation Engine", "Azure OpenAI GPT-4o + Azure AI Search. Performs prompt-based category classification, Pass 1 broad extraction, and Pass 2+ targeted deep dives.", 550, 360, 820, 190),
    ("Ontology & Principle Assessment Engine", "Structured rule matcher evaluating extracted clauses against 6 category ontologies (Lease, Vendor, Service, Tech, Facilities, Marketing).", 550, 570, 820, 160),
    ("Audit, Findings & Risk Visibility Service", "Azure SQL Database + React Cockpit. Stores full provenance chain, coordinate citations, and feeds interactive legal review dashboard.", 550, 750, 820, 160),
]
for sname, sdesc, sx, sy, sw, sh in sub_systems:
    d3.rounded_rectangle([(sx, sy), (sx + sw, sy + sh)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
    d3.text((sx + 20, sy + 18), sname, fill=(15, 23, 42), font=get_font(14, True))
    d3.text((sx + 20, sy + 50), sdesc, fill=(71, 85, 105), font=get_font(11, False))

# Right Box: Enterprise Outbound & Deliverables
d3.rounded_rectangle([(1440, 110), (1880, 980)], radius=12, fill=(240, 253, 244), outline=(34, 197, 94), width=2)
d3.rectangle([(1440, 110), (1880, 160)], fill=(34, 197, 94))
d3.text((1460, 125), 'DELIVERABLES & OUTBOUND ARTIFACTS', fill=(255, 255, 255), font=get_font(16, True))

outbounds = [
    ("Consolidated Contract Risk Register", "Automated Excel/CSV export following existing procurement review columns with direct clause-level citation URLs.", (15, 23, 42)),
    ("Executive Deviation Summary Pack", "One-click PPTX generation summarizing portfolio risk distribution, severe liability exposures, and approval statuses.", (15, 23, 42)),
    ("Exceptions & Unresolved Terms Digest", "Actionable log of documents or open-textured clauses requiring human paralegal intervention or re-scanning.", (15, 23, 42)),
    ("Benchmark Evaluation Report", "Precision, recall, and groundedness metrics scored against legal-confirmed ground truth test set.", (15, 23, 42))
]
oy = 180
for oname, odesc, ocol in outbounds:
    d3.rounded_rectangle([(1460, oy), (1860, oy + 170)], radius=8, fill=(255, 255, 255), outline=(226, 232, 240))
    d3.text((1480, oy + 18), oname, fill=ocol, font=get_font(14, True))
    d3.text((1480, oy + 50), odesc, fill=(71, 85, 105), font=get_font(11, False))
    oy += 195

img3.save('exports/assets/diagrams/arch_contextual_diagram.png')
print('Contextual Architecture Diagram saved')

# =========================================================================
# 4. End-to-End Data Flow Diagram (Numbered Sequences)
# =========================================================================
img4 = Image.new('RGB', (w, h), (248, 250, 252))
d4 = ImageDraw.Draw(img4)
d4.rectangle([(0, 0), (w, 80)], fill=(15, 23, 42))
d4.text((40, 24), 'END-TO-END NUMBERED DATA FLOW & SERVICE INVOCATION PIPELINE', fill=(255, 255, 255), font=get_font(24, True))
d4.text((1420, 30), 'Synchronous & Async Flow', fill=(56, 189, 248), font=get_font(14, True))

flows = [
    ("01", "Storage Ingestion", "Legal Ops uploads executed contract PDF into Azure Blob Storage container /contracts/raw.", "Azure Blob Storage", (99, 102, 241)),
    ("02", "Event Notification", "BlobCreated event triggers Azure Functions Ingestion Dispatcher via Event Grid.", "Azure Functions (FaaS)", (99, 102, 241)),
    ("03", "Layout Decomposition", "Dispatcher calls Azure AI Doc Intelligence (Layout API). Extracts text, tables, and bounding boxes.", "Azure AI Doc Intelligence", (14, 165, 233)),
    ("04", "Chunking & Vector Indexing", "Document parsed into 512-token chunks along clause boundaries; embedded via text-emb-3-large into AI Search.", "Azure AI Search", (14, 165, 233)),
    ("05", "Category Classification", "Classification Agent examines opening sections and structure to assign one of 6 contract categories.", "Azure OpenAI (GPT-4o mini)", (245, 158, 11)),
    ("06", "Pass 1 Clause Extraction", "Retrieves candidate chunks and extracts well-defined entities (dates, jurisdiction, standard caps).", "Azure OpenAI (GPT-4o)", (245, 158, 11)),
    ("07", "Multi-Pass Ambiguity Triage", "Unresolved or vague terms trigger targeted Pass 2/3 queries. Bounded by max 3 passes before exception.", "Container Apps Engine", (168, 85, 247)),
    ("08", "Principle Assessment Engine", "Extracted clauses compared against category ontology rules -> Agree / Agree w/ Mgmt Approval / Not Agree.", "Azure AI Foundry / OpenAI", (245, 158, 11)),
    ("09", "Findings Store & Grounding", "Risk outcomes, rationales, pass count, and source bounding box coordinates written to Azure SQL.", "Azure SQL Database", (16, 185, 129)),
    ("10", "Cockpit Surfacing & HITL", "React UI loads risk register with interactive side-by-side coordinate highlights for reviewer sign-off.", "Azure App Service", (16, 185, 129))
]

card_h = 75
fy = 110
for num, step_title, step_desc, svc_name, scol in flows:
    d4.rounded_rectangle([(40, fy), (w - 40, fy + card_h)], radius=8, fill=(255, 255, 255), outline=(226, 232, 240))
    # Number badge
    d4.rectangle([(40, fy), (120, fy + card_h)], fill=scol)
    d4.text((60, fy + 22), num, fill=(255, 255, 255), font=get_font(20, True))
    
    d4.text((140, fy + 14), step_title, fill=(15, 23, 42), font=get_font(15, True))
    d4.text((140, fy + 42), step_desc, fill=(71, 85, 105), font=get_font(11, False))
    
    # Service badge
    d4.rounded_rectangle([(1550, fy + 20), (1850, fy + 54)], radius=4, fill=(scol[0], scol[1], scol[2], 25), outline=scol)
    d4.text((1565, fy + 26), svc_name, fill=scol, font=get_font(11, True))
    
    fy += 87

img4.save('exports/assets/diagrams/arch_dataflow_diagram.png')
print('Data Flow Diagram saved')
