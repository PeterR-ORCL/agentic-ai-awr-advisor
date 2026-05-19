"""Tests for Phase 7CM dashboard runtime interaction wiring."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from importlib import util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_phase7_dashboard_runtime_interaction_validation.py"
PHASE7CM_UX_FIXTURE = """
<section id="phase7cm-source-intake-panel" data-phase7-index-source-selection="true" data-dashboard-default-state="{&quot;selectedSourceMode&quot;:&quot;local_staged&quot;,&quot;selectedSourcePath&quot;:&quot;data/input&quot;,&quot;sourceSelectionMethod&quot;:&quot;backend_path&quot;}">
  <p>Choose the input source context and submit governed source handoff request.</p>
  <p>The browser does not read local files and never browser-side bucket reads.</p>
  <section class="card prominent pipeline-card" data-phase7-current-runtime-pipeline="true" data-phase7-system-flow-dynamic="true">
    <div class="section-kicker">System Flow</div>
    <h2>AWR Intelligence Pipeline</h2>
    <p>Local development fallback: data/input.</p>
    <p data-phase7-source-summary-card="pipeline_mode">Current source mode: Local folder / local staged AWR</p>
    <p data-phase7-source-summary-card="pipeline_active">Active source: data/input</p>
    <p data-phase7-source-summary-card="pipeline_validation">Current source validation: backend path validation pending</p>
    <p data-phase7-source-summary-card="pipeline_handoff">Current handoff target: Screen 3</p>
    <p>Source selection changes the governed handoff context only. Deterministic parsing, scoring, decision, and recommendation remain authoritative after the accepted backend workflow processes the selected source.</p>
    <small data-phase7-source-summary-card="pipeline_node_source">Local staged AWR source. Path: data/input.</small>
  </section>
  <section class="card secondary future-input-card" data-phase7-current-source-context="true" data-phase7-source-configuration-reference="true">
    <h2>Source Configuration Reference / Staging Context</h2>
    <p>Local development fallback: data/input.</p>
    <h3>Current Source Type</h3><p data-phase7-source-summary-card="config_type">Current source type: Local folder / local staged AWR</p>
    <h3>Current Source Location</h3><p data-phase7-source-summary-card="config_location">Current source location: data/input</p>
    <h3>Current Source Metadata</h3><p data-phase7-source-summary-card="config_candidates">Candidate AWR files: 1; .out files: 1; samples: sample.out</p>
    <h3>Current Source Validation</h3><p data-phase7-source-summary-card="config_validation">Current source validation: backend validation pending</p>
    <h3>Current Handoff Status</h3><p data-phase7-source-summary-card="config_handoff">Current handoff status: Ready to submit Local Folder source handoff.</p>
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
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="local_staged" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="local_staged" data-entity-type="source_mode" data-downstream-action="governed-source-handoff-local-staged" data-source-selection-method="backend_path" data-source-default-path="data/input"><p>Selection state: not selected.</p></article>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="local_file" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="local_file" data-entity-type="source_mode" data-downstream-action="governed-source-handoff-local-file" data-source-selection-method="os_file_picker" data-source-default-path=""><p>Selection state: not selected.</p></article>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="existing_run" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="existing_run" data-entity-type="source_mode" data-downstream-action="governed-source-handoff-existing-run" data-source-selection-method="existing_run_reference" data-source-default-run-reference=""><p>Selection state: not selected.</p></article>
  <article data-phase7-current-source-card="true" data-dashboard-selectable="true" data-dashboard-select-key="selectedSourceMode" data-dashboard-select-id="object_storage" data-dashboard-filter-key="selectedSourceMode" data-dashboard-filter-value="object_storage" data-entity-type="source_mode" data-downstream-action="governed-source-handoff-object-storage" data-source-selection-method="object_storage_metadata" data-object-storage-namespace="axxduehrw7lz" data-object-storage-bucket="agentic-ai-awr-raw" data-object-storage-object-name="awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out" data-object-storage-region="us-phoenix-1"><p>Selection state: not selected.</p></article>
  <section data-phase7-source-configuration="true">
    <label for="phase7cm-local-folder-picker">Choose Folder</label>
    <input id="phase7cm-local-folder-picker" type="file" webkitdirectory multiple data-phase7-source-picker="local_folder" data-picker-summary-target="phase7cm-local-folder-picker-summary">
    <small id="phase7cm-local-folder-picker-summary" data-phase7-picker-summary="local_folder">Your browser may label this as Upload. Folder selected. 2 files available for governed validation. 1 AWR candidates found. Nothing has been submitted yet. Folder selected by OS picker; backend validation pending; governed submit not yet performed.</small>
    <input value="data/input" data-dashboard-state-input="true" data-dashboard-state-key="selectedSourcePath" data-phase7-source-path-field="local_staged">
    <label for="phase7cm-local-file-picker">Choose File</label>
    <input id="phase7cm-local-file-picker" type="file" accept=".out" data-phase7-source-picker="local_file" data-picker-summary-target="phase7cm-local-file-picker-summary">
    <small id="phase7cm-local-file-picker-summary" data-phase7-picker-summary="local_file">File selected. Nothing has been submitted yet. Backend validation is pending until Submit Governed Source Handoff is clicked.</small>
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
    <p>Governed workflow service unavailable. Start scripts/dashboard_workflow_service.py and retry.</p>
  </section>
  <section data-phase7-current-selection-panel="true" data-phase7-active-source-configuration="true">
    <h3>Active Source Configuration / Runtime Source State</h3>
    <p><strong>Active Source Selection.</strong></p>
    <p>Submit Local Folder Source Handoff. Submit Local File Source Handoff. Submit Existing Run Source Handoff. Submit Object Storage Source Handoff.</p>
    <div data-phase7-dynamic-source-summary="true">
      <p data-phase7-source-summary-card="active">Active Source. if (mode === 'local_staged') if (mode === 'local_file') if (mode === 'existing_run') if (mode === 'object_storage')</p>
      <p data-phase7-source-summary-card="metadata">Source Metadata. Folder picker metadata. File picker metadata. Service-selected persisted run reference: RUN_HISTORY_ID:9001. Object Storage metadata. Namespace: axxduehrw7lz</p>
      <p data-phase7-source-summary-card="validation">Validation Status</p>
      <p data-phase7-source-summary-card="missing">Required Metadata / Missing Fields</p>
      <p data-phase7-source-summary-card="handoff">Handoff Target</p>
      <p data-phase7-source-summary-card="action">Action State</p>
      <p data-phase7-source-summary-card="next_step">Next Step</p>
    </div>
  </section>
  <section data-phase7-runtime-source-validation="true">
    <h3>Runtime Source Validation</h3>
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
  <a href="screen_3_history_selector.html">Open Screen 3</a>
