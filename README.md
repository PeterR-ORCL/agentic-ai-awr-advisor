## OCI AWR Sizing Advisor — Progress Overview

### Overview

This project builds an **agentic AI system** that transforms Oracle AWR reports into **actionable performance insights and OCI sizing decisions**.

The system evolves from raw data parsing to autonomous analysis and, ultimately, to recommendation and sizing.

---

## Development Progress

### Day 1 — AWR Parsing Foundation
- Implemented ingestion of Oracle AWR `.out` files
- Built section detection (CPU, waits, SQL, etc.)
- Extracted run metadata (DB name, host, snapshots)
- Established canonical data model (`ParseResult`, `RunMetadata`)

**Outcome:** Reliable, structured extraction from raw AWR reports

---

### Day 2 — Structured Metrics Extraction
- Parsed CPU load profile metrics
- Parsed foreground wait events
- Introduced structured metric objects
- Established deterministic parsing pipeline

**Outcome:** Raw AWR text converted into structured, queryable data

---

### Day 3 — Automated Performance Issue Detection

The system now performs **deterministic performance analysis**, converting metrics into **prioritized, evidence-backed insights**.

#### Detected Issue Types

- **CPU Pressure**  
  Identifies when CPU is the dominant bottleneck.

- **SQL Concentration**  
  Detects when a small number of SQL statements dominate workload, including module attribution.

- **I/O Pressure**  
  Highlights significant User I/O wait events.

- **Commit Pressure**  
  Detects commit latency via `log file sync`.

- **Concurrency Pressure**  
  Identifies contention patterns (buffer busy waits, latch contention).

---

### Example Output

Detected Issues:
	•	cpu_pressure (high)
CPU is the dominant bottleneck, consuming 64.8% of total DB time.
	•	sql_concentration (high)
SQL concentration is high, with the top 2 SQL statements from module ‘OrderService’
accounting for 26.6% of total elapsed SQL time.
	•	io_pressure (high)
User I/O is a significant contributor, with ‘cell single block physical read’
accounting for 12.4% of DB time.
	•	commit_pressure (high)
Commit latency is material, with log file sync consuming 8.2% of DB time.
	•	concurrency_pressure (medium)
Concurrency waits are present but secondary, accounting for 2.6% of DB time.

---

## Key Capabilities

- Deterministic, explainable performance analysis  
- Evidence-backed insights with precise metrics  
- Priority-based issue detection  
- Workload attribution to application modules  

---

## Value Proposition

This system replaces manual AWR interpretation with:

- Rapid identification of performance bottlenecks  
- Consistent and repeatable analysis  
- A foundation for automated recommendations and OCI sizing  

---

## Roadmap

### Day 4 — Recommendation Layer
- Map issues → actionable tuning recommendations  
- Identify likely root causes  

### Day 5 — OCI Sizing Engine
- Translate workload → OCPU, memory, storage  
- Estimate cost and performance impact  

### Day 6 — Visualization
- HTML dashboard  
- Historical trend analysis  

### Day 7 — Agentic Layer
- Predict workload growth  
- Automate decision-making  

---

## Vision

From:

AWR Report → Manual Analysis → Guesswork

To:

AWR Report → Automated Analysis → Actionable Decisions → OCI Sizing
