import os
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    font_names = ['arialbd.ttf' if bold else 'arial.ttf', 'segoeuib.ttf' if bold else 'segoeui.ttf', 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf']
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            pass
    return ImageFont.load_default()

os.makedirs('exports/assets/ui', exist_ok=True)

# 2. UI Clause Inspector (Split-Screen)
w, h = 1920, 1080
img2 = Image.new('RGB', (w, h), (248, 250, 252))
d2 = ImageDraw.Draw(img2)
font_title = get_font(24, True)
font_sec = get_font(16, True)
font_reg = get_font(14, False)
font_code = get_font(13, False)
font_small = get_font(12, False)
font_badge = get_font(11, True)

# Top Bar
d2.rectangle([(0, 0), (w, 64)], fill=(15, 23, 42))
d2.text((32, 20), 'ENTERPRISE CONTRACT INTELLIGENCE PLATFORM  •  CLAUSE INSPECTION COCKPIT', fill=(255, 255, 255), font=font_sec)
d2.text((1650, 22), 'Contract: CTR-LSE-0081 [PoC Mode]', fill=(56, 189, 248), font=font_badge)

# Subheader
d2.rectangle([(0, 64), (w, 120)], fill=(255, 255, 255), outline=(226, 232, 240))
d2.text((32, 76), 'Contract Document: Commercial Multiplex Lease Agreement (Executed Sample)', fill=(15, 23, 42), font=font_title)
d2.text((32, 100), 'Category: Commercial Lease  •  Document ID: c89f2-2023  •  Azure AI Doc Intelligence Layout Bounding Box Verified', fill=(100, 116, 139), font=font_small)

# Split Screen
d2.rounded_rectangle([(32, 136), (932, 1040)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225), width=1)
d2.rectangle([(32, 136), (932, 180)], fill=(241, 245, 249))
d2.text((50, 150), 'Original Document View: Page 14 of 48 [PDF Layout Coordinates: 72 DPI Normalized]', fill=(30, 41, 59), font=font_sec)
d2.text((780, 150), 'Zoom: 100% | BBoxes: ON', fill=(14, 165, 233), font=font_small)

pdf_lines = [
    ('SECTION 11. INDEMNIFICATION AND LIABILITY ALLOCATION', True),
    ('11.1 Landlord and Tenant agree that neither party shall be held liable for any punitive or exemplary damages.', False),
    ('11.2 LIMITATION OF LIABILITY AND REVENUE SHARE DEFICIT RECOVERY:', True),
    ('In no event shall Landlord aggregate liability under this Commercial Lease Agreement exceed a sum equivalent', False),
    ('to twelve (12) months of standard monthly minimum guaranteed rent (MG) paid immediately preceding the event.', False),
    ('11.3 TENANT REVENUE SHARE ESCALATOR AND CAP EXCLUSIONS:', True),
    ('Notwithstanding any provision herein to the contrary, the Tenant annual revenue share escalation clause shall be', False),
    ('strictly capped at 4.5% (four point five percent) compounded annually, regardless of footfall or retail index gains,', False),
    ('and shall supersede any standard retail mall development escalator tariff published by the Landlord consortium.', False),
    ('11.4 Maintenance and common area charges (CAM) are fixed at INR 38 per sq.ft and subject to bi-annual revision.', False),
    ('11.5 Termination for convenience requires nine (9) months prior written notice by either executing party.', False),
    ('11.6 Governing law shall be the laws of New Delhi, India. All disputes subject to exclusive High Court jurisdiction.', False)
]
py = 200
for line_text, is_h in pdf_lines:
    if '11.3 TENANT REVENUE SHARE ESCALATOR' in line_text or 'strictly capped at 4.5%' in line_text:
        d2.rectangle([(48, py - 4), (915, py + 24)], fill=(254, 243, 199), outline=(245, 158, 11), width=2)
        d2.text((54, py), line_text, fill=(180, 83, 9), font=get_font(13, True))
        d2.text((740, py - 18), 'BoundingBox: [x:48, y:312, w:867, h:56]', fill=(217, 119, 6), font=font_badge)
    else:
        d2.text((54, py), line_text, fill=(15, 23, 42) if is_h else (71, 85, 105), font=get_font(13, is_h))
    py += 36

# RIGHT PANE
d2.rounded_rectangle([(952, 136), (w - 32, 1040)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225), width=1)
d2.rectangle([(952, 136), (w - 32, 180)], fill=(241, 245, 249))
d2.text((972, 150), 'Extracted Clause Intelligence & Contracting Principle Assessment Engine', fill=(30, 41, 59), font=font_sec)

d2.rounded_rectangle([(972, 196), (w - 52, 330)], radius=6, fill=(248, 250, 252), outline=(226, 232, 240))
d2.text((988, 208), 'CLAUSE METADATA & EXTRACTION PROVENANCE', fill=(100, 116, 139), font=font_badge)
d2.text((988, 228), 'Target Clause: Revenue Share Escalator & Commercial Cap', fill=(15, 23, 42), font=get_font(18, True))
d2.text((988, 258), 'Extraction Pipeline: Pass 2 (Targeted Open-Textured Clause Deep Dive)', fill=(147, 51, 234), font=get_font(13, True))
d2.text((988, 282), 'Source Coordinates: Document ID c89f2  •  Page 14  •  BoundingBox [48, 312, 867, 56]  •  ChunkID: CHK-LSE-014-03', fill=(71, 85, 105), font=font_small)
d2.text((988, 304), 'Verbatim Text: "...annual revenue share escalation clause shall be strictly capped at 4.5% compounded annually..."', fill=(30, 41, 59), font=font_code)

d2.rounded_rectangle([(972, 346), (w - 52, 600)], radius=6, fill=(255, 255, 255), outline=(245, 158, 11), width=2)
d2.rectangle([(972, 346), (w - 52, 376)], fill=(254, 243, 199))
d2.text((988, 352), 'GOVERNING CONTRACTING PRINCIPLE: PR-LSE-03 (COMMERCIAL ESCALATOR THRESHOLD)', fill=(180, 83, 9), font=font_badge)

d2.text((988, 388), 'Standard Contracting Principle Rule:', fill=(100, 116, 139), font=font_small)
d2.text((988, 406), '"Standard commercial lease contracts must enforce minimum 7.0% annual revenue share escalator or match prevailing CPI index. Any cap below 7.0% but >= 4.0% requires Chief Financial Officer & Head of Real Estate approval. Cap < 4.0% is Strictly Rejected."', fill=(30, 41, 59), font=font_reg)

d2.text((988, 460), 'Synthesized Assessment Outcome:', fill=(100, 116, 139), font=font_small)
d2.rounded_rectangle([(988, 480), (1340, 520)], radius=4, fill=(245, 158, 11))
d2.text((1000, 492), 'WARNING: AGREE WITH MANAGEMENT APPROVAL', fill=(255, 255, 255), font=get_font(13, True))

d2.text((988, 532), 'Model Rationale & Deviation Explanation:', fill=(100, 116, 139), font=font_small)
d2.text((988, 550), '"The extracted clause enforces a 4.5% annual escalation ceiling, which falls below the approved 7.0% baseline standard but exceeds the 4.0% critical rejection threshold. Flagged as Moderate Commercial Exposure; mandatory sign-off required from CFO prior to lease renewal."', fill=(71, 85, 105), font=font_reg)

d2.rounded_rectangle([(972, 616), (w - 52, 700)], radius=6, fill=(240, 253, 250), outline=(13, 148, 136))
d2.text((988, 626), 'RESPONSIBLE AI & EVALUATION CHECKPOINTS [AZURE AI EVALUATION HARNESS]', fill=(13, 148, 136), font=font_badge)
d2.text((988, 648), '• Semantic Groundedness Score: 98.4% (Threshold: >= 90.0%)  [PASS]', fill=(15, 23, 42), font=font_reg)
d2.text((988, 668), '• Hallucination & Factuality Check: 0.00 False Positives  •  Traceability Index: 100% Page Citation Linked', fill=(15, 23, 42), font=font_reg)

d2.rounded_rectangle([(972, 716), (w - 52, 1020)], radius=6, fill=(248, 250, 252), outline=(226, 232, 240))
d2.text((988, 730), 'HUMAN-IN-THE-LOOP (HITL) LEGAL & PROCUREMENT ACTIONS [PoC & Pilot Feature]', fill=(100, 116, 139), font=font_badge)

actions = [
    ('[ Confirm Finding & Route for Leadership Approval ]', (15, 23, 42), 760),
    ('[ Override: Accept as Standard (Provide Justification) ]', (16, 185, 129), 820),
    ('[ Override: Reject Contract Term (Not Agree) ]', (239, 68, 68), 880),
    ('[ Re-run Pass 3 with Focused Prompting ]', (147, 51, 234), 940)
]
for abtn, acol, ay in actions:
    d2.rounded_rectangle([(988, ay), (1450, ay + 44)], radius=4, fill=acol)
    d2.text((1010, ay + 14), abtn, fill=(255, 255, 255), font=get_font(13, True))

img2.save('exports/assets/ui/ui_clause_inspector.png')
print('UI Clause Inspector saved successfully')

# 3. UI Exceptions & System Health Cockpit
img3 = Image.new('RGB', (w, h), (248, 250, 252))
d3 = ImageDraw.Draw(img3)
d3.rectangle([(0, 0), (w, 64)], fill=(15, 23, 42))
d3.text((32, 20), 'ENTERPRISE CONTRACT INTELLIGENCE PLATFORM  •  OPERATIONS & HEALTH COCKPIT', fill=(255, 255, 255), font=font_sec)
d3.text((1600, 22), 'Environment: Production Grade [Prod]', fill=(16, 185, 129), font=font_badge)

d3.rectangle([(0, 64), (w, 120)], fill=(255, 255, 255), outline=(226, 232, 240))
d3.text((32, 76), 'Exceptions Management Queue & Real-Time Operational Telemetry', fill=(15, 23, 42), font=font_title)
d3.text((32, 100), 'Automated Synthetic Health Probes  •  Azure Monitor / App Insights  •  Self-Healing Circuit Breakers', fill=(100, 116, 139), font=font_small)

# Left Column: Exceptions Queue
d3.rounded_rectangle([(32, 136), (940, 1040)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
d3.rectangle([(32, 136), (940, 180)], fill=(241, 245, 249))
d3.text((50, 150), 'Automated Exceptions Queue (Human Triage Required) [PoC / Pilot / Prod]', fill=(30, 41, 59), font=font_sec)

exc_items = [
    ('EXC-0104', 'CTR-MKT-0089', 'Pass Count Exceeded (>3 Passes)', 'Open-textured concession indemnity unresolved; ambiguous counterparty phrasing.', 'Paralegal Review Assigned', (245, 158, 11)),
    ('EXC-0105', 'CTR-LSE-0244', 'OCR Layout Low Confidence (<70%)', 'Scanned image degradation on Pages 18-20. Recommended re-upload via OCR Phase 2 pipeline.', 'Requires New PDF Scan', (239, 68, 68)),
    ('EXC-0106', 'CTR-VND-0381', 'Category Classification Low Conf', 'Hybrid agreement spanning Facility Maintenance and Software Licensing.', 'Category Overridden to Dual', (14, 165, 233)),
    ('EXC-0107', 'CTR-SRV-0199', 'Missing Required Mandatory Clause', 'Statutory labour compliance schedule omitted in vendor execution draft.', 'Escalated to Legal Lead', (239, 68, 68)),
    ('EXC-0108', 'CTR-TCH-0062', 'Schema Validation Failure', 'JSON output from LLM had malformed date string in renewal duration array.', 'Auto-Repaired via Schema Tool', (16, 185, 129)),
]

ey = 200
for eid, docid, rtype, rdesc, rstatus, rcol in exc_items:
    d3.rounded_rectangle([(48, ey), (924, ey + 140)], radius=6, fill=(248, 250, 252), outline=(226, 232, 240))
    d3.rectangle([(48, ey), (924, ey + 4)], fill=rcol)
    d3.text((64, ey + 14), f'{eid}  |  Doc: {docid}', fill=(15, 23, 42), font=get_font(14, True))
    d3.rounded_rectangle([(680, ey + 12), (908, ey + 36)], radius=4, fill=(rcol[0], rcol[1], rcol[2]), outline=rcol)
    d3.text((690, ey + 16), rtype[:26], fill=(255, 255, 255), font=font_badge)
    d3.text((64, ey + 44), f'Description: {rdesc}', fill=(71, 85, 105), font=font_reg)
    d3.text((64, ey + 72), f'Triage Resolution: {rstatus}', fill=(15, 23, 42), font=get_font(13, True))
    d3.rounded_rectangle([(64, ey + 98), (220, ey + 128)], radius=4, fill=(15, 23, 42))
    d3.text((78, ey + 106), 'Open Triage Ticket', fill=(255, 255, 255), font=font_badge)
    ey += 160

# Right Column: Production Health Monitor
d3.rounded_rectangle([(960, 136), (w - 32, 1040)], radius=8, fill=(255, 255, 255), outline=(203, 213, 225))
d3.rectangle([(960, 136), (w - 32, 180)], fill=(241, 245, 249))
d3.text((980, 150), 'Production Service Health Telemetry & Synthetic Probes [Production]', fill=(30, 41, 59), font=font_sec)

health_metrics = [
    ('Azure AI Document Intelligence Endpoint', 'Healthy (99.98% SLA)', 'P95 Latency: 1.84s  •  HTTP 200: 99.9%  •  Zero Throttling', (16, 185, 129)),
    ('Azure OpenAI Service (GPT-4o India Central)', 'Healthy (Quota 68%)', 'P95 Latency: 3.12s  •  Tokens/min: 142k / 200k  •  TPM Safe', (16, 185, 129)),
    ('Azure AI Search (Hybrid Vector Index)', 'Healthy (120ms P95)', 'Index Size: 24,000 Chunks  •  Storage: 420 MB  •  Top-5 Recall: 98.1%', (16, 185, 129)),
    ('Azure SQL Database (Findings & Register Store)', 'Healthy (DTU: 24%)', 'Connections: 32  •  Deadlocks: 0  •  Backup Retention: 35 Days Geo-Repl', (16, 185, 129)),
    ('Automated Synthetic Canary Probe (Hourly)', 'Passing (5/5 Tests)', 'Synthetic test contracts processed end-to-end every 60 min to verify ground truth', (14, 165, 233)),
]

hy = 200
for sname, sstatus, sdetail, scol in health_metrics:
    d3.rounded_rectangle([(980, hy), (w - 52, hy + 100)], radius=6, fill=(248, 250, 252), outline=(226, 232, 240))
    d3.rectangle([(980, hy), (986, hy + 100)], fill=scol)
    d3.text((1002, hy + 16), sname, fill=(15, 23, 42), font=get_font(15, True))
    d3.rounded_rectangle([(1600, hy + 12), (1840, hy + 40)], radius=4, fill=(scol[0], scol[1], scol[2]), outline=scol)
    d3.text((1615, hy + 18), sstatus, fill=(255, 255, 255), font=font_badge)
    d3.text((1002, hy + 52), sdetail, fill=(71, 85, 105), font=font_reg)
    hy += 116

d3.rounded_rectangle([(980, 810), (w - 52, 1010)], radius=6, fill=(241, 245, 249), outline=(203, 213, 225))
d3.text((1002, 824), 'ACTIVE AUTOMATED REMEDIATION & ALERT POLICIES [PROD OPERATIONAL RUNBOOK]', fill=(30, 41, 59), font=font_badge)
d3.text((1002, 852), '1. Quota Backoff: On HTTP 429 from Azure OpenAI, exponential retry with jitter (1s, 2s, 4s, 8s); queues to Service Bus.', fill=(51, 65, 85), font=font_small)
d3.text((1002, 882), '2. Evaluation Drift: If canary groundedness drops below 92%, alert Ops Slack/Teams and freeze automated export.', fill=(51, 65, 85), font=font_small)
d3.text((1002, 912), '3. Circuit Breaker: If Document Intelligence fails >3 consecutive times, failover to secondary India South endpoint.', fill=(51, 65, 85), font=font_small)
d3.text((1002, 942), '4. Auto-Scaling: Container Apps scale from 1 to 5 replicas based on Service Bus queue length (>50 messages).', fill=(51, 65, 85), font=font_small)

img3.save('exports/assets/ui/ui_exceptions_health.png')
print('UI Exceptions and Health saved successfully')