</section>
<details id="index-source-mode-entry-panel" class="phase7-legacy-boundary-details" data-phase7-legacy-context="true"><summary>Historical Phase Boundary Evidence - Legacy 7BQ Source Mode Entry</summary><p>Legacy 7BQ Read-Only Context.</p></details>
<details id="index-source-status-panel" class="phase7-legacy-boundary-details" data-phase7-legacy-context="true"><summary>Historical Phase Boundary Evidence - Legacy 7BR Source Status</summary><p>Legacy 7BR Read-Only Context.</p></details>
<details id="index-object-storage-config-panel" class="phase7-legacy-boundary-details" data-phase7-legacy-context="true"><summary>Historical Phase Boundary Evidence - Legacy 7BS Object Storage Configuration</summary><p>Legacy 7BS Read-Only Context.</p></details>
<details id="index-screen3-handoff-panel" class="phase7-legacy-boundary-details" data-phase7-legacy-context="true"><summary>Historical Phase Boundary Evidence - Legacy 7BT Index to Screen 3 Handoff Preview</summary><p>Legacy 7BT Read-Only Context. In this legacy evidence only, no backend request is created.</p></details>
<section data-phase7-selection-workflow="true">
  <h3>Selection Workflow</h3>
  <ol>
    <li>Step 1: Select source mode or source context</li>
    <li>Step 2: Review source readiness and Screen 3 handoff target</li>
    <li>Step 3: Choose governed source-selection handoff</li>
    <li>Step 4: Submit governed source handoff request</li>
    <li>Step 5: Review result, request ID, audit ID, and Open Screen 3</li>
  </ol>
</section>
<a data-phase7-action-control="true"
   data-screen-id="index_source_mode"
   data-action-type="source_selection_handoff"
   data-workflow-type="index_source_selection_handoff"
   data-target-type="source_selection"
   data-target-id="index-source-selection"
   data-required-selection-key="selectedSourceMode"
   data-action-enabled-state="disabled-no-selection"><strong data-phase7-source-submit-label="true">Submit Object Storage Source Handoff</strong></a>
