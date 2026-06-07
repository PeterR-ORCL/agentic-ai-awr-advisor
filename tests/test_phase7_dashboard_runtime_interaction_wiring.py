"""Tests for Phase 7CM dashboard runtime interaction wiring."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from importlib import util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_dashboard_runtime_interaction_validation.py"


def read_dashboard_source_text() -> str:
    source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
        encoding="utf-8",
        errors="ignore",
    )
    styles_path = ROOT / "src" / "reporting" / "dashboard" / "styles.py"
    if styles_path.is_file():
        source += "\n" + styles_path.read_text(encoding="utf-8", errors="ignore")
    return source


PHASE7CM_UX_FIXTURE = """
<section id="phase7cm-source-intake-panel" data-phase7-index-source-selection="true" data-dashboard-default-state="{&quot;selectedSourceMode&quot;:&quot;local_staged&quot;,&quot;selectedSourcePath&quot;:&quot;data/input&quot;,&quot;sourceSelectionMethod&quot;:&quot;backend_path&quot;}">
  <h2>What do you want to work with?</h2>
  <p>Choose a primary path, then submit governed source intake request.</p>
  <p>The browser does not read local files and never browser-side bucket reads.</p>
  <div data-phase7-primary-entry-paths="true">
    <article data-phase7-entry-path="new_source" data-phase7-entry-source-modes="local_staged local_file object_storage">
      <strong>Load / Ingest New Source</strong>
      <p>Primary handoff: Screen 1 - Ingestion / Parser / Source Governance</p>
      <a href="screen_1_ingestion.html">Open Screen 1 Ingestion</a>
    </article>
    <article data-phase7-entry-path="existing_platform_evidence" data-phase7-entry-source-modes="existing_run">
      <strong>Use Existing Platform Evidence</strong>
      <p>Primary handoff: Screen 2 - Runtime Scope &amp; Analysis Control</p>
      <a href="screen_2_control.html">Open Screen 2 Control</a>
    </article>
  </div>
  <details data-phase7-index-technical-context="true">
  <summary>Technical Details - Runtime / Truth / Memory Context</summary>
  <section class="evidence-pane pipeline-card" data-phase7-current-runtime-pipeline="true" data-phase7-system-flow-dynamic="true">
    <div class="section-kicker">System Flow</div>
    <h2>Deterministic Analysis Pipeline</h2>
    <p>Local development fallback: data/input.</p>
    <p data-phase7-source-summary-card="pipeline_mode">Current source mode: Local folder / local staged AWR</p>
    <p data-phase7-source-summary-card="pipeline_active">Active source: data/input</p>
    <p data-phase7-source-summary-card="pipeline_validation">Current source validation: backend path validation pending</p>
    <p data-phase7-source-summary-card="pipeline_handoff">Current handoff target: Screen 3</p>
    <p>Home records path intent only. Screen 1 or Screen 2 prepares valid evidence context. Deterministic parsing, scoring, decision, and recommendation remain authoritative only after the governed backend workflow processes the selected source or selected existing evidence.</p>
    <small data-phase7-source-summary-card="pipeline_node_source">Local staged AWR source. Path: data/input.</small>
  </section>
  <section class="card secondary future-input-card" data-phase7-current-source-context="true" data-phase7-source-configuration-reference="true">
    <h2>Source Configuration Reference / Staging Context</h2>
    <p>Local development fallback: data/input.</p>
    <h3>Current Source Type</h3><p data-phase7-source-summary-card="config_type">Current source type: Local folder / local staged AWR</p>
    <h3>Current Source Location</h3><p data-phase7-source-summary-card="config_location">Current source location: data/input</p>
    <h3>Current Source Metadata</h3><p data-phase7-source-summary-card="config_candidates">Candidate AWR files: 1; .out files: 1; samples: sample.out</p>
    <h3>Current Source Validation</h3><p data-phase7-source-summary-card="config_validation">Current source validation: backend validation pending</p>
    <h3>Current Source Intake Status</h3><p data-phase7-source-summary-card="config_handoff">Current source intake status: Ready to submit governed backend Local Folder source intake.</p>
  </section>
  <p>The current verified parser path supports .out AWR reports. HTML AWR input is planned for a future parser/source adapter.</p>
  <section class="card secondary memory-explainer-card">
    <div class="section-kicker">Governed Memory</div>
    <h2>Governed Memory &amp; Semantic Recall</h2>
    <p>Governed memory preserves analysis runs, recommendations, actions, outcomes, feedback, parser unknowns, approvals, and knowledge artifacts. Semantic recall provides optional reviewer-assist context outside deterministic runtime truth generation.</p>
    <strong>Run Tracking</strong>
    <strong>Recommendation Tracking</strong>
    <strong>Action Tracking</strong>
    <strong>Outcome Tracking</strong>
    <strong>Feedback Capture</strong>
    <strong>Parser Unknowns</strong>
    <p>Runtime influence remains gated, auditable, and denied by default.</p>
  </section>
  </details>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="local_staged" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="local_staged" data-entity-type="source_mode" data-downstream-action="governed-source-intake-local-staged" data-source-selection-method="backend_path" data-source-default-path="data/input"><p>Selection state: not selected.</p></article>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="local_file" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="local_file" data-entity-type="source_mode" data-downstream-action="governed-source-intake-local-file" data-source-selection-method="os_file_picker" data-source-default-path=""><p>Selection state: not selected.</p></article>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="existing_run" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="existing_run" data-entity-type="source_mode" data-downstream-action="governed-source-handoff-existing-run" data-source-selection-method="existing_run_reference" data-source-default-run-reference=""><p>Selection state: not selected.</p></article>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="object_storage" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="object_storage" data-entity-type="source_mode" data-downstream-action="governed-source-intake-object-storage" data-source-selection-method="object_storage_metadata" data-object-storage-namespace="axxduehrw7lz" data-object-storage-bucket="agentic-ai-awr-raw" data-object-storage-object-name="awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out" data-object-storage-region="us-phoenix-1"><p>Selection state: not selected.</p></article>
  <section data-phase7-source-configuration="true">
    <label for="phase7cm-local-folder-picker">Choose Folder</label>
    <input id="phase7cm-local-folder-picker" type="file" webkitdirectory multiple data-phase7-source-picker="local_folder" data-picker-summary-target="phase7cm-local-folder-picker-summary">
    <small id="phase7cm-local-folder-picker-summary" data-phase7-picker-summary="local_folder">Your browser may label this as Upload. Folder selected. 2 files available for governed validation. 1 AWR candidates found. Nothing has been submitted yet. Folder selected by OS picker; backend validation pending; governed submit not yet performed.</small>
    <input value="data/input" data-dashboard-state-input="true" data-dashboard-state-key="selectedSourcePath" data-phase7-source-path-field="local_staged">
    <label for="phase7cm-local-file-picker">Choose File</label>
    <input id="phase7cm-local-file-picker" type="file" accept=".out" data-phase7-source-picker="local_file" data-picker-summary-target="phase7cm-local-file-picker-summary">
    <small id="phase7cm-local-file-picker-summary" data-phase7-picker-summary="local_file">File selected. Nothing has been submitted yet. Backend validation is pending until Run Governed Source Intake is clicked.</small>
    <input placeholder="/path/to/report.out or C:\\path\\to\\report.out" data-dashboard-state-input="true" data-dashboard-state-key="selectedSourcePath" data-phase7-source-path-field="local_file">
    <input placeholder="Select a service-returned run below" data-dashboard-state-input="true" data-dashboard-state-key="selectedRunReference" data-phase7-existing-run-field="true" readonly>
    <button type="button" data-phase7-existing-run-lookup-control="true" data-phase7-service-endpoint="existing_runs">Load Existing Runs</button>
    <select data-phase7-existing-run-options="true"><option>Run options load from governed service</option></select>
    <p>No prior runs found in governed persistence. Existing run lookup unavailable. Governed workflow service is not connected to DB or returned no runs.</p>
    <input value="axxduehrw7lz" data-dashboard-state-input="true" data-dashboard-state-key="objectStorageNamespace">
    <input value="agentic-ai-awr-raw" data-dashboard-state-input="true" data-dashboard-state-key="objectStorageBucket">
    <input value="awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out" data-dashboard-state-input="true" data-dashboard-state-key="objectStorageObjectName">
    <input value="us-phoenix-1" data-dashboard-state-input="true" data-dashboard-state-key="objectStorageRegion">
    <button type="button" data-phase7-object-storage-validation-control="true" data-phase7-service-endpoint="object_storage_validate">Validate Object Storage Source</button>
    <p>Object Storage is governed metadata validation only; full load, parse, and analyze remain backend-gated.</p>
    <p>Dashboard workflow service is not running. Start the service to use interactive features.</p>
  </section>
  <section data-phase7-current-selection-panel="true" data-phase7-active-source-configuration="true">
    <h3>Selected Source Summary</h3>
    <p><strong>Active Source Selection.</strong></p>
    <p>Run Local Folder Source Intake. Run Local File Source Intake. Submit Existing Run Source Handoff. Run Object Storage Source Intake.</p>
    <div data-phase7-dynamic-source-summary="true">
      <p data-phase7-source-summary-card="active">Active Source. if (mode === 'local_staged') if (mode === 'local_file') if (mode === 'existing_run') if (mode === 'object_storage')</p>
      <p data-phase7-source-summary-card="metadata">Source Metadata. Folder picker metadata. File picker metadata. Service-selected persisted run reference: RUN_HISTORY_ID:9001. Object Storage metadata. Namespace: axxduehrw7lz</p>
      <p data-phase7-source-summary-card="validation">Validation Status</p>
      <p data-phase7-source-summary-card="missing">Required Metadata / Missing Fields</p>
      <p data-phase7-source-summary-card="handoff">Execution Target</p>
      <p data-phase7-source-summary-card="action">Action State</p>
      <p data-phase7-source-summary-card="next_step">Next Step</p>
    </div>
  </section>
  <section data-phase7-runtime-source-validation="true">
    <h3>Validation / Execution Status</h3>
    <div data-phase7-runtime-source-validation-grid="true">
      <p data-phase7-source-validation-card="local_folder">Local folder validation appears here.</p>
      <p data-phase7-source-validation-card="local_file">Local file validation appears here.</p>
      <p data-phase7-source-validation-card="existing_run">Existing run lookup appears here.</p>
      <p data-phase7-source-validation-card="object_storage">Object Storage validation appears here.</p>
      <p data-phase7-source-validation-card="service" data-phase7-service-availability-status="true">Governed workflow service: local source-intake service endpoint. Local development service: scripts/dashboard_workflow_service.py.</p>
      <p data-phase7-source-validation-card="result" data-phase7-submit-result-reference="true">Request / Audit Result appears here.</p>
    </div>
  </section>
  <details data-phase7-advanced-debug-state="true"><summary>Advanced Debug State / Browser Selection State</summary>
  <p data-dashboard-selected-summary data-phase7-current-selection-summary="true">Collapsed browser selection debug state.</p>
  <dl data-phase7-source-metadata-summary="true">
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedSourceMode">local_staged</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedSourcePath">data/input</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="sourceSelectionMethod">backend_path</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderFileCount">0</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderOutFileCount">0</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderCandidateCount">0</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderAwrCandidateCount">0</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderRejectedCount">0</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderValidationStatus">backend validation pending</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderSampleFiles">none</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalRelativePaths">none</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalTotalBytes">0</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderValidationMessages">none</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileName">none</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileSize">0</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileType">unknown</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileExtension">unknown</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileValidationStatus">backend validation pending</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="awrSignatureValidation">AWR signature validation backend validation pending</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedRunReference">RUN_HISTORY_ID:9001</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="existingRunLookupStatus">valid</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="objectStorageValidationStatus">valid</dd>
    <dd data-dashboard-state-input="true" data-dashboard-state-key="objectStorageValidationMessage">Object Storage metadata accepted by governed backend validation.</dd>
  </dl>
  </details>
  <a href="screen_2_control.html">Open Screen 2 Control</a>
</section>
<section data-phase7-selection-workflow="true">
  <h3>Selection Workflow</h3>
  <ol>
    <li>Step 1: Choose a primary path: new source or existing platform evidence</li>
    <li>Step 2: Review source readiness and next governed screen</li>
    <li>Step 3: Submit a governed backend source intake request</li>
    <li>Step 4: Review request state, request ID, and audit ID</li>
    <li>Step 5: After backend completion, review generated evidence and continue Screen 1 governance</li>
  </ol>
</section>
<a data-phase7-action-control="true"
   data-screen-id="screen_1"
   data-action-type="screen1_source_intake_execute"
   data-workflow-type="screen1_source_intake_execution"
   data-target-type="source_intake"
   data-target-id="screen1-source-intake-execute"
   data-required-selection-key="selectedSourceMode"
   data-action-enabled-state="disabled-no-selection"><strong data-phase7-source-submit-label="true">Run Object Storage Source Intake</strong></a>
<p data-phase7-action-result-panel="true" data-phase7-request-id-target="true" data-phase7-audit-status-area="true">
  success/failure, Request ID and Audit record appear here.
