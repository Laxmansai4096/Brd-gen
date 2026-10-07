# Contract Intelligence & Risk Visibility Platform
## Business Requirements Document (BRD) & Technical Delivery Baseline
**Client:** PVR INOX  
**Engagement Type:** Proof of Concept (PoC)  
**Target Platform:** Microsoft Azure (India Region)  
**Timeline:** 6.0 Weeks (28-Sep-2026 to 06-Nov-2026)  
**Document Version:** 1.0 (Standardized)

---

## 1. Executive Summary

| Attribute | Details |
| :--- | :--- |
| **Client / Account** | **PVR INOX** |
| **Engagement Name** | Contract Intelligence & Risk Visibility Platform |
| **Delivery Tier** | **Proof of Concept (PoC)** (Single environment trial, throwaway build, happy-path and edge validation) |
| **Hosting Platform** | **Microsoft Azure** (Single-region: India; existing non-production subscription) |
| **Solution Domain** | AI / GenAI (Layout-aware document intelligence, hybrid retrieval, Azure OpenAI multi-pass orchestration) |
| **Planned Reference Duration** | **6.0 Weeks** (30 working days: 28-Sep-2026 to 06-Nov-2026) |
| **Base Delivery Effort** | **97.5 Person-Days** (direct engineering tasks) |
| **Total Project Effort** | **127.1 Person-Days** (inclusive of 6.3 days direct PM tasks, 11.7 days PM governance overhead uplift, and 11.6 days [10%] contingency) |
| **Key Stakeholders** | Executive Sponsor: **Nithin Arora** <br> Lead SPOC: **Jitender Verma** <br> IT Governance SPOC: **Gaurav** |

---

## 2. Business Context & Problem Statement

### 2.1 The Business Problem
PVR INOX enters into commercial contracts across six major categories:
1. **Lease Contracts**
2. **Vendor Contracts**
3. **Service Contracts**
4. **Facilities Contracts**
5. **Technology Contracts**
6. **Marketing Contracts**

Key operational and risk challenges identified:
* **Manual Review Overhead:** Reviewing each contractual clause is labor-intensive and heavily dependent on scarce legal and procurement subject matter experts (SMEs).
* **Format & Layout Variance:** Contracts are received and stored in disparate digital formats, layouts, and styles.
* **Category-Specific Principles:** Each category must be assessed against distinct legal, commercial, and operational contracting guidelines.
* **Non-Standard Deviations:** Deviations from approved corporate standards are difficult to spot manually and consistently.
* **Information Fragmentation:** Findings are maintained in disconnected spreadsheets without a centralized risk register or audit trail connecting identified risks back to the source clauses.

### 2.2 Objective & Success Metrics
Demonstrate the feasibility, operational viability, and accuracy of automated contract classification, clause extraction, principle assessment, and risk logging using representative historical contract samples.

#### Technical Success Metrics
* **100% Processing:** Complete execution across all agreed sample contract datasets (~100 contracts per category across 6 categories = ~600 documents).
* **$\ge 95\%$ Classification Accuracy:** Correct categorization into the 6 designated categories.
* **$\ge 95\%$ Clause Extraction Accuracy:** High precision extraction against agreed clause lists and attributes.
* **100% Traceability:** Absolute provenance linking every risk finding to the source document, page number, and bounding box coordinates.
* **$\ge 95\%$ Workflow Execution:** Robust automated execution without pipeline failures.

#### Business Success Metrics
* **100% Assessment Coverage:** All identified clauses evaluated against relevant contracting principles.
* **100% Categorization:** Findings categorized into:
  1. **Agree**
  2. **Agree with Management Approval**
  3. **Not Agree**
* **Consolidated Contract Risk Register:** Automated generation matching existing spreadsheet schema, enriched with source links.
* **Risk Visibility Dashboard:** Centralized view of risk exposure, approval bottlenecks, and deviation metrics.

---

## 3. Project Scope Boundaries

### 3.1 In-Scope (Phase 1 PoC)
* **Historical Contract Processing:** Representative sample of ~100 digital English contracts per category.
* **Ontology & Principles Configuration:** Elicitation, configuration, and validation of category-specific rules.
* **Contract Classification:** Prompt-based classification across the 6 defined categories.
* **Multi-Pass Clause Extraction:** 
  * *Pass 1:* Broad extraction of standardized, well-defined attributes.
  * *Pass 2+:* Targeted, clause-specific retrieval and extraction passes for ambiguous or heavily negotiated terms.
