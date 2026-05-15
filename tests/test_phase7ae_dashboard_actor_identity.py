from __future__ import annotations

import ast
import importlib
import os
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "architecture"
BOUNDARY_DOC = DOCS / "phase7ae_dashboard_actor_identity.md"
MODEL_DOC = DOCS / "phase7ae_actor_identity_model.md"
README = DOCS / "README.md"
MODULE_PATH = ROOT / "src" / "learning" / "dashboard_actor_identity.py"

RUNTIME_IMPORT_PATHS = (
    "scripts/run_analysis.py",
    "src/parser",
    "src/parsing",
    "src/scoring",
    "src/decision",
    "src/recommendation",
    "src/recommendations",
    "src/analysis/decision_engine.py",
    "src/analysis/recommendation_engine.py",
    "src/analysis/scoring_adapter.py",
)

FORBIDDEN_BEHAVIOR_FILES = (
    "src/reporting/html_dashboard.py",
    "src/reporting/ai_display_metadata.py",
    "scripts/awr_memory_cli.py",
    "scripts/run_analysis.py",
)

FORBIDDEN_IMPORT_PREFIXES = (
    "oracledb",
    "sqlite3",
    "oci",
    "requests",
    "socket",
    "urllib",
    "http.client",
    "httpx",
    "src.reporting",
    "src.parser",
    "src.parsing",
    "src.scoring",
    "src.decision",
    "src.recommendation",
    "src.recommendations",
    "src.analysis",
    "src.memory",
    "scripts.awr_memory_cli",
    "scripts.run_analysis",
)