</p>
"""

PHASE7CR_INDEX_FIXTURE = """
<section id="phase7cr-platform-entry-panel" data-phase7-index-source-selection="true">
  <h1>Platform Entry / Source Intake</h1>
  <h2>What do you want to work with?</h2>
  <p>Start here. Choose whether to begin with a new source on Screen 1 or continue with existing platform evidence on Screen 2.</p>
  <p>Home records source-path intent only. It does not validate sources, load runtime options, select scope, assign targets, decide readiness, generate diagnostics, or compare evidence.</p>
  <div data-phase7-primary-entry-paths="true">
    <a href="screen_1_ingestion.html" data-dashboard-propagate-state="true" data-phase7-entry-path="new_source" data-phase7-entry-source-modes="local_staged local_file object_storage">
      <strong>Load / Ingest New Source</strong>
      <p>Use this when the operator has a new AWR file, local staged folder, selected file, or Object Storage object metadata.</p>
      <p>Primary handoff: Screen 1 - Ingestion / Parser / Source Governance.</p>
      <span>Open Screen 1 Ingestion</span>
    </a>
    <a href="screen_2_control.html" data-dashboard-propagate-state="true" data-phase7-entry-path="existing_platform_evidence" data-phase7-entry-source-modes="existing_run">
      <strong>Use Existing Platform Evidence</strong>
      <p>Use this when evidence is already available inside the platform. Continue to Screen 2 to load runtime options, select runtime scope, choose target/time window context, and prepare comparison readiness.</p>
      <p>Primary handoff: Screen 2 - Runtime Scope &amp; Analysis Control. Screen 2 loads runtime options, selects scope/window, and prepares Target A/B comparison readiness.</p>
      <span>Open Screen 2 Control</span>
    </a>
  </div>
</section>
<section class="pipeline-card" data-phase7-current-runtime-pipeline="true" data-phase7-system-flow-dynamic="true">
  <h2>Deterministic Analysis Pipeline</h2>
  <p>The platform separates entry, intake, runtime scope, deterministic analysis, and downstream review. Home explains the starting path; Screen 1 owns new-source intake and parser governance; Screen 2 owns existing-evidence runtime scope and comparison preparation; deterministic analysis remains the source of dashboard truth.</p>
  <ol><li class="pipeline-node"><small>Evidence Context</small></li></ol>
</section>
<section><h2>Deterministic Runtime Architecture</h2><p>Runtime orchestration remains governed by backend services.</p></section>
<section><h2>Deterministic Truth vs AI Explanation</h2><p>Deterministic truth remains authoritative; AI text is explanation only.</p></section>
<section class="memory-explainer-card">
  <div class="section-kicker">Governed Memory</div>
  <h2>Governed Memory &amp; Semantic Recall</h2>
  <p>Governed memory preserves analysis runs, recommendations, actions, outcomes, feedback, parser unknowns, approvals, and knowledge artifacts. Semantic recall provides optional reviewer-assist context outside deterministic runtime truth generation.</p>
  <strong>Run Tracking</strong>
  <strong>Recommendation Tracking</strong>
  <strong>Action Tracking</strong>
  <strong>Outcome Tracking</strong>
  <strong>Feedback Capture</strong>
  <strong>Parser Unknowns</strong>
  <p>Runtime influence remains gated, auditable, and denied by default.</p>
</section>
<section><h2>LLM / Explanation Provider</h2><p>LLM output is optional explanatory support, never deterministic truth.</p></section>
<section><h2>6-Screen Product Model</h2><p>Home, 1 Ingestion, 2 Control, 3 Analysis, 4 Review, 5 Action, 6 Learning.</p></section>
"""

PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE = """
<section id="phase7cm-source-intake-panel" data-phase7-index-source-selection="true" data-dashboard-default-state="{&quot;selectedSourceMode&quot;:&quot;local_staged&quot;,&quot;selectedSourcePath&quot;:&quot;data/input&quot;,&quot;sourceSelectionMethod&quot;:&quot;backend_path&quot;}">
  <h2>New Source Intake / Validation Workflow</h2>
  <p>For new sources, configure and validate source metadata here, then continue ingestion, parser review, and source governance on Screen 1.</p>
  <p>The browser does not read local files and never browser-side bucket reads.</p>
  <section data-phase7-selection-workflow="true">
    <h3>Selection Workflow</h3>
    <ol>
      <li>Step 1: Select the new source mode or source context.</li>
      <li>Step 2: Review source readiness and configure validation through the governed service path.</li>
      <li>Step 3: Submit a governed backend source intake request.</li>
      <li>Step 4: Review request state, Request ID, and Audit record.</li>
      <li>Step 5: After backend completion, generated run evidence and the file/report table become available.</li>
    </ol>
  </section>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="local_staged" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="local_staged" data-entity-type="source_mode" data-downstream-action="governed-source-intake-local-staged" data-source-selection-method="backend_path" data-source-default-path="data/input"><p>Selection state: not selected.</p></article>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="local_file" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="local_file" data-entity-type="source_mode" data-downstream-action="governed-source-intake-local-file" data-source-selection-method="os_file_picker" data-source-default-path=""><p>Selection state: not selected.</p></article>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="object_storage" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="object_storage" data-entity-type="source_mode" data-downstream-action="governed-source-intake-object-storage" data-source-selection-method="object_storage_metadata" data-object-storage-namespace="axxduehrw7lz" data-object-storage-bucket="agentic-ai-awr-raw" data-object-storage-object-name="awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out" data-object-storage-region="us-phoenix-1"><p>Selection state: not selected.</p></article>
  <section data-phase7-source-configuration="true">
    <h3>Source Mode Configuration</h3>
    <label for="phase7cm-local-folder-picker">Choose Folder</label>
    <input id="phase7cm-local-folder-picker" type="file" webkitdirectory multiple data-phase7-source-picker="local_folder" data-picker-summary-target="phase7cm-local-folder-picker-summary">
    <small id="phase7cm-local-folder-picker-summary" data-phase7-picker-summary="local_folder">Your browser may label this as Upload. Folder selected. 2 files available for governed validation. 1 AWR candidates found. Nothing has been submitted yet. Folder selected by OS picker; backend validation pending; governed submit not yet performed.</small>
    <input value="data/input" data-dashboard-state-input="true" data-dashboard-state-key="selectedSourcePath" data-phase7-source-path-field="local_staged">
    <label for="phase7cm-local-file-picker">Choose File</label>
    <input id="phase7cm-local-file-picker" type="file" accept=".out" data-phase7-source-picker="local_file" data-picker-summary-target="phase7cm-local-file-picker-summary">
    <small id="phase7cm-local-file-picker-summary" data-phase7-picker-summary="local_file">File selected. Nothing has been submitted yet. Backend validation is pending until Run Governed Source Intake is clicked.</small>
    <input placeholder="/path/to/report.out or C:\\path\\to\\report.out" data-dashboard-state-input="true" data-dashboard-state-key="selectedSourcePath" data-phase7-source-path-field="local_file">
    <input value="axxduehrw7lz" data-dashboard-state-input="true" data-dashboard-state-key="objectStorageNamespace">
    <input value="agentic-ai-awr-raw" data-dashboard-state-input="true" data-dashboard-state-key="objectStorageBucket">
    <input value="awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out" data-dashboard-state-input="true" data-dashboard-state-key="objectStorageObjectName">
    <input value="us-phoenix-1" data-dashboard-state-input="true" data-dashboard-state-key="objectStorageRegion">
    <input value="backend validation pending" data-dashboard-state-input="true" data-dashboard-state-key="objectStorageValidationStatus">
    <button type="button" data-phase7-object-storage-validation-control="true" data-phase7-service-endpoint="object_storage_validate">Validate Object Storage Source</button>
    <p>Object Storage is governed metadata validation only; full load, parse, and analyze remain backend-gated.</p>
    <p>Dashboard workflow service is not running. Start the service to use interactive features.</p>
    <p>AWR signature validation. The current verified parser path supports .out AWR reports. HTML AWR input is planned for a future parser/source adapter.</p>
  </section>
  <section data-phase7-current-selection-panel="true" data-phase7-active-source-configuration="true">
    <h3>Selected Source Summary</h3>
    <p><strong>Active Source Selection.</strong></p>
    <p>Run Local Folder Source Intake. Run Local File Source Intake. Run Object Storage Source Intake.</p>
    <div data-phase7-dynamic-source-summary="true">
      <p data-phase7-source-summary-card="active"><strong>Active Source</strong> No source selected</p>
      <p data-phase7-source-summary-card="metadata"><strong>Source Metadata</strong> Select a source mode or choose a folder/file before submitting.</p>
      <p data-phase7-source-summary-card="validation"><strong>Validation Status</strong> Not checked</p>
      <p data-phase7-source-summary-card="missing"><strong>Required Metadata / Missing Fields</strong> Select a source to see required metadata.</p>
      <p data-phase7-source-summary-card="handoff"><strong>Execution Target</strong> No execution target selected.</p>
      <p data-phase7-source-summary-card="action"><strong>Action State</strong> Select a source to continue.</p>
      <p data-phase7-source-summary-card="next_step"><strong>Next Step</strong> Choose a source mode, then configure source metadata.</p>
    </div>
    <template>Folder picker metadata. File picker metadata. Object Storage metadata. Namespace: if (mode === 'local_staged') if (mode === 'local_file') if (mode === 'object_storage')</template>
  </section>
  <section data-phase7-runtime-source-validation="true">
    <h3>Validation / Execution Status</h3>
    <div data-phase7-runtime-source-validation-grid="true">
      <p data-phase7-source-validation-card="local_folder">Local folder validation appears here.</p>
      <p data-phase7-source-validation-card="local_file">Local file validation appears here.</p>
      <p data-phase7-source-validation-card="object_storage">Object Storage validation appears here.</p>
      <p data-phase7-source-validation-card="service" data-phase7-service-availability-status="true">Governed workflow service: local source-intake service endpoint. Local development service: scripts/dashboard_workflow_service.py.</p>
      <p data-phase7-source-validation-card="result" data-phase7-submit-result-reference="true">Request / Audit Result appears here.</p>
    </div>
  </section>
  <details data-phase7-advanced-debug-state="true"><summary>Advanced Debug State / Browser Selection State</summary>
    <p data-dashboard-selected-summary data-phase7-current-selection-summary="true">Collapsed browser selection debug state.</p>
    <dl data-phase7-source-metadata-summary="true">
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedSourceMode">local_staged</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedSourcePath">data/input</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="sourceSelectionMethod">backend_path</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderFileCount">0</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderOutFileCount">0</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderCandidateCount">0</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderAwrCandidateCount">0</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderRejectedCount">0</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderValidationStatus">backend validation pending</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderSampleFiles">none</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalRelativePaths">none</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalTotalBytes">0</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFolderValidationMessages">none</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileName">none</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileSize">0</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileType">unknown</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileExtension">unknown</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="selectedLocalFileValidationStatus">backend validation pending</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="awrSignatureValidation">AWR signature validation backend validation pending</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="objectStorageValidationStatus">valid</dd>
      <dd data-dashboard-state-input="true" data-dashboard-state-key="objectStorageValidationMessage">Object Storage metadata accepted by governed backend validation.</dd>
    </dl>
  </details>
  <a data-phase7-action-control="true"
     data-screen-id="screen_1"
     data-action-type="screen1_source_intake_execute"
     data-workflow-type="screen1_source_intake_execution"
     data-target-type="source_intake"
     data-target-id="screen1-source-intake-execute"
     data-required-selection-key="selectedSourceMode"
     data-action-enabled-state="disabled-no-selection"><strong data-phase7-source-submit-label="true">Run Object Storage Source Intake</strong></a>
  <p data-phase7-action-result-panel="true" data-phase7-request-id-target="true" data-phase7-audit-status-area="true">
    success/failure, Request ID and Audit record appear here.
  </p>
  <section>
    <p>No generated run evidence is available yet.</p>
    <p>No generated file/report rows are available yet.</p>
    <p>No parser health is available yet.</p>
    <p>No parser unknown-signal results are available yet.</p>
    <p>No parser governance backlog is available yet.</p>
  </section>