<p data-phase7-action-result-panel="true" data-phase7-request-id-target="true" data-phase7-audit-status-area="true">
  success/failure, Request ID and Audit record appear here.
</p>
"""


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
        generated += PHASE7CM_UX_FIXTURE
        for relative_path in module.GENERATED_DASHBOARD_FILES:
            (Path(cls.generated_dir.name) / Path(relative_path).name).write_text(
                generated,
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
        self.assertEqual(["index_source_mode"], sorted(screens))
        self.assertEqual("passed", screens["index_source_mode"]["status"])
        self.assertIn(
            "source_selection_handoff",
            screens["index_source_mode"]["present_action_types"],
        )
        self.assertEqual(
            "index_source_selection_runtime_workflow",
            self.payload["scope"],
        )
        self.assertIn("7CO Screen 2", self.payload["deferred_screens"][0])
        self.assertIn("7CT cross-screen", self.payload["deferred_screens"][-1])

    def test_index_source_card_selection_state_keys_are_supported(self) -> None:
        module = validation_module()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
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
        self.assertIn("sourceMode: 'selectedSourceMode'", source)
        self.assertIn("'source-mode': 'selectedSourceMode'", source)
        self.assertIn('data-dashboard-select-key="selectedSourceMode"', source)
        self.assertIn('data-required-selection-key="selectedSourceMode"', source)

        coverage = module.validate_dashboard_state_key_coverage(
            source,
            {"awr_dashboard/index.html": PHASE7CM_UX_FIXTURE},
        )
        self.assertEqual("passed", coverage["status"])

    def test_index_source_card_selection_click_path_contract_is_validated(self) -> None:
        module = validation_module()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        result = module.validate_index_source_selection_behavior_contract(
            source,
            {"awr_dashboard/index.html": PHASE7CM_UX_FIXTURE},
        )
        self.assertEqual("passed", result["status"])

        missing_summary = PHASE7CM_UX_FIXTURE.replace(
            'data-phase7-current-selection-summary="true"',
            'data-phase7-current-selection-summary="missing"',
        )
        failed = module.validate_index_source_selection_behavior_contract(
            source,
            {"awr_dashboard/index.html": missing_summary},
        )
        self.assertEqual("failed", failed["status"])
        self.assertIn("generated index missing", failed["reason"])

    def test_os_file_and_folder_picker_support_is_validated(self) -> None:
        module = validation_module()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        result = module.validate_picker_source_selection_support(
            source,
            {"awr_dashboard/index.html": PHASE7CM_UX_FIXTURE},
        )
        self.assertEqual("passed", result["status"])

        missing_folder_picker = PHASE7CM_UX_FIXTURE.replace(
            'data-phase7-source-picker="local_folder"',
            'data-phase7-source-picker="missing_folder"',
        )
        failed = module.validate_picker_source_selection_support(
            source,
            {"awr_dashboard/index.html": missing_folder_picker},
        )
        self.assertEqual("failed", failed["status"])
        self.assertIn("local_folder", failed["reason"])

    def test_pipeline_source_summary_is_compact_and_overflow_safe(self) -> None:
        module = validation_module()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )

        result = module.validate_pipeline_source_summary(
            source,
            {"awr_dashboard/index.html": PHASE7CM_UX_FIXTURE},
        )
        self.assertEqual("passed", result["status"])
        self.assertIn("sourcePipelineActiveSummary", source)
        self.assertIn("sourcePipelineNodeSummary", source)
        self.assertIn("Object Storage source selected. Object:", source)
        self.assertIn("pipeline_node_source: pipelineNode", source)

        generated_with_full_object_in_pipeline = PHASE7CM_UX_FIXTURE.replace(
            '<small data-phase7-source-summary-card="pipeline_node_source">Local staged AWR source. Path: data/input.</small>',
            '<small data-phase7-source-summary-card="pipeline_node_source">Object Storage: agentic-ai-awr-raw/awr/raw/FINDB/2026-03-29/adg_awr_snap_06_adg_transport_lag.out</small>',
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
            {"awr_dashboard/index.html": PHASE7CM_UX_FIXTURE},
        )
        self.assertEqual("passed", result["status"])

        generated_with_phase_wording = PHASE7CM_UX_FIXTURE.replace(
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
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )

        self.assertIn("PHASE7CM_ALLOWED_LOCAL_FILE_EXTENSIONS = Object.freeze(['out'])", source)
        self.assertIn("PHASE7CM_AWR_CANDIDATE_EXTENSIONS = Object.freeze(['out'])", source)
        self.assertIn('accept=".out"', PHASE7CM_UX_FIXTURE)
        self.assertNotIn('accept=".out,.txt,.html,.awr"', PHASE7CM_UX_FIXTURE)

        generated_with_html_accept = PHASE7CM_UX_FIXTURE.replace(
            'accept=".out"',
            'accept=".out,.txt,.html,.awr"',
        )
        failed = module.validate_picker_source_selection_support(
            source,
            {"awr_dashboard/index.html": generated_with_html_accept},
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
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
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
        generated += PHASE7CM_UX_FIXTURE
        result = module.validate_dashboard_runtime_interaction(
            source_text=source,
            generated_texts={"awr_dashboard/index.html": generated},
            service_exists=True,
            contract_exists=True,
        )
        self.assertTrue(result["generated_dashboard"]["validated"])
        for screen in result["generated_dashboard"]["screens"].values():
            with self.subTest(screen=screen["screen_id"]):
                self.assertEqual("passed", screen["status"])

    def test_generated_dashboard_evidence_is_required(self) -> None:
        module = validation_module()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
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
        self.assertEqual("empty", bridge["existing_run_empty_response"]["validation_status"])
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

    def test_service_or_contract_missing_blocks_validation(self) -> None:
        module = validation_module()
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
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
        generated += PHASE7CM_UX_FIXTURE
        result = module.validate_dashboard_runtime_interaction(
            source_text=source,
            generated_texts={"awr_dashboard/index.html": generated},
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
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        generated = (
            '<section data-phase7-runtime-interaction-panel="true">'
            '<button data-phase7-action-control="true" '
            'data-screen-id="index_source_mode" '
            'data-action-type="source_selection_handoff" '
            'data-workflow-type="index_source_selection_handoff" '
            'data-target-type="unit" data-target-id="unit" '
            'data-required-selection-key="selectedSourceMode">Submit</button>'
            "</section>"
            + PHASE7CM_UX_FIXTURE.replace(
                '<details id="index-source-mode-entry-panel"',
                'Screen 3 selection handoff remains a future controlled workflow.'
                '<details id="index-source-mode-entry-panel"',
            )
        )
        result = module.validate_dashboard_runtime_interaction(
            source_text=source,
            generated_texts={"awr_dashboard/index.html": generated},
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
                "awr_dashboard/index.html": (
                    '<section id="phase7cm-source-intake-panel" '
                    'data-phase7-index-source-selection="true">'
                    '<a data-phase7-action-control="true" '
                    'data-required-selection-key="selectedSourceMode" '
                    'data-phase7-action-result-panel="true" '
                    'data-phase7-request-id-target="true" '
                    'href="screen_3_history_selector.html">Submit</a>'
                    "</section>"
                )
            }
        )
        self.assertEqual("failed", result["status"])
        self.assertTrue(
            any("missing current selectable source card" in offender for offender in result["offenders"])
        )

    def test_index_legacy_panel_before_current_source_workflow_blocks_validation(self) -> None:
        module = validation_module()
        index = (
            '<details id="index-source-mode-entry-panel" class="phase7-legacy-boundary-details"></details>'
            + PHASE7CM_UX_FIXTURE
            + '<a data-phase7-action-control="true" data-screen-id="index_source_mode" '
            'data-action-type="source_selection_handoff" '
            'data-required-selection-key="selectedSourceMode"></a>'
        )
        result = module.validate_index_source_selection_workflow({"awr_dashboard/index.html": index})
        self.assertEqual("failed", result["status"])
        self.assertIn("legacy source preview panel appears before primary", result["reason"])

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
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )
        action_text = validation_module().action_control_text(source)
        self.assertNotIn("scripts/run_analysis.py", action_text)
        self.assertNotIn("run_analysis_coupling=true", action_text)
        self.assertNotIn('data-phase4i-mutation-allowed="true"', source)
        self.assertNotIn('data-phase8-behavior="true"', source)

    def test_dashboard_endpoint_is_configurable_for_oci_api(self) -> None:
        source = (ROOT / "src" / "reporting" / "html_dashboard.py").read_text(
            encoding="utf-8",
            errors="ignore",
        )

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