FORBIDDEN_FUNCTION_NAMES = (
    "login",
    "logout",
    "authenticate",
    "authorize",
    "grant_permission",
    "revoke_permission",
    "validate_password",
    "create_session",
    "enforce_authorization",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def lower_text(path: Path) -> str:
    return read_text(path).lower()


def python_files(paths: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for relative_path in paths:
        path = ROOT / relative_path
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
    return files


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def function_names(path: Path) -> set[str]:
    tree = ast.parse(read_text(path), filename=str(path))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def actor_module():
    return importlib.import_module("src.learning.dashboard_actor_identity")


def make_actor(**overrides):
    module = actor_module()
    values = {
        "actor_id": "ACTOR-LOCAL-JANE-REVIEWER",
        "display_name": "Jane Reviewer",
        "role": "reviewer",
        "actor_source": "local",
        "permission_scope": "review",
        "authenticated": False,
        "email": "jane.reviewer@example.com",
        "organization": "Example",
        "audit_reference": "AUDIT-REF-1",
        "created_at": None,
        "notes": "unit test",
    }
    values.update(overrides)
    return module.DashboardActorIdentity(**values)


class Phase7AEDashboardActorIdentityTests(unittest.TestCase):
    def test_module_import_safety(self) -> None:
        before_environment = dict(os.environ)
        module = actor_module()
        self.assertEqual(before_environment, dict(os.environ))
        self.assertTrue(hasattr(module, "DashboardActorIdentity"))
        self.assertTrue(hasattr(module, "ActorAuditContext"))

        imports = imported_modules(MODULE_PATH)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES:
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        imported == forbidden or imported.startswith(f"{forbidden}.")
                        for imported in imports
                    )
                )

    def test_docs_exist(self) -> None:
        self.assertTrue(BOUNDARY_DOC.is_file(), BOUNDARY_DOC)
        self.assertTrue(MODEL_DOC.is_file(), MODEL_DOC)

    def test_docs_contain_required_boundary_phrases(self) -> None:
        text = lower_text(BOUNDARY_DOC) + "\n" + lower_text(MODEL_DOC)
        for phrase in (
            "does not implement authentication",
            "does not implement authorization enforcement",
            "permission scope is metadata only",
            "actor identity does not grant runtime authority",
            "actor identity does not mutate backend truth",
            "actor identity is required for future governed write workflows",
            "no dashboard ui is changed",
            "no cli behavior is changed",
            "no run_analysis.py wiring is added",
            "deterministic runtime remains authoritative",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_docs_contain_required_sections(self) -> None:
        boundary_text = read_text(BOUNDARY_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. Scope",
            "## 3. Non-Goals",
            "## 4. Why Actor Identity Is Needed",
            "## 5. Actor Identity Boundary",
            "## 6. Reviewer Boundary",
            "## 7. Actor Roles",
            "## 8. Actor Sources",
            "## 9. Permission Scopes",
            "## 10. Audit Context",
            "## 11. Authentication Boundary",
            "## 12. Authorization Boundary",
            "## 13. Runtime Truth Boundary",
            "## 14. Dashboard Workflow Relationship",
            "## 15. Relationship to Future 7AF",
            "## 16. Relationship to Future 7AG",
            "## 17. Relationship to Future Screen Workflows",
            "## 18. Relationship to Phase 8",
            "## 19. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, boundary_text)

        model_text = read_text(MODEL_DOC)
        for section in (
            "## 1. Purpose",
            "## 2. DashboardActorIdentity Object Shape",
            "## 3. ActorAuditContext Object Shape",
            "## 4. Actor Roles",
            "## 5. Actor Sources",
            "## 6. Permission Scopes",
            "## 7. Deterministic ID Rules",
            "## 8. Validation Rules",
            "## 9. Serialization Rules",
            "## 10. Metadata Helper Rules",
            "## 11. Non-Goals",
            "## 12. Acceptance Criteria",
        ):
            with self.subTest(section=section):
                self.assertIn(section, model_text)

    def test_supported_roles(self) -> None:
        module = actor_module()
        self.assertEqual(
            module.ACTOR_ROLES,
            ("viewer", "reviewer", "approver", "operator", "admin", "system"),
        )
        for role in module.ACTOR_ROLES:
            with self.subTest(role=role):
                actor = make_actor(role=role)
                self.assertEqual(actor.role, role)
        with self.assertRaises(module.DashboardActorIdentityError):
            make_actor(role="owner")

    def test_supported_sources(self) -> None:
        module = actor_module()
        self.assertEqual(
            module.ACTOR_SOURCES,
            ("local", "cli", "dashboard", "system", "unknown"),
        )
        for source in module.ACTOR_SOURCES:
            with self.subTest(source=source):
                actor = make_actor(actor_source=source)
                self.assertEqual(actor.actor_source, source)
        with self.assertRaises(module.DashboardActorIdentityError):
            make_actor(actor_source="sso")

    def test_supported_permission_scopes(self) -> None:
        module = actor_module()
        self.assertEqual(
            module.PERMISSION_SCOPES,
            ("read_only", "review", "approve", "execute", "administer"),
        )
        for scope in module.PERMISSION_SCOPES:
            with self.subTest(scope=scope):
                actor = make_actor(permission_scope=scope)
                self.assertEqual(actor.permission_scope, scope)
        with self.assertRaises(module.DashboardActorIdentityError):
            make_actor(permission_scope="write")

    def test_actor_creation_and_validation(self) -> None:
        module = actor_module()
        first = module.create_actor_id(
            "Jane Reviewer",
            actor_source="dashboard",
            email="Jane.Reviewer@example.com",
        )
        second = module.create_actor_id(
            "  Jane   Reviewer  ",
            actor_source="dashboard",
            email="jane.reviewer@example.com",
        )
        self.assertEqual(first, second)
        self.assertEqual(first, "ACTOR-DASHBOARD-JANE-REVIEWER-EXAMPLE-COM")

        system_actor = module.create_system_actor(notes="system audit")
        self.assertEqual(system_actor.actor_id, "ACTOR-SYSTEM-SYSTEM")
        self.assertEqual(system_actor.role, "system")
        self.assertEqual(system_actor.actor_source, "system")
        self.assertFalse(system_actor.authenticated)

        unknown_actor = module.create_unknown_actor(notes="fallback")
        self.assertEqual(unknown_actor.actor_id, "ACTOR-UNKNOWN-UNKNOWN-ACTOR")
        self.assertEqual(unknown_actor.role, "viewer")
        self.assertEqual(unknown_actor.permission_scope, "read_only")

        actor = make_actor()
        self.assertIs(module.validate_dashboard_actor_identity(actor), actor)

        with self.assertRaises(module.DashboardActorIdentityError):
            make_actor(actor_id="")
        with self.assertRaises(module.DashboardActorIdentityError):
            make_actor(display_name=" ")
        with self.assertRaises(module.DashboardActorIdentityError):
            make_actor(authenticated="false")

    def test_audit_context_creation_and_validation(self) -> None:
        module = actor_module()
        actor = make_actor()
        context = module.create_actor_audit_context(
            actor,
            action_scope="Diagnostic Review",
            notes="review request",
        )
        expected_id = (
            "ACTOR-AUDIT-ACTOR-LOCAL-JANE-REVIEWER-DIAGNOSTIC-REVIEW"
        )
        self.assertEqual(context.audit_context_id, expected_id)
        self.assertEqual(context.actor_id, actor.actor_id)
        self.assertEqual(context.display_name, actor.display_name)
        self.assertEqual(context.role, actor.role)
        self.assertEqual(context.actor_source, actor.actor_source)
        self.assertEqual(context.permission_scope, actor.permission_scope)
        self.assertFalse(context.authenticated)
        self.assertEqual(context.action_scope, "Diagnostic Review")
        self.assertIs(module.validate_actor_audit_context(context), context)

        same_context = module.create_actor_audit_context(
            actor,
            action_scope="Diagnostic Review",
            notes="review request",
        )
        self.assertEqual(context, same_context)

        with self.assertRaises(module.DashboardActorIdentityError):
            module.ActorAuditContext(
                audit_context_id="CTX",
                actor_id="",
                display_name="Jane Reviewer",
                role="reviewer",
                actor_source="local",
                permission_scope="review",
                authenticated=False,
            )

    def test_metadata_helper_behavior(self) -> None:
        module = actor_module()
        viewer = make_actor(role="viewer", permission_scope="read_only")
        reviewer = make_actor(role="reviewer", permission_scope="review")
        approver = make_actor(role="approver", permission_scope="approve")
        operator = make_actor(role="operator", permission_scope="execute")
        admin = make_actor(role="admin", permission_scope="administer")
        system = module.create_system_actor()

        before = module.dashboard_actor_identity_to_dict(reviewer)
        self.assertFalse(module.actor_can_request_approval(viewer))
        self.assertFalse(module.actor_can_request_execution(viewer))
        self.assertTrue(module.actor_can_request_review(reviewer))
        self.assertTrue(module.actor_can_request_approval(approver))
        self.assertTrue(module.actor_can_request_execution(operator))
        self.assertTrue(module.actor_can_request_execution(admin))
        self.assertFalse(module.actor_can_request_review(system))
        self.assertFalse(module.actor_can_request_approval(system))
        self.assertFalse(module.actor_can_request_execution(system))
        after = module.dashboard_actor_identity_to_dict(reviewer)
        self.assertEqual(before, after)

    def test_serialization_round_trip(self) -> None:
        module = actor_module()
        actor = make_actor()
        actor_payload = module.dashboard_actor_identity_to_dict(actor)
        actor_round_trip = module.dashboard_actor_identity_from_dict(actor_payload)
        self.assertEqual(actor, actor_round_trip)
        self.assertEqual(
            actor_payload,
            module.dashboard_actor_identity_to_dict(actor_round_trip),
        )

        context = module.create_actor_audit_context(actor, action_scope="review")
        context_payload = module.actor_audit_context_to_dict(context)
        context_round_trip = module.actor_audit_context_from_dict(context_payload)
        self.assertEqual(context, context_round_trip)
        self.assertEqual(
            context_payload,
            module.actor_audit_context_to_dict(context_round_trip),
        )

        bad_payload = dict(actor_payload)
        bad_payload["runtime_authority"] = True
        with self.assertRaises(module.DashboardActorIdentityError):
            module.dashboard_actor_identity_from_dict(bad_payload)

    def test_no_authentication_or_authorization_functions(self) -> None:
        names = function_names(MODULE_PATH)
        for forbidden in FORBIDDEN_FUNCTION_NAMES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, names)

    def test_runtime_import_isolation(self) -> None:
        run_analysis_imports = imported_modules(ROOT / "scripts" / "run_analysis.py")
        for module_name in (
            "src.learning.dashboard_actor_identity",
            "learning.dashboard_actor_identity",
            "dashboard_actor_identity",
        ):
            with self.subTest(module_name=module_name):
                self.assertNotIn(module_name, run_analysis_imports)

        for path in python_files(RUNTIME_IMPORT_PATHS):
            imports = imported_modules(path)
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertNotIn("src.learning.dashboard_actor_identity", imports)
                self.assertNotIn("learning.dashboard_actor_identity", imports)
                self.assertNotIn("dashboard_actor_identity", imports)

    def test_behavior_files_are_not_modified_by_phase7ae(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not available")
        if not (ROOT / ".git").exists():
            self.skipTest("not a git checkout")

        completed = subprocess.run(
            ("git", "diff", "--name-only", "--", *FORBIDDEN_BEHAVIOR_FILES),
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            self.skipTest(completed.stderr.strip() or "git diff unavailable")

        changed = {
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip()
        }
        changed -= {"src/reporting/html_dashboard.py"}  # Phase 7AN owns disabled Screen 3 action UI.
        self.assertFalse(changed, f"behavior files modified: {sorted(changed)}")

    def test_readme_links_new_docs(self) -> None:
        text = read_text(README)
        for title, filename in (
            (
                "Phase 7AE Dashboard Actor / Reviewer Identity",
                "phase7ae_dashboard_actor_identity.md",
            ),
            (
                "Phase 7AE Actor Identity Model",
                "phase7ae_actor_identity_model.md",
            ),
        ):
            with self.subTest(title=title):
                self.assertIn(title, text)
                self.assertIn(filename, text)


if __name__ == "__main__":
    unittest.main()