* **Principle Assessment Engine:** Categorization into *Agree / Agree with Mgmt Approval / Not Agree* with supporting rationale.
* **Exception Handling:** Explicit exception queues for unprocessable files or clauses exceeding max pass limits.
* **Evaluation Harness:** Replayable scoring against a legal-confirmed benchmark golden set.
* **Risk Register & Dashboard:** Exportable spreadsheet register and read-only demonstration UI protected by corporate SSO.
* **Deliverable Documentation:** Target architecture, Azure deployment roadmap, and operating cost estimates for Phase 2.

### 3.2 Out-of-Scope (Deferred to Phase 2 / Production)
* Automated approval routing, e-signature workflows, and workflow automation.
* Real-time integrations with live ERP, Document Management Systems (DMS), or Contract Lifecycle Management (CLM).
* Optical Character Recognition (OCR) tuning for physical scans, photographs, or handwritten documents.
* Ingestion of unsigned / draft contracts (Phase 1 strictly evaluates executed historical contracts).
* Non-English contracts.
* Multi-document relational synthesis (e.g., linking amendments, addenda, and side letters to parent contracts).
* Granular row-level/function-level user permissions (all authorized demo users view all contracts).
* Customer-Managed Keys (CMK), High Availability / Disaster Recovery (HA/DR) multi-region clusters, and 24/7 SLA operations.

---

## 4. Technical Architecture & Component Specification

The solution architecture is structured around six core components built within an existing Microsoft Azure non-production subscription in the India region:

### Component Decomposition

| Component ID | Component Name | Azure Service / Technology | Key Architectural Decisions |
| :--- | :--- | :--- | :--- |
| **C001** | **Contract Landing Store & Ingestion Pipeline** | Azure Blob Storage + Azure AI Document Intelligence | Authoritative executed copies uploaded by PVR INOX. Preserves raw files untouched. Uses layout-aware extraction to retrieve text with exact coordinates. Enforces clause-boundary chunking. |
| **C002** | **Clause Index & Retrieval Layer** | Azure AI Search (Managed Vector + Keyword) | Hybrid retrieval combining keyword matching (for statutory boilerplate) and vector similarity (1536-dim embeddings for negotiated clauses). Segregated indexes per environment (Dev, Test, UAT). |
| **C003** | **Classification, Multi-Pass Extraction & Principle Assessment Engine** | Azure OpenAI Service (GPT-4o / GPT-5 reasoning models) | **Multi-Pass Architecture:** Pass-aware orchestrator re-queues empty/ambiguous clause items with bounded retry caps. Decouples clause extraction from principle assessment to isolate error types during benchmark testing. |
| **C004** | **Ontology, Principle Config & Risk Register Store** | Azure Managed Database (Azure SQL / PostgreSQL) | Decouples legal principles into configuration records rather than hardcoded prompts. Stores extracted clauses, provenance data, pass numbers, exception logs, and final risk register findings. Retained for 12 months. |
| **C005** | **Evaluation Harness, Dashboard & Operational Telemetry** | Azure App Service / Power BI embedded + Azure Monitor | Evaluates benchmark golden sets; outputs first-pass vs. multi-pass accuracy differentials. Read-only demonstration UI displaying category risk concentrations and approval triggers. Tracks token/cost metrics. |
| **C006** | **Identity, Secrets & Environment Landing Zone** | Microsoft Entra ID + Azure Key Vault | Enforces Corporate Single Sign-On (SSO) for authorized project users. Inter-service authentication is handled via Azure Managed Identities (eliminating hardcoded credentials). Platform-managed encryption throughout. |

---

## 5. Estimation Engine & Effort Breakdown

### 5.1 Estimation Parameters & Modifiers
* **Estimation Unit:** Person-Days (9 hours/day).
* **Delivery Tier Multiplier:** PoC baseline rigour factor of **0.289** relative to full production.
* **Complexity Multiplier:** Low (0.850 applied to all tasks).
* **Compliance Multiplier:** Internal policy only (1.050 applied to compliance-tagged tasks).
* **Security Multiplier:** Standard (1.000 applied to security-tagged tasks).
* **Scale Drivers:** 1 Use Case, 4 Personas (1.45x), 0 Integrations (0.50x floor), 2 Data Sources, 3 Environments, 6 Components, 50,000 live corpus documents (1.0x).

