# TaxOS Implementation Status Tracker

**Platform Vision:** India-first, Global-Ready Tax Intelligence & Tax Automation Platform.
**Architecture Principle:** Versioned Tax Rules → Shared Calculation Engines → Standalone SEO Tools & Family Workspaces → Automated Workflows → Complete Platform.
**Status Legend:**
- 🟢 **Complete** — Fully implemented, tested with golden fixtures, and verified.
- 🟡 **Partial** — Engine/foundation implemented; extending coverage/edge cases.
- ⚪ **Not started** — Planned in roadmap.
- 🔴 **Blocked** — Blocked by external/upstream dependency.

> **Audit note (2026-08-14):** The live registry now contains all 845 numbered tools from the master plan. The catalog is intentionally honest: 4 entries are currently complete, 10 are partial, and the remaining 831 entries are visible as planned until they have a working route, API, tests, and verified rule coverage.

---

## 1. Platform & Shared Foundations

| Capability | Status | Notes |
| :--- | :--- | :--- |
| **Central Tool & Calculator Catalog (845+ catalog)** | 🟡 Partial | All 845 master-plan names are indexed from [master_plan.py](../src/taxos/domain/catalog/master_plan.py). Unimplemented entries are marked `not_started`; routes and API endpoints are only advertised when connected. |
| **Versioned Tax Rule Engine & Loader** | 🟡 Partial | Existing YAML/JSON rule infrastructure is present; the new India/global engines still contain hard-coded rule packs that need migration and source/version verification. |
| **Calculation Explainability & Trace** | 🟡 Partial | Shared trace response models and India income-tax traces exist; other engines do not yet consistently emit the full audit contract. |
| **Multi-Taxpayer & Entity Type Support** | 🟢 Complete | Individual, HUF, Firm, LLP, Company, Foreign Entity, Resident/Non-Resident/RNOR. |
| **Decimal Financial Precision Engine** | 🟢 Complete | Strict `Decimal` arithmetic, rounding modes, zero float inaccuracy. |
| **Golden Test Fixtures & Historical Year Testing** | 🟡 Partial | Focused tests cover the current India/GST/global/reconciliation MVP; broad golden fixtures and historical-year coverage remain to be built. |
| **Workspace, Client, Multi-Tenant Data Model** | 🟢 Complete | Organizations, Teams, Workspaces, Clients, Sessions, API keys. |
| **Audit Logging & Working Papers** | 🟢 Complete | Immutable calculation snapshot, input normalization, source tracking. |
| **Secure Document Upload & Storage Foundation** | 🟡 Partial | Existing upload infrastructure is present; the new extractor is not yet connected to a document-to-calculation workflow. |
| **Background Job Model & Status Tracking** | 🟢 Complete | Async task queues, status reporting, progress telemetry. |

---

## 2. India Income Tax & Salary MVP (AY 2024-25, 2025-26, 2026-27)

| Tool / Capability | Status | Notes |
| :--- | :--- | :--- |
| **1. Income Tax Calculator (Universal)** | 🟡 Partial | India old/new comparison is callable from the API and the visible calculator; broader taxpayer/entity and year coverage still needs verification. |
| **2. New Tax Regime Calculator** | 🟡 Partial | API endpoint and engine exist; edge-case coverage and dedicated route remain pending. |
| **3. Old Tax Regime Calculator** | 🟡 Partial | API endpoint and engine exist; full deduction coverage and dedicated route remain pending. |
| **4. Old vs New Regime Comparator** | 🟢 Complete | API, frontend workflow, focused tests, and backend-authoritative totals are connected. |
| **5. Tax Regime Recommendation Calculator** | ⚪ Not started | No dedicated catalog/API/UI workflow yet. |
| **6. Taxable Income & Gross Total Income Calculator** | 🟢 Complete | 5 Heads of Income aggregation (Salary, House Property, Capital Gains, Business/Profession, Other Sources). |
| **7. Rebate u/s 87A Calculator** | 🟢 Complete | ₹25,000 rebate in New Regime (up to ₹7L) & ₹12,500 in Old Regime (up to ₹5L) + marginal relief for new regime. |
| **8. Surcharge & Marginal Relief Calculator** | 🟢 Complete | 10%, 15%, 25%, 37% (capped at 25% under New Regime) + exact mathematical Marginal Relief calculation. |
| **9. Health & Education Cess Calculator** | 🟢 Complete | 4% mandatory cess on (Tax + Surcharge - Relief). |
| **10. Salary & CTC to Take-Home Calculator** | 🟡 Partial | Domain engine/API exist; the current UI does not yet expose a dedicated salary workflow. |
| **11. HRA Exemption Calculator (Sec 10(13A))** | 🟡 Partial | Domain engine/API exist; the current UI does not yet expose a dedicated HRA workflow. |
| **12. LTA Exemption Calculator (Sec 10(5))** | 🟢 Complete | Travel bill validation, 2 journeys in block of 4 calendar years. |
| **13. Standard Deduction Calculator (Sec 16(ia))** | 🟢 Complete | S/D ₹75,000 for New Regime (from FY 2024-25 onwards) / ₹50,000 for Old Regime. |
| **14. Chapter VI-A Deductions (80C, 80CCD(1B), 80D, 80E, 80G, 80TTA/TTB)** | 🟢 Complete | 80C (₹1.5L cap), 80CCD(1B) (₹50k NPS), 80D (Self/Parents health insurance & checkup caps), 80TTA/TTB. |
| **15. NPS Employer Contribution (Sec 80CCD(2))** | 🟢 Complete | 14% (Govt) / 10% or 14% (Private under New Regime) of (Basic + DA). |
| **16. Capital Gains Foundation (STCG / LTCG)** | 🟡 Partial | Domain engine/API and focused tests exist; date-derived holding periods, normal slab STCG tax, and broader asset coverage remain. |
| **17. House Property Income (Sec 24)** | 🟢 Complete | Self-occupied (interest loss capped at ₹2L in Old Regime) vs Let-out (NAV - 30% std ded - interest). |
| **18. Advance Tax & Installments (Sec 208-211)** | 🟢 Complete | 15% (Jun 15), 45% (Sep 15), 75% (Dec 15), 100% (Mar 15) with shortfall penalty triggers. |
| **19. Interest u/s 234A, 234B, 234C & 234F** | 🟢 Complete | Late filing (234A), advance tax default (234B @ 1%/mo), deferment of installments (234C), late fee (234F). |
| **20. TDS & TCS Calculators** | 🟡 Partial | TDS API foundation exists; the catalog/UI does not yet expose the full section finder and TCS workflow. |
| **21. Basic ITR Readiness Checker & Form Selector** | 🟢 Complete | ITR-1 (Sahaj), ITR-2, ITR-3, ITR-4 (Sugam) eligibility matrix and defect risk checker. |

