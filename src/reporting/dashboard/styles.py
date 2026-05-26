def _shared_page_styles() -> str:
    """Return the shared multi-page product styling."""

    return """
    :root {
      --bg: #08111d;
      --panel: #0f1b2d;
      --panel-soft: rgba(15, 27, 45, 0.95);
      --panel-strong: #14243a;
      --text: #e8eef7;
      --muted: #9fb0c7;
      --line: #233754;
      --accent: #5ad1ff;
      --accent-soft: rgba(90, 209, 255, 0.12);
      --high: #ff6b6b;
      --medium: #f6b84c;
      --low: #7fb3d5;
      --pass: #66bb6a;
      --marginal: #f6b84c;
      --fail: #ff6b6b;
      --na: #8ea3ba;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      background:
        radial-gradient(circle at top right, rgba(90, 209, 255, 0.10), transparent 28%),
        linear-gradient(180deg, #08111d 0%, #07101a 100%);
      color: var(--text);
      line-height: 1.6;
    }
    [data-dashboard-evidence-gated-content="true"],
    [data-screen1-artifact-ready-content="true"] {
      display: none !important;
    }
    body[data-dashboard-evidence-ready="true"] [data-dashboard-evidence-gated-content="true"],
    [data-screen1-generated-artifact-ready="true"] [data-screen1-artifact-ready-content="true"] {
      display: block !important;
    }
    body[data-dashboard-evidence-ready="true"] [data-dashboard-evidence-gate-empty="true"],
    [data-screen1-generated-artifact-ready="true"] [data-screen1-artifact-empty-state="true"] {
      display: none !important;
    }
    .container {
      max-width: 1600px;
      margin: 0 auto;
      padding: 28px 20px 40px;
    }
    .top-shell {
      display: grid;
      gap: 14px;
      margin-bottom: 22px;
    }
    .top-shell.sticky-shell {
      position: sticky;
      top: 0;
      z-index: 40;
      padding-top: 12px;
      backdrop-filter: blur(14px);
    }
    .hero {
      position: relative;
      padding: 28px;
      padding-right: 280px;
      border: 1px solid var(--line);
      border-radius: 22px;
      background: linear-gradient(135deg, rgba(20, 36, 58, 0.98), rgba(10, 20, 34, 0.96));
      box-shadow: 0 18px 44px rgba(0, 0, 0, 0.28);
    }
    .eyebrow {
      color: var(--accent);
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      margin-bottom: 10px;
    }
    h1 { margin: 0 0 10px; font-size: 34px; line-height: 1.1; }
    h2 { margin: 0 0 14px; font-size: 21px; }
    h3 { margin: 0 0 10px; font-size: 17px; }
    .hero-summary { margin: 0 0 10px; color: var(--text); max-width: 820px; }
    .hero-meta, .meta { color: var(--muted); font-size: 13px; }
    .page-nav {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      width: 100%;
      gap: 8px;
      overflow-x: visible;
      white-space: nowrap;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(10, 20, 34, 0.88);
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
    }
    .nav-link {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      border-radius: 999px;
      padding: 7px 12px;
      color: var(--text);
      text-decoration: none;
      border: 1px solid rgba(159, 176, 199, 0.26);
      background: rgba(16, 28, 45, 0.72);
      font-size: 13px;
      font-weight: 600;
    }
    .nav-link.active {
      color: #08111d;
      background: var(--accent);
      border-color: rgba(90, 209, 255, 0.6);
    }
    .runtime-badge {
      position: absolute;
      top: 16px;
      right: 16px;
      display: grid;
      justify-items: end;
      gap: 5px;
      width: max-content;
      max-width: calc(100% - 32px);
      text-align: right;
      contain: layout style;
    }
    .runtime-meta {
      display: grid;
      justify-items: center;
      gap: 4px;
      font-size: 12px;
      color: var(--muted);
      margin-top: 4px;
    }
    .runtime-state-line {
      white-space: nowrap;
    }
    .runtime-state-pills {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 4px;
      flex-wrap: nowrap;
      width: max-content;
      max-width: 100%;
    }
    .runtime-mini-pill {
      display: inline-flex;
      align-items: baseline;
      justify-content: center;
      gap: 4px;
      flex: 0 0 auto;
      width: auto;
      max-width: none;
      min-width: 0;
      min-height: 21px;
      border: 1px solid rgba(159, 176, 199, 0.2);
      border-radius: 999px;
      padding: 2px 6px;
      background: rgba(11, 20, 34, 0.58);
      color: var(--muted);
      font-size: 11px;
      line-height: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .runtime-mini-pill strong {
      display: inline-block;
      min-width: 0;
      font-weight: 800;
      line-height: 1;
      position: relative;
      top: -0.5px;
    }
    .state-pass {
      color: var(--pass);
    }
    .state-warning {
      color: var(--medium);
    }
    .state-low {
      color: var(--low);
    }
    .state-accent {
      color: var(--accent);
    }
    .state-muted {
      color: var(--muted);
      opacity: 0.85;
    }
    .state-error {
      color: var(--high);
    }
    .grid, .subgrid, .chart-grid, .flow-grid, .nav-card-grid, .health-check-grid {
      display: grid;
      gap: 18px;
    }
    .grid, .subgrid, .chart-grid { grid-template-columns: repeat(12, 1fr); }
    .flow-grid, .nav-card-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .health-check-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .card {
      grid-column: span 12;
      background: var(--panel-soft);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
    }
    .card.primary {
      background: linear-gradient(135deg, rgba(24, 42, 66, 0.98), rgba(14, 27, 46, 0.98));
      border-color: rgba(90, 209, 255, 0.38);
    }
    .card.secondary {
      background: rgba(12, 22, 36, 0.88);
      padding: 16px;
    }
    .card.prominent {
      background: linear-gradient(135deg, rgba(20, 36, 58, 0.96), rgba(13, 24, 40, 0.96));
      border-color: rgba(90, 209, 255, 0.34);
    }
    .home-product-model-panel {
      background:
        radial-gradient(circle at 18% 0%, rgba(90, 209, 255, 0.22), transparent 34%),
        linear-gradient(135deg, rgba(32, 58, 88, 0.98), rgba(16, 34, 57, 0.98));
      border-color: rgba(110, 214, 255, 0.58);
      box-shadow: 0 18px 40px rgba(20, 120, 190, 0.18), 0 10px 24px rgba(0, 0, 0, 0.24);
    }
    .home-product-model-panel .nav-card {
      background: linear-gradient(135deg, rgba(36, 66, 100, 0.82), rgba(21, 42, 70, 0.84));
      border-color: rgba(124, 219, 255, 0.42);
    }
    .card.compact-card {
      padding: 16px 18px;
    }
    .compact-card h2 {
      margin-bottom: 8px;
    }
    .compact-card p {
      margin-top: 0;
      margin-bottom: 8px;
    }
    .ai-explanation-card h2 {
      font-size: 18px;
      line-height: 1.25;
    }
    .ai-explanation-card .chart-support-note {
      font-size: 13px;
      line-height: 1.45;
    }
    .ai-explanation-card .info-box strong {
      font-size: 12px;
      line-height: 1.35;
    }
    .ai-explanation-card .info-box div {
      font-size: 13px;
      line-height: 1.45;
    }
    .section-kicker {
      color: var(--accent);
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 10px;
    }
    .half, .evidence-pane, .chart-panel { grid-column: span 12; }
    .stack { display: grid; gap: 12px; }
    .item, .flow-step, .nav-card, .visual-layer-card, .health-check-card {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: rgba(20, 36, 58, 0.7);
    }
    .nav-card {
      display: block;
      text-decoration: none;
      color: inherit;
    }
    .nav-card h3, .flow-step strong, .visual-layer-card strong, .info-box strong, .scalar-box strong {
      color: var(--accent);
      display: block;
      margin-bottom: 6px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .decision-grid, .info-grid, .provider-grid, .scalar-grid, .visual-layer-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .visual-layer-grid, .scalar-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .diagnostic-block {
      display: grid;
      gap: 12px;
      margin-top: 18px;
    }
    .diagnostic-block:first-of-type { margin-top: 0; }
    .domain-strip {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 10px;
    }
    .domain-strip-item {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
    }
    .domain-strip-label {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      color: var(--text);
      font-size: 12px;
      margin-bottom: 8px;
    }
    .domain-strip-track {
      height: 8px;
      border-radius: 999px;
      overflow: hidden;
      background: rgba(159, 176, 199, 0.18);
    }
    .domain-strip-fill {
      height: 100%;
      border-radius: inherit;
      background: var(--accent);
    }
    .selector-control-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .selector-control {
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .selector-control input,
    .selector-control select {
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 9px 10px;
      color: var(--text);
      background: rgba(16, 28, 45, 0.82);
      font: inherit;
      text-transform: none;
      letter-spacing: 0;
    }
    .static-selection-note {
      margin: 0 0 14px;
      color: var(--muted);
      font-size: 13px;
    }
    [data-dashboard-selectable] {
      cursor: pointer;
    }
    [data-dashboard-selectable].is-selected,
    [data-dashboard-selectable][data-selected="true"] {
      border-color: rgba(90, 209, 255, 0.74);
      box-shadow: 0 0 0 2px rgba(90, 209, 255, 0.18);
    }
    [data-dashboard-selected-summary] {
      color: var(--muted);
      font-size: 13px;
    }
    [data-dashboard-filter-active="false"] {
      opacity: 0.72;
    }
    .screen3-control-center {
      border-color: rgba(90, 209, 255, 0.32);
    }
    .screen3-selected-state-panel {
      border-color: rgba(90, 209, 255, 0.34);
      background: rgba(90, 209, 255, 0.08);
    }
    .screen3-selected-summary {
      margin: 0 0 12px;
      color: var(--text);
      font-size: 14px;
      font-weight: 700;
    }
    .screen3-source-received-panel,
    .screen3-work-area,
    .screen3-runtime-options-loader-panel,
    .screen3-runtime-scope-panel,
    .screen3-existing-run-selection-panel,
    .screen3-snapshot-interval-panel,
    .screen3-comparison-setup-panel,
    .screen3-review-mode-panel,
    .screen3-selection-impact-panel,
    .screen3-readiness-panel,
    .screen3-result-panel,
    .screen3-explanation-panel,
    .screen3-runtime-boundary-panel {
      border-color: rgba(90, 209, 255, 0.26);
      background: rgba(16, 28, 45, 0.52);
    }
    .screen3-work-area {
      display: grid;
      gap: 14px;
      grid-column: 1 / -1;
      padding: 16px;
      border-radius: 12px;
    }
    .screen3-work-area > h3 {
      margin-bottom: 2px;
    }
    .screen3-source-scope-stack,
    .screen3-workflow-subgrid,
    .screen3-explanation-list {
      display: grid;
      gap: 12px;
    }
    .screen3-source-context-summary {
      display: grid;
      gap: 10px;
    }
    .screen3-source-context-header {
      display: grid;
      gap: 4px;
      padding: 10px 12px;
      border: 1px solid rgba(90, 209, 255, 0.24);
      border-radius: 10px;
      background: rgba(90, 209, 255, 0.08);
    }
    .screen3-source-context-header strong {
      color: var(--text);
      font-size: 14px;
    }
    .screen3-source-context-header span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen3-source-context-grid {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 8px;
    }
    .screen3-source-context-card {
      min-height: 0;
      padding: 8px 10px;
      border: 1px solid rgba(159, 176, 199, 0.22);
      border-radius: 12px;
      background: rgba(16, 28, 45, 0.62);
    }
    .screen3-source-context-card.primary {
      border-color: rgba(90, 209, 255, 0.32);
      background: rgba(90, 209, 255, 0.1);
    }
    .screen3-source-context-card span {
      display: block;
      margin-bottom: 4px;
      color: var(--accent);
      font-size: 10px;
      font-weight: 850;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .screen3-source-context-card strong {
      display: block;
      color: var(--text);
      font-size: 11px;
      line-height: 1.28;
      overflow-wrap: anywhere;
    }
    .screen2-control-card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 10px;
      align-items: stretch;
    }
    .screen2-control-card-grid-balanced {
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    }
    .screen2-control-info-box {
      min-height: 0;
      padding: 10px 12px;
      border: 1px solid rgba(159, 176, 199, 0.22);
      border-radius: 12px;
      background: rgba(16, 28, 45, 0.66);
      overflow-wrap: anywhere;
    }
    .screen2-control-info-box.wide {
      grid-column: span 2;
    }
    .screen2-control-info-box.full {
      grid-column: 1 / -1;
    }
    .screen2-control-info-box strong {
      display: block;
      margin-bottom: 4px;
      color: var(--accent);
      font-size: 11px;
      font-weight: 850;
      letter-spacing: 0;
      line-height: 1.2;
      text-transform: uppercase;
    }
    .screen2-control-info-box div {
      color: var(--text);
      font-size: 13px;
      font-weight: 700;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .screen2-control-subvalue {
      display: inline;
    }
    .screen2-control-prefix {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }
    .screen2-control-separator {
      color: var(--muted);
      margin: 0 4px;
    }
    .screen3-workflow-subgrid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .screen3-workflow-subgrid .screen3-context-subpanel:first-child {
      grid-column: 1 / -1;
    }
    .screen3-target-card-grid .screen3-context-subpanel:first-child,
    .screen3-target-card-grid .screen3-comparison-target-card {
      grid-column: auto;
    }
    .screen3-runtime-detail-grid {
      grid-template-columns: 1fr;
    }
    .screen3-interval-full-width-panel {
      grid-column: 1 / -1;
      width: 100%;
    }
    .screen3-filter-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .screen3-filter-control {
      display: grid;
      gap: 6px;
      min-width: 0;
    }
    .screen3-filter-control h5,
    .screen3-filter-control label,
    .screen3-filter-toolbar label,
    .screen3-apply-selection-inline h5 {
      margin: 0;
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-filter-toolbar {
      display: grid;
      grid-template-columns: minmax(180px, 1fr) auto auto minmax(120px, 160px);
      gap: 8px;
      align-items: end;
    }
    .screen3-filter-toolbar label {
      grid-column: 1 / -1;
    }
    .screen3-filter-select,
    .screen3-filter-search {
      width: 100%;
      min-height: 38px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      padding: 8px 10px;
      color: var(--text);
      background: rgba(8, 15, 26, 0.88);
      font: inherit;
    }
    .screen3-filter-select:focus,
    .screen3-filter-search:focus {
      outline: 2px solid rgba(90, 209, 255, 0.4);
      outline-offset: 2px;
      border-color: rgba(90, 209, 255, 0.58);
    }
    .screen3-filter-action-button {
      min-height: 38px;
      white-space: nowrap;
    }
    .screen3-result-limit-control {
      display: grid;
      gap: 4px;
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-apply-selection-inline {
      display: grid;
      gap: 8px;
      margin: 10px 0 12px;
      padding: 10px;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 8px;
      background: rgba(8, 15, 26, 0.34);
    }
    .screen3-comparison-target-panel,
    .screen3-comparison-preview-panel {
      grid-column: 1 / -1;
    }
    .screen3-comparison-controls-card,
    .screen3-target-assignment-card,
    .screen3-target-card-grid,
    .screen3-target-picker-details {
      grid-column: 1 / -1;
    }
    .screen3-comparison-control-grid,
    .screen3-target-card-grid,
    .screen3-target-picker-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .screen3-comparison-control-grid section {
      display: grid;
      gap: 8px;
      min-width: 0;
    }
    .screen3-comparison-control-grid h5 {
      margin: 0;
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-comparison-target-card {
      display: grid;
      gap: 8px;
      padding: 14px;
      min-width: 0;
    }
    .screen3-comparison-target-card h4 {
      margin: 0;
      font-size: 12px;
    }
    .screen3-target-resolution-grid {
      grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
      gap: 8px;
    }
    .screen3-target-resolution-grid .screen2-control-info-box {
      display: grid;
      align-content: start;
      min-width: 0;
      padding: 8px 10px;
      border-radius: 10px;
    }
    .screen3-target-resolution-grid .screen2-control-info-box.wide {
      grid-column: span 2;
    }
    .screen3-target-resolution-grid .screen2-control-info-box strong {
      font-size: 10px;
      line-height: 1.25;
    }
    .screen3-target-resolution-grid .screen2-control-info-box div {
      font-size: 11px;
      line-height: 1.3;
      overflow-wrap: anywhere;
    }
    .screen3-context-subpanel,
    .screen3-explanation-article {
      border: 1px solid rgba(159, 176, 199, 0.18);
      border-radius: 8px;
      padding: 12px;
      background: rgba(11, 20, 34, 0.42);
    }
    .screen3-context-subpanel h4,
    .screen3-explanation-article h4 {
      margin: 0 0 8px;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-explanation-article p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .screen3-table-wrap {
      width: 100%;
      overflow-x: auto;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 10px;
      background: rgba(11, 20, 34, 0.34);
    }
    .screen3-inventory-table-wrap {
      max-height: 520px;
      overflow: auto;
    }
    .screen3-interval-table-wrap {
      max-height: 320px;
      overflow: auto;
    }
    .screen3-runtime-scope-table {
      width: 100%;
      min-width: 1120px;
      border-collapse: collapse;
      font-size: 11px;
    }
    .screen3-runtime-scope-table th,
    .screen3-runtime-scope-table td {
      padding: 7px 8px;
      border-bottom: 1px solid rgba(159, 176, 199, 0.12);
      text-align: left;
      vertical-align: middle;
      overflow-wrap: anywhere;
    }
    .screen3-runtime-scope-table th {
      color: var(--accent);
      background: rgba(15, 27, 45, 0.98);
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      position: sticky;
      top: 0;
      z-index: 3;
      box-shadow: 0 1px 0 rgba(159, 176, 199, 0.18);
    }
    .screen3-table-header-control {
      display: grid;
      grid-template-columns: 1fr auto auto;
      align-items: center;
      gap: 5px;
      min-width: 0;
    }
    .screen3-table-header-label {
      min-width: 0;
      color: var(--accent);
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .screen3-table-sort-button,
    .screen3-table-filter-toggle {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 6px;
      padding: 0;
      color: var(--muted);
      background: rgba(6, 13, 23, 0.35);
      font: inherit;
      cursor: pointer;
    }
    .screen3-table-sort-button small {
      color: inherit;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.02em;
    }
    .screen3-table-filter-toggle span {
      font-size: 12px;
      line-height: 1;
    }
    .screen3-table-sort-button.is-active,
    .screen3-table-filter-toggle.is-active,
    .screen3-table-header-control.has-active-filter .screen3-table-filter-toggle {
      color: #08111d;
      border-color: rgba(90, 209, 255, 0.72);
      background: var(--accent);
    }
    .screen3-table-sort-button:focus-visible,
    .screen3-table-filter-toggle:focus-visible,
    .screen3-table-filter-input:focus-visible {
      outline: 2px solid rgba(90, 209, 255, 0.48);
      outline-offset: 2px;
      border-radius: 4px;
    }
    .screen3-table-filter-input {
      display: none;
      grid-column: 1 / -1;
      width: 100%;
      min-width: 64px;
      height: 22px;
      margin-top: 2px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 6px;
      padding: 2px 6px;
      color: var(--text);
      background: rgba(6, 13, 23, 0.78);
      font-size: 10px;
      letter-spacing: 0;
      text-transform: none;
    }
    .screen3-table-header-control.is-filter-open .screen3-table-filter-input,
    .screen3-table-header-control.has-active-filter .screen3-table-filter-input {
      display: block;
    }
    .screen3-table-filter-input::placeholder {
      color: rgba(159, 176, 199, 0.62);
    }
    .screen3-table-control-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin: 8px 0 10px;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 10px;
      padding: 8px 10px;
      color: var(--muted);
      background: rgba(11, 20, 34, 0.38);
      font-size: 12px;
    }
    .screen3-table-clear-button {
      min-height: 28px;
      padding: 5px 9px;
      font-size: 11px;
    }
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(1),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(1) {
      width: 118px;
      min-width: 118px;
    }
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(2),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(2) {
      width: 112px;
      min-width: 112px;
    }
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(3),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(3),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(4),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(4),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(5),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(5),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(6),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(6),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(12),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(12),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(13),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(13) {
      white-space: nowrap;
      overflow-wrap: normal;
    }
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(5),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(5) {
      min-width: 96px;
    }
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(7),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(7),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(8),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(8),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table th:nth-child(9),
    .screen3-inventory-table-wrap .screen3-runtime-scope-table td:nth-child(9) {
      min-width: 120px;
    }
    .screen3-runtime-scope-table tr[data-dashboard-selectable="true"]:hover {
      background: rgba(90, 209, 255, 0.08);
    }
    .screen3-runtime-scope-table tr.is-selected,
    .screen3-runtime-scope-table tr[data-selected="true"] {
      background: rgba(90, 209, 255, 0.08);
      outline: 1px solid rgba(90, 209, 255, 0.28);
      outline-offset: -1px;
      box-shadow: inset 2px 0 0 rgba(90, 209, 255, 0.46);
    }
    .screen3-runtime-scope-table tr.screen3-selected-runtime-row {
      background: rgba(90, 209, 255, 0.17);
      outline-color: rgba(90, 209, 255, 0.66);
      box-shadow: inset 3px 0 0 rgba(90, 209, 255, 0.8);
    }
    .screen3-runtime-scope-table tr.screen3-selected-interval-row {
      background: rgba(65, 220, 168, 0.11);
      outline: 1px dashed rgba(65, 220, 168, 0.62);
      box-shadow: inset 3px 0 0 rgba(65, 220, 168, 0.58);
    }
    .screen3-runtime-scope-table tr.screen3-selected-advanced-row {
      background: rgba(166, 139, 255, 0.1);
      outline: 1px dashed rgba(166, 139, 255, 0.62);
      box-shadow: inset 3px 0 0 rgba(166, 139, 255, 0.62);
    }
    .screen3-runtime-scope-table tr.is-selected:hover,
    .screen3-runtime-scope-table tr[data-selected="true"]:hover,
    .screen3-runtime-scope-table tr.screen3-selected-runtime-row:hover,
    .screen3-runtime-scope-table tr.screen3-selected-interval-row:hover,
    .screen3-runtime-scope-table tr.screen3-selected-advanced-row:hover {
      background: rgba(90, 209, 255, 0.2);
    }
    .screen3-disabled-placeholder-row {
      color: var(--muted);
      background: rgba(159, 176, 199, 0.05);
      opacity: 0.7;
      cursor: not-allowed;
    }
    .screen3-runtime-scope-table .empty-state {
      padding: 12px;
      color: var(--muted);
    }
    .screen3-interval-table {
      min-width: 0;
      table-layout: auto;
    }
    .screen3-interval-table th:nth-child(1),
    .screen3-interval-table td:nth-child(1),
    .screen3-interval-table th:nth-child(2),
    .screen3-interval-table td:nth-child(2),
    .screen3-interval-table th:nth-child(5),
    .screen3-interval-table td:nth-child(5) {
      white-space: nowrap;
      overflow-wrap: normal;
    }
    .screen3-interval-table th,
    .screen3-interval-table td {
      white-space: normal;
      overflow-wrap: anywhere;
    }
    .screen3-active-assignment-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin: 6px 0 10px;
      border: 1px solid rgba(90, 209, 255, 0.22);
      border-radius: 10px;
      padding: 9px 11px;
      color: var(--muted);
      background: rgba(90, 209, 255, 0.07);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen3-active-assignment-banner strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-operator-steps {
      margin: 8px 0 0;
      padding-left: 20px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .screen3-operator-steps li + li {
      margin-top: 5px;
    }
    .screen3-selected-context-strip {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 10px;
    }
    .screen3-selected-context-chip {
      border: 1px solid rgba(159, 176, 199, 0.18);
      border-radius: 10px;
      padding: 10px;
      background: rgba(12, 24, 40, 0.58);
      min-width: 0;
    }
    .screen3-selected-context-chip h5,
    .screen3-selected-context-chip p,
    .screen3-selected-context-chip small {
      margin: 0;
    }
    .screen3-selected-context-chip h5 {
      color: var(--accent);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .screen3-selected-context-chip p {
      margin-top: 6px;
      color: var(--text);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    .screen3-selected-context-chip small {
      display: block;
      margin-top: 4px;
      color: var(--muted);
      font-size: 11px;
      overflow-wrap: anywhere;
    }
    .screen3-selection-legend {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
      color: var(--muted);
      font-size: 11px;
    }
    .screen3-selection-legend span {
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
    .screen3-legend-swatch {
      width: 16px;
      height: 9px;
      border-radius: 999px;
      display: inline-block;
      border: 1px solid rgba(159, 176, 199, 0.2);
    }
    .screen3-legend-swatch.runtime {
      background: rgba(90, 209, 255, 0.2);
      border-color: rgba(90, 209, 255, 0.7);
    }
    .screen3-legend-swatch.interval {
      background: rgba(65, 220, 168, 0.14);
      border-style: dashed;
      border-color: rgba(65, 220, 168, 0.7);
    }
    .screen3-legend-swatch.advanced {
      background: rgba(166, 139, 255, 0.14);
      border-style: dashed;
      border-color: rgba(166, 139, 255, 0.72);
    }
    .screen3-pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .screen3-pill-button {
      display: inline-flex;
      flex-direction: column;
      align-items: flex-start;
      max-width: 220px;
      min-height: 54px;
      padding: 8px 10px;
      border: 1px solid rgba(90, 209, 255, 0.34);
      border-radius: 999px;
      color: var(--text);
      background: rgba(16, 28, 45, 0.72);
      font: inherit;
      text-align: left;
      cursor: pointer;
    }
    .screen3-pill-button span {
      font-size: 12px;
      font-weight: 800;
    }
    .screen3-pill-button small {
      color: var(--muted);
      font-size: 11px;
      line-height: 1.25;
    }
    .screen3-submit-result-grid {
      display: grid;
      grid-template-columns: minmax(260px, 0.86fr) minmax(320px, 1.14fr);
      gap: 12px;
      align-items: start;
    }
    .screen3-secondary-selector-details {
      grid-column: 1 / -1;
      border: 1px solid rgba(159, 176, 199, 0.2);
      border-radius: 10px;
      padding: 12px;
      background: rgba(11, 20, 34, 0.36);
    }
    .screen3-secondary-selector-details summary {
      color: var(--accent);
      cursor: pointer;
      font-size: 13px;
      font-weight: 800;
    }
    .screen3-secondary-selector-grid {
      margin-top: 12px;
    }
    .screen3-target-picker-details .screen3-table-wrap {
      max-height: 260px;
      overflow: auto;
    }
    .screen3-source-scope-grid dt {
      color: var(--accent);
    }
    .screen3-source-scope-grid dd {
      overflow-wrap: anywhere;
    }
    .screen3-actions-inline {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      margin: 8px 0 14px;
    }
    .screen3-runtime-options-button.secondary {
      border-color: rgba(90, 209, 255, 0.38);
      background: rgba(90, 209, 255, 0.1);
    }
    .screen3-runtime-options-status-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .screen3-runtime-options-status-grid dd,
    .screen3-runtime-options-debug-grid dd {
      overflow-wrap: anywhere;
    }
    .screen3-runtime-coverage-details {
      margin-top: 10px;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 10px;
      padding: 10px;
      background: rgba(8, 15, 26, 0.3);
    }
    .screen3-dynamic-option-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }
    .screen3-runtime-option-card {
      display: grid;
      gap: 6px;
      min-height: 92px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 10px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
      overflow-wrap: anywhere;
    }
    .screen3-runtime-option-card .selector-card-title {
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-runtime-option-card .selector-card-detail {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen3-selector-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .screen3-selector-card {
      display: grid;
      gap: 6px;
      min-height: 104px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 10px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }
    .screen3-selector-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-selector-card span {
      color: var(--text);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .screen3-selector-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen3-selector-card.active {
      border-color: rgba(90, 209, 255, 0.62);
      background: rgba(90, 209, 255, 0.12);
    }
    .screen3-reanalysis-actions-panel {
      border-color: rgba(246, 184, 76, 0.34);
      background: rgba(246, 184, 76, 0.06);
    }
    .screen3-governed-actions-card,
    .screen3-result-panel {
      border-radius: 12px;
      border: 1px solid rgba(90, 209, 255, 0.26);
      padding: 14px;
      background: rgba(16, 28, 45, 0.56);
    }
    .screen3-action-grid,
    .screen3-source-mode-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
    }
    .screen3-source-mode-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .screen3-reanalysis-action-card,
    .screen3-source-mode-card {
      display: grid;
      gap: 6px;
      min-height: 116px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }
    .screen3-governed-action-control {
      display: grid;
      gap: 8px;
      color: inherit;
      text-decoration: none;
    }
    .screen3-governed-action-control.is-disabled,
    .screen3-governed-action-control[aria-disabled="true"] {
      opacity: 0.72;
      cursor: not-allowed;
    }
    .screen3-reanalysis-action-card.disabled-preview-only {
      border-color: rgba(246, 184, 76, 0.42);
      opacity: 0.82;
      cursor: not-allowed;
    }
    .screen3-reanalysis-action-card strong,
    .screen3-source-mode-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-reanalysis-action-card span,
    .screen3-reanalysis-action-card em,
    .screen3-source-mode-card p {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen3-reanalysis-action-card p,
    .screen3-source-mode-card p {
      margin: 0;
    }
    .screen3-action-state-pill,
    .screen3-action-missing-gate {
      display: inline-flex;
      width: fit-content;
      max-width: 100%;
      padding: 5px 8px;
      border: 1px solid rgba(246, 184, 76, 0.34);
      border-radius: 999px;
      color: #fff6e2;
      background: rgba(246, 184, 76, 0.08);
      font-size: 11px;
      font-weight: 800;
      line-height: 1.25;
    }
    .screen3-action-missing-gate {
      border-color: rgba(159, 176, 199, 0.22);
      color: var(--muted);
      background: rgba(11, 20, 34, 0.32);
      font-weight: 600;
    }
    .screen3-action-submit-button {
      justify-content: center;
      width: fit-content;
      min-height: 32px;
      padding: 6px 10px;
    }
    .screen3-action-facts {
      display: grid;
      gap: 7px;
      margin: 4px 0 0;
    }
    .screen3-action-facts div {
      display: grid;
      gap: 3px;
      padding-top: 7px;
      border-top: 1px solid rgba(159, 176, 199, 0.14);
    }
    .screen3-action-facts dt {
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-action-facts dd {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen3-reanalysis-action-card em {
      font-style: normal;
      font-weight: 800;
      text-transform: uppercase;
    }
    .screen3-technical-details {
      margin-top: 4px;
      color: var(--muted);
      font-size: 12px;
    }
    .screen3-technical-details summary {
      cursor: pointer;
    }
    .screen3-technical-details p {
      margin: 6px 0 0;
    }
    .screen3-action-status {
      margin-top: 6px;
      padding: 9px 10px;
      border: 1px solid rgba(159, 176, 199, 0.18);
      border-radius: 8px;
      color: var(--muted);
      background: rgba(11, 20, 34, 0.48);
      font-size: 12px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }
    .screen3-result-summary-banner {
      display: block;
      margin: 10px 0 12px;
      padding: 12px;
      border: 1px solid rgba(90, 209, 255, 0.24);
      border-radius: 10px;
      background: rgba(90, 209, 255, 0.08);
    }
    .screen3-result-summary-banner div {
      display: grid;
      gap: 4px;
    }
    .screen3-result-summary-banner dt {
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-result-summary-banner dd {
      margin: 0;
      color: var(--text);
      font-size: 13px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .screen3-result-subcard-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      align-items: start;
    }
    .screen3-result-subcard {
      min-width: 0;
      border-radius: 10px;
      padding: 12px;
    }
    .screen3-result-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .screen3-result-grid dd {
      overflow-wrap: anywhere;
      line-height: 1.35;
    }
    .screen3-comparison-result-summary,
    .screen3-backend-references-details {
      grid-column: 1 / -1;
    }
    .screen3-backend-references-details summary {
      color: var(--accent);
      cursor: pointer;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen3-backend-references-details[open] summary {
      margin-bottom: 8px;
    }
    .screen3-source-handoff-empty {
      border: 1px solid rgba(246, 184, 76, 0.28);
      border-radius: 8px;
      padding: 10px 12px;
      background: rgba(246, 184, 76, 0.08);
    }
    .inline-action-link {
      display: inline-flex;
      align-items: center;
      min-height: 36px;
      padding: 7px 11px;
      border: 1px solid rgba(90, 209, 255, 0.42);
      border-radius: 8px;
      color: var(--accent);
      text-decoration: none;
      font-size: 13px;
      font-weight: 800;
    }
    .screen3-action-status[data-phase7-action-status="blocked"] {
      color: #fff6e2;
      border-color: rgba(246, 184, 76, 0.46);
    }
    .screen3-action-status[data-phase7-action-status="accepted"],
    .screen3-action-status[data-phase7-action-status="completed"] {
      color: #effbef;
      border-color: rgba(102, 187, 106, 0.42);
    }
    .screen3-action-status[data-phase7-action-status="failed"],
    .screen3-action-status[data-phase7-action-status="failed_safely"] {
      color: #fff4f4;
      border-color: rgba(255, 107, 107, 0.42);
    }
    .scope-chip.active {
      color: #08111d;
      background: var(--accent);
      border-color: rgba(90, 209, 255, 0.6);
    }
    .static-option-row {
      margin-top: 2px;
    }
    .decision-summary-confidence {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 14px;
      flex-wrap: wrap;
    }
    .decision-summary-confidence .confidence-note {
      margin: 0;
      line-height: 1.3;
    }
    .diagnostic-compact-card {
      padding: 16px;
    }
    .diagnostic-snapshot-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    .diagnostic-snapshot-grid .info-box {
      padding: 12px;
    }
    .diagnostic-confidence-strip {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: 12px;
      flex-wrap: wrap;
    }
    .confidence-cell {
      display: grid;
      justify-items: center;
      align-content: center;
      gap: 8px;
    }
    .diagnostic-confidence-strip .confidence-note {
      margin: 0;
      line-height: 1.3;
      align-self: center;
    }
    .diagnostic-drivers-card {
      padding: 16px;
    }
    .diagnostic-driver-stack {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .diagnostic-driver-row {
      display: block;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
      min-height: auto;
      background: rgba(16, 28, 45, 0.72);
    }
    .diagnostic-driver-row .severity,
    .diagnostic-driver-row .status-pill {
      display: none;
    }
    .diagnostic-driver-row h3 {
      margin: 0 0 4px;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .diagnostic-driver-row p {
      margin: 0;
      color: var(--text);
      font-size: 13px;
      line-height: 1.35;
    }
    .diagnostic-driver-evidence {
      margin: 6px 0 0;
      font-size: 12px;
      line-height: 1.35;
    }
    .screen1-governance-parser-exploration {
      border-color: rgba(90, 209, 255, 0.32);
    }
    .screen1-selected-governance-parser-panel {
      border-color: rgba(90, 209, 255, 0.34);
      background: rgba(90, 209, 255, 0.08);
    }
    .screen1-selected-governance-parser-summary {
      margin: 0 0 12px;
      color: var(--text);
      font-size: 14px;
      font-weight: 700;
    }
    .screen1-selector-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .screen1-selector-card {
      display: grid;
      gap: 6px;
      min-height: 104px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 10px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }
    .screen1-selector-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen1-selector-card span {
      color: var(--text);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .screen1-selector-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen1-selector-card.active {
      border-color: rgba(90, 209, 255, 0.62);
      background: rgba(90, 209, 255, 0.12);
    }
    .screen1-parser-governance-runtime {
      border-color: rgba(90, 209, 255, 0.34);
      background: rgba(16, 28, 45, 0.74);
    }
	    .screen1-parser-governance-review {
	      border-color: rgba(90, 209, 255, 0.38);
	      background: rgba(16, 28, 45, 0.78);
	    }
		    .screen1-governance-explanation-panel {
		      display: grid;
		      gap: 10px;
		      margin-top: 12px;
		      border: 1px solid rgba(90, 209, 255, 0.18);
		      border-radius: 8px;
		      padding: 12px;
		      background: rgba(11, 20, 34, 0.34);
		    }
		    .screen1-governance-explanation-panel h3 {
		      margin: 0;
		      color: var(--accent);
		      font-size: 12px;
		      font-weight: 900;
		      letter-spacing: 0.05em;
		      text-transform: uppercase;
		    }
		    .screen1-governance-explanation {
		      display: grid;
		      grid-template-columns: 1fr;
		      gap: 8px;
		      margin-top: 0;
		    }
		    .screen1-governance-explanation article {
		      display: grid;
		      gap: 6px;
		      min-width: 0;
		      border: 1px solid rgba(159, 176, 199, 0.14);
		      border-radius: 8px;
		      padding: 10px 12px;
		      background: rgba(11, 20, 34, 0.36);
		    }
	    .screen1-governance-explanation strong {
	      color: var(--accent);
	      font-size: 12px;
	      font-weight: 900;
	      letter-spacing: 0.05em;
	      text-transform: uppercase;
	    }
	    .screen1-governance-explanation p {
	      margin: 0;
	      color: var(--muted);
	      font-size: 12px;
	      line-height: 1.45;
	      overflow-wrap: anywhere;
	    }
	    .screen1-operator-workflow {
	      display: grid;
	      grid-template-columns: minmax(280px, 1.05fr) minmax(260px, 0.95fr);
      gap: 12px;
      margin-top: 16px;
    }
    .screen1-review-item,
    .screen1-selected-review-item,
    .screen1-decision-form,
    .screen1-request-result {
      display: grid;
      gap: 10px;
      min-width: 0;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      padding: 14px;
      background: rgba(11, 20, 34, 0.68);
      color: var(--text);
    }
    .screen1-review-item {
      cursor: pointer;
    }
    .screen1-review-item.is-selected,
    .screen1-review-item[data-selected="true"],
    .screen1-review-item:hover,
    .screen1-review-item:focus {
      border-color: rgba(90, 209, 255, 0.72);
      box-shadow: 0 0 0 2px rgba(90, 209, 255, 0.16);
      outline: none;
    }
    .screen1-review-item-header,
    .screen1-review-item-metrics {
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
    }
    .screen1-review-item-header strong,
    .screen1-selected-review-item h3,
    .screen1-decision-form h3,
    .screen1-request-result h3,
    .screen1-governance-boundary h3,
    .screen1-example-files strong {
      margin: 0;
      color: var(--accent);
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .screen1-review-item-header span,
    .screen1-review-item-metrics span {
      color: var(--text);
      font-size: 12px;
      font-weight: 800;
    }
    .screen1-review-item p,
    .screen1-selected-review-item p,
    .screen1-request-result dd,
    .screen1-governance-boundary p,
    .screen1-empty-state p {
      margin: 0;
      color: var(--text);
      font-size: 13px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }
    .screen1-example-files ul {
      margin: 6px 0 0;
      padding-left: 18px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen1-review-facts {
      display: grid;
      gap: 8px;
      margin: 0;
    }
    .screen1-review-facts div {
      display: grid;
      grid-template-columns: minmax(120px, 0.75fr) minmax(0, 1.25fr);
      gap: 10px;
      align-items: start;
      border-bottom: 1px solid rgba(159, 176, 199, 0.14);
      padding-bottom: 8px;
    }
    .screen1-review-facts div:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }
    .screen1-review-facts dt {
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
    }
    .screen1-review-facts dd {
      margin: 0;
      color: var(--text);
      font-size: 13px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .screen1-review-question {
      border-top: 1px solid rgba(159, 176, 199, 0.18);
      padding-top: 10px;
      font-weight: 800;
    }
    .screen1-decision-form label {
      display: grid;
      gap: 6px;
      margin: 0;
    }
    .screen1-decision-form label span {
      color: var(--accent);
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .screen1-decision-form select,
    .screen1-decision-form input,
    .screen1-decision-form textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      color: var(--text);
      background: rgba(7, 15, 26, 0.86);
      font: inherit;
      font-size: 13px;
      letter-spacing: 0;
    }
    .screen1-submit-requirements {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen1-governance-submit {
      justify-self: start;
      border: 1px solid rgba(102, 187, 106, 0.55);
      border-radius: 8px;
      padding: 10px 14px;
      color: var(--text);
      background: rgba(102, 187, 106, 0.18);
      font-weight: 900;
      cursor: pointer;
    }
    .screen1-governance-submit:disabled {
      cursor: not-allowed;
      opacity: 0.58;
      border-color: rgba(159, 176, 199, 0.24);
      background: rgba(159, 176, 199, 0.08);
    }
    .screen1-governance-boundary {
      margin-top: 12px;
      border: 1px solid rgba(255, 205, 86, 0.26);
      border-radius: 8px;
      padding: 12px;
      background: rgba(64, 51, 24, 0.14);
    }
    .screen1-field-mapping-empty-state {
      border-color: rgba(159, 176, 199, 0.24);
      background: rgba(16, 28, 45, 0.68);
    }
    .screen1-empty-state {
      display: grid;
      gap: 8px;
      border: 1px solid rgba(159, 176, 199, 0.2);
      border-radius: 8px;
      padding: 14px;
      background: rgba(11, 20, 34, 0.62);
    }
    .screen1-empty-state strong {
      color: var(--text);
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    .screen1-workflow-grid,
    .screen1-review-queue-grid,
    .screen1-action-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      margin: 14px 0;
    }
    .screen1-workflow-step,
    .screen1-review-target-card,
    .screen1-governance-action-card {
      display: grid;
      gap: 8px;
      min-height: 96px;
      padding: 14px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      background: rgba(11, 20, 34, 0.68);
      color: inherit;
      min-width: 0;
    }
    .screen1-review-target-card {
      cursor: pointer;
    }
    .screen1-review-target-card.is-selected,
    .screen1-review-target-card[data-selected="true"],
    .screen1-review-target-card:hover,
    .screen1-review-target-card:focus {
      border-color: rgba(90, 209, 255, 0.62);
      background: rgba(90, 209, 255, 0.12);
      outline: none;
    }
    .screen1-workflow-step strong,
    .screen1-review-target-card strong,
    .screen1-governance-action-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen1-workflow-step p,
    .screen1-review-target-card p,
    .screen1-governance-action-card p {
      margin: 0;
      color: var(--text);
      font-size: 13px;
      line-height: 1.4;
      overflow-wrap: anywhere;
    }
    .screen1-review-target-card p span {
      color: var(--muted);
      font-weight: 800;
    }
    .screen1-drilldown-details,
    .screen1-historical-evidence {
      margin-top: 12px;
      border: 1px dashed rgba(159, 176, 199, 0.26);
      border-radius: 8px;
      padding: 12px;
      background: rgba(11, 20, 34, 0.38);
    }
    .screen1-drilldown-details summary,
    .screen1-historical-evidence summary {
      cursor: pointer;
      color: var(--accent);
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .screen1-drilldown-group h4 {
      margin: 12px 0 8px;
      color: var(--text);
      font-size: 14px;
    }
    .screen1-governance-boundary {
      border-color: rgba(255, 205, 86, 0.36);
      background: rgba(64, 51, 24, 0.18);
    }
    .screen1-governance-boundary p,
    .empty-state-note {
      color: var(--text);
      font-size: 13px;
      line-height: 1.45;
    }
    .screen2-diagnostic-exploration {
      border-color: rgba(90, 209, 255, 0.32);
    }
    .screen2-selected-diagnostic-panel {
      border-color: rgba(90, 209, 255, 0.34);
      background: rgba(90, 209, 255, 0.08);
      border-radius: 14px;
      padding: 14px;
      box-shadow: inset 0 0 0 1px rgba(90, 209, 255, 0.08);
    }
    .screen2-selected-diagnostic-summary {
      margin: 0 0 12px;
      color: var(--text);
      font-size: 14px;
      font-weight: 700;
    }
    .screen2-selector-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .screen2-selector-card {
      display: grid;
      gap: 7px;
      min-height: 104px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 10px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }
    .screen2-selector-card[hidden],
    .screen2-selector-grid[data-screen2-domain-scoped="true"] .screen2-selector-card:not([data-screen2-domain-scope-active="true"]),
    .screen2-selector-scope-empty[hidden] {
      display: none !important;
    }
    .screen2-selector-card .screen2-selector-kicker {
      color: var(--accent);
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen2-selector-card strong {
      color: var(--text);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .screen2-selector-card .screen2-selector-detail {
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .screen2-selector-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen2-report-section-focus {
      border-color: rgba(159, 176, 199, 0.22);
      background: rgba(8, 16, 28, 0.34);
    }
    .screen2-selector-card.active {
      border-color: rgba(90, 209, 255, 0.62);
      background: rgba(90, 209, 255, 0.12);
    }
    .screen2-review-panel {
      border-color: rgba(102, 187, 106, 0.28);
    }
    .screen2-review-safety-labels {
      margin: 12px 0 0;
    }
    .screen2-review-subgrid {
      margin-top: 14px;
    }
    .screen2-review-copy-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0 0;
    }
    .screen2-review-copy-grid article {
      border: 1px solid rgba(159, 176, 199, 0.18);
      border-radius: 10px;
      padding: 10px 12px;
      background: rgba(8, 16, 28, 0.48);
    }
    .screen2-review-copy-grid strong {
      display: block;
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 5px;
    }
    .screen2-review-copy-grid p {
      margin: 0;
      color: var(--text);
      font-size: 12px;
      line-height: 1.4;
    }
    .screen2-review-target-summary {
      border-color: rgba(102, 187, 106, 0.30);
      background: rgba(102, 187, 106, 0.08);
      border-radius: 14px;
      padding: 14px;
      box-shadow: inset 0 0 0 1px rgba(102, 187, 106, 0.08);
    }
    .screen2-review-selected-summary {
      margin: 0 0 12px;
      color: var(--text);
      font-size: 14px;
      font-weight: 700;
    }
    .screen2-focus-summary-compact {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin: 0 0 12px;
    }
    .screen2-focus-summary-group,
    .screen2-focus-summary-facts {
      border: 1px solid rgba(90, 209, 255, 0.20);
      border-radius: 10px;
      padding: 10px 12px;
      background: rgba(8, 16, 28, 0.42);
    }
    .screen2-focus-summary-group > strong,
    .screen2-focus-summary-facts > strong {
      display: block;
      margin-bottom: 7px;
      color: var(--accent);
      font-size: 11px;
      font-weight: 850;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .screen2-focus-summary-facts {
      grid-column: 1 / -1;
    }
    .screen2-focus-summary-facts p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .screen2-selected-evidence-card {
      display: grid;
      gap: 6px;
      margin: 0;
    }
    .screen2-selected-evidence-card div {
      display: grid;
      grid-template-columns: minmax(120px, 0.55fr) minmax(0, 1.45fr);
      gap: 8px;
      align-items: start;
    }
    .screen2-selected-evidence-card .screen2-outcome-row {
      align-items: center;
    }
    .screen2-selected-evidence-card dt {
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .screen2-selected-evidence-card .screen2-outcome-row dt {
      align-self: center;
    }
	    .screen2-selected-evidence-card dd {
	      margin: 0;
	      color: var(--text);
	      font-size: 12px;
	      line-height: 1.4;
	    }
    .screen2-selected-evidence-card .screen2-outcome-row dd {
      display: flex;
      align-items: center;
    }
    .screen2-selected-evidence-card .screen2-outcome-row .status-pill,
    .screen2-selected-evidence-card .screen2-outcome-row .confidence-pill {
      justify-content: center;
      min-width: 72px;
      text-align: center;
    }
    @media (max-width: 760px) {
      .screen2-focus-summary-compact {
        grid-template-columns: 1fr;
      }
    }
	    .screen2-focused-explanation-panel {
	      display: grid;
	      gap: 10px;
	      margin: 12px 0;
	      border: 1px solid rgba(159, 176, 199, 0.18);
	      border-radius: 12px;
	      padding: 12px;
	      background: rgba(8, 16, 28, 0.38);
	    }
	    .screen2-focused-explanation-panel h3 {
	      margin: 0;
	      color: var(--accent);
	      font-size: 14px;
	      font-weight: 900;
	      letter-spacing: 0.04em;
	      text-transform: uppercase;
	    }
	    .screen2-focused-explanation-list {
	      display: grid;
	      grid-template-columns: 1fr;
	      gap: 9px;
	    }
	    .screen2-focused-explanation-item {
	      border: 1px solid rgba(159, 176, 199, 0.18);
	      border-radius: 10px;
	      padding: 10px 12px;
	      background: rgba(11, 20, 34, 0.58);
	    }
	    .screen2-focused-explanation-item strong {
	      display: block;
	      margin-bottom: 5px;
	      color: var(--accent);
	      font-size: 11px;
	      font-weight: 800;
	      letter-spacing: 0.05em;
	      text-transform: uppercase;
	    }
	    .screen2-focused-explanation-item p {
	      margin: 0;
	      color: var(--muted);
	      font-size: 12px;
	      line-height: 1.45;
	    }
	    .screen2-explanation-control {
	      display: grid;
	      grid-template-columns: 1fr;
	      gap: 9px;
	      align-items: center;
	      justify-items: center;
	      text-align: center;
	      margin: 12px 0;
	      border: 1px solid rgba(90, 209, 255, 0.20);
	      border-radius: 12px;
	      padding: 12px;
	      background: rgba(8, 16, 28, 0.50);
	    }
	    .screen2-explanation-button {
	      border: 1px solid rgba(90, 209, 255, 0.50);
	      border-radius: 8px;
	      padding: 9px 12px;
	      background: rgba(90, 209, 255, 0.14);
	      color: var(--text);
	      font-weight: 800;
	      font-size: 12px;
	      cursor: pointer;
	    }
	    .screen2-explanation-button:hover,
	    .screen2-explanation-button:focus-visible {
	      background: rgba(90, 209, 255, 0.22);
	      outline: none;
	    }
	    .screen2-explanation-control-copy {
	      display: grid;
	      gap: 5px;
	      max-width: 760px;
	    }
	    .screen2-explanation-control-copy strong {
	      color: var(--accent);
	      font-size: 11px;
	      font-weight: 800;
	      letter-spacing: 0.05em;
	      text-transform: uppercase;
	    }
	    .screen2-explanation-control-copy p {
	      margin: 0;
	      color: var(--muted);
	      font-size: 12px;
	      line-height: 1.4;
	    }
	    .screen2-focus-boundary-note {
	      margin: 0 0 10px;
	      color: var(--muted);
	      font-size: 12px;
	      line-height: 1.45;
	      text-align: left;
	    }
	    .screen2-focus-helper {
	      margin-top: 12px;
	      border: 1px solid rgba(159, 176, 199, 0.18);
	      border-radius: 12px;
	      padding: 10px 12px;
	      background: rgba(8, 16, 28, 0.42);
	    }
	    .screen2-focus-helper summary {
	      color: var(--accent);
	      cursor: pointer;
	      font-size: 12px;
	      font-weight: 800;
	      letter-spacing: 0.04em;
	      text-transform: uppercase;
	    }
	    .screen2-review-action-grid {
	      display: grid;
	      grid-template-columns: repeat(2, minmax(0, 1fr));
	      gap: 10px;
    }
    .screen2-review-form-field {
      display: grid;
      gap: 6px;
      margin-bottom: 12px;
      color: var(--text);
      font-size: 13px;
      font-weight: 700;
    }
    .screen2-review-form-field span {
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .screen2-review-form-field input,
    .screen2-review-form-field select,
    .screen2-review-form-field textarea {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid rgba(159, 176, 199, 0.32);
      border-radius: 8px;
      padding: 9px 10px;
      background: rgba(8, 16, 28, 0.82);
      color: var(--text);
      font: inherit;
    }
    .screen2-review-form-field textarea {
      resize: vertical;
      min-height: 92px;
    }
    .screen2-review-submit-control {
      display: grid;
      gap: 6px;
      border: 1px solid rgba(102, 187, 106, 0.42);
      border-radius: 8px;
      padding: 12px;
      background: rgba(102, 187, 106, 0.12);
      color: inherit;
      text-decoration: none;
    }
    .screen2-review-submit-control strong {
      color: var(--text);
      font-size: 13px;
    }
    .screen2-review-submit-control span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen2-review-submit-control.is-disabled {
      border-color: rgba(159, 176, 199, 0.24);
      background: rgba(16, 28, 45, 0.52);
      opacity: 0.72;
      cursor: not-allowed;
    }
    .screen2-action-status {
      border: 1px solid rgba(159, 176, 199, 0.26);
      border-radius: 8px;
      padding: 12px;
      background: rgba(8, 16, 28, 0.58);
      color: var(--text);
      font-size: 13px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }
    .screen2-action-status strong {
      display: block;
      color: var(--text);
      font-size: 13px;
      margin-bottom: 8px;
    }
    .screen2-action-result-list {
      display: grid;
      gap: 8px;
      margin: 0;
    }
    .screen2-action-result-list div {
      display: grid;
      grid-template-columns: minmax(140px, 0.55fr) minmax(0, 1.45fr);
      gap: 10px;
      border-top: 1px solid rgba(159, 176, 199, 0.12);
      padding-top: 8px;
    }
    .screen2-action-result-list dt {
      color: var(--accent);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .screen2-action-result-list dd {
      margin: 0;
      color: var(--text);
    }
    .screen2-technical-audit-details {
      margin-top: 10px;
      border-top: 1px solid rgba(159, 176, 199, 0.12);
      padding-top: 8px;
    }
    .screen2-technical-audit-details summary {
      cursor: pointer;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }
    .screen2-technical-audit-details code {
      display: block;
      margin-top: 8px;
      color: var(--muted);
      font-size: 11px;
      white-space: normal;
      overflow-wrap: anywhere;
    }
    .screen2-review-action-card {
      display: grid;
      gap: 6px;
      min-height: 72px;
      border: 1px dashed rgba(159, 176, 199, 0.32);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.58);
      color: inherit;
      opacity: 0.78;
    }
    .screen2-review-action-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen2-review-action-card span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen2-review-summary-list {
      display: grid;
      gap: 8px;
      margin: 0;
    }
    .screen2-review-summary-list div {
      display: grid;
      grid-template-columns: minmax(140px, 0.7fr) minmax(0, 1.3fr);
      gap: 10px;
      align-items: start;
      border-bottom: 1px solid rgba(159, 176, 199, 0.14);
      padding-bottom: 8px;
    }
    .screen2-review-summary-list div:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }
    .screen2-review-summary-list dt {
      color: var(--accent);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen2-review-summary-list dd {
      margin: 0;
      color: var(--text);
      font-size: 12px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .decision-box, .info-box, .provider-box, .scalar-box {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: rgba(16, 28, 45, 0.72);
    }
    .screen4-summary-card {
      padding: 16px;
    }
    .screen4-historical-exploration {
      border-color: rgba(90, 209, 255, 0.32);
    }
    .screen4-selected-historical-panel {
      border-color: rgba(90, 209, 255, 0.34);
      background: rgba(90, 209, 255, 0.08);
    }
    .screen4-selected-historical-summary {
      margin: 0 0 12px;
      color: var(--text);
      font-size: 14px;
      font-weight: 700;
    }
    .screen4-selector-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .screen4-selector-card {
      display: grid;
      gap: 6px;
      min-height: 104px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 10px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }
    .screen4-selector-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen4-selector-card span {
      color: var(--text);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .screen4-selector-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen4-selector-card.active {
      border-color: rgba(90, 209, 255, 0.62);
      background: rgba(90, 209, 255, 0.12);
    }
    .screen4-historical-review-preview-panel {
      border-color: rgba(102, 187, 106, 0.30);
    }
    .screen4-historical-review-preview-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0;
    }
    .screen4-historical-review-preview-card {
      display: grid;
      gap: 6px;
      min-height: 86px;
      border: 1px dashed rgba(159, 176, 199, 0.32);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.58);
      color: inherit;
      opacity: 0.78;
    }
    .screen4-historical-review-preview-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      overflow-wrap: anywhere;
    }
    .screen4-historical-review-preview-card span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen4-historical-review-preview-summary {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
    }
    .screen5-recommendation-action-exploration {
      border-color: rgba(90, 209, 255, 0.32);
    }
    .screen5-action-tracking-preview-panel {
      border-color: rgba(102, 187, 106, 0.30);
    }
    .screen5-action-preview-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0;
    }
    .screen5-action-preview-card {
      display: grid;
      gap: 6px;
      min-height: 92px;
      border: 1px dashed rgba(159, 176, 199, 0.32);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.58);
      color: inherit;
      opacity: 0.80;
    }
    .screen5-action-preview-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen5-action-preview-card span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen5-action-preview-card p {
      margin: 0;
      color: var(--text);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen5-action-preview-summary {
      border-color: rgba(102, 187, 106, 0.30);
      background: rgba(102, 187, 106, 0.08);
    }
    .screen5-action-preview-list {
      display: grid;
      gap: 8px;
      margin: 0;
    }
    .screen5-action-preview-list div {
      display: grid;
      grid-template-columns: minmax(170px, 0.72fr) minmax(0, 1.28fr);
      gap: 10px;
      align-items: start;
      border-bottom: 1px solid rgba(159, 176, 199, 0.14);
      padding-bottom: 8px;
    }
    .screen5-action-preview-list div:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }
    .screen5-action-preview-list dt {
      color: var(--accent);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen5-action-preview-list dd {
      margin: 0;
      color: var(--text);
      font-size: 12px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .screen5-outcome-capture-preview-panel {
      border-color: rgba(255, 205, 86, 0.32);
    }
    .screen5-outcome-preview-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0;
    }
    .screen5-outcome-preview-card {
      display: grid;
      gap: 6px;
      min-height: 92px;
      border: 1px dashed rgba(159, 176, 199, 0.32);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.58);
      color: inherit;
      opacity: 0.80;
    }
    .screen5-outcome-preview-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen5-outcome-preview-card span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen5-outcome-preview-card p {
      margin: 0;
      color: var(--text);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen5-outcome-preview-summary {
      border-color: rgba(255, 205, 86, 0.32);
      background: rgba(255, 205, 86, 0.08);
    }
    .screen5-outcome-preview-list {
      display: grid;
      gap: 8px;
      margin: 0;
    }
    .screen5-outcome-preview-list div {
      display: grid;
      grid-template-columns: minmax(190px, 0.74fr) minmax(0, 1.26fr);
      gap: 10px;
      align-items: start;
      border-bottom: 1px solid rgba(159, 176, 199, 0.14);
      padding-bottom: 8px;
    }
    .screen5-outcome-preview-list div:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }
    .screen5-outcome-preview-list dt {
      color: var(--accent);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen5-outcome-preview-list dd {
      margin: 0;
      color: var(--text);
      font-size: 12px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .screen5-selected-recommendation-panel {
      border-color: rgba(90, 209, 255, 0.34);
      background: rgba(90, 209, 255, 0.08);
    }
    .screen5-selected-recommendation-summary {
      margin: 0 0 12px;
      color: var(--text);
      font-size: 14px;
      font-weight: 700;
    }
    .screen5-selector-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .screen5-selector-card {
      display: grid;
      gap: 6px;
      min-height: 104px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 10px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }
    .screen5-selector-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen5-selector-card span {
      color: var(--text);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .screen5-selector-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen5-selector-card.active {
      border-color: rgba(90, 209, 255, 0.62);
      background: rgba(90, 209, 255, 0.12);
    }
    .screen6-fleet-governance-learning-exploration {
      border-color: rgba(90, 209, 255, 0.32);
    }
    .screen6-selected-panel {
      border-color: rgba(90, 209, 255, 0.34);
      background: rgba(90, 209, 255, 0.08);
    }
    .screen6-selected-summary {
      margin: 0 0 12px;
      color: var(--text);
      font-size: 14px;
      font-weight: 700;
    }
    .screen6-selector-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .screen6-selector-card {
      display: grid;
      gap: 6px;
      min-height: 104px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 10px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }
    .screen6-selector-card strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen6-selector-card span {
      color: var(--text);
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .screen6-selector-card p {
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen6-selector-card.active {
      border-color: rgba(90, 209, 255, 0.62);
      background: rgba(90, 209, 255, 0.12);
    }
    .screen6-candidate-review-preview-panel {
      border-color: rgba(246, 184, 76, 0.36);
      background: rgba(246, 184, 76, 0.06);
    }
    .screen6-candidate-review-safety-labels {
      margin: 10px 0 14px;
    }
    .screen6-candidate-review-control-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0;
    }
    .screen6-candidate-review-control {
      display: grid;
      gap: 6px;
      min-height: 112px;
      border: 1px solid rgba(246, 184, 76, 0.42);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
      text-align: left;
      cursor: not-allowed;
      opacity: 0.82;
    }
    .screen6-candidate-review-control strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen6-candidate-review-control span,
    .screen6-candidate-review-control small {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen6-candidate-review-control small {
      display: block;
    }
    .screen6-candidate-review-summary {
      margin-top: 14px;
    }
    .screen6-materialization-review-preview-panel {
      border-color: rgba(102, 187, 106, 0.34);
      background: rgba(102, 187, 106, 0.06);
    }
    .screen6-materialization-review-safety-labels {
      margin: 10px 0 14px;
    }
    .screen6-materialization-review-control-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0;
    }
    .screen6-materialization-review-control {
      display: grid;
      gap: 6px;
      min-height: 112px;
      border: 1px solid rgba(102, 187, 106, 0.42);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
      text-align: left;
      cursor: not-allowed;
      opacity: 0.82;
    }
    .screen6-materialization-review-control strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen6-materialization-review-control span,
    .screen6-materialization-review-control small {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen6-materialization-review-control small {
      display: block;
    }
    .screen6-materialization-review-summary {
      margin-top: 14px;
    }
    .screen6-model-registry-review-preview-panel {
      border-color: rgba(126, 178, 255, 0.34);
      background: rgba(126, 178, 255, 0.06);
    }
    .screen6-model-registry-review-safety-labels {
      margin: 10px 0 14px;
    }
    .screen6-model-registry-review-control-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0;
    }
    .screen6-model-registry-review-control {
      display: grid;
      gap: 6px;
      min-height: 112px;
      border: 1px solid rgba(126, 178, 255, 0.42);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
      text-align: left;
      cursor: not-allowed;
      opacity: 0.82;
    }
    .screen6-model-registry-review-control strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen6-model-registry-review-control span,
    .screen6-model-registry-review-control small {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen6-model-registry-review-control small {
      display: block;
    }
    .screen6-model-registry-review-summary {
      margin-top: 14px;
    }
    .screen6-runtime-gate-review-preview-panel {
      border-color: rgba(233, 139, 255, 0.34);
      background: rgba(233, 139, 255, 0.06);
    }
    .screen6-runtime-gate-review-safety-labels {
      margin: 10px 0 14px;
    }
    .screen6-runtime-gate-review-control-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 14px 0;
    }
    .screen6-runtime-gate-review-control {
      display: grid;
      gap: 6px;
      min-height: 112px;
      border: 1px solid rgba(233, 139, 255, 0.42);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
      text-align: left;
      cursor: not-allowed;
      opacity: 0.82;
    }
    .screen6-runtime-gate-review-control strong {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .screen6-runtime-gate-review-control span,
    .screen6-runtime-gate-review-control small {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .screen6-runtime-gate-review-control small {
      display: block;
    }
    .screen6-runtime-gate-review-summary {
      margin-top: 14px;
    }
    .screen4-compact-pane {
      padding: 14px;
    }
    .screen4-compact-info-grid {
      gap: 10px;
    }
    .screen4-compact-info-grid .info-box,
    .screen4-verdict-grid .info-box,
    .screen4-topology-grid .info-box {
      padding: 11px 12px;
      border-radius: 12px;
    }
    .screen4-verdict-pane > .meta,
    .screen4-topology-pane > .meta {
      margin: -2px 0 12px;
    }
    .screen4-verdict-grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .screen4-memory-block {
      padding: 14px;
    }
    .screen4-memory-block p {
      margin: 8px 0 0;
    }
    .screen4-topology-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    .screen4-interpretation-block {
      padding: 14px;
    }
    .screen4-interpretation-block .narrative {
      margin-top: 8px;
    }
    .supportive-panel {
      border: 1px dashed rgba(159, 176, 199, 0.28);
      border-radius: 14px;
      padding: 18px;
      background: rgba(11, 21, 35, 0.45);
    }
    .supportive-panel h3 { font-size: 16px; }
    .supportive-block {
      padding-top: 14px;
      margin-top: 14px;
      border-top: 1px solid rgba(159, 176, 199, 0.16);
    }
    .supportive-block:first-of-type {
      padding-top: 0;
      margin-top: 12px;
      border-top: none;
    }
    .severity, .status-pill, .health-pill, .decision-banner {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .severity.critical, .severity.error, .decision-banner.scale-now, .health-pill.fail {
      color: #fff4f4;
      background: rgba(255, 107, 107, 0.24);
      border: 1px solid rgba(255, 107, 107, 0.36);
    }
    .severity.high {
      color: #fff4f4;
      background: rgba(255, 107, 107, 0.16);
      border: 1px solid rgba(255, 107, 107, 0.30);
    }
    .severity.medium, .severity.warning, .health-pill.marginal, .decision-banner.defer {
      color: #fff8ed;
      background: rgba(246, 184, 76, 0.24);
      border: 1px solid rgba(246, 184, 76, 0.36);
    }
    .severity.low, .health-pill.pass, .decision-banner.do-not-scale {
      color: #eff7ff;
      background: rgba(127, 179, 213, 0.16);
      border: 1px solid rgba(127, 179, 213, 0.36);
    }
    .severity.success {
      color: #effbef;
      background: rgba(102, 187, 106, 0.16);
      border: 1px solid rgba(102, 187, 106, 0.34);
    }
    .severity.accent {
      color: #eef9ff;
      background: rgba(90, 209, 255, 0.14);
      border: 1px solid rgba(90, 209, 255, 0.34);
    }
    .severity.neutral {
      color: #eef3f8;
      background: rgba(159, 176, 199, 0.14);
      border: 1px solid rgba(159, 176, 199, 0.34);
    }
    .health-pill.na {
      color: #eef3f8;
      background: rgba(159, 176, 199, 0.14);
      border: 1px solid rgba(159, 176, 199, 0.34);
    }
    .health-pill.pass {
      color: #effbef;
      background: rgba(102, 187, 106, 0.16);
      border: 1px solid rgba(102, 187, 106, 0.34);
    }
    .status-pill.success {
      background: rgba(102, 187, 106, 0.16);
      border: 1px solid rgba(102, 187, 106, 0.34);
      color: #effbef;
    }
    .status-pill.warning {
      background: rgba(246, 184, 76, 0.16);
      border: 1px solid rgba(246, 184, 76, 0.34);
      color: #fff8ed;
    }
    .status-pill.error {
      background: rgba(255, 107, 107, 0.16);
      border: 1px solid rgba(255, 107, 107, 0.34);
      color: #fff4f4;
    }
    .status-pill.accent {
      color: #eef9ff;
      background: rgba(90, 209, 255, 0.14);
      border: 1px solid rgba(90, 209, 255, 0.34);
    }
    .status-pill.low {
      color: #eef7ff;
      background: rgba(127, 179, 213, 0.18);
      border: 1px solid rgba(127, 179, 213, 0.34);
    }
    .status-pill.neutral,
    .status-pill.na {
      color: #eef3f8;
      background: rgba(159, 176, 199, 0.14);
      border: 1px solid rgba(159, 176, 199, 0.34);
    }
    .scope-chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    .scope-chip {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      background: rgba(90, 209, 255, 0.1);
      border: 1px solid rgba(90, 209, 255, 0.22);
      color: #eef9ff;
    }
    .confidence-pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 30px;
      border-radius: 999px;
      padding: 6px 14px;
      font-size: 12px;
      font-weight: 800;
      line-height: 1;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      white-space: nowrap;
      border: 1px solid rgba(255, 255, 255, 0.16);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
    }
    .confidence-pill.low,
    .status-pill.confidence-low,
    .mini-pill.confidence-low {
      background: rgba(127, 179, 213, 0.24);
      border: 1px solid rgba(127, 179, 213, 0.48);
      color: #eef7ff;
    }
    .confidence-pill.medium,
    .status-pill.confidence-medium,
    .mini-pill.confidence-medium {
      background: rgba(246, 184, 76, 0.22);
      border: 1px solid rgba(246, 184, 76, 0.42);
      color: #fff8ed;
    }
    .confidence-pill.high,
    .status-pill.confidence-high,
    .mini-pill.confidence-high {
      background: rgba(102, 187, 106, 0.20);
      border: 1px solid rgba(102, 187, 106, 0.42);
      color: #effbef;
    }
    .mini-pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 11px;
      font-weight: 800;
      line-height: 1.3;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .mini-pill.success {
      color: #effbef;
      background: rgba(102, 187, 106, 0.16);
      border: 1px solid rgba(102, 187, 106, 0.34);
    }
    .mini-pill.warning {
      color: #fff8ed;
      background: rgba(246, 184, 76, 0.16);
      border: 1px solid rgba(246, 184, 76, 0.34);
    }
    .mini-pill.error {
      color: #fff4f4;
      background: rgba(255, 107, 107, 0.16);
      border: 1px solid rgba(255, 107, 107, 0.34);
    }
    .mini-pill.low {
      color: #eef7ff;
      background: rgba(127, 179, 213, 0.18);
      border: 1px solid rgba(127, 179, 213, 0.34);
    }
    .mini-pill.neutral {
      color: #eef3f8;
      background: rgba(159, 176, 199, 0.14);
      border: 1px solid rgba(159, 176, 199, 0.34);
    }
    .parser-review-grid,
    .governance-summary-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin: 12px 0 14px;
    }
    .governance-summary-grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    .governance-artifact-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .workflow-summary-grid {
      grid-template-columns: repeat(5, minmax(0, 1fr));
    }
    .memory-count-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 12px;
      padding: 10px 12px;
      background: rgba(16, 28, 45, 0.56);
    }
    .memory-count-card span {
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.05em;
      line-height: 1.25;
      text-transform: uppercase;
    }
    .parser-review-list,
    .parser-governance-list,
    .unknown-pattern-list,
    .governance-linkage-list,
    .semantic-context-list,
    .learning-candidate-list,
    .learning-governance-list {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }
    .validation-note-list {
      display: grid;
      gap: 8px;
      margin-top: 8px;
    }
    .validation-note-row {
      display: grid;
      gap: 4px;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 10px;
      padding: 10px;
      background: rgba(16, 28, 45, 0.48);
    }
    .validation-note-row strong {
      color: var(--text);
      font-size: 13px;
      line-height: 1.3;
    }
    .validation-note-row span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .parser-review-row,
    .parser-governance-row,
    .unknown-pattern-row,
    .governance-linkage-row,
    .semantic-context-row,
    .learning-candidate-row,
    .learning-governance-row {
      display: grid;
      align-items: center;
      gap: 10px;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 12px;
      padding: 10px 12px;
      background: rgba(16, 28, 45, 0.56);
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .parser-review-row {
      grid-template-columns: 0.95fr 0.65fr 1.7fr 0.75fr 0.65fr 0.8fr 0.9fr 1.35fr;
    }
    .parser-governance-row {
      grid-template-columns: 0.9fr 1fr 0.8fr 0.9fr 1.2fr 1fr 1fr;
    }
    .unknown-pattern-row {
      grid-template-columns: 1fr 1.7fr 0.65fr 1.25fr 1fr 0.8fr;
    }
    .governance-linkage-row {
      grid-template-columns: 0.65fr 1fr 0.75fr 0.75fr 1fr 0.75fr 1.1fr 1fr;
    }
    .semantic-context-row {
      grid-template-columns: 0.85fr 0.35fr 2fr;
    }
    .learning-candidate-row {
      grid-template-columns: 1.2fr 1fr 0.9fr 0.9fr 0.9fr 0.55fr 1.05fr 1.4fr 1fr;
    }
    .learning-governance-row {
      grid-template-columns: 1.35fr 0.9fr 1.4fr 1.1fr 1.25fr 0.9fr;
    }
    .parser-review-row strong,
    .parser-governance-row strong,
    .unknown-pattern-row strong,
    .governance-linkage-row strong,
    .semantic-context-row strong,
    .learning-candidate-row strong,
    .learning-governance-row strong {
      color: var(--text);
    }
    .parser-review-row span:not(.mini-pill),
    .parser-governance-row span:not(.mini-pill),
    .unknown-pattern-row span:not(.mini-pill),
    .learning-candidate-row span:not(.mini-pill) {
      display: block;
      margin-top: 2px;
      color: var(--muted);
    }
    .parser-pattern-summary {
      margin-top: 14px;
    }
    .parser-pattern-summary h3,
    .parser-review-list h3 {
      margin-bottom: 6px;
      font-size: 14px;
    }
    .mini-pill-group {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    .parser-review-header,
    .parser-governance-header,
    .unknown-pattern-header,
    .governance-linkage-header,
    .semantic-context-header,
    .learning-candidate-header,
    .learning-governance-header {
      background: transparent;
      border-color: transparent;
      padding-top: 0;
      padding-bottom: 0;
      color: var(--muted);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .governance-section-block {
      margin-top: 14px;
    }
    .governance-section-block h3 {
      margin-bottom: 8px;
      font-size: 14px;
    }
    .semantic-assist-scope-list {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
      margin: 10px 0 0;
      padding: 0;
      list-style: none;
    }
    .semantic-assist-scope-list li {
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 10px;
      padding: 9px 10px;
      background: rgba(16, 28, 45, 0.48);
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .semantic-boundary-notice,
    .semantic-status-message,
    .learning-boundary-notice {
      margin-top: 10px;
    }
    .learning-empty-state {
      display: grid;
      gap: 8px;
      margin-top: 12px;
    }
    .learning-summary-grid {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    .nav-card-note {
      margin-top: 8px;
      font-size: 12px;
      line-height: 1.35;
    }
    .pill-stack {
      display: grid;
      grid-template-columns: repeat(3, max-content);
      justify-content: start;
      gap: 10px;
    }
    .pill-cell {
      display: grid;
      justify-items: center;
      align-content: start;
      gap: 8px;
    }
    .banner-meta-strip {
      margin-top: 18px;
      margin-bottom: 6px;
      padding-top: 2px;
    }
    .visual-summary-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .mini-trend-card {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      background: rgba(16, 28, 45, 0.72);
    }
    .mini-trend-svg {
      width: 100%;
      height: 110px;
      display: block;
      margin-top: 10px;
    }
    .mini-trend-fallback {
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
    }
    .inline-nav-hint {
      display: inline-flex;
      align-items: center;
      margin-top: 14px;
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
      font-size: 13px;
    }
    .pill-label-row {
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .pill-caption {
      text-align: center;
      white-space: nowrap;
    }
    .engineering-detail {
      margin-top: 12px;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(16, 28, 45, 0.48);
      overflow: hidden;
    }
    .engineering-detail summary {
      cursor: pointer;
      list-style: none;
      padding: 14px 16px;
      color: var(--text);
      font-weight: 700;
    }
    .engineering-detail summary::-webkit-details-marker {
      display: none;
    }
    .engineering-detail-body {
      padding: 0 16px 16px;
      display: grid;
      gap: 14px;
    }
    .guidance-panel {
      display: grid;
      gap: 12px;
    }
    .action-page-card {
      padding: 18px;
    }
    .action-page-layout {
      display: grid;
      gap: 14px;
    }
    .action-conclusion-card {
      grid-column: auto;
      padding: 0;
      border: none;
      background: transparent;
    }
    .action-summary-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .action-summary-pane {
      grid-column: auto;
      padding: 14px;
    }
    .action-conclusion-block {
      border: 1px solid rgba(90, 209, 255, 0.28);
      border-radius: 14px;
      padding: 16px;
      background: rgba(16, 28, 45, 0.72);
    }
    .action-conclusion-block h4 {
      margin: 12px 0 6px;
      font-size: 18px;
    }
    .action-conclusion-block p {
      margin: 0;
      color: var(--text);
    }
    .action-conclusion-block ul {
      margin-top: 10px;
    }
    .status-insight-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-top: 12px;
    }
    .status-insight {
      display: grid;
      grid-template-columns: max-content 1fr;
      grid-template-areas:
        "pill note"
        "label note";
      column-gap: 12px;
      row-gap: 6px;
      align-items: center;
      padding: 12px;
      border: 1px solid rgba(159, 176, 199, 0.18);
      border-radius: 12px;
      background: rgba(16, 28, 45, 0.56);
    }
    .status-insight-pill {
      grid-area: pill;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 30px;
      border-radius: 999px;
      padding: 6px 14px;
      font-size: 12px;
      font-weight: 800;
      line-height: 1;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      white-space: nowrap;
      border: 1px solid rgba(255, 255, 255, 0.16);
    }
    .status-insight-label {
      grid-area: label;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      text-align: center;
    }
    .status-insight-note {
      grid-area: note;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
      align-self: center;
    }
    .status-insight-pill--success {
      background: rgba(102, 187, 106, 0.20);
      border-color: rgba(102, 187, 106, 0.42);
      color: #effbef;
    }
    .status-insight-pill--warning {
      background: rgba(246, 184, 76, 0.22);
      border-color: rgba(246, 184, 76, 0.42);
      color: #fff8ed;
    }
    .status-insight-pill--error {
      background: rgba(255, 107, 107, 0.20);
      border-color: rgba(255, 107, 107, 0.42);
      color: #fff4f4;
    }
    .status-insight-pill--low,
    .status-insight-pill--confidence-low {
      background: rgba(127, 179, 213, 0.24);
      border-color: rgba(127, 179, 213, 0.48);
      color: #eef7ff;
    }
    .status-insight-pill--confidence-medium {
      background: rgba(246, 184, 76, 0.22);
      border-color: rgba(246, 184, 76, 0.42);
      color: #fff8ed;
    }
    .status-insight-pill--confidence-high {
      background: rgba(102, 187, 106, 0.20);
      border-color: rgba(102, 187, 106, 0.42);
      color: #effbef;
    }
    .status-insight-pill--accent {
      background: rgba(90, 209, 255, 0.16);
      border-color: rgba(90, 209, 255, 0.40);
      color: #eef9ff;
    }
    .status-insight-pill--neutral {
      background: rgba(159, 176, 199, 0.14);
      border-color: rgba(159, 176, 199, 0.34);
      color: #eef3f8;
    }
    .compact-supportive-panel {
      padding: 12px;
    }
    .compact-supportive-panel ul {
      margin-bottom: 0;
    }
    .compact-evidence-stack {
      gap: 8px;
    }
    .compact-evidence-stack .item {
      padding: 10px;
      border-radius: 12px;
    }
    .validation-plan-groups,
    .evidence-checklist {
      display: grid;
      gap: 10px;
    }
    .validation-plan-group {
      padding-top: 8px;
      border-top: 1px solid rgba(159, 176, 199, 0.16);
    }
    .validation-plan-group:first-child {
      padding-top: 0;
      border-top: none;
    }
    .validation-plan-group strong,
    .evidence-checklist-item h3 {
      display: block;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }
    .validation-plan-group ul,
    .compact-list {
      margin-top: 4px;
    }
    .compact-inline-list {
      color: var(--text);
      font-size: 13px;
      line-height: 1.35;
    }
    .evidence-checklist-item.warning-note {
      border-color: rgba(246, 184, 76, 0.32);
      background: rgba(66, 48, 24, 0.36);
    }
    .action-final-statement {
      border: 1px solid rgba(90, 209, 255, 0.26);
      border-radius: 12px;
      padding: 12px 14px;
      color: var(--text);
      background: rgba(90, 209, 255, 0.08);
      font-weight: 700;
    }
    .fleet-preview-note {
      max-width: 980px;
      margin-top: -4px;
    }
    .fleet-compact-card {
      padding: 16px;
    }
    .fleet-summary-strip {
      display: flex;
      align-items: stretch;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 10px;
    }
    .fleet-summary-fact {
      min-width: 150px;
      flex: 1 1 150px;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 10px;
      background: rgba(16, 28, 45, 0.72);
    }
    .fleet-summary-fact span {
      display: block;
      margin-bottom: 4px;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .fleet-summary-fact strong {
      color: var(--text);
      font-size: 13px;
      line-height: 1.25;
    }
    .fleet-detail-list {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 10px;
    }
    .fleet-detail-row {
      display: block;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 10px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.54);
    }
    .fleet-detail-row.reason-row {
      grid-column: 1 / -1;
    }
    .fleet-detail-row strong {
      display: block;
      margin-bottom: 6px;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .fleet-detail-row span {
      color: var(--text);
      font-size: 13px;
      line-height: 1.35;
    }
    .similarity-case-grid {
      gap: 8px;
    }
    .similarity-case-grid .info-box {
      padding: 9px 10px;
    }
    .scalar-context-note {
      margin-top: -2px;
      margin-bottom: 12px;
    }
    .narrative > p, .narrative > ol, .narrative > ul, .narrative > div { margin-top: 0; margin-bottom: 12px; }
    .data-table-wrap {
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(16, 28, 45, 0.72);
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 860px;
    }
    .data-table th, .data-table td {
      padding: 10px 12px;
      border-bottom: 1px solid rgba(35, 55, 84, 0.7);
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }
    .data-table th {
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      background: rgba(11, 21, 35, 0.7);
    }
    .screen1-run-intake-report {
      padding: 14px 16px;
    }
    .screen1-run-intake-report h2 {
      margin-bottom: 6px;
      font-size: 18px;
    }
    .screen1-generated-run-boundary-note {
      margin-bottom: 10px;
      font-size: 12px;
      line-height: 1.45;
    }
    .screen1-generated-evidence-group-stack {
      display: grid;
      gap: 14px;
      margin-top: 12px;
    }
    .screen1-generated-evidence-group {
      display: grid;
      gap: 8px;
    }
    .screen1-generated-evidence-group h3 {
      margin: 0;
      color: var(--text);
      font-size: 15px;
      line-height: 1.25;
    }
    .screen1-generated-evidence-info-grid {
      grid-template-columns: repeat(auto-fit, minmax(185px, 1fr));
      gap: 10px;
    }
    .screen1-generated-evidence-info-box {
      min-height: 0;
      padding: 10px 12px;
      border: 1px solid rgba(159, 176, 199, 0.22);
      border-radius: 12px;
      background: rgba(20, 36, 58, 0.70);
    }
    .screen1-generated-evidence-info-box strong {
      display: block;
      margin-bottom: 4px;
      color: var(--accent);
      font-size: 11px;
      font-weight: 850;
      letter-spacing: 0.05em;
      line-height: 1.25;
      text-transform: uppercase;
      overflow-wrap: anywhere;
    }
    .screen1-generated-evidence-info-box div {
      color: var(--text);
      font-size: 13px;
      line-height: 1.35;
      overflow-wrap: anywhere;
    }
    .screen1-unknown-signals-compact {
      display: grid;
      gap: 12px;
      margin-top: 10px;
    }
    .screen1-unknown-signals-overview {
      display: grid;
      gap: 8px;
    }
    .screen1-unknown-signals-overview h3 {
      margin: 0;
      font-size: 15px;
      line-height: 1.25;
    }
    .screen1-unknown-signals-summary-grid {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
    }
    .screen1-unknown-signals-summary-grid .info-box {
      min-height: 0;
      padding: 10px 12px;
    }
    .screen1-unknown-signals-handoff-note {
      margin: 0;
    }
    .screen1-generated-evidence-empty-state {
      padding: 10px 12px;
      border: 1px dashed rgba(159, 176, 199, 0.24);
      border-radius: 10px;
      color: var(--muted);
      background: rgba(11, 20, 34, 0.34);
      font-size: 13px;
    }
    .screen1-full-report-table-wrap {
      max-height: 520px;
      overflow: auto;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 10px;
    }
    .screen1-full-report-table-compact {
      min-width: 0;
      width: 100%;
      table-layout: fixed;
    }
    .screen1-full-report-table-compact th,
    .screen1-full-report-table-compact td {
      padding: 8px 9px;
      font-size: 12px;
      line-height: 1.35;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .screen1-full-report-table-compact th {
      position: sticky;
      top: 0;
      z-index: 3;
      background: rgba(15, 27, 45, 0.98);
      box-shadow: 0 1px 0 rgba(159, 176, 199, 0.18);
      font-size: 11px;
      letter-spacing: 0.04em;
    }
    .screen1-status-stack {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 7px;
    }
    .screen1-full-report-table-compact .status-pill {
      border-radius: 6px;
      padding: 3px 8px;
      font-size: 11px;
      font-weight: 700;
      line-height: 1.15;
      letter-spacing: 0.02em;
    }
    .screen1-report-file,
    .screen1-report-parser-notes {
      white-space: normal;
      overflow-wrap: anywhere;
      word-break: break-word;
    }
    .chart-panel, .violin-chart-card {
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      background: rgba(20, 36, 58, 0.62);
      min-height: 320px;
    }
    .chart-support-note, .chart-domain-heading {
      color: rgba(216, 228, 242, 0.82);
    }
    .chart-domain-group { margin-top: 20px; }
    .chart-domain-heading {
      margin: 0 0 12px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .violin-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 18px;
    }
    .violin-group { margin-top: 20px; }
    .violin-group-note { color: rgba(216, 228, 242, 0.82); font-size: 14px; }
    .violin-chart { height: 300px; }
    .chart-canvas { position: relative; height: 240px; }
    .chart-empty {
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 240px;
      color: var(--muted);
      font-size: 14px;
      text-align: center;
      border: 1px dashed rgba(159, 176, 199, 0.22);
      border-radius: 12px;
      background: rgba(11, 21, 35, 0.45);
    }
    .health-check-summary { margin-bottom: 12px; }
    .health-check-card p { margin: 0; }
    .pipeline-card {
      overflow: hidden;
    }

    .pipeline-intro {
      max-width: 980px;
      margin-bottom: 14px;
    }

    .pipeline-mode-badge {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: 10px;
      margin: 14px 0 18px;
      flex-wrap: wrap;
    }

    .pipeline-mode-badge .status-pill,
    .pipeline-mode-badge .meta {
      margin: 0;
      line-height: 1.2;
    }

    .pipeline-mode-badge .meta {
      display: inline-flex;
      align-items: center;
      opacity: 0.85;
      min-width: 0;
      overflow-wrap: anywhere;
      word-break: break-word;
    }

    .pipeline-flow {
      display: grid;
      grid-template-columns: repeat(7, minmax(0, 1fr));
      gap: 10px;
      margin-top: 18px;
    }

    .pipeline-lane {
      border: 1px solid rgba(159, 176, 199, 0.18);
      border-radius: 16px;
      padding: 12px;
      background: rgba(9, 18, 30, 0.42);
    }

    .pipeline-lane-header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .pipeline-lane-header strong {
      color: var(--text);
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .pipeline-lane-header span {
      color: var(--muted);
      font-size: 13px;
    }

    .pipeline-boundary-note {
      margin: 8px 0 0;
      font-size: 12px;
      line-height: 1.4;
    }

    .pipeline-node {
      position: relative;
      min-height: 104px;
      padding: 14px 12px;
      border-radius: 16px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      background:
        linear-gradient(180deg, rgba(20, 36, 58, 0.88), rgba(13, 24, 40, 0.9));
      box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.04),
        0 10px 22px rgba(0, 0, 0, 0.18);
      transition:
        transform 0.18s ease,
        border-color 0.18s ease,
        box-shadow 0.18s ease,
        background 0.18s ease;
    }

    .pipeline-node:hover {
      transform: translateY(-3px);
      border-color: rgba(90, 209, 255, 0.62);
      background:
        linear-gradient(180deg, rgba(24, 44, 70, 0.96), rgba(13, 24, 40, 0.96));
      box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.06),
        0 14px 28px rgba(0, 0, 0, 0.22),
        0 0 0 1px rgba(90, 209, 255, 0.08);
    }

    .pipeline-node span {
      display: block;
      color: var(--text);
      font-size: 14px;
      font-weight: 800;
      line-height: 1.2;
      margin-bottom: 6px;
    }

    .pipeline-node small {
      display: block;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      min-width: 0;
      overflow-wrap: anywhere;
      word-break: break-word;
    }

    .pipeline-node.source-node {
      border-color: rgba(102, 187, 106, 0.42);
      background:
        linear-gradient(180deg, rgba(27, 59, 44, 0.72), rgba(13, 24, 40, 0.92));
    }

    .pipeline-node.core-node {
      border-color: rgba(255, 107, 107, 0.55);
      background:
        linear-gradient(180deg, rgba(70, 34, 42, 0.56), rgba(13, 24, 40, 0.92));
      box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.04),
        0 10px 22px rgba(0, 0, 0, 0.18),
        0 0 0 1px rgba(255, 107, 107, 0.15);
    }

    .pipeline-node.memory-node {
      border-color: rgba(90, 209, 255, 0.52);
      background:
        linear-gradient(180deg, rgba(28, 67, 84, 0.62), rgba(13, 24, 40, 0.92));
    }

    .pipeline-support-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 14px;
    }

    .pipeline-side-panel {
      border: 1px solid rgba(159, 176, 199, 0.22);
      border-radius: 16px;
      padding: 14px 16px;
      background:
        linear-gradient(180deg, rgba(16, 28, 45, 0.78), rgba(10, 19, 32, 0.86));
    }

    .pipeline-side-panel strong {
      display: block;
      color: var(--text);
      font-size: 15px;
      margin-bottom: 6px;
    }

    .pipeline-side-panel p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }

    .governed-memory-panel {
      border-color: rgba(90, 209, 255, 0.45);
    }

    .semantic-recall-panel {
      border-color: rgba(255, 205, 86, 0.42);
      background:
        linear-gradient(180deg, rgba(64, 51, 24, 0.48), rgba(10, 19, 32, 0.88));
    }

    .phase7-boundary-note {
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid rgba(159, 176, 199, 0.16);
    }

    .phase7-governed-action-panel {
      border-color: rgba(90, 209, 255, 0.34);
      background: rgba(16, 28, 45, 0.74);
    }

    .phase7cm-source-card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 12px;
      margin: 14px 0;
    }

    .phase7cm-source-card {
      display: grid;
      gap: 8px;
      min-height: 124px;
      padding: 14px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 10px;
      background: rgba(11, 20, 34, 0.68);
    }

    .phase7cr-entry-card-link {
      color: inherit;
      text-decoration: none;
      cursor: pointer;
    }

    .phase7cr-entry-card-link .phase7cr-entry-card-cta {
      align-self: end;
      width: fit-content;
    }

    .phase7cm-source-card:hover,
    .phase7cm-source-card:focus,
    .phase7cm-source-card.is-selected,
    .phase7cm-source-card[data-selected="true"] {
      border-color: rgba(90, 209, 255, 0.72);
      outline: none;
    }

    .phase7cm-source-card strong {
      color: var(--accent);
      font-size: 14px;
    }

    .phase7cm-source-card p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }

    .phase7cm-source-config-panel {
      margin: 14px 0;
    }

    .phase7cm-source-config-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
      margin-top: 10px;
    }

    @media (min-width: 1180px) {
      .phase7cm-source-config-grid[data-active-source-mode="object_storage"] {
        grid-template-columns:
          minmax(160px, 1fr)
          minmax(180px, 1fr)
          minmax(260px, 1.4fr)
          minmax(150px, 0.8fr)
          minmax(190px, 0.9fr);
        align-items: start;
      }

      .phase7cm-object-storage-config-field {
        min-width: 0;
      }

      .phase7cm-object-storage-config-field .phase7cm-service-button {
        width: 100%;
      }
    }

    .phase7cm-source-config-field {
      display: grid;
      gap: 7px;
      padding: 12px;
      border: 1px solid rgba(159, 176, 199, 0.20);
      border-radius: 10px;
      background: rgba(11, 20, 34, 0.58);
    }

    .phase7cm-source-config-field[hidden] {
      display: none;
    }

    .phase7cm-source-config-field span {
      color: var(--accent);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .phase7cm-source-config-field input {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      padding: 9px 10px;
      color: var(--text);
      background: rgba(8, 16, 28, 0.78);
      font: inherit;
      font-size: 13px;
    }

    .phase7cm-picker-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: fit-content;
      min-height: 36px;
      padding: 8px 12px;
      border: 1px solid rgba(90, 209, 255, 0.38);
      border-radius: 8px;
      color: var(--text);
      background: rgba(90, 209, 255, 0.12);
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
    }

    .phase7cm-picker-button:hover,
    .phase7cm-picker-button:focus {
      border-color: rgba(90, 209, 255, 0.72);
    }

    .phase7cm-service-button {
      width: fit-content;
      min-height: 36px;
      border: 1px solid rgba(102, 187, 106, 0.38);
      border-radius: 8px;
      padding: 8px 12px;
      color: var(--text);
      background: rgba(102, 187, 106, 0.12);
      font: inherit;
      font-size: 13px;
      font-weight: 800;
      cursor: pointer;
    }

    .phase7cm-service-button:hover,
    .phase7cm-service-button:focus {
      border-color: rgba(102, 187, 106, 0.72);
      outline: none;
    }

    .phase7cm-source-config-field select {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      padding: 9px 10px;
      color: var(--text);
      background: rgba(8, 16, 28, 0.78);
      font: inherit;
      font-size: 13px;
    }

    .phase7cm-source-picker-input {
      position: absolute;
      inline-size: 1px;
      block-size: 1px;
      overflow: hidden;
      opacity: 0;
      pointer-events: none;
    }

    .phase7cm-source-config-field small {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .phase7cm-source-summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 10px;
      margin: 12px 0;
    }

    .phase7cm-source-summary-card {
      border: 1px solid rgba(90, 209, 255, 0.20);
      border-radius: 10px;
      padding: 10px 12px;
      background: rgba(11, 20, 34, 0.56);
    }

    .phase7cm-source-summary-card strong {
      display: block;
      color: var(--accent);
      font-size: 12px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 5px;
    }

    .phase7cm-source-summary-card p {
      margin: 0;
      color: var(--text);
      font-size: 12px;
      line-height: 1.35;
      min-width: 0;
      overflow-wrap: anywhere;
      word-break: break-word;
    }

    .phase7cm-source-metadata-summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 8px;
      margin: 12px 0 0;
    }

    .phase7cm-source-metadata-summary div {
      padding: 9px 10px;
      border: 1px solid rgba(159, 176, 199, 0.16);
      border-radius: 8px;
      background: rgba(11, 20, 34, 0.52);
    }

    .phase7cm-source-metadata-summary dt {
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .phase7cm-source-metadata-summary dd {
      margin: 4px 0 0;
      color: var(--text);
      font-size: 12px;
      overflow-wrap: anywhere;
    }

    .phase7-legacy-boundary-details summary {
      cursor: pointer;
      color: var(--text);
      font-weight: 800;
      list-style: none;
    }

    .phase7-legacy-boundary-details summary::-webkit-details-marker {
      display: none;
    }

    .phase7-governed-action-control,
    .screen1-governed-action-control {
      display: grid;
      gap: 8px;
      min-height: 104px;
      padding: 14px;
      border: 1px solid rgba(90, 209, 255, 0.30);
      border-radius: 12px;
      text-decoration: none;
      color: var(--text);
      background: rgba(11, 20, 34, 0.72);
    }

    .phase7-governed-action-control:hover,
    .phase7-governed-action-control:focus,
    .screen1-governed-action-control:hover,
    .screen1-governed-action-control:focus {
      border-color: rgba(90, 209, 255, 0.72);
      outline: none;
    }

    .phase7-governed-action-control strong,
    .screen1-governed-action-control strong {
      color: var(--accent);
      font-size: 14px;
    }

    .phase7-governed-action-control span,
    .screen1-governed-action-control span {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }

    .phase7-governed-action-status,
    .screen1-action-status {
      margin-top: 12px;
      padding: 10px 12px;
      border: 1px solid rgba(159, 176, 199, 0.18);
      border-radius: 10px;
      color: var(--muted);
      background: rgba(11, 20, 34, 0.52);
      font-size: 12px;
      line-height: 1.45;
      font-weight: 500;
      overflow-wrap: anywhere;
    }

	    .phase7-governed-action-status[data-phase7-action-status="accepted"],
	    .phase7-governed-action-status[data-phase7-action-status="running"],
	    .phase7-governed-action-status[data-phase7-action-status="pending"],
	    .phase7-governed-action-status[data-phase7-action-status="completed_artifact_ready"],
	    .screen1-action-status[data-phase7-action-status="accepted"],
	    .screen1-action-status[data-phase7-action-status="running"],
	    .screen1-action-status[data-phase7-action-status="pending"],
	    .screen1-action-status[data-phase7-action-status="completed_artifact_ready"],
	    .screen2-action-status[data-phase7-action-status="accepted"] {
	      color: #effbef;
	      border-color: rgba(102, 187, 106, 0.42);
	    }

	    .phase7-governed-action-status[data-phase7-action-status="failed"],
	    .phase7-governed-action-status[data-phase7-action-status="failed_safely"],
	    .phase7-governed-action-status[data-phase7-action-status="timed_out"],
	    .screen1-action-status[data-phase7-action-status="failed"],
	    .screen1-action-status[data-phase7-action-status="failed_safely"],
	    .screen1-action-status[data-phase7-action-status="timed_out"],
	    .screen2-action-status[data-phase7-action-status="failed"] {
	      color: #fff4f4;
	      border-color: rgba(255, 107, 107, 0.42);
	    }

	    .screen1-source-intake-result {
	      display: grid;
	      gap: 8px;
	    }

	    .screen1-source-intake-result > strong {
	      color: var(--text);
	      font-size: 13px;
	      text-transform: uppercase;
	      letter-spacing: 0.05em;
	    }

	    .screen1-source-intake-result dl {
	      display: grid;
	      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
	      gap: 8px;
	      margin: 0;
	    }

	    .screen1-source-intake-result div {
	      min-width: 0;
	      padding: 7px 9px;
	      border: 1px solid rgba(159, 176, 199, 0.18);
	      border-radius: 8px;
	      background: rgba(16, 28, 45, 0.64);
	    }

	    .screen1-source-intake-result dt {
	      color: var(--accent);
	      font-size: 10px;
	      font-weight: 850;
	      letter-spacing: 0.05em;
	      text-transform: uppercase;
	    }

	    .screen1-source-intake-result dd {
	      margin: 3px 0 0;
	      color: var(--text);
	      font-size: 12px;
	      line-height: 1.3;
	      overflow-wrap: anywhere;
	    }

    .phase7cm-next-step-note {
      margin-top: 10px;
      font-size: 12px;
      line-height: 1.4;
    }

    .future-input-layout {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 12px;
    }

    .future-input-card {
      padding: 14px 16px;
    }

    .index-source-mode-entry-panel {
      border-color: rgba(90, 209, 255, 0.26);
      background: rgba(90, 209, 255, 0.05);
    }

    .index-source-mode-entry-safety-labels {
      margin: 10px 0 14px;
    }

    .index-source-mode-entry-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .index-source-mode-entry-card {
      display: grid;
      gap: 10px;
      min-height: 260px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }

    .index-source-mode-entry-card.disabled-preview-only {
      border-color: rgba(90, 209, 255, 0.32);
    }

    .index-source-mode-entry-card strong {
      display: block;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .index-source-mode-entry-card span,
    .index-source-mode-entry-card p,
    .index-source-mode-entry-flags {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .index-source-mode-entry-card p {
      margin: 0;
    }

    .index-source-mode-entry-flags {
      display: grid;
      gap: 6px;
      margin: 0;
    }

    .index-source-mode-entry-flags div {
      display: grid;
      grid-template-columns: minmax(96px, 0.9fr) minmax(0, 1.1fr);
      gap: 8px;
    }

    .index-source-mode-entry-flags dt,
    .index-source-mode-entry-flags dd {
      margin: 0;
      overflow-wrap: anywhere;
    }

    .index-source-mode-entry-flags dt {
      color: var(--text);
      font-weight: 800;
    }

    .index-source-mode-entry-control.preview-only {
      min-height: 36px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      color: var(--muted);
      background: rgba(20, 36, 58, 0.84);
      font: inherit;
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
      cursor: not-allowed;
    }

    .index-source-mode-entry-boundary-note {
      margin-top: 12px;
      padding: 12px;
    }

    .index-source-status-panel {
      border-color: rgba(246, 184, 76, 0.28);
      background: rgba(246, 184, 76, 0.05);
    }

    .index-source-status-safety-labels {
      margin: 10px 0 14px;
    }

    .index-source-status-summary-grid {
      margin-bottom: 12px;
    }

    .index-source-status-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .index-source-status-card {
      display: grid;
      gap: 10px;
      min-height: 244px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }

    .index-source-status-card.disabled-preview-only {
      border-color: rgba(246, 184, 76, 0.36);
    }

    .index-source-status-card strong {
      display: block;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .index-source-status-card span,
    .index-source-status-flags {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .index-source-status-flags {
      display: grid;
      gap: 6px;
      margin: 0;
    }

    .index-source-status-flags div {
      display: grid;
      grid-template-columns: minmax(112px, 0.9fr) minmax(0, 1.1fr);
      gap: 8px;
    }

    .index-source-status-flags dt,
    .index-source-status-flags dd {
      margin: 0;
      overflow-wrap: anywhere;
    }

    .index-source-status-flags dt {
      color: var(--text);
      font-weight: 800;
    }

    .index-source-status-boundary-note {
      margin-top: 12px;
      padding: 12px;
    }

    .index-object-storage-config-panel {
      border-color: rgba(38, 166, 154, 0.28);
      background: rgba(38, 166, 154, 0.05);
    }

    .index-object-storage-config-safety-labels {
      margin: 10px 0 14px;
    }

    .index-object-storage-config-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .index-object-storage-config-card {
      display: grid;
      gap: 10px;
      min-height: 218px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }

    .index-object-storage-config-card.disabled-preview-only {
      border-color: rgba(38, 166, 154, 0.36);
    }

    .index-object-storage-config-card strong {
      display: block;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .index-object-storage-config-flags {
      display: grid;
      gap: 6px;
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .index-object-storage-config-flags div {
      display: grid;
      grid-template-columns: minmax(136px, 1fr) minmax(0, 1fr);
      gap: 8px;
    }

    .index-object-storage-config-flags dt,
    .index-object-storage-config-flags dd {
      margin: 0;
      overflow-wrap: anywhere;
    }

    .index-object-storage-config-flags dt {
      color: var(--text);
      font-weight: 800;
    }

    .index-object-storage-config-boundary-note {
      margin-top: 12px;
      padding: 12px;
    }

    .index-screen3-handoff-panel {
      border-color: rgba(171, 120, 255, 0.28);
      background: rgba(171, 120, 255, 0.05);
    }

    .index-screen3-handoff-safety-labels {
      margin: 10px 0 14px;
    }

    .index-screen3-handoff-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }

    .index-screen3-handoff-card {
      display: grid;
      gap: 10px;
      min-height: 222px;
      border: 1px solid rgba(159, 176, 199, 0.24);
      border-radius: 8px;
      padding: 12px;
      background: rgba(16, 28, 45, 0.72);
      color: inherit;
    }

    .index-screen3-handoff-card.disabled-preview-only {
      border-color: rgba(171, 120, 255, 0.36);
    }

    .index-screen3-handoff-card strong {
      display: block;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .index-screen3-handoff-flags {
      display: grid;
      gap: 6px;
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }

    .index-screen3-handoff-flags div {
      display: grid;
      grid-template-columns: minmax(136px, 1fr) minmax(0, 1fr);
      gap: 8px;
    }

    .index-screen3-handoff-flags dt,
    .index-screen3-handoff-flags dd {
      margin: 0;
      overflow-wrap: anywhere;
    }

    .index-screen3-handoff-flags dt {
      color: var(--text);
      font-weight: 800;
    }

    .index-screen3-handoff-boundary-note {
      margin-top: 12px;
      padding: 12px;
    }

    .future-input-panel {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 10px;
      background: rgba(16, 28, 45, 0.72);
    }

    .future-input-panel h3 {
      margin-bottom: 10px;
    }

    .phase7-dynamic-source-context-card h2 {
      font-size: 18px;
    }

    .phase7-dynamic-source-context-card > .meta {
      font-size: 12px;
      line-height: 1.45;
    }

    .phase7-dynamic-source-context-card .future-input-panel h3 {
      color: var(--accent);
      display: block;
      margin-bottom: 6px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      line-height: 1.35;
    }

    .phase7-dynamic-source-context-card .future-note strong {
      font-size: 13px;
      line-height: 1.35;
    }

    .phase7-dynamic-source-context-card .future-input-panel p,
    .phase7-dynamic-source-context-card .future-note p {
      font-size: 12px;
      line-height: 1.45;
    }

    .source-option-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .source-option {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 7px 11px;
      font-size: 12px;
      font-weight: 700;
      color: var(--text);
      background: rgba(20, 36, 58, 0.84);
      border: 1px solid rgba(159, 176, 199, 0.24);
    }

    .source-option.active {
      color: #08111d;
      background: var(--accent);
      border-color: rgba(90, 209, 255, 0.62);
    }

    .future-input-field {
      width: 100%;
      min-height: 42px;
      border: 1px solid rgba(90, 209, 255, 0.28);
      border-radius: 10px;
      padding: 9px 11px;
      color: var(--text);
      background: rgba(11, 21, 35, 0.74);
      font: inherit;
    }

    .input-note {
      margin-top: 8px;
    }

    .future-note {
      margin-top: 10px;
      padding: 12px;
    }

    .future-note strong {
      color: var(--accent);
    }

    .future-note p {
      margin: 6px 0 0;
      color: var(--muted);
    }

    .agent-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 16px;
    }

    .agent-card {
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 10px;
      background: rgba(16, 28, 45, 0.72);
    }

    .agent-card strong {
      display: block;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }

    .agent-card p {
      margin: 0;
      color: var(--text);
      font-size: 13px;
    }

    .truth-boundary-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-top: 16px;
    }

    .truth-boundary-pane {
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      background: rgba(16, 28, 45, 0.72);
    }

    .truth-boundary-pane h3 {
      margin-bottom: 10px;
    }

    .deterministic-pane {
      border-color: rgba(102, 187, 106, 0.34);
      background:
        linear-gradient(180deg, rgba(24, 54, 40, 0.58), rgba(13, 24, 40, 0.92));
    }

    .ai-pane {
      border-color: rgba(246, 184, 76, 0.34);
      background:
        linear-gradient(180deg, rgba(66, 48, 24, 0.54), rgba(13, 24, 40, 0.92));
    }

    .truth-boundary-pane ul {
      margin-top: 14px;
    }

    .memory-capability-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 16px;
    }

    .memory-capability {
      border: 1px solid rgba(90, 209, 255, 0.22);
      border-radius: 14px;
      padding: 10px;
      background: rgba(90, 209, 255, 0.07);
    }

    .memory-capability strong {
      display: block;
      color: var(--accent);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }

    .memory-capability span {
      display: block;
      color: var(--muted);
      font-size: 13px;
    }

    @media (max-width: 1100px) {
      .agent-grid,
      .index-source-mode-entry-grid,
      .index-source-status-grid,
      .index-object-storage-config-grid,
      .index-screen3-handoff-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 900px) {
      .pipeline-flow {
        grid-template-columns: 1fr;
      }

      .pipeline-node {
        min-height: auto;
      }

      .future-input-layout,
      .truth-boundary-grid,
      .memory-capability-grid,
      .action-summary-grid,
      .status-insight-row,
      .parser-review-grid,
      .governance-summary-grid,
      .governance-artifact-grid,
      .workflow-summary-grid,
      .index-source-mode-entry-grid,
      .index-source-status-grid,
      .index-object-storage-config-grid,
      .index-screen3-handoff-grid,
      .pipeline-support-grid,
      .semantic-assist-scope-list,
      .screen1-selector-grid,
      .screen1-operator-workflow,
      .screen2-control-card-grid,
      .screen2-selector-grid,
      .screen2-review-action-grid,
	      .screen3-selector-grid,
	      .screen3-action-grid,
	      .screen3-source-mode-grid,
	      .screen3-source-context-grid,
	      .screen3-filter-grid,
	      .screen3-filter-toolbar,
	      .screen3-workflow-subgrid,
	      .screen3-submit-result-grid,
	      .screen3-comparison-control-grid,
	      .screen3-target-card-grid,
	      .screen3-selected-context-strip,
	      .screen3-target-picker-grid,
	      .screen3-result-subcard-grid,
	      .screen3-result-grid,
	      .screen4-selector-grid,
      .screen4-historical-review-preview-grid,
      .screen5-action-preview-grid,
      .screen5-outcome-preview-grid,
      .screen5-selector-grid,
      .screen6-selector-grid,
      .screen6-candidate-review-control-grid,
      .screen6-materialization-review-control-grid,
      .screen6-model-registry-review-control-grid,
      .screen6-runtime-gate-review-control-grid,
      .fleet-detail-list {
        grid-template-columns: 1fr;
      }
      .parser-review-header,
      .parser-governance-header,
      .unknown-pattern-header,
      .governance-linkage-header,
      .semantic-context-header,
      .learning-candidate-header,
      .learning-governance-header {
        display: none;
      }
      .parser-review-row,
      .parser-governance-row,
      .unknown-pattern-row,
      .governance-linkage-row,
      .semantic-context-row,
      .learning-candidate-row,
      .learning-governance-row {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 700px) {
      .agent-grid {
        grid-template-columns: 1fr;
      }
    }

    .footer { margin-top: 18px; color: var(--muted); font-size: 12px; text-align: right; }
    ul, ol { margin: 10px 0 0 18px; padding: 0; }
    li { margin: 4px 0; }
    @media (min-width: 900px) {
      .half, .chart-panel { grid-column: span 6; }
    }
    @media (max-width: 780px) {
      .page-nav {
        display: flex;
        overflow-x: auto;
      }
      .hero {
        padding-right: 28px;
      }
      .runtime-badge {
        position: static;
        justify-items: start;
        text-align: left;
        margin-bottom: 12px;
      }
      .runtime-state-pills {
        justify-content: flex-start;
        flex-wrap: wrap;
        width: auto;
      }
      .runtime-mini-pill {
        justify-content: flex-start;
        min-width: 0;
        max-width: 100%;
      }
      .nav-link {
        flex: 0 0 auto;
        width: auto;
      }
      .flow-grid, .nav-card-grid, .health-check-grid,
      .decision-grid, .info-grid, .provider-grid, .scalar-grid, .visual-layer-grid,
      .visual-summary-grid, .domain-strip, .selector-control-grid,
      .diagnostic-snapshot-grid,
      .diagnostic-driver-stack,
      .index-source-mode-entry-grid,
      .index-source-status-grid,
      .index-object-storage-config-grid,
      .index-screen3-handoff-grid,
	      .screen4-verdict-grid,
	      .screen4-topology-grid {
	        grid-template-columns: 1fr;
	      }
      h1 { font-size: 28px; }
    }
"""