### 5.2 Phase-wise Effort Summary (P01 – P18)

| Phase | Phase Description | Production Base Days | PoC Factor | PoC Effort (Days) |
| :---: | :--- | :---: | :---: | :---: |
| **P01** | Mobilisation & Discovery | 13.0 | 1.00 | **9.78** |
| **P02** | Requirements & Use Case Definition | 22.0 | 0.40 | **7.94** |
| **P03** | Data Discovery, Prep & Governance | 27.0 | 0.30 | **7.01** |
| **P04** | Solution & Technical Architecture | 23.0 | 0.35 | **6.40** |
| **P05** | Environment, Landing Zone & Platform Setup | 20.0 | 0.25 | **4.26** |
| **P06** | Data Pipeline, Chunking & Embedding | 33.0 | 0.40 | **11.20** |
| **P07** | Retrieval / Index / Knowledge Build | 17.0 | 0.50 | **7.24** |
| **P08** | Model Selection, Prompting & Orchestration | 35.0 | 0.55 | **15.44** |
| **P09** | Fine-tuning / Model Adaptation (Feasibility only) | 16.0 | 0.20 | **2.72** |
| **P10** | Application, API & Integration Layer | 39.0 | 0.25 | **7.80** |
| **P11** | Evaluation, Benchmarking & Golden Sets | 22.0 | 0.25 | **4.67** |
| **P12** | Responsible AI, Safety & Security | 31.0 | 0.10 | **2.72** |
| **P13** | MLOps / LLMOps, IaC & CI-CD | 24.0 | 0.05 | **1.03** |
| **P14** | Observability, Cost & FinOps | 19.0 | 0.10 | **1.63** |
| **P15** | Testing (Functional, Performance, UAT) | 33.0 | 0.15 | **4.56** |
| **P16** | Deployment, Cutover & Hypercare | 18.0 | 0.05 | **0.77** |
| **P17** | Documentation, Training & Handover | 16.0 | 0.15 | **2.27** |
| **P18** | Project Management & Governance (Direct) | 21.0 | 0.35 | **6.25** |
| — | **Subtotal Baseline Delivery Effort** | **429.0** | — | **97.5** |
| — | **PM Overhead Uplift (12% on Delivery)** | — | — | **11.7** |
| — | **Contingency Allowance (10%)** | — | — | **11.6** |
| **TOTAL** | **Comprehensive Project Effort** | — | — | **127.1 Person-Days** |

---

## 6. Staffing Model & Resource Loading

### 6.1 Role Taxonomy & Allocation
* **AI / ML Engineer (AIE):** 30.3 days (29.2%) — Prompting, multi-pass agents, embeddings, benchmark harness.
* **Data Engineer (DE):** 14.0 days (13.5%) — Blob landing, layout parsing, chunking, metadata tagging.
* **Project Manager (PM):** 10.5 direct days (10.1%) — Governance, reporting, RAID management, gate control.
* **Business Analyst (BA):** 10.0 days (9.6%) — Workshop facilitation, ontology capture, UAT facilitation.
* **Solution Architect (SA):** 9.5 days (9.2%) — End-to-end technical architecture, sizing, decision records.
* **Full-stack Software Engineer (SWE):** 7.1 days (6.8%) — API implementation, dashboard integration.
* **MLOps / LLMOps Engineer (MLO):** 5.1 days (4.9%) — Environment setup, prompt registry, monitoring.
* **SRE / Platform Engineer (SRE):** 4.6 days (4.4%) — Azure foundations, storage setup, telemetry.
* **Security Engineer (SEC):** 4.3 days (4.1%) — Access controls, DPIA conformance, threat modeling.
* **UX / UI Designer (UX):** 3.8 days (3.8%) — Persona journeys, wireframing, usability reviews.
* **QA / Test Engineer (QA):** 2.9 days (2.8%) — Test strategy, functional verification, regression suite.
* **Responsible AI Lead (RAI):** 1.5 days (1.4%) — AI safety policies, grounding validation, bias checks.