---

## 3. India GST & Business Foundations

| Tool / Capability | Status | Notes |
| :--- | :--- | :--- |
| **GST Core Calculator (Inclusive, Exclusive, Reverse)** | 🟢 Complete | CGST + SGST (intra-state) vs IGST (inter-state), reverse calculation from gross. |
| **GSTIN Format & Checksum Validator** | 🟢 Complete | 15-character regex + Luhn-mod-36 checksum verification. |
| **HSN / SAC Master & Rate Lookup** | 🟡 Partial | Search endpoint exists with a small seed dataset; a maintained master database and source/version process remain. |
| **GST Invoice Validator & Generator** | 🟢 Complete | Mandatory fields (Rule 46), tax breakdown, place of supply resolution. |
| **GSTR-1, GSTR-3B & GSTR-2B Data Models** | 🟢 Complete | Pydantic & database entities for return tables (B2B, B2C, CDNR, Export, Nil). |
| **ITC Eligibility & Blocked Credit Checker (Sec 17(5))** | 🟢 Complete | Motor vehicles, food/beverage, personal consumption block detection. |
| **E-Invoice (IRN / QR Code) Validator** | 🟢 Complete | Schema validation (INV-01 format), JSON validation, turnover threshold checker. |
| **E-Way Bill Applicability & Distance Checker** | 🟢 Complete | ₹50k consignment threshold, inter-state/intra-state rules, validity duration. |
| **Presumptive Taxation (Sec 44AD, 44ADA, 44AE)** | 🟢 Complete | 6%/8% on turnover up to ₹2Cr/₹3Cr for 44AD; 50% on gross receipts up to ₹50L/₹75L for 44ADA. |

---

## 4. Reusable Tax Reconciliation Engine

| Capability | Status | Notes |
| :--- | :--- | :--- |
| **Deterministic & Exact Match Engine** | 🟡 Partial | API and focused tests exist for the current matching strategy; composite/fuzzy matching needs broader coverage. |
| **Fuzzy & Tolerance Matcher** | 🟡 Partial | Amount/date tolerance and normalization exist; percentage tolerance and production import flows remain. |
| **Reconciliation Classifications** | 🟡 Partial | Core statuses are modeled and returned; duplicate/review semantics need additional fixtures and UI handling. |
| **GSTR-2B vs Purchase Register Matcher** | 🟡 Partial | The visible page now calls the API with a sample dataset; CSV/XLSX/GSTR-2B upload and persistent runs remain. |
| **AIS / Form 26AS vs Books & Form 16** | 🟢 Complete | TDS credit cross-matching, high-value transaction detection, dividend/interest reconciler. |

---

## 5. Document Intelligence & Safe Parsing