</section>
"""

PHASE7CR_INDEX_AND_SCREEN1_FIXTURES = {
    "awr_dashboard/index.html": PHASE7CR_INDEX_FIXTURE,
    "awr_dashboard/screen_1_ingestion.html": PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE,
}

PHASE7CP_SCREEN3_FIXTURE = """
<section data-phase7-runtime-interaction-panel="true">
  <title>Screen 2 - Runtime Scope & Analysis Control</title>
  <h1>Screen 2 - Runtime Scope & Analysis Control</h1>
  <h2>Screen 2 - Runtime Scope & Analysis Control</h2>
  <h3>Runtime Evidence Path</h3>
  <h4>Evidence path status</h4>
  <p>Screen 2 receives the operator path from Platform Entry or the completed artifact state from Screen 1.</p>
  <p>DB-backed runtime options to select scope, interval, and comparison targets.</p>
  <div>None selected. No valid runtime evidence path yet. Choose a path from Platform Entry.</div>
  <h3>Load Runtime Options</h3>
  <div hidden>
  <p>Runtime Scope Selection</p>
  <h3>Select Runtime Scope</h3>
  <h3>Load Runtime Options</h3>
  <p>screen2-control-card-grid</p>
  <p>screen2-control-info-box</p>
  <button type="button" class="phase7cm-service-button screen3-runtime-options-button" data-screen3-runtime-options-load="true">Load available runtime options</button>
  <p>Dashboard workflow service is available, but it does not expose the runtime-control options route. Restart dashboard_workflow_service.py.</p>
  <p>/phase7/dashboard/screen3/options</p>
  <p>screen3_load_runtime_options</p>
  <p>screen3-runtime-filter-panel</p>
  <p>data-screen3-runtime-options-target="runtime-filter-application"</p>
  <p>data-screen3-runtime-options-target="runtime-filter-db"</p>
  <p>data-screen3-runtime-options-target="runtime-filter-dbid"</p>
  <p>data-screen3-runtime-options-target="runtime-filter-instance"</p>
  <p>data-screen3-runtime-options-target="runtime-filter-host"</p>
  <p>data-screen3-runtime-options-target="runtime-filter-source-type"</p>
  <p>data-screen3-runtime-options-target="runtime-filter-time-range"</p>
  <p>screen3-filter-select</p>
  <p>screen3RuntimeFilterSearch</p>
  <p>Apply Filters</p>
  <p>Clear Filters</p>
  <p>data-screen3-filtered-result-count</p>
  <p>data-screen3-runtime-sort</p>
  <p>data-screen3-table-sort</p>
  <p>data-screen3-table-filter</p>
  <p>data-screen3-table-filter-toggle</p>
  <p>data-screen3-clear-table-filters</p>
  <p>data-screen3-table-count</p>
  <p>data-screen3-table-sort-summary</p>
  <p>data-screen3-table-filter-summary</p>
  <p>data-screen3-table-id="screen3-runtime-inventory"</p>
  <p>data-screen3-table-id="screen3-intervals"</p>
  <p>data-screen3-table-id="screen3-target-a-options"</p>
  <p>data-screen3-table-id="screen3-target-b-options"</p>
  <p>screen3-selection-legend</p>
  <p>screen3-selected-context-strip</p>
  <p>screen3-selected-runtime-row</p>
  <p>screen3-selected-interval-row</p>
  <p>screen3-selected-advanced-row</p>
  <p>initializeScreen3Tables</p>
  <p>data-screen3-sort-indicator</p>
  <p>screen3SelectedRuntimeScopeRowId</p>
  <p>screen3SelectedTargetARowId</p>
  <p>screen3SelectedTargetBRowId</p>
  <p>screen3RuntimeScopeSelectionSource</p>
  <p>screen3TargetASelectionSource</p>
  <p>screen3TargetBSelectionSource</p>
  <p>State source:</p>
  <p>screen3RuntimeRowIdentity</p>
  <p>screen3IntervalRowIdentity</p>
  <p>screen3-table-sort-button</p>
  <p>screen3-table-filter-toggle</p>
  <p>position: sticky</p>
  <p>screen3-runtime-scope-table</p>
  <p>data-screen3-runtime-options-target="runtime-scope-rows"</p>
  <p>data-screen3-runtime-options-target="interval-rows"</p>
  <p>screen3-interval-full-width-panel</p>
  <p>screen3ActiveSelectionTarget</p>
  <p>Application: Not available</p>
  <h4>Runtime Scope Filters</h4>
  <h4>Filtered AWR / Run / Report Results</h4>
  <h4>Selected AWR / Report Row</h4>
  <p>Apply selection to</p>
  <p>Runtime Scope</p>
  <h3>Snapshot / Interval Selection</h3>
  <p>Apply interval to</p>
  <p>Application / DB Name / DBID / Instance / Host/System</p>
  <p>AWR / Run and Snapshot / Time Window</p>
  <h4>Selected Runtime Scope / Assignment Summary</h4>
  <p>Effective Snapshot / Window</p>
  <p>Comparison Target Preparation</p>
  <h3>Resolve Comparison Targets</h3>
  <p>Target A and Target B identify selected candidate sides for later comparison review.</p>
  <p>Cached Target A/B labels restore operator context only; readiness must be confirmed by current governed backend metadata before downstream comparison review.</p>
  <p>Assignment records selection context only.</p>
  <p>Only its selected row gets the strong table highlight.</p>
  <p>Targets: Target A unresolved · Target B unresolved</p>
  <p>Target A Resolution</p>
  <p>Target B Resolution</p>
  <p>source_type + scope_type + scope_value + time_window + resolution_state + readiness_state</p>
  <p>Source Type / Scope Type / Scope Value / Time window / Resolution / Readiness / Missing gates</p>
  <p>Resolved AWRs</p>
  <p>Resolved Windows</p>
  <p>Comparison Readiness / Request Handoff</p>
  <p>Readiness is not a comparison result</p>
  <p>Comparison &amp; Review Controls</p>
  <p>Both Comparable</p>
  <p>load_required</p>
  <p>Current DB history</p>
  <p>Similar AWRs</p>
  <p>Cluster baseline</p>
  <p>Fleet baseline</p>
  <h3>Review Mode</h3>
  <p>Diagnosis</p>
  <p>Historical proof</p>
  <p>Anomaly review</p>
  <p>Period comparison</p>
  <p>Similarity review</p>
  <p>Governed Request Handoff</p>
  <h3>Submit Governed Action and Review Result</h3>
  <h3 class="screen3-governed-actions-card">Governed Actions</h3>
  <h3>Request / Result Receipt</h3>
  <p>Request receipt is not deterministic analysis truth unless a governed deterministic service returns a real output artifact reference.</p>
  <p>Request ID, transaction ID, audit reference, persistence, and output fields are displayed from the service response only.</p>
  <p>If receipt fields are restored from browser state, they are prior backend-returned context only until a current backend response supersedes them.</p>
  <p>A governed request/audit record may be created only when the backend returns that state.</p>
  <p>Backend status is service-returned only. Missing gates mean request receipt, not analysis execution or comparison output.</p>
  <p>screen3-result-summary-banner</p>
  <h4>Comparison Request / Handoff Summary</h4>
  <p>Requested Artifact / Reference</p>
  <p>Screen 4 Handoff</p>
  <dl>
    <dt>Selected source mode</dt>
    <dt>Selected application</dt>
    <dt>Selected DB</dt>
    <dt>Selected DBID</dt>
    <dt>Selected host</dt>
    <dt>Selected instance</dt>
    <dt>Selected AWR/run</dt>
    <dt>Selected snapshot/window</dt>
    <dt>Runtime scope</dt>
    <dt>Comparison mode</dt>
    <dt>Comparison Target A</dt>
    <dt>Comparison Target B</dt>
    <dt>Target A readiness</dt>
    <dt>Target B readiness</dt>
    <dt>Both targets comparable</dt>
    <dt>Requested artifact/reference</dt>
    <dt>Screen 4 handoff</dt>
    <dt>Review mode</dt>
    <dt>Request ID</dt>
    <dt>Transaction ID</dt>
    <dt>Validation status</dt>
    <dt>Audit ID/reference</dt>
    <dt>Persistence</dt>
    <dt>Backend / Gate Status</dt>
    <dt>Output artifact</dt>
    <dt>New run/output reference</dt>
    <dt>Existing run truth</dt>
    <dt>Next step</dt>
  </dl>
  <h3>Runtime Safety and Selection Impact</h3>
  <p>Local selection changes only browser/local request context.</p>
  <p>Existing run truth unchanged</p>
  <p>Runtime options route unavailable</p>
  <p>route available</p>
  <p>No runtime options found</p>
  <p>Runtime options loaded</p>
  <p>runtime_options_source_tables</p>
  <p>table_exists</p>
  <p>key_columns_used</p>
  <p>included_in_screen3_runtime_options</p>
  <p>AWR_SNAPSHOT</p>
  <p>screen3RuntimeOptionsCache</p>
  <p>screen3-runtime-options-v1</p>
  <p>Runtime options restored from browser cache</p>
  <p>it is not current backend, runtime-options, readiness, request, or evidence truth</p>
  <p>Continuity only; not active backend truth</p>
  <p>Dashboard workflow service unavailable. Cached runtime options can remain visible for continuity only</p>
  <p>Cached runtime options are restored for continuity only. Re-query the workflow service before using runtime options for active evidence readiness.</p>
  <p>Cached Screen 2 state restores operator context only.</p>
  <p>failed refresh must remain visible and must not promote cache to current truth.</p>
  <p>Cached Screen 2 state restores operator context only.</p>
  <p>Cache Status</p>
  <p>Generated at build time</p>
  <p>Dashboard generated without DB context</p>
  <p>AI DB:</p>
  <p>Workflow:</p>
  <p>LLM:</p>
  <p>data-dashboard-runtime-badge="true"</p>
  <p>data-runtime-badge-hydration="in-place"</p>
  <p>data-dashboard-runtime-workflow-status="true"</p>
  <p>runtime-badge-hydrated</p>
  <p>readStoredWorkflowStatus</p>
  <p>screen3LiveServiceStatusSource</p>
  <p>screen3LiveServiceStatusCheckedAt</p>
  <p>screen3WorkflowRuntimeFreshChecked</p>
  <p>dashboardRuntimeModeSuppressesCachedWorkflow</p>
  <p>Not checked</p>
  <p>Available (cached)</p>
  <p>Advanced target picker: external / baseline options</p>
  <a data-phase7-action-control="true"
     data-screen-id="screen_3"
     data-action-type="screen3_active_reanalysis"
     data-workflow-type="screen3_runtime_control_center"
     data-target-type="backend_execution_request"
     data-target-id="screen3-selected-source-scope"
     data-required-selection-key="selectedSourceMode"
     data-execution-mode="local_backend_execution">Analyze Selection</a>
  </div>