### 6.2 6-Week Delivery Schedule & Team Ramping
| Schedule Period | Weekly Team FTE | Primary Delivery Activities |
| :--- | :---: | :--- |
| **Week 1 (28-Sep to 02-Oct)** | 2.83 FTE | Kick-off, discovery workshops, data profiling, initial landing container setup. |
| **Week 2 (05-Oct to 09-Oct)** | 4.36 FTE | Architecture baseline, ontology elicitation, Document Intelligence pipeline build. |
| **Week 3 (12-Oct to 16-Oct)** | 3.49 FTE | Hybrid index construction, embedding generation, prompt design. |
| **Week 4 (19-Oct to 23-Oct)** | 3.28 FTE | Multi-pass extraction orchestration, principle assessment logic, API & UI build. |
| **Week 5 (26-Oct to 30-Oct)** | **5.13 FTE (Peak)** | Benchmark golden-set scoring, RAI impact audits, dashboard integration, UAT prep. |
| **Week 6 (02-Nov to 06-Nov)** | 2.67 FTE | UAT execution, defect triage, accuracy report finalization, Executive Decision Gate. |

*Feasibility Analysis:* The peak role allocation is 2.45 FTE (AI Engineer in Week 4), which is well below the 20.0 FTE single-role threshold. The maximum week-over-week ramp is 1.53 FTE (well below the 80.0 limit). **No schedule stretch is required.**

---

## 7. Cloud Sizing Drivers & Bill of Materials (BoM)

### 7.1 Sizing Calculations (Modeled for Live Reference & PoC Headroom)
* **Monthly Model Call Demand:** 2,000 requests/day $\times$ 22 working days = **44,000 requests/month**.
* **Token Sizing:** 3,410 input tokens/request + 2,000 output tokens/request = **238.04M total tokens/month**.
* **Peak Model Throughput:** 3.0 peak req/sec $\rightarrow$ **973,800 tokens/minute peak reservation**.
* **Vector Index Footprint:** 50,000 docs $\times$ 40 chunks = **2,000,000 vectors** $\rightarrow$ **23.76 GB searchable index total**.
* **Persistent Storage:** Raw corpus (1.0 GB) + Processed corpus (1.4 GB) + Logs/traces (6.34 GB) + History (11.43 GB) = **32.26 GB total storage** across all non-production environments.

### 7.2 Bill of Materials (Key Azure Components)
* **B001:** Azure OpenAI Generative Model (GPT-4o / GPT-5 reasoning tier) in India region.
* **B002:** Azure OpenAI Text Embedding Model (1536 dimensions).
* **B003:** Azure AI Document Intelligence (Layout Model API).
* **B004:** Azure AI Search (Standard Tier, hybrid vector + semantic search).
* **B005 & B007:** Azure Blob Storage (landing zone container + extraction intermediate cache).
* **B006:** Azure Managed Relational Database (Azure SQL / PostgreSQL) for ontologies and findings.
* **B008–B010:** Azure App Services / Container Apps (orchestrator workers and dashboard hosting).
* **B013–B016:** Microsoft Entra ID (SSO), Azure Key Vault, Azure Monitor, Log Analytics.

---

## 8. Governance, Risk Controls & Decision Gate

### 8.1 Key Assumptions (Gate Status: PASSED)
1. **Clause List Freeze (A001):** The clause and attribute checklist for each of the 6 categories is agreed and frozen in Workshop 1.
2. **Document Quality (A005):** All sample files provided in Phase 1 are digitally created, machine-readable documents in English. Physical scanned documents are deferred to Phase 2.
3. **Execution Status (A006):** Ingested contracts are final executed agreements. Review of pre-execution drafts is documented as a Phase 2 capability.
4. **Multi-Pass Stopping Rules (A051/A052):** Unresolved ambiguous terms undergo a maximum capped number of targeted passes before being flagged in the exception queue.
5. **Human-in-the-Loop Governance (A014):** The AI engine is an advisory assistant. All findings require human validation; no automated legal decisions are made.
6. **Data Residency (P001):** All processing and storage remain strictly within the India region of Azure under PVR INOX internal policy.

### 8.2 Executive Decision Gate Sign-Off
At the end of Week 6, the Executive Sponsor (**Nithin Arora**) will formally review:
1. Classification accuracy ($\ge 95\%$)
2. Clause extraction accuracy ($\ge 95\%$)
3. Principle assessment validity and risk register completeness
4. Business usability of the demonstration dashboard
5. Phase 2 Target Architecture & Azure Deployment Roadmap