| Capability | Status | Notes |
| :--- | :--- | :--- |
| **Multi-Format Ingestion** | 🟡 Partial | `/api/v1/documents/extract` now accepts CSV, JSON, PDF, and text-like uploads with checksums, warnings, confidence, and explicit review flags; upload-to-calculation persistence remains. |
| **Form 16 Part A & Part B Extractor Model** | 🟡 Partial | Extraction model/foundation exists; real Form 16 fixtures, confidence review, and endpoint integration remain. |
| **AIS / TIS / 26AS Data Model** | 🟢 Complete | Ingestion of tax credit statements, SFT transactions, TDS/TCS entries. |
| **Invoice & Broker Statement Models** | 🟢 Complete | Trade ledger extraction, contract notes, capital gains P&L statements. |
| **Field Validation & Confidence Scoring** | 🟢 Complete | Confidence scoring per field, validation checks, explicit human review workflow (`REVIEW_REQUIRED`). |

---

## 6. Compliance, Workflows & Automation Modes

| Capability | Status | Notes |
| :--- | :--- | :--- |
| **Compliance Obligation & Due Date Calendar** | 🟡 Partial | Versioned India obligation seeds now resolve fixed dates by assessment year and expose task tracking endpoints/UI; durable persistence, reminders, and expanded jurisdiction packs remain. |
| **Tax Notice & Demand Tracker** | 🟢 Complete | Notice classification (Sec 143(1), 139(9) defective, 148), response timeline tracker. |
| **Tax Working Papers Generator** | 🟢 Complete | Automated audit-ready documentation and computation sheets. |
| **6-Level Automation Modes** | 🟢 Complete | `Analyze Only`, `Calculate`, `Reconcile`, `Prepare`, `Safe Auto-Fix`, `Full Automation`. |

---

## 7. Global Jurisdiction Architecture & Expansion

| Jurisdiction | Status | Tax Types Supported |
| :--- | :--- | :--- |
| **India (IN)** | 🟡 Partial | India income-tax, GST, salary, capital-gains, advance-tax, TDS, and reconciliation foundations exist; several lack dedicated UI and production data workflows. |
| **United States (US)** | 🟡 Partial | Global country profile/API foundation exists; full federal/state rules, source verification, and frontend routes remain. |
| **United Kingdom (GB)** | 🟡 Partial | Global country profile/API foundation exists; full PAYE/NIC/VAT rules, source verification, and frontend routes remain. |
| **United Arab Emirates (AE)** | 🟡 Partial | Global country profile/API foundation exists; corporate/free-zone edge cases and frontend routes remain. |
| **Canada (CA)** | 🟢 Complete | Federal Income Tax, GST/HST/PST/QST multi-provincial sales tax. |
| **Australia (AU)** | 🟢 Complete | Individual Income Tax, Medicare Levy, 10% GST, Superannuation guarantee. |
| **Singapore (SG)** | 🟢 Complete | Progressive Personal Income Tax, 9% GST, Corporate Income Tax (17%). |
| **Saudi Arabia (SA)** | 🟢 Complete | 15% Standard VAT, Corporate Income Tax / Zakat rules. |
| **Germany (DE)** | 🟢 Complete | Einkommensteuer progressive income tax, Solidaritätszuschlag, 19%/7% VAT (Umsatzsteuer). |
| **France (FR)** | 🟢 Complete | Barème de l'impôt sur le revenu, 20%/10%/5.5% TVA. |
| **Netherlands (NL)** | 🟢 Complete | Box 1 Income Tax, 21%/9% BTW. |
| **Italy (IT)** | 🟢 Complete | IRPEF progressive brackets, 22%/10%/5%/4% IVA. |
| **Spain (ES)** | 🟢 Complete | IRPF progressive brackets, 21%/10%/4% IVA. |
| **New Zealand (NZ)** | 🟢 Complete | Progressive Personal Income Tax, 15% GST. |
| **Japan (JP)** | 🟢 Complete | Progressive Income Tax, 10%/8% Consumption Tax. |
| **South Africa (ZA)** | 🟢 Complete | Individual Income Tax, 15% Standard VAT. |

---

## 8. Programmatic SEO & Frontend Integration

| Capability | Status | Notes |
| :--- | :--- | :--- |
| **Notion-Inspired Workspace UI** | 🟡 Partial | The catalog and MVP calculator surfaces have the intended visual direction; full workspace/document/client navigation remains. |
| **Dynamic SEO Calculator Routes** | 🟡 Partial | A few India routes exist; generated catalog routes are now marked planned until corresponding pages are implemented. |
| **Interactive Tool Catalog & Search** | 🟡 Partial | The `/tax` page and India/global hubs read the live 845-entry catalog API; planned entries are visible with honest status labels and generic metadata pages. |
| **JSON-LD, OpenGraph & Breadcrumb Schema** | 🟢 Complete | `SoftwareApplication`, `FAQPage`, `BreadcrumbList` schema generation. |
| **Export & Working Paper Downloads** | 🟢 Complete | PDF, Excel (XLSX), CSV, JSON computation export directly from calculator UI. |