</section>
"""

PHASE7M_DOWNSTREAM_GATE_FIXTURES = {
    "screen_3_analysis.html": (
        '<section data-dashboard-evidence-gate-empty="true">'
        "<h2>Evidence Handoff Required</h2>"
        "<p>No diagnostic evidence is selected yet.</p>"
        "</section>"
        '<div data-dashboard-evidence-gated-content="true" hidden>'
        "Current Diagnostic Drivers. "
        "The Diagnostic Snapshot explains the currently selected deterministic evidence context. "
        "If this context is Target A or Target B, Screen 3 explains that target's individual deterministic diagnostic output only. "
        "Target labels do not change diagnosis, scores, confidence, severity, recommendations, evidence, or thresholds. "
        "Screen 3 does not compare Target A vs Target B, decide improvement/degradation, assign comparison readiness, compute comparison results, render comparison violin panels, or change diagnostic truth. "
        "A-vs-B comparison review and future comparison violin panels remain a Screen 4 responsibility once deterministic comparison output exists."
        "</div>"
    ),
    "screen_4_historical_review.html": (
        '<section data-dashboard-evidence-gate-empty="true">'
        "<h2>Evidence Handoff Required</h2>"
        "<p>No review evidence is selected yet.</p>"
        "</section>"
        '<div data-dashboard-evidence-gated-content="true" hidden>'
        "Evidence Review / Historical Supporting Context. "
        "No review evidence is selected yet. Complete source intake or select a runtime scope first. "
        "Target A/B preparation alone does not create Screen 4 comparison evidence. "
        "Evidence Review Modes. "
        "Screen 4 reflects upstream selected source, run, scope, and target context for display only. "
        "Deterministic evidence remains authoritative. "
        "Selected context does not create diagnosis, scores, readiness, comparison output, recommendations, actions, outcomes, or learning state. "
        "Screen 4 separates Historical Supporting Context, contract-bound Deep Analysis, and deterministic Comparative Review. "
        "Historical Review is active. "
        "It reviews deterministic trends, anomalies, historical baseline context, historical period context, and similarity evidence already available on this page as supporting context only. "
        "Deep Analysis renders guarded state, contract-backed evidence, and selected visual evidence only after the deterministic current-scope contract validates. "
        "Historical rows remain supporting context; cache, prepared Target A/B, comparative output, and LLM text do not create Deep Analysis evidence. "
        "Comparative Review requires deterministic comparison output before evidence can be reviewed here. "
        "Target A/B prepared-only state is not comparison output. "
        "Screen 4 does not compute comparison or comparative graphics in the browser. "
        "Comparative Review Guarded State. "
        "Target A/B selections are preparation only. "
        "Comparative Review is not ready yet. "
        "No governed deterministic comparison output has been returned to Screen 4. "
        "Prepared Target A/B context can identify what should be compared, but it does not create comparison evidence. "
        "No comparison graphics are available because no validated deterministic comparison output contract is present. "
        "Future A/B comparison violin panels belong on Screen 4 but may render only from validated deterministic comparison output. "
        "LLM-assisted wording may explain validated deterministic comparison output only after that output exists. "
        "it does not compute comparison meaning or decide outcome direction."
        "</div>"
    ),
    "screen_5_recommendation_action.html": (
        '<section data-dashboard-evidence-gate-empty="true">'
        "<h2>Evidence Handoff Required</h2>"
        "<p>No recommendation/action context is selected yet.</p>"
        "</section>"
        '<div data-dashboard-evidence-gated-content="true" hidden>'
        "Action Rationale. "
        "LLM-assisted wording may explain deterministic recommendation meaning, action rationale, governed action request context, outcome capture meaning, and post-action evidence context when available. "
        "Wording-only explanation does not change recommendation truth, action state, owner/status truth, outcome state, validation result, or future-run behavior."
        "</div>"
    ),
    "screen_6_fleet_overview.html": (
        '<section data-dashboard-evidence-gate-empty="true">'
        "<h2>Evidence Handoff Required</h2>"
        "<p>No learning governance context is selected yet.</p>"
        "</section>"
        '<div data-dashboard-evidence-gated-content="true" hidden>'
        "Nearest Similar AWRs. "
        "LLM-assisted wording may explain learning governance, candidate meaning, materialization meaning, runtime eligibility meaning, model registry/governance state, and why materialization and runtime eligibility are separate. "
        "Wording-only explanation does not accept/reject candidates, materialize candidates, activate runtime eligibility, train/activate models, change registry state, or change future-run behavior."
        "</div>"
    ),
}


def validation_module():
    spec = util.spec_from_file_location(
        "phase7_dashboard_runtime_interaction_validation_test_module",
        SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load {SCRIPT}")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def screen1_source_intake_request(
    mode: str = "local_staged",
    payload_overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "selectedSourceMode": mode,
        "source_type": mode,
        "source_channel": mode,
        "sourceSelectionMethod": "backend_path",
        "selectedSourcePath": "data/input",
        "target_screen": "screen_1",
        "browser_file_read_attempted": False,
        "browser_file_upload_performed": False,
        "browser_object_storage_access_attempted": False,
        "browser_db_query_attempted": False,
        "browser_parsing_performed": False,
        "direct_object_storage_execution_attempted": False,
        "run_analysis_coupling": False,
        "client_completed_artifact_ready": False,
        "client_artifact_ready_claimed": False,
    }
    if payload_overrides:
        payload.update(payload_overrides)
    return {
        "screen_id": "screen_1",
        "action_type": "screen1_source_intake_execute",
        "workflow_type": "screen1_source_intake_execution",
        "actor_id": "ACTOR-LOCAL-TEST",
        "target_type": "source_intake",
        "target_id": "SCREEN1-SOURCE-INTAKE-EXECUTE",
        "execution_mode": "governed_backend_execution",
        "runtime_influence_granted": False,
        "phase4i_mutation_allowed": False,
        "phase8_behavior": False,
        "run_analysis_coupling": False,
        "payload": payload,
    }


class Phase7DashboardRuntimeInteractionWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generated_dir = tempfile.TemporaryDirectory()
        module = validation_module()
        generated = "\n".join(
            (
                '<section data-phase7-runtime-interaction-panel="true">'
                f'<button data-phase7-action-control="true" '
                f'data-screen-id="{screen_id}" '
                f'data-action-type="{action_type}" '
                f'data-workflow-type="{screen_id}_{action_type}" '
                f'data-target-type="unit" '
                f'data-target-id="{screen_id}-{action_type}" '
                f'data-required-selection-key="selectedSourceMode">Submit</button>'
                "</section>"
            )
            for screen_id, action_types in module.REQUIRED_SCREEN_ACTIONS.items()
            for action_type in action_types
        )
        for relative_path in module.GENERATED_DASHBOARD_FILES:
            file_name = Path(relative_path).name
            content = ""
            if file_name == "index.html":
                content += PHASE7CR_INDEX_FIXTURE
            if file_name == "screen_1_ingestion.html":
                content += generated + PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE
            if file_name == "screen_2_control.html":
                content += generated + PHASE7CP_SCREEN3_FIXTURE
            content += PHASE7M_DOWNSTREAM_GATE_FIXTURES.get(file_name, "")
            (Path(cls.generated_dir.name) / Path(relative_path).name).write_text(
                content,
                encoding="utf-8",
            )
        cls.completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--json",
                "--generated-dir",
                cls.generated_dir.name,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
            shell=False,
        )
        cls.payload = json.loads(cls.completed.stdout)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.generated_dir.cleanup()

    def test_validation_script_emits_valid_json(self) -> None:
        self.assertEqual(0, self.completed.returncode, self.completed.stderr)
        self.assertEqual("Phase 7", self.payload["phase"])
        self.assertEqual("7CM", self.payload["subphase"])
        self.assertEqual(
            "DASHBOARD_RUNTIME_INTERACTION_NOT_WIRED",
            self.payload["blocker_id"],
        )
        self.assertIs(self.payload["dashboard_runtime_interaction_ready"], True)
        self.assertIs(self.payload["blocker_active"], False)

    def test_inert_preview_only_sample_keeps_blocker_active(self) -> None:
        module = validation_module()
        result = module.validate_dashboard_runtime_interaction(
            source_text='<div data-preview-only="true">Preview only</div>',
            generated_texts={},
            service_exists=False,
            contract_exists=False,
        )
        self.assertIs(result["dashboard_runtime_interaction_ready"], False)
        self.assertIs(result["blocker_active"], True)
        self.assertIn("DASHBOARD_RUNTIME_INTERACTION_NOT_WIRED", result["blocker_id"])

    def test_index_source_selection_screen_is_represented(self) -> None:
        screens = self.payload["screens"]
        self.assertEqual(["screen_1", "screen_3"], sorted(screens))
        self.assertEqual("passed", screens["screen_1"]["status"])
        self.assertIn(
            "screen1_source_intake_execute",
            screens["screen_1"]["present_action_types"],
        )
        self.assertEqual("passed", screens["screen_3"]["status"])
        self.assertIn(
            "screen3_active_reanalysis",
            screens["screen_3"]["present_action_types"],
        )
        self.assertEqual(
            "index_source_selection_runtime_workflow",
            self.payload["scope"],
        )
        self.assertIn("7CO Screen 2", self.payload["deferred_screens"][0])
        self.assertIn("7CT cross-screen", self.payload["deferred_screens"][-1])

    def test_index_source_card_selection_state_keys_are_supported(self) -> None:
        module = validation_module()
        source = read_dashboard_source_text()
        supported_keys = module.extract_dashboard_state_keys(source)

        self.assertIn("selectedSourceMode", supported_keys)
        self.assertIn("selectedSourceContext", supported_keys)
        self.assertIn("selectedSourcePath", supported_keys)
        self.assertIn("sourceSelectionMethod", supported_keys)
        self.assertIn("selectedLocalFolderFileCount", supported_keys)
        self.assertIn("selectedLocalFolderOutFileCount", supported_keys)
        self.assertIn("selectedLocalFolderSampleFiles", supported_keys)
        self.assertIn("selectedLocalRelativePaths", supported_keys)
        self.assertIn("selectedLocalTotalBytes", supported_keys)
        self.assertIn("selectedLocalFolderCandidateCount", supported_keys)
        self.assertIn("selectedLocalFolderAwrCandidateCount", supported_keys)
        self.assertIn("selectedLocalFolderRejectedCount", supported_keys)
        self.assertIn("selectedLocalFolderValidationStatus", supported_keys)
        self.assertIn("selectedLocalFolderValidationMessages", supported_keys)
        self.assertIn("selectedLocalFileName", supported_keys)
        self.assertIn("selectedLocalFileSize", supported_keys)
        self.assertIn("selectedLocalFileType", supported_keys)
        self.assertIn("selectedLocalFileExtension", supported_keys)
        self.assertIn("selectedLocalFileValidationStatus", supported_keys)
        self.assertIn("awrSignatureValidation", supported_keys)
        self.assertIn("selectedRunReference", supported_keys)
        self.assertIn("existingRunLookupStatus", supported_keys)
        self.assertIn("existingRunLookupMessage", supported_keys)
        self.assertIn("existingRunLookupCount", supported_keys)
        self.assertIn("objectStorageNamespace", supported_keys)
        self.assertIn("objectStorageBucket", supported_keys)
        self.assertIn("objectStorageObjectName", supported_keys)
        self.assertIn("objectStorageRegion", supported_keys)
        self.assertIn("objectStorageValidationStatus", supported_keys)
        self.assertIn("objectStorageValidationMessage", supported_keys)
        self.assertIn("screen1SourceIntakeExecutionStatus", supported_keys)
        self.assertIn("screen1GeneratedArtifactPath", supported_keys)
        self.assertIn("dashboardEvidenceReady", supported_keys)
        self.assertIn("sourceMode: 'selectedSourceMode'", source)
        self.assertIn("'source-mode': 'selectedSourceMode'", source)
        self.assertIn("source_type: dashboardState.selectedSourceMode", source)
        self.assertIn("source_channel: dashboardState.selectedSourceMode", source)
        self.assertIn("sourceSelectionSessionId: dashboardState.sourceSelectionSessionId", source)
        self.assertIn("browser_truth_boundary", source)
        self.assertIn("client_completed_artifact_ready: false", source)
        self.assertIn('data-dashboard-select-key="selectedSourceMode"', source)
        self.assertIn('data-required-selection-key="selectedSourceMode"', source)

        coverage = module.validate_dashboard_state_key_coverage(
            source,
            PHASE7CR_INDEX_AND_SCREEN1_FIXTURES,
        )
        self.assertEqual("passed", coverage["status"])

    def test_index_source_card_selection_click_path_contract_is_validated(self) -> None:
        module = validation_module()
        source = read_dashboard_source_text()
        result = module.validate_index_source_selection_behavior_contract(
            source,
            PHASE7CR_INDEX_AND_SCREEN1_FIXTURES,
        )
        self.assertEqual("passed", result["status"])

        missing_summary = PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE.replace(
            'data-phase7-action-result-panel="true"',
            'data-phase7-action-result-panel="missing"',
        )
        failed = module.validate_index_source_selection_behavior_contract(
            source,
            {
                "awr_dashboard/index.html": PHASE7CR_INDEX_FIXTURE,
                "awr_dashboard/screen_1_ingestion.html": missing_summary,
            },
        )
        self.assertEqual("failed", failed["status"])
        self.assertIn("generated Screen 1 missing", failed["reason"])

    def test_os_file_and_folder_picker_support_is_validated(self) -> None:
        module = validation_module()
        source = read_dashboard_source_text()
        result = module.validate_picker_source_selection_support(
            source,
            PHASE7CR_INDEX_AND_SCREEN1_FIXTURES,
        )
        self.assertEqual("passed", result["status"])

        missing_folder_picker = PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE.replace(
            'data-phase7-source-picker="local_folder"',
            'data-phase7-source-picker="missing_folder"',
        )
        failed = module.validate_picker_source_selection_support(
            source,
            {
                "awr_dashboard/index.html": PHASE7CR_INDEX_FIXTURE,
                "awr_dashboard/screen_1_ingestion.html": missing_folder_picker,
            },
        )
        self.assertEqual("failed", failed["status"])
        self.assertIn("local_folder", failed["reason"])

    def test_screen1_source_intake_uses_pollable_operator_feedback_contract(self) -> None:
        source = read_dashboard_source_text()

        self.assertIn("PHASE7_ACTION_STATUS_ENDPOINT", source)
        self.assertIn("PHASE7_HEALTH_ENDPOINT", source)
        self.assertIn("verifyScreen1SourceIntakeService", source)
        self.assertIn("pollScreen1SourceIntakeStatus", source)
        self.assertIn("screen1SourceIntakeStatusEndpoint", source)
        self.assertIn("screen1-source-intake-result", source)
        self.assertIn("completed_artifact_ready", source)
        self.assertIn("screen1SourceIntakeServiceRestartCommand", source)
        self.assertIn("Workflow service supports screen1_source_intake_execute", source)

    def test_screen1_source_intake_reconciles_stored_request_on_page_load(self) -> None:
        source = read_dashboard_source_text()

        self.assertIn("function reconcileScreen1SourceIntakeStatus(root, state)", source)
        self.assertIn("screen1SourceIntakeActionRequestFromState(element, safeState)", source)
        self.assertIn("invokePhase7Get(screen1SourceIntakeStatusEndpoint(requestId))", source)
        self.assertIn("readLocalStorageState()", source)
        self.assertIn("parseHashState(window.location.hash)", source)
        self.assertIn("reconcileScreen1SourceIntakeStatus(scope, appliedState)", source)
        self.assertIn("reconcileScreen1SourceIntakeStatus(document, appliedState)", source)
        self.assertIn("Polling resumed after page navigation", source)
        self.assertIn("scheduleScreen1SourceIntakePoll(element, actionRequest, Date.now())", source)

    def test_screen1_source_intake_status_matrix_stops_terminal_statuses(self) -> None:
        source = read_dashboard_source_text()

        self.assertIn("function screen1SourceIntakeStatusIsRunning(status)", source)
        self.assertIn("function screen1SourceIntakeStatusIsTerminal(status)", source)
        for status in (
            "accepted",
            "pending",
            "running",
            "completed",
            "completed_artifact_ready",
            "failed",
            "failed_safely",
            "rejected",
            "timed_out",
        ):
            self.assertIn(status, source)
        self.assertIn("finishScreen1SourceIntakeCompleted(element, actionRequest, body)", source)
        self.assertIn("failScreen1SourceIntake(", source)
        self.assertIn("clearScreen1SourceIntakePolling()", source)

    def test_screen1_source_intake_persists_request_id_before_backend_response(self) -> None:
        source = read_dashboard_source_text()

        self.assertIn("request_id: actionRequest.request_id", source)
        self.assertIn("payload.request_id ||", source)
        self.assertIn("nextState.sourceHandoffRequestId ||", source)
        self.assertIn("nextState.sourceHandoffRequestId = requestId", source)
        self.assertIn("screen1SourceIntakePayloadWithRequest(actionRequest, result.payload)", source)

    def test_screen1_completed_source_intake_hydrates_visible_ui_from_persisted_state(self) -> None:
        source = read_dashboard_source_text()

        self.assertIn("SCREEN1_SOURCE_INTAKE_DURABLE_STATE_KEYS", source)
        self.assertIn("screen1SourceIntakeStateIsCompletedArtifactReady", source)
        self.assertIn("screen1SourceIntakeHasPersistedRequest(nextState)", source)
        self.assertIn("Object.assign(nextState, durableScreen1State)", source)
        self.assertIn("if (screen1SourceIntakeStateIsCompletedArtifactReady(safeState))", source)
        self.assertIn("Completed source intake request", source)
        self.assertIn("Source intake completed with artifact-ready status", source)
        self.assertIn("No source intake request has been submitted.", source)
        self.assertLess(
            source.index("screen1SourceIntakeHasPersistedRequest(safeState)"),
            source.index("active: 'No source selected'"),
        )

    def test_screen1_terminal_source_intake_status_panel_hydrates_without_reload_loop(self) -> None:
        source = read_dashboard_source_text()

        self.assertIn("function screen1SourceIntakePayloadFromState(actionRequest, state)", source)
        self.assertIn("function hydrateScreen1SourceIntakeStatusFromState(root, state)", source)
        self.assertIn("dashboard_regenerated: artifactReady", source)
        self.assertIn("Generated artifact path", source)
        self.assertIn("const terminalStoredStatus = screen1SourceIntakeStatusIsTerminal(currentStatus)", source)
        self.assertIn("hydrateScreen1SourceIntakeStatusFromState(scope, safeState)", source)
        self.assertIn("Backend status confirms generated artifact readiness", source)
        self.assertIn("setScreen1GeneratedArtifactReadyState(true, body)", source)

    def test_pipeline_source_summary_is_compact_and_overflow_safe(self) -> None:
        module = validation_module()
        source = read_dashboard_source_text()

        result = module.validate_pipeline_source_summary(
            source,
            {"awr_dashboard/index.html": PHASE7CR_INDEX_FIXTURE},
        )
        self.assertEqual("passed", result["status"])
        self.assertIn("sourcePipelineActiveSummary", source)
        self.assertIn("sourcePipelineNodeSummary", source)
        self.assertIn("Object Storage source selected. Object:", source)
        self.assertIn("pipeline_node_source: pipelineNode", source)

        generated_with_full_object_in_pipeline = PHASE7CR_INDEX_FIXTURE.replace(
            "The platform separates entry, intake, runtime scope, deterministic",
            "Object Storage: agentic-ai-awr-raw/awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out. The platform separates entry, intake, runtime scope, deterministic",
        )
        failed = module.validate_pipeline_source_summary(
            source,
            {"awr_dashboard/index.html": generated_with_full_object_in_pipeline},
        )
        self.assertEqual("failed", failed["status"])
        self.assertIn("full Object Storage object path", failed["reason"])

    def test_governed_memory_block_uses_production_wording(self) -> None:
        module = validation_module()

        result = module.validate_governed_memory_production_wording(
            {"awr_dashboard/index.html": PHASE7CR_INDEX_FIXTURE},
        )
        self.assertEqual("passed", result["status"])

        generated_with_phase_wording = PHASE7CR_INDEX_FIXTURE.replace(
            '<div class="section-kicker">Governed Memory</div>',
            '<div class="section-kicker">Phase 6</div>',
        )
        failed = module.validate_governed_memory_production_wording(
            {"awr_dashboard/index.html": generated_with_phase_wording},
        )
        self.assertEqual("failed", failed["status"])
        self.assertIn("phase reference", failed["reason"])

    def test_html_awr_is_not_advertised_as_phase7_supported_input(self) -> None:
        module = validation_module()
        source = read_dashboard_source_text()

        self.assertIn("PHASE7CM_ALLOWED_LOCAL_FILE_EXTENSIONS = Object.freeze(['out'])", source)
        self.assertIn("PHASE7CM_AWR_CANDIDATE_EXTENSIONS = Object.freeze(['out'])", source)
        self.assertIn('accept=".out"', PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE)
        self.assertNotIn('accept=".out,.txt,.html,.awr"', PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE)

        generated_with_html_accept = PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE.replace(
            'accept=".out"',
            'accept=".out,.txt,.html,.awr"',
        )
        failed = module.validate_picker_source_selection_support(
            source,
            {
                "awr_dashboard/index.html": PHASE7CR_INDEX_FIXTURE,
                "awr_dashboard/screen_1_ingestion.html": generated_with_html_accept,
            },
        )
        self.assertEqual("failed", failed["status"])
        self.assertIn("unsupported Phase 7 local input extension", failed["reason"])

    def test_missing_source_mode_state_key_blocks_selection_validation(self) -> None:
        module = validation_module()
        source = """
DASHBOARD_INTERACTIVITY_STATE_KEYS = ("selectedAwr",)
const DASHBOARD_TYPE_TO_STATE_KEY = Object.freeze({
  sourceMode: 'selectedSourceMode',
  'source-mode': 'selectedSourceMode'
});
"""
        result = module.validate_dashboard_state_key_coverage(
            source,
            {
                "awr_dashboard/index.html": (
                    '<article data-dashboard-select-key="selectedSourceMode"></article>'
                    '<a data-required-selection-key="selectedSourceMode"></a>'
                )
            },
        )
        self.assertEqual("failed", result["status"])
        self.assertIn("selectedSourceMode missing", result["reason"])

    def test_generated_dashboard_controls_are_validated_when_present(self) -> None:
        module = validation_module()
        source = read_dashboard_source_text()
        generated = "\n".join(
            (
                '<section data-phase7-runtime-interaction-panel="true">'
                f'<button data-phase7-action-control="true" '
                f'data-screen-id="{screen_id}" '
                f'data-action-type="{action_type}" '
                f'data-workflow-type="{screen_id}_{action_type}" '
                f'data-target-type="unit" '
                f'data-target-id="{screen_id}-{action_type}" '
                f'data-required-selection-key="selectedSourceMode">Submit</button>'
                "</section>"
            )
            for screen_id, action_types in module.REQUIRED_SCREEN_ACTIONS.items()
            for action_type in action_types
        )
        result = module.validate_dashboard_runtime_interaction(
            source_text=source,
            generated_texts={
                "awr_dashboard/index.html": PHASE7CR_INDEX_FIXTURE,
                "awr_dashboard/screen_1_ingestion.html": generated
                + PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE,
                "awr_dashboard/screen_2_control.html": generated
                + PHASE7CP_SCREEN3_FIXTURE,
                **{
                    f"awr_dashboard/{file_name}": fixture
                    for file_name, fixture in PHASE7M_DOWNSTREAM_GATE_FIXTURES.items()
                },
            },
            service_exists=True,
            contract_exists=True,
        )
        self.assertTrue(result["generated_dashboard"]["validated"])
        for screen in result["generated_dashboard"]["screens"].values():
            with self.subTest(screen=screen["screen_id"]):
                self.assertEqual("passed", screen["status"])

    def test_generated_dashboard_evidence_is_required(self) -> None:
        module = validation_module()
        source = read_dashboard_source_text()
        result = module.validate_dashboard_runtime_interaction(
            source_text=source,
            generated_texts={},
            service_exists=True,
            contract_exists=True,
        )
        self.assertIs(result["dashboard_runtime_interaction_ready"], False)
        self.assertIs(result["blocker_active"], True)
        self.assertTrue(
            any(
                "generated dashboard evidence is missing" in failure
                for failure in result["failures"]
            )
        )

    def test_generated_screen3_stale_preview_scaffold_blocks_validation(self) -> None:
        module = validation_module()
        stale_screen3 = (
            '<section data-phase7-runtime-interaction-panel="true">'
            '<div class="section-kicker">Phase 7H.2</div>'
            "<p>Phase 7H.2 Screen 3 Control Center: read-only selectors only.</p>"
            "</section>"
        )
        result = module.validate_generated_screen3_control_center(
            {"awr_dashboard/screen_2_control.html": stale_screen3}
        )
        self.assertEqual("failed", result["status"])
        self.assertTrue(
            any("stale primary Screen 3 preview marker" in offender for offender in result["offenders"])
        )

    def test_service_bridge_smoke_test_accepts_and_queues_request(self) -> None:
        bridge = self.payload["service_bridge"]
        self.assertEqual("passed", bridge["status"])
        self.assertIs(bridge["accepted"], True)
        self.assertIs(bridge["queued"], True)
        self.assertIs(bridge["audit_reference_exists"], True)
        self.assertIs(bridge["index_source_request_accepted"], True)
        self.assertIs(bridge["invalid_request_rejected"], True)
        self.assertIs(bridge["invalid_source_requests_rejected"], True)
        self.assertIs(bridge["existing_run_lookup_tested"], True)
        self.assertIs(bridge["existing_run_empty_state_tested"], True)
        self.assertIs(bridge["existing_run_unavailable_state_tested"], True)
        self.assertIs(bridge["screen3_runtime_options_tested"], True)
        self.assertIs(bridge["screen3_runtime_request_processed"], True)
        self.assertIn(
            bridge["screen3_runtime_response"]["status"],
            {"blocked", "completed", "accepted"},
        )
        self.assertIs(
            bridge["screen3_runtime_response"]["source_summary"]["current_run_truth_mutated"],
            False,
        )
        self.assertIs(
            bridge["screen3_runtime_response"]["source_summary"]["phase8_started"],
            False,
        )
        self.assertEqual("empty", bridge["existing_run_empty_response"]["validation_status"])
        self.assertTrue(bridge["screen3_runtime_options_response"]["options"]["runs"])
        self.assertTrue(bridge["screen3_runtime_options_response"]["options"]["databases"])
        self.assertTrue(bridge["screen3_runtime_options_response"]["options"]["intervals"])
        self.assertEqual("unavailable", bridge["existing_run_unavailable_response"]["validation_status"])
        self.assertIn(
            "No prior runs found in governed persistence",
            bridge["existing_run_empty_response"]["message"],
        )
        self.assertIn(
            "Existing run lookup unavailable",
            bridge["existing_run_unavailable_response"]["message"],
        )
        self.assertEqual(
            ["existing_run", "local_file", "local_staged", "object_storage"],
            bridge["accepted_source_modes"],
        )
        accepted_actions = {
            result["action_type"]
            for result in bridge["request_results"]
            if result["accepted"]
        }
        self.assertEqual({"source_selection_handoff"}, accepted_actions)

    def test_contract_rejects_incomplete_index_source_selection(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            {
                "screen_id": "index_source_mode",
                "action_type": "source_selection_handoff",
                "workflow_type": "index_source_selection_handoff",
                "actor_id": "ACTOR-LOCAL-TEST",
                "target_type": "source_selection",
                "target_id": "INDEX-SOURCE-SELECTION",
                "runtime_influence_granted": False,
                "phase4i_mutation_allowed": False,
                "phase8_behavior": False,
                "run_analysis_coupling": False,
                "payload": {
                    "selectedSourceMode": "object_storage",
                    "objectStorageNamespace": "axxduehrw7lz",
                    "objectStorageBucket": "agentic-ai-awr-raw",
                    "target_screen": "screen3",
                    "browser_file_read_attempted": False,
                    "browser_object_storage_access_attempted": False,
                    "em_extract_attempted": False,
                },
            }
        )
        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)

    def test_contract_rejects_direct_browser_source_execution_attempts(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            {
                "screen_id": "index_source_mode",
                "action_type": "source_selection_handoff",
                "workflow_type": "index_source_selection_handoff",
                "actor_id": "ACTOR-LOCAL-TEST",
                "target_type": "source_selection",
                "target_id": "INDEX-SOURCE-SELECTION",
                "runtime_influence_granted": False,
                "phase4i_mutation_allowed": False,
                "phase8_behavior": False,
                "run_analysis_coupling": False,
                "payload": {
                    "selectedSourceMode": "local_staged",
                    "selectedSourcePath": "data/input",
                    "target_screen": "screen3",
                    "browser_file_read_attempted": True,
                    "browser_object_storage_access_attempted": False,
                    "em_extract_attempted": False,
                },
            }
        )
        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)

    def test_contract_rejects_unknown_screen1_source_action_type(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            {
                "screen_id": "screen_1",
                "action_type": "unsupported_screen1_source_execute",
                "workflow_type": "screen1_source_intake_execution",
                "actor_id": "ACTOR-LOCAL-TEST",
                "target_type": "source_intake",
                "target_id": "SCREEN1-SOURCE-INTAKE-EXECUTE",
                "execution_mode": "governed_backend_execution",
                "runtime_influence_granted": False,
                "phase4i_mutation_allowed": False,
                "phase8_behavior": False,
                "run_analysis_coupling": False,
                "payload": {
                    "selectedSourceMode": "local_staged",
                    "source_type": "local_staged",
                    "source_channel": "local_staged",
                    "sourceSelectionMethod": "backend_path",
                    "selectedSourcePath": "data/input",
                    "target_screen": "screen_1",
                    "browser_file_read_attempted": False,
                    "browser_object_storage_access_attempted": False,
                    "browser_db_query_attempted": False,
                    "browser_parsing_performed": False,
                    "run_analysis_coupling": False,
                },
            }
        )
        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)
        self.assertIn("action_type must be one of", result.message)

    def test_screen1_source_intake_execute_sets_artifact_ready_only_after_backend_completion(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        def complete_source_intake(_request: object) -> dict[str, object]:
            return {
                "status": "completed_artifact_ready",
                "execution_status": "completed_artifact_ready",
                "artifact_ready": True,
                "dashboard_regenerated": True,
                "dashboard_artifact_path": "awr_dashboard/index.html",
                "runner_invoked": True,
                "message": "Source intake completed. Generated artifact is ready.",
            }

        result = process_dashboard_action(
            {
                "screen_id": "screen_1",
                "action_type": "screen1_source_intake_execute",
                "workflow_type": "screen1_source_intake_execution",
                "actor_id": "ACTOR-LOCAL-TEST",
                "target_type": "source_intake",
                "target_id": "SCREEN1-SOURCE-INTAKE-EXECUTE",
                "execution_mode": "governed_backend_execution",
                "runtime_influence_granted": False,
                "phase4i_mutation_allowed": False,
                "phase8_behavior": False,
                "run_analysis_coupling": False,
                "payload": {
                    "selectedSourceMode": "local_staged",
                    "source_type": "local_staged",
                    "source_channel": "local_staged",
                    "sourceSelectionMethod": "backend_path",
                    "selectedSourcePath": "data/input",
                    "target_screen": "screen_1",
                    "browser_file_read_attempted": False,
                    "browser_object_storage_access_attempted": False,
                    "browser_db_query_attempted": False,
                    "browser_parsing_performed": False,
                    "run_analysis_coupling": False,
                },
            },
            source_intake_executor=complete_source_intake,
        )
        self.assertEqual("completed_artifact_ready", result.status)
        self.assertTrue(result.source_summary["artifact_ready"])
        self.assertTrue(result.source_summary["screen1GeneratedArtifactReady"])
        self.assertTrue(result.source_summary["screen1GeneratedRunExecuted"])
        self.assertTrue(result.source_summary["screen1SelectedGeneratedArtifactReady"])
        self.assertFalse(result.source_summary["browser_file_read_attempted"])
        self.assertFalse(result.run_analysis_called)

    def test_screen1_source_intake_acceptance_without_runner_does_not_mark_artifact_ready(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(screen1_source_intake_request())
        self.assertEqual("blocked", result.status)
        self.assertFalse(result.source_summary["artifact_ready"])
        self.assertFalse(result.source_summary["screen1GeneratedArtifactReady"])
        self.assertIn("runner is not wired", result.message)

    def test_screen1_source_intake_requires_explicit_source_type(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        request = screen1_source_intake_request()
        request["payload"].pop("source_type")

        result = process_dashboard_action(request)

        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)
        self.assertIn("must include source_type", result.message)

    def test_screen1_source_intake_rejects_mismatched_source_type(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            screen1_source_intake_request(payload_overrides={"source_type": "object_storage"})
        )

        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)
        self.assertIn("source_type must match selectedSourceMode", result.message)

    def test_screen1_source_intake_rejects_client_artifact_ready_claims(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            screen1_source_intake_request(
                "object_storage",
                {
                    "sourceSelectionMethod": "object_storage_metadata",
                    "selectedSourcePath": "",
                    "objectStorageNamespace": "axxduehrw7lz",
                    "objectStorageBucket": "agentic-ai-awr-raw",
                    "objectStorageObjectName": "awr/raw/report.out",
                    "objectStorageRegion": "us-phoenix-1",
                    "objectStorageValidationStatus": "valid",
                    "client_completed_artifact_ready": "completed_artifact_ready",
                },
            )
        )

        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)
        self.assertIn("must not claim Screen 1 artifact readiness", result.message)

    def test_screen1_source_intake_rejects_nested_dashboard_state_artifact_ready_claims(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            screen1_source_intake_request(
                payload_overrides={
                    "dashboard_state": {
                        "screen1GeneratedArtifactReady": "completed_artifact_ready",
                    }
                }
            )
        )

        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)
        self.assertIn("payload.dashboard_state.screen1GeneratedArtifactReady", result.message)

    def test_screen1_object_storage_source_intake_rejects_credentials(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            screen1_source_intake_request(
                "object_storage",
                {
                    "sourceSelectionMethod": "object_storage_metadata",
                    "selectedSourcePath": "",
                    "objectStorageNamespace": "axxduehrw7lz",
                    "objectStorageBucket": "agentic-ai-awr-raw",
                    "objectStorageObjectName": "awr/raw/report.out",
                    "objectStorageRegion": "us-phoenix-1",
                    "objectStorageValidationStatus": "valid",
                    "credential_value": "not-allowed",
                },
            )
        )

        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)
        self.assertIn("must not include secrets or credentials", result.message)

    def test_screen1_object_storage_metadata_validation_never_marks_artifact_ready(self) -> None:
        from src.learning.dashboard_runtime_interaction import validate_object_storage_source

        result = validate_object_storage_source(
            {
                "screen_id": "index_source_mode",
                "action_type": "object_storage_source_validation",
                "workflow_type": "index_object_storage_source_validation",
                "target_screen": "screen3",
                "governance_mode": "governed_request",
                "objectStorageNamespace": "axxduehrw7lz",
                "objectStorageBucket": "agentic-ai-awr-raw",
                "objectStorageObjectName": "awr/raw/report.out",
                "objectStorageRegion": "us-phoenix-1",
                "browser_object_storage_access_attempted": False,
                "direct_object_storage_execution_attempted": False,
                "direct_truth_mutation_allowed": False,
                "phase4i_mutation_allowed": False,
                "phase8_behavior": False,
                "run_analysis_coupling": False,
            }
        )

        self.assertEqual("accepted", result["status"])
        self.assertEqual("valid", result["validation_status"])
        self.assertNotIn("completed_artifact_ready", result)
        self.assertNotIn("artifact_ready", result)
        self.assertFalse(result["browser_object_storage_access_performed"])

    def test_screen1_source_intake_rejects_existing_run_and_future_channels(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        existing_result = process_dashboard_action(
            screen1_source_intake_request(
                "existing_run",
                {
                    "sourceSelectionMethod": "existing_run_reference",
                    "selectedRunReference": "RUN_HISTORY_ID:9001",
                    "existingRunLookupStatus": "valid",
                },
            )
        )
        future_result = process_dashboard_action(
            screen1_source_intake_request(
                "enterprise_manager_oem",
                {"sourceSelectionMethod": "future_governed_source"},
            )
        )

        self.assertEqual("rejected", existing_result.status)
        self.assertEqual("rejected", future_result.status)
        self.assertIn("requires local_staged, local_file, or object_storage", existing_result.message)
        self.assertIn("requires local_staged, local_file, or object_storage", future_result.message)

    def test_workflow_service_local_file_and_object_storage_fail_safely_without_artifact_ready(self) -> None:
        import scripts.dashboard_workflow_service as service
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        local_file_result = process_dashboard_action(
            screen1_source_intake_request(
                "local_file",
                {
                    "sourceSelectionMethod": "backend_path",
                    "selectedSourcePath": "report.out",
                },
            ),
            source_intake_executor=service.run_screen1_source_intake_execution,
        )
        object_storage_result = process_dashboard_action(
            screen1_source_intake_request(
                "object_storage",
                {
                    "sourceSelectionMethod": "object_storage_metadata",
                    "selectedSourcePath": "",
                    "objectStorageNamespace": "axxduehrw7lz",
                    "objectStorageBucket": "agentic-ai-awr-raw",
                    "objectStorageObjectName": "awr/raw/report.out",
                    "objectStorageRegion": "us-phoenix-1",
                    "objectStorageValidationStatus": "valid",
                },
            ),
            source_intake_executor=service.run_screen1_source_intake_execution,
        )

        self.assertEqual("failed_safely", local_file_result.status)
        self.assertFalse(local_file_result.source_summary["artifact_ready"])
        self.assertIn("metadata/path validation only", local_file_result.message)
        self.assertEqual("failed_safely", object_storage_result.status)
        self.assertFalse(object_storage_result.source_summary["artifact_ready"])
        self.assertIn("metadata-validation only", object_storage_result.message)

    def test_workflow_service_returns_completed_artifact_ready_for_mocked_screen1_execution(self) -> None:
        import scripts.dashboard_workflow_service as service

        module = validation_module()
        original_runner = service.run_screen1_source_intake_execution

        def mocked_runner(_request: object) -> dict[str, object]:
            return {
                "status": "completed_artifact_ready",
                "execution_status": "completed_artifact_ready",
                "artifact_ready": True,
                "dashboard_regenerated": True,
                "dashboard_artifact_path": "awr_dashboard/index.html",
                "runner_invoked": True,
                "message": "Source intake completed. Generated artifact is ready.",
            }

        service.run_screen1_source_intake_execution = mocked_runner
        try:
            with tempfile.TemporaryDirectory(prefix="screen1-source-intake-service-") as tmp:
                response, status_code = module.invoke_service_handler(
                    service.Phase7DashboardWorkflowHandler,
                    service.ENDPOINT_PATH,
                    json.dumps(
                        {
                            "screen_id": "screen_1",
                            "action_type": "screen1_source_intake_execute",
                            "workflow_type": "screen1_source_intake_execution",
                            "actor_id": "ACTOR-LOCAL-TEST",
                            "target_type": "source_intake",
                            "target_id": "SCREEN1-SOURCE-INTAKE-EXECUTE",
                            "execution_mode": "governed_backend_execution",
                            "runtime_influence_granted": False,
                            "phase4i_mutation_allowed": False,
                            "phase8_behavior": False,
                            "run_analysis_coupling": False,
                            "payload": {
                                "selectedSourceMode": "local_staged",
                                "source_type": "local_staged",
                                "source_channel": "local_staged",
                                "sourceSelectionMethod": "backend_path",
                                "selectedSourcePath": "data/input",
                                "target_screen": "screen_1",
                                "browser_file_read_attempted": False,
                                "browser_object_storage_access_attempted": False,
                                "browser_db_query_attempted": False,
                                "browser_parsing_performed": False,
                                "run_analysis_coupling": False,
                            },
                        }
                    ).encode("utf-8"),
                    Path(tmp),
                )
                self.assertEqual(202, status_code)
                self.assertEqual("running", response["status"])
                request_id = response["request_id"]
                status_response = response
                status_code = 202
                for _ in range(40):
                    status_response, status_code = service.screen1_source_intake_status_payload(
                        {"request_id": [request_id]},
                        queue_dir=Path(tmp),
                    )
                    if status_response["status"] == "completed_artifact_ready":
                        break
                    time.sleep(0.05)
        finally:
            service.run_screen1_source_intake_execution = original_runner

        self.assertEqual(200, status_code)
        self.assertEqual("completed_artifact_ready", status_response["status"])
        self.assertTrue(status_response["source_summary"]["artifact_ready"])
        self.assertTrue(status_response["source_summary"]["screen1GeneratedArtifactReady"])
        self.assertFalse(status_response["run_analysis_called"])

    def test_contract_rejects_html_awr_input_in_phase7(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            {
                "screen_id": "index_source_mode",
                "action_type": "source_selection_handoff",
                "workflow_type": "index_source_selection_handoff",
                "actor_id": "ACTOR-LOCAL-TEST",
                "target_type": "source_selection",
                "target_id": "INDEX-SOURCE-SELECTION",
                "runtime_influence_granted": False,
                "phase4i_mutation_allowed": False,
                "phase8_behavior": False,
                "run_analysis_coupling": False,
                "payload": {
                    "selectedSourceMode": "local_file",
                    "sourceSelectionMethod": "os_file_picker",
                    "selectedLocalFileName": "awr_report.html",
                    "selectedLocalFileSize": "2048",
                    "selectedLocalFileType": "html",
                    "selectedLocalFileExtension": "html",
                    "selectedLocalFileValidationStatus": "warning-backend-validation-pending",
                    "target_screen": "screen3",
                    "browser_file_read_attempted": False,
                    "browser_object_storage_access_attempted": False,
                    "em_extract_attempted": False,
                },
            }
        )
        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)
        self.assertIn(
            "HTML AWR input is not supported by the current governed handoff",
            result.message,
        )

    def test_service_accepts_false_em_extract_safety_flag(self) -> None:
        from src.learning.dashboard_runtime_interaction import validate_object_storage_source

        result = validate_object_storage_source(
            {
                "screen_id": "index_source_mode",
                "action_type": "object_storage_source_validation",
                "workflow_type": "index_object_storage_source_validation",
                "target_screen": "screen3",
                "governance_mode": "governed_request",
                "objectStorageNamespace": "axxduehrw7lz",
                "objectStorageBucket": "agentic-ai-awr-raw",
                "objectStorageObjectName": "awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out",
                "objectStorageRegion": "us-phoenix-1",
                "browser_object_storage_access_attempted": False,
                "direct_object_storage_execution_attempted": False,
                "direct_truth_mutation_allowed": False,
                "phase4i_mutation_allowed": False,
                "phase8_behavior": False,
                "run_analysis_coupling": False,
                "em_extract_attempted": False,
            }
        )

        self.assertEqual("accepted", result["status"])
        self.assertEqual("valid", result["validation_status"])

    def test_screen3_runtime_options_use_service_side_db_boundary(self) -> None:
        from src.learning.dashboard_runtime_interaction import load_screen3_runtime_options

        module = validation_module()
        result = load_screen3_runtime_options(
            module.screen3_runtime_options_smoke_payload(),
            connection_factory=module.fake_existing_run_connection_factory,
        )

        self.assertEqual("accepted", result["status"])
        self.assertTrue(result["runtime_options_loaded"])
        self.assertFalse(result["browser_db_query_performed"])
        self.assertFalse(result["current_run_truth_mutated"])
        self.assertTrue(result["options"]["runs"])
        self.assertTrue(result["options"]["databases"])
        self.assertTrue(result["options"]["intervals"])
        self.assertTrue(result["options"]["target_scope_options"])
        self.assertTrue(result["options"]["comparison_target_resolutions"])
        self.assertGreaterEqual(result["run_count"], 4)
        self.assertIn("OrderService", {item.get("application") for item in result["options"]["applications"]})
        target = result["options"]["target_scope_options"][0]
        for key in (
            "source_type",
            "scope_type",
            "scope_value",
            "time_window",
            "resolution_state",
            "readiness_state",
            "awr_count",
            "snapshot_count",
        ):
            self.assertIn(key, target)
        self.assertEqual(
            "source_type + scope_type + scope_value + time_window + resolution_state + readiness_state",
            result["target_resolution"]["target_model"],
        )
        self.assertIn("both_targets_comparable", result["comparison_readiness"])
        self.assertIn("similarity candidates unavailable", result["missing_gates"])
        self.assertEqual("available", result["service_status"])
        self.assertEqual("available", result["db_persistence_status"])
        self.assertIn("AWR_RUN_HISTORY", result["metadata"]["source"])
        self.assertIn("AWR_REPORT", result["metadata"]["source"])
        self.assertTrue(result["metadata"]["runtime_options_source_tables"])
        self.assertTrue(result["runtime_options_source_tables"])
        source_table_names = {
            item["table_name"]
            for item in result["runtime_options_source_tables"]
        }
        self.assertIn("AWR_RUN_HISTORY", source_table_names)
        self.assertIn("AWR_REPORT", source_table_names)
        coverage = {
            item["table_name"]: item
            for item in result["runtime_options_source_tables"]
        }
        self.assertEqual(3, coverage["AWR_REPORT"]["row_count"])
        self.assertEqual(3, coverage["AWR_REPORT"]["selectable_row_count"])
        self.assertEqual(2, coverage["AWR_SOURCE_SYSTEM"]["application_non_null_count"])
        for item in result["runtime_options_source_tables"]:
            self.assertIn("table_exists", item)
            self.assertIn("key_columns_used", item)
            self.assertIn("columns_found", item)
            self.assertIn("missing_columns", item)
            self.assertIn("selectable_row_count", item)
            self.assertIn("included_in_screen3_runtime_options", item)
        self.assertIn("runtime_options_rows_returned", result["metadata"])
        self.assertIn("runtime_options_query_limit", result["metadata"])
        self.assertIn("runtime_options_source_note", result["metadata"])
        self.assertFalse(result["llm_changed_status"])
        self.assertFalse(result["llm_changed_validation"])
        self.assertFalse(result["llm_changed_execution"])
        self.assertFalse(result["llm_changed_truth"])

    def test_workflow_service_health_exposes_screen3_runtime_options_route(self) -> None:
        service_path = ROOT / "scripts" / "dashboard_workflow_service.py"
        spec = util.spec_from_file_location(
            "phase7_dashboard_workflow_service_health_test",
            service_path,
        )
        if spec is None or spec.loader is None:
            raise AssertionError(f"unable to load {service_path}")
        service = util.module_from_spec(spec)
        spec.loader.exec_module(service)
        handler = object.__new__(service.Phase7DashboardWorkflowHandler)
        handler.server = type(
            "Phase7HealthTestServer",
            (),
            {"server_address": ("127.0.0.1", 8765)},
        )()

        payload = service.Phase7DashboardWorkflowHandler._health_payload(handler)

        self.assertIn(
            "/phase7/dashboard/screen3/options",
            payload["supported_endpoints"],
        )
        self.assertIn(
            "/phase7/dashboard/actions/status",
            payload["supported_endpoints"],
        )
        self.assertIn(
            "/phase7/dashboard/screen3/evidence-context/explanation",
            payload["supported_endpoints"],
        )
        self.assertEqual(
            "/phase7/dashboard/actions/status",
            payload["screen1_source_intake_status_endpoint"],
        )
        self.assertIn(
            payload["screen3_evidence_context_explanation_provider_mode"],
            payload["supported_provider_modes"],
        )
        self.assertFalse(payload["creates_screen3_evidence_context_records"])
        self.assertIn(
            "screen1_source_intake_execute",
            payload["supported_action_types"],
        )
        self.assertIn(
            "screen1_source_intake_execute",
            payload["supported_screen_action_types"]["screen_1"],
        )

    def test_screen3_runtime_options_mark_external_targets_load_required(self) -> None:
        from src.learning.dashboard_runtime_interaction import load_screen3_runtime_options

        module = validation_module()
        payload = module.screen3_runtime_options_smoke_payload()
        payload.update(
            {
                "selectedSourceMode": "object_storage",
                "sourceSelectionMethod": "object_storage_metadata",
                "objectStorageObjectName": "awr/raw/FINDB/sample.out",
            }
        )
        result = load_screen3_runtime_options(
            payload,
            connection_factory=module.fake_existing_run_connection_factory,
        )
        external_targets = [
            target
            for target in result["options"]["target_scope_options"]
            if target.get("source_type") == "object_storage_object"
        ]

        self.assertTrue(external_targets)
        self.assertEqual("load_required", external_targets[0]["readiness_state"])
        self.assertIn("load/parse/ingest/analyze", " ".join(external_targets[0]["missing_gates"]))

    def test_run_analysis_requires_screen3_route_before_reusing_service(self) -> None:
        source = (ROOT / "scripts" / "run_analysis.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )

        self.assertIn(
            "_phase7_dashboard_local_service_supports_required_routes",
            source,
        )
        self.assertIn(
            "PHASE7_DASHBOARD_REQUIRED_RUNTIME_ENDPOINTS",
            source,
        )
        self.assertIn(
            "_phase7_dashboard_local_service_advertises_required_routes(host, port)",
            source,
        )
        self.assertIn(
            "_phase7_dashboard_local_service_supports_screen3_options(host, port)",
            source,
        )
        self.assertIn(
            "_phase7_dashboard_local_service_supports_screen3_evidence_context_explanation",
            source,
        )
        self.assertIn(
            "_phase7_dashboard_stop_stale_local_service(host, port)",
            source,
        )
        self.assertIn(
            "/phase7/dashboard/screen3/options",
            source,
        )
        self.assertIn(
            "/phase7/dashboard/actions/status",
            source,
        )
        self.assertIn(
            "/phase7/dashboard/health",
            source,
        )
        self.assertIn(
            "/phase7/dashboard/actions",
            source,
        )
        self.assertIn(
            "/phase7/dashboard/existing-runs",
            source,
        )
        self.assertIn(
            "/phase7/dashboard/screen3/evidence-context/explanation",
            source,
        )
        self.assertIn(
            "Dashboard runtime contract: run_analysis.py generates dashboard HTML",
            source,
        )
        self.assertIn(
            "Dashboard workflow service health: http://{host}:{port}/phase7/dashboard/health",
            source,
        )
        self.assertIn(
            "PYTHONPATH=. .venv/bin/python scripts/dashboard_workflow_service.py ",
            source,
        )
        self.assertIn(
            'PHASE7_DASHBOARD_RUNTIME_DIR = Path(__file__).resolve().parents[1] / ".runtime"',
            source,
        )
        self.assertIn(
            'PHASE7_DASHBOARD_WORKFLOW_SERVICE_LOG_PATH',
            source,
        )
        self.assertIn(
            'PHASE7_DASHBOARD_WORKFLOW_SERVICE_PID_PATH',
            source,
        )
        self.assertIn(
            'PHASE7_DASHBOARD_WORKFLOW_SERVICE_STATUS_PATH',
            source,
        )
        self.assertIn(
            'env["PYTHONPATH"] = "."',
            source,
        )
        self.assertIn(
            "start_new_session=True",
            source,
        )
        self.assertIn(
            "close_fds=True",
            source,
        )
        self.assertIn(
            "_phase7_dashboard_write_runtime_status",
            source,
        )
        self.assertIn(
            "Dashboard workflow service PID file",
            source,
        )
        self.assertIn(
            "Dashboard workflow service status file",
            source,
        )
        self.assertIn(
            f"--host {{host}} --port {{port}}",
            source,
        )
        self.assertIn(
            "records_created",
            source,
        )

    def test_service_or_contract_missing_blocks_validation(self) -> None:
        module = validation_module()
        source = read_dashboard_source_text()
        generated = "\n".join(
            (
                '<section data-phase7-runtime-interaction-panel="true">'
                f'<button data-phase7-action-control="true" '
                f'data-screen-id="{screen_id}" '
                f'data-action-type="{action_type}" '
                f'data-workflow-type="{screen_id}_{action_type}" '
                f'data-target-type="unit" '
                f'data-target-id="{screen_id}-{action_type}" '
                f'data-required-selection-key="selectedSourceMode">Submit</button>'
                "</section>"
            )
            for screen_id, action_types in module.REQUIRED_SCREEN_ACTIONS.items()
            for action_type in action_types
        )
        result = module.validate_dashboard_runtime_interaction(
            source_text=source,
            generated_texts={
                "awr_dashboard/index.html": PHASE7CR_INDEX_FIXTURE,
                "awr_dashboard/screen_1_ingestion.html": generated
                + PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE,
            },
            service_exists=False,
            contract_exists=True,
        )
        self.assertIs(result["dashboard_runtime_interaction_ready"], False)
        checks = {check["name"]: check for check in result["checks"]}
        self.assertEqual("failed", checks["service_script_exists"]["status"])
        self.assertEqual(
            "failed",
            checks["service_bridge_accepts_index_source_request"]["status"],
        )
        self.assertEqual(
            "failed",
            checks["service_bridge_rejects_invalid_request"]["status"],
        )

    def test_contradictory_operational_text_blocks_validation(self) -> None:
        module = validation_module()
        source = read_dashboard_source_text()
        generated = (
            PHASE7CR_INDEX_FIXTURE.replace(
                '<section id="phase7cr-platform-entry-panel"',
                'Screen 3 selection handoff remains a future controlled workflow.'
                '<section id="phase7cr-platform-entry-panel"',
            )
        )
        result = module.validate_dashboard_runtime_interaction(
            source_text=source,
            generated_texts={
                "awr_dashboard/index.html": generated,
                "awr_dashboard/screen_1_ingestion.html": (
                    '<section data-phase7-runtime-interaction-panel="true">'
                    '<button data-phase7-action-control="true" '
                    'data-screen-id="screen_1" '
                    'data-action-type="screen1_source_intake_execute" '
                    'data-workflow-type="screen1_source_intake_execution" '
                    'data-target-type="source_intake" data-target-id="unit" '
                    'data-required-selection-key="selectedSourceMode">Submit</button>'
                    "</section>"
                    + PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE
                ),
                "awr_dashboard/screen_2_control.html": PHASE7CP_SCREEN3_FIXTURE,
            },
            service_exists=True,
            contract_exists=True,
        )
        self.assertIs(result["dashboard_runtime_interaction_ready"], False)
        self.assertTrue(
            any(
                "contradictory" in failure
                for failure in result["failures"]
            )
        )

    def test_unmarked_preview_only_generated_panel_blocks_validation(self) -> None:
        module = validation_module()
        result = module.validate_preview_only_context_markers(
            "",
            {
                "awr_dashboard/index.html": (
                    '<section><button data-preview-only="true">Old preview</button></section>'
                )
            },
        )
        self.assertEqual(
            "failed",
            result["status"],
        )

    def test_invalid_index_required_selection_key_blocks_validation(self) -> None:
        module = validation_module()
        controls = module.extract_action_controls(
            '<a data-phase7-action-control="true" '
            'data-screen-id="index_source_mode" '
            'data-action-type="source_selection_handoff" '
            'data-required-selection-key="Insufficient data for a reliable conclusion"></a>'
        )
        result = module.validate_required_selection_keys(controls)
        self.assertEqual("failed", result["status"])
        self.assertIn("invalid required-selection-key", result["reason"])

    def test_index_source_selection_requires_current_source_cards(self) -> None:
        module = validation_module()
        result = module.validate_index_source_selection_workflow(
            {
                "awr_dashboard/index.html": PHASE7CR_INDEX_FIXTURE,
                "awr_dashboard/screen_1_ingestion.html": (
                    '<section id="phase7cm-source-intake-panel" '
                    'data-phase7-index-source-selection="true"></section>'
                ),
            }
        )
        self.assertEqual("failed", result["status"])
        self.assertTrue(
            any("screen1 missing selectable new-source card" in offender for offender in result["offenders"])
        )

    def test_index_legacy_panel_on_product_index_blocks_validation(self) -> None:
        module = validation_module()
        index = (
            PHASE7CR_INDEX_FIXTURE
            + '<details id="index-source-mode-entry-panel" class="phase7-legacy-boundary-details"></details>'
            + '<a data-phase7-action-control="true" data-screen-id="index_source_mode" '
            'data-action-type="source_selection_handoff" '
            'data-required-selection-key="selectedSourceMode"></a>'
        )
        result = module.validate_index_source_selection_workflow(
            {
                "awr_dashboard/index.html": index,
                "awr_dashboard/screen_1_ingestion.html": PHASE7CR_SCREEN1_SOURCE_WORKFLOW_FIXTURE,
            }
        )
        self.assertEqual("failed", result["status"])
        self.assertIn("legacy source preview panel remains rendered", result["reason"])

    def test_safety_invariants_are_preserved(self) -> None:
        invariants = self.payload["invariants"]
        self.assertIs(invariants["phase4i_contract_protected"], True)
        self.assertIs(invariants["deterministic_runtime_authoritative"], True)
        self.assertIs(invariants["ml_scoring_shadow_or_advisory_only"], True)
        self.assertIs(
            invariants["trend_aware_scoring_shadow_or_advisory_only"],
            True,
        )
        self.assertIs(invariants["phase8_behavior_implemented"], False)
        self.assertIs(invariants["adaptive_runtime_default_active"], False)
        self.assertIs(invariants["recommendation_truth_direct_mutation_allowed"], False)
        self.assertIs(invariants["run_analysis_direct_button_coupling_allowed"], False)
        self.assertIs(invariants["dashboard_controls_activate_trend_aware_scoring"], False)

    def test_trend_aware_scoring_7u_artifacts_remain_shadow_only(self) -> None:
        checks = {check["name"]: check for check in self.payload["checks"]}
        self.assertEqual(
            "passed",
            checks["trend_aware_scoring_7u_artifacts_present"]["status"],
        )
        self.assertEqual(
            "passed",
            checks["trend_aware_scoring_shadow_only"]["status"],
        )

    def test_dashboard_source_does_not_wire_buttons_to_run_analysis(self) -> None:
        source = read_dashboard_source_text()
        action_text = validation_module().action_control_text(source)
        self.assertNotIn("scripts/run_analysis.py", action_text)
        self.assertNotIn("run_analysis_coupling=true", action_text)
        self.assertNotIn('data-phase4i-mutation-allowed="true"', source)
        self.assertNotIn('data-phase8-behavior="true"', source)

    def test_dashboard_endpoint_is_configurable_for_oci_api(self) -> None:
        source = read_dashboard_source_text()

        self.assertIn("window.PHASE7_DASHBOARD_ACTION_ENDPOINT", source)
        self.assertIn("derivePhase7Endpoint", source)
        self.assertIn("window.PHASE7_DASHBOARD_EXISTING_RUN_LOOKUP_ENDPOINT", source)
        self.assertIn("window.PHASE7_DASHBOARD_OBJECT_STORAGE_VALIDATE_ENDPOINT", source)

    def test_action_contract_queues_auditable_request_without_truth_mutation(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        with tempfile.TemporaryDirectory() as tempdir:
            result = process_dashboard_action(
                {
                    "screen_id": "screen_5",
                    "action_type": "outcome_capture",
                    "workflow_type": "screen5_outcome_capture",
                    "actor_id": "ACTOR-LOCAL-TEST",
                    "target_type": "outcome",
                    "target_id": "RECO-1",
                    "payload": {"outcome_status": "improved"},
                    "runtime_influence_granted": False,
                    "phase4i_mutation_allowed": False,
                    "phase8_behavior": False,
                    "future_run_influence_metadata": {
                        "requires_governed_materialization": True,
                        "requires_runtime_eligibility": True,
                        "future_runs_only": True,
                        "runtime_activation_granted": False,
                    },
                },
                queue_dir=Path(tempdir),
            )
            self.assertEqual("accepted", result.status)
            self.assertTrue(result.queued)
            self.assertFalse(result.phase4i_mutated)
            self.assertFalse(result.phase8_behavior)
            self.assertFalse(result.direct_truth_mutation_performed)
            self.assertFalse(result.run_analysis_called)
            self.assertTrue(Path(result.audit_reference or "").is_file())
            envelope = json.loads(Path(result.audit_reference or "").read_text())
            self.assertTrue(
                envelope["audit"]["future_run_influence_requires_materialization"]
            )
            self.assertTrue(
                envelope["audit"]["future_run_influence_requires_runtime_eligibility"]
            )

    def test_screen3_runtime_action_records_blocked_governed_request(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        with tempfile.TemporaryDirectory() as tempdir:
            result = process_dashboard_action(
                {
                    "screen_id": "screen_3",
                    "action_type": "screen3_active_reanalysis",
                    "workflow_type": "screen3_runtime_control_center",
                    "actor_id": "ACTOR-7CP-UNIT",
                    "target_type": "backend_execution_request",
                    "target_id": "SCREEN3-UNIT-ANALYZE",
                    "execution_mode": "local_backend_execution",
                    "runtime_influence_granted": False,
                    "phase4i_mutation_allowed": False,
                    "phase8_behavior": False,
                    "run_analysis_coupling": False,
                    "payload": {
                        "requested_screen3_action": "analyze_selection",
                        "target_screen": "screen_3",
                        "selectedSourceMode": "local_staged",
                        "sourceSelectionMethod": "backend_path",
                        "selectedSourcePath": "data/input",
                        "current_run_truth_mutated": False,
                        "deterministic_truth_changed": False,
                        "parser_mutated": False,
                        "learning_candidate_created": False,
                        "materialization_changed": False,
                        "runtime_eligibility_changed": False,
                        "phase8_started": False,
                        "browser_file_read_attempted": False,
                        "browser_object_storage_access_attempted": False,
                        "browser_db_query_attempted": False,
                        "em_extract_attempted": False,
                    },
                },
                queue_dir=Path(tempdir),
                db_persistence_enabled=False,
            )

        self.assertEqual("blocked", result.status)
        self.assertTrue(result.queued)
        self.assertFalse(result.phase4i_mutated)
        self.assertFalse(result.run_analysis_called)
        self.assertFalse(result.direct_truth_mutation_performed)
        self.assertIn("JSON audit fallback", result.message)
        self.assertEqual("blocked", result.source_summary["execution_status"])
        self.assertFalse(result.source_summary["current_run_truth_mutated"])
        self.assertFalse(result.source_summary["phase8_started"])
        self.assertIn(
            "capability gap: no injected deterministic runner is configured",
            " ".join(result.source_summary["missing_execution_gates"]),
        )

    def test_screen3_object_storage_full_load_is_blocked_without_governed_chain(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        with tempfile.TemporaryDirectory() as tempdir:
            result = process_dashboard_action(
                {
                    "screen_id": "screen_3",
                    "action_type": "screen3_active_reanalysis",
                    "workflow_type": "screen3_runtime_control_center",
                    "actor_id": "ACTOR-7CP-UNIT",
                    "target_type": "source_execution_request",
                    "target_id": "SCREEN3-UNIT-OBJECT-STORAGE",
                    "execution_mode": "local_backend_execution",
                    "runtime_influence_granted": False,
                    "phase4i_mutation_allowed": False,
                    "phase8_behavior": False,
                    "run_analysis_coupling": False,
                    "payload": {
                        "requested_screen3_action": "load_from_object_storage",
                        "target_screen": "screen_3",
                        "selectedSourceMode": "object_storage",
                        "sourceSelectionMethod": "object_storage_metadata",
                        "objectStorageNamespace": "axxduehrw7lz",
                        "objectStorageBucket": "agentic-ai-awr-raw",
                        "objectStorageObjectName": "awr/raw/FINDB/report.out",
                        "objectStorageRegion": "us-phoenix-1",
                        "objectStorageValidationStatus": "valid",
                        "objectStorageValidationMessage": "metadata accepted",
                        "current_run_truth_mutated": False,
                        "deterministic_truth_changed": False,
                        "parser_mutated": False,
                        "learning_candidate_created": False,
                        "materialization_changed": False,
                        "runtime_eligibility_changed": False,
                        "phase8_started": False,
                        "browser_file_read_attempted": False,
                        "browser_object_storage_access_attempted": False,
                        "browser_db_query_attempted": False,
                        "em_extract_attempted": False,
                    },
                },
                queue_dir=Path(tempdir),
                db_persistence_enabled=False,
            )

        self.assertEqual("blocked", result.status)
        self.assertTrue(result.queued)
        self.assertFalse(result.source_summary["current_run_truth_mutated"])
        self.assertFalse(result.source_summary["phase8_started"])
        missing_gates = " ".join(result.source_summary["missing_execution_gates"])
        self.assertIn("external target server-side load client is not configured", missing_gates)
        self.assertIn("external target load to parser/ingestion chain is not connected", missing_gates)

    def test_screen3_build_comparison_uses_scope_target_readiness_gates(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        with tempfile.TemporaryDirectory() as tempdir:
            result = process_dashboard_action(
                {
                    "screen_id": "screen_3",
                    "action_type": "screen3_active_reanalysis",
                    "workflow_type": "screen3_runtime_control_center",
                    "actor_id": "ACTOR-7CP-UNIT",
                    "target_type": "backend_execution_request",
                    "target_id": "SCREEN3-UNIT-BUILD-COMPARISON",
                    "execution_mode": "local_backend_execution",
                    "runtime_influence_granted": False,
                    "phase4i_mutation_allowed": False,
                    "phase8_behavior": False,
                    "run_analysis_coupling": False,
                    "payload": {
                        "requested_screen3_action": "build_comparison",
                        "target_screen": "screen_3",
                        "selectedSourceMode": "existing_run",
                        "sourceSelectionMethod": "existing_run_reference",
                        "selectedRunReference": "RUN_HISTORY_ID:9001",
                        "existingRunLookupStatus": "valid",
                        "selectedComparisonTargetA": "db_backed | dbid | 123456789 | 2026-03-29T06:00:00 -> 2026-03-29T07:00:00",
                        "selectedComparisonTargetASourceType": "db_backed",
                        "selectedComparisonTargetAScopeType": "dbid",
                        "selectedComparisonTargetAScopeValue": "123456789",
                        "selectedComparisonTargetATimeWindow": "2026-03-29T06:00:00 -> 2026-03-29T07:00:00",
                        "selectedComparisonTargetAReadinessState": "comparable",
                        "current_run_truth_mutated": False,
                        "deterministic_truth_changed": False,
                        "parser_mutated": False,
                        "learning_candidate_created": False,
                        "materialization_changed": False,
                        "runtime_eligibility_changed": False,
                        "phase8_started": False,
                        "browser_file_read_attempted": False,
                        "browser_object_storage_access_attempted": False,
                        "browser_db_query_attempted": False,
                        "em_extract_attempted": False,
                    },
                },
                queue_dir=Path(tempdir),
                db_persistence_enabled=False,
            )

        self.assertEqual("blocked", result.status)
        missing_gates = " ".join(result.source_summary["missing_execution_gates"])
        self.assertIn("comparison gap: Target B unresolved", missing_gates)
        self.assertNotIn("no injected deterministic runner", missing_gates)

    def test_screen3_rejects_unsafe_execution_mode_and_llm_status_mutation(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        base_payload = {
            "screen_id": "screen_3",
            "action_type": "screen3_active_reanalysis",
            "workflow_type": "screen3_runtime_control_center",
            "actor_id": "ACTOR-7CP-UNIT",
            "target_type": "backend_execution_request",
            "target_id": "SCREEN3-UNIT-UNSAFE",
            "runtime_influence_granted": False,
            "phase4i_mutation_allowed": False,
            "phase8_behavior": False,
            "run_analysis_coupling": False,
            "payload": {
                "requested_screen3_action": "analyze_selection",
                "target_screen": "screen_3",
                "selectedSourceMode": "local_staged",
                "sourceSelectionMethod": "backend_path",
                "selectedSourcePath": "data/input",
                "current_run_truth_mutated": False,
                "deterministic_truth_changed": False,
                "parser_mutated": False,
                "learning_candidate_created": False,
                "materialization_changed": False,
                "runtime_eligibility_changed": False,
                "phase8_started": False,
                "browser_file_read_attempted": False,
                "browser_object_storage_access_attempted": False,
                "browser_db_query_attempted": False,
                "em_extract_attempted": False,
            },
        }

        unsafe_mode = dict(base_payload)
        unsafe_mode["execution_mode"] = "direct_run_analysis_subprocess"
        mode_result = process_dashboard_action(unsafe_mode)
        self.assertEqual("rejected", mode_result.status)
        self.assertIn("execution_mode", mode_result.message)

        llm_mutation = json.loads(json.dumps(base_payload))
        llm_mutation["execution_mode"] = "local_backend_execution"
        llm_mutation["payload"]["llm_changed_status"] = True
        llm_result = process_dashboard_action(llm_mutation)
        self.assertEqual("rejected", llm_result.status)
        self.assertIn("llm_changed_status", llm_result.message)

    def test_contract_rejects_immediate_future_run_activation(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            {
                "screen_id": "screen_1",
                "action_type": "parser_mapping_approval_intent",
                "workflow_type": "screen1_parser_mapping_approval_intent",
                "actor_id": "ACTOR-LOCAL-TEST",
                "target_type": "parser_mapping_candidate",
                "target_id": "PARSER-MAP-1",
                "future_run_influence_metadata": {
                    "runtime_activation_granted": True,
                },
            }
        )
        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)

    def test_contract_rejects_trend_aware_runtime_activation(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            {
                "screen_id": "screen_4",
                "action_type": "historical_review",
                "workflow_type": "screen4_historical_review",
                "actor_id": "ACTOR-LOCAL-TEST",
                "target_type": "trend_aware_scoring_reference",
                "target_id": "TREND-AWARE-1",
                "future_run_influence_metadata": {
                    "trend_aware_runtime_activation": True,
                },
            }
        )
        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)

    def test_contract_rejects_phase4i_or_runtime_influence(self) -> None:
        from src.learning.dashboard_runtime_interaction import process_dashboard_action

        result = process_dashboard_action(
            {
                "screen_id": "screen_5",
                "action_type": "recommendation_decision",
                "workflow_type": "screen5_recommendation_decision",
                "actor_id": "ACTOR-LOCAL-TEST",
                "target_type": "recommendation",
                "target_id": "RECO-1",
                "runtime_influence_granted": True,
                "phase4i_mutation_allowed": True,
            }
        )
        self.assertEqual("rejected", result.status)
        self.assertFalse(result.queued)


if __name__ == "__main__":
    unittest.main()
