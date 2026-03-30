"""Tests for vault_init tool: setup (seed/scan) and migrate actions."""

from __future__ import annotations

import json

import frontmatter
import pytest

from tests.conftest import MemoryAdapter, McpStub
from vault_mcp.tools.init_tool import _convert_todo_syntax, register_init_tools


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def setup_init(files: dict[str, str] | None = None):
    adapter = MemoryAdapter(files)
    mcp = McpStub()
    register_init_tools(mcp, adapter)
    return adapter, mcp.tools["vault_init"]


# ---------------------------------------------------------------------------
# _convert_todo_syntax unit tests
# ---------------------------------------------------------------------------

class TestConvertTodoSyntax:
    def test_unchecked_becomes_plain_bullet(self):
        body = "- [ ] Write blog post\n- [ ] Launch feature"
        result = _convert_todo_syntax(body)
        assert "- Write blog post" in result
        assert "- Launch feature" in result
        assert "[ ]" not in result

    def test_checked_becomes_strikethrough(self):
        body = "- [x] Shipped v1\n- [X] Fixed bug"
        result = _convert_todo_syntax(body)
        assert "- ~~Shipped v1~~" in result
        assert "- ~~Fixed bug~~" in result
        assert "[x]" not in result
        assert "[X]" not in result

    def test_asterisk_and_plus_bullets(self):
        body = "* [ ] asterisk todo\n+ [x] plus done"
        result = _convert_todo_syntax(body)
        assert "* asterisk todo" in result
        assert "+ ~~plus done~~" in result

    def test_non_todo_lines_unchanged(self):
        body = "Regular line\n- plain bullet\n## Heading"
        result = _convert_todo_syntax(body)
        assert result == body

    def test_mixed_content(self):
        body = "Intro\n- [x] Done thing\n- [ ] Pending\nConclusion"
        result = _convert_todo_syntax(body)
        assert "~~Done thing~~" in result
        assert "- Pending" in result
        assert "Intro" in result
        assert "Conclusion" in result


# ---------------------------------------------------------------------------
# setup action — empty vault
# ---------------------------------------------------------------------------

class TestSetupEmptyVault:
    def test_empty_vault_returns_seeded_status(self):
        _, tool = setup_init({})
        result = tool(action="setup")
        assert result["status"] == "seeded"

    def test_seeded_files_include_tags_yaml(self):
        adapter, tool = setup_init({})
        tool(action="setup")
        assert "tags.yaml" in adapter.files

    def test_seeded_files_include_brain_json(self):
        adapter, tool = setup_init({})
        tool(action="setup")
        assert ".brain/graph.json" in adapter.files
        assert ".brain/clusters.json" in adapter.files

    def test_seeded_files_include_templates(self):
        adapter, tool = setup_init({})
        tool(action="setup")
        assert "templates/capture.md" in adapter.files
        assert "templates/note.md" in adapter.files

    def test_seeded_dirs_created_via_gitkeep(self):
        adapter, tool = setup_init({})
        tool(action="setup")
        # .gitkeep files are written to trigger directory creation
        assert "captures/.gitkeep" in adapter.files
        assert "notes/.gitkeep" in adapter.files

    def test_files_created_list_populated(self):
        _, tool = setup_init({})
        result = tool(action="setup")
        assert len(result["files_created"]) > 0


# ---------------------------------------------------------------------------
# setup action — already initialized vault
# ---------------------------------------------------------------------------

class TestSetupAlreadyInitialized:
    def test_returns_already_initialized_when_only_managed_files(self):
        _, tool = setup_init({"captures/2026-01-01-note.md": "content"})
        result = tool(action="setup")
        assert result["status"] == "already_initialized"


# ---------------------------------------------------------------------------
# setup action — non-empty vault (scan)
# ---------------------------------------------------------------------------

class TestSetupNonEmptyVault:
    def test_returns_scan_complete_status(self):
        _, tool = setup_init({"daily/2025-01-15.md": "Short note."})
        result = tool(action="setup")
        assert result["status"] == "scan_complete"

    def test_summary_counts_are_correct(self):
        files = {
            "daily/2025-01-01.md": "Short daily.",
            "projects/big-note.md": "# Big Project\n\n" + "word " * 310,
        }
        _, tool = setup_init(files)
        result = tool(action="setup")
        summary = result["summary"]
        assert summary["total_files"] == 2
        assert summary["auto_captures"] + summary["auto_notes"] + summary["ambiguous"] == 2

    def test_managed_dirs_excluded_from_scan(self):
        files = {
            "daily/2025-01-01.md": "Short note.",
            "captures/2026-01-01-existing.md": "---\ntitle: Existing\nstatus: capture\n---\nbody",
            "notes/existing-note.md": "---\ntitle: Note\nstatus: note\n---\nbody",
        }
        _, tool = setup_init(files)
        result = tool(action="setup")
        assert result["summary"]["total_files"] == 1  # only daily/

    def test_plan_written_to_brain(self):
        adapter, tool = setup_init({"loose/note.md": "Some content here."})
        tool(action="setup")
        assert ".brain/import-plan.json" in adapter.files
        plan = json.loads(adapter.files[".brain/import-plan.json"])
        assert plan["status"] == "pending"

    def test_ambiguous_files_returned_without_full_content(self):
        # A medium-length file with H1 but short — should be ambiguous
        body = "# My Project\n\n" + "word " * 150
        _, tool = setup_init({"project/idea.md": body})
        result = tool(action="setup")
        # May be auto_note or ambiguous depending on word count; either way
        # ambiguous_files should not contain full body
        for f in result.get("ambiguous_files", []):
            assert len(f.get("body_preview", "")) <= 210  # preview only

    def test_short_file_classified_as_auto_capture(self):
        files = {"loose/quick.md": "A short note."}  # < 80 words
        _, tool = setup_init(files)
        result = tool(action="setup")
        assert result["summary"]["auto_captures"] == 1

    def test_daily_note_filename_classified_as_auto_capture(self):
        files = {"2025-03-15.md": "word " * 200}
        _, tool = setup_init(files)
        result = tool(action="setup")
        assert result["summary"]["auto_captures"] == 1

    def test_long_structured_note_classified_as_auto_note(self):
        body = "# Architecture Overview\n\n" + "word " * 350
        files = {"tech/architecture.md": body}
        _, tool = setup_init(files)
        result = tool(action="setup")
        assert result["summary"]["auto_notes"] == 1

    def test_title_inferred_from_h1(self):
        body = "# My Great Idea\n\nSome content here."
        adapter, tool = setup_init({"loose/idea.md": body})
        tool(action="setup")
        plan = json.loads(adapter.files[".brain/import-plan.json"])
        all_entries = (
            plan["auto_captures"] + plan["auto_notes"] + plan["ambiguous"]
        )
        entry = next(e for e in all_entries if e["path"] == "loose/idea.md")
        assert entry["inferred_title"] == "My Great Idea"
        assert entry["title_source"] == "h1"

    def test_title_inferred_from_frontmatter(self):
        body = "---\ntitle: FM Title\n---\nContent here."
        adapter, tool = setup_init({"loose/note.md": body})
        tool(action="setup")
        plan = json.loads(adapter.files[".brain/import-plan.json"])
        all_entries = (
            plan["auto_captures"] + plan["auto_notes"] + plan["ambiguous"]
        )
        entry = next(e for e in all_entries if e["path"] == "loose/note.md")
        assert entry["inferred_title"] == "FM Title"
        assert entry["title_source"] == "frontmatter"

    def test_title_inferred_from_filename(self):
        body = "Just content, no heading."
        adapter, tool = setup_init({"loose/my-project-idea.md": body})
        tool(action="setup")
        plan = json.loads(adapter.files[".brain/import-plan.json"])
        all_entries = (
            plan["auto_captures"] + plan["auto_notes"] + plan["ambiguous"]
        )
        entry = next(e for e in all_entries if e["path"] == "loose/my-project-idea.md")
        assert entry["inferred_title"] == "My Project Idea"
        assert entry["title_source"] == "filename"


# ---------------------------------------------------------------------------
# migrate action
# ---------------------------------------------------------------------------

class TestMigrateAction:
    def _setup_with_plan(self, files: dict[str, str], plan: dict) -> tuple:
        all_files = {**files, ".brain/import-plan.json": json.dumps(plan)}
        adapter = MemoryAdapter(all_files)
        mcp = McpStub()
        register_init_tools(mcp, adapter)
        return adapter, mcp.tools["vault_init"]

    def test_migrate_without_plan_returns_error(self):
        _, tool = setup_init({})
        result = tool(action="migrate")
        assert result["status"] == "error"
        assert "import plan" in result["message"].lower()

    def test_auto_capture_migrated_to_captures_dir(self):
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "My Note",
                                "created_from_meta": None, "auto_tags": []}],
            "auto_notes": [],
            "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": "Some content here."}, plan)
        result = tool(action="migrate")
        assert result["status"] == "success"
        assert result["as_captures"] == 1
        assert any(k.startswith("captures/") for k in adapter.files)

    def test_auto_note_migrated_to_notes_dir(self):
        plan = {
            "status": "pending",
            "auto_captures": [],
            "auto_notes": [{"path": "tech/arch.md", "inferred_title": "Architecture",
                             "created_from_meta": None, "auto_tags": ["programming"],
                             "inferred_domain": "programming"}],
            "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan(
            {"tech/arch.md": "# Architecture\n\nContent."}, plan
        )
        result = tool(action="migrate")
        assert result["as_notes"] == 1
        assert any(k.startswith("notes/") for k in adapter.files)

    def test_original_deleted_by_default(self):
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "Note",
                                "created_from_meta": None, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": "content"}, plan)
        tool(action="migrate", keep_original=False)
        assert "loose/note.md" not in adapter.files

    def test_keep_original_preserves_source_file(self):
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "Note",
                                "created_from_meta": None, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": "content"}, plan)
        tool(action="migrate", keep_original=True)
        assert "loose/note.md" in adapter.files

    def test_plan_file_deleted_after_migration(self):
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "Note",
                                "created_from_meta": None, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": "content"}, plan)
        tool(action="migrate")
        assert ".brain/import-plan.json" not in adapter.files

    def test_created_date_preserved_from_original_frontmatter(self):
        original_created = "2024-06-15T10:00:00+00:00"
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "Note",
                                "created_from_meta": original_created, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": "content"}, plan)
        tool(action="migrate")
        new_key = next(k for k in adapter.files if k.startswith("captures/"))
        post = frontmatter.loads(adapter.files[new_key])
        assert post.metadata["created"] == original_created

    def test_capture_created_date_used_in_filename(self):
        original_created = "2024-06-15T10:30:00+00:00"
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "My Note",
                                "created_from_meta": original_created, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": "content"}, plan)
        tool(action="migrate")
        new_key = next(k for k in adapter.files if k.startswith("captures/"))
        assert "2024-06-15" in new_key

    def test_obsidian_custom_fields_not_preserved(self):
        """Only 'created' is preserved; all other original frontmatter is discarded."""
        content = "---\ntitle: Old Title\ncssclass: wide\nmodified: 2024-01-01\ncreated: 2024-01-01T00:00:00+00:00\n---\nBody"
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "Note",
                                "created_from_meta": "2024-01-01T00:00:00+00:00", "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": content}, plan)
        tool(action="migrate")
        new_key = next(k for k in adapter.files if k.startswith("captures/"))
        post = frontmatter.loads(adapter.files[new_key])
        assert "cssclass" not in post.metadata
        assert "modified" not in post.metadata
        assert post.metadata["status"] == "capture"

    def test_capture_frontmatter_has_vault_schema(self):
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "My Note",
                                "created_from_meta": None, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": "content"}, plan)
        tool(action="migrate")
        new_key = next(k for k in adapter.files if k.startswith("captures/"))
        post = frontmatter.loads(adapter.files[new_key])
        for field in ["title", "status", "created", "updated", "source", "tags", "aliases"]:
            assert field in post.metadata
        assert post.metadata["status"] == "capture"
        assert post.metadata["source"] == "imported"

    def test_note_frontmatter_has_vault_schema(self):
        plan = {
            "status": "pending",
            "auto_captures": [],
            "auto_notes": [{"path": "tech/arch.md", "inferred_title": "Architecture",
                             "created_from_meta": None, "auto_tags": [],
                             "inferred_domain": "programming"}],
            "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"tech/arch.md": "# Arch\n\nContent."}, plan)
        tool(action="migrate")
        new_key = next(k for k in adapter.files if k.startswith("notes/"))
        post = frontmatter.loads(adapter.files[new_key])
        for field in ["title", "status", "created", "updated", "domain", "confidence", "tags", "aliases", "promoted_from"]:
            assert field in post.metadata
        assert post.metadata["status"] == "note"
        assert post.metadata["confidence"] == 0.5

    def test_note_has_summary_notes_links_sections(self):
        plan = {
            "status": "pending",
            "auto_captures": [],
            "auto_notes": [{"path": "tech/arch.md", "inferred_title": "Architecture",
                             "created_from_meta": None, "auto_tags": [],
                             "inferred_domain": "programming"}],
            "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan(
            {"tech/arch.md": "Original content about architecture."}, plan
        )
        tool(action="migrate")
        new_key = next(k for k in adapter.files if k.startswith("notes/"))
        post = frontmatter.loads(adapter.files[new_key])
        assert "# Summary" in post.content
        assert "(imported — summary pending)" in post.content
        assert "# Notes" in post.content
        assert "Original content about architecture." in post.content
        assert "# Links" in post.content

    def test_ambiguous_defaults_to_capture_without_override(self):
        plan = {
            "status": "pending",
            "auto_captures": [], "auto_notes": [],
            "ambiguous": [{"path": "loose/idea.md", "inferred_title": "Idea",
                            "created_from_meta": None, "auto_tags": []}],
        }
        adapter, tool = self._setup_with_plan({"loose/idea.md": "content"}, plan)
        result = tool(action="migrate")
        assert result["as_captures"] == 1
        assert result["as_notes"] == 0

    def test_ambiguous_with_override_target_note(self):
        plan = {
            "status": "pending",
            "auto_captures": [], "auto_notes": [],
            "ambiguous": [{"path": "loose/idea.md", "inferred_title": "Idea",
                            "created_from_meta": None, "auto_tags": []}],
        }
        adapter, tool = self._setup_with_plan({"loose/idea.md": "content"}, plan)
        result = tool(
            action="migrate",
            manual_overrides=[{"path": "loose/idea.md", "target": "notes", "title": "Big Idea"}],
        )
        assert result["as_notes"] == 1

    def test_missing_file_reported_as_failed(self):
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "nonexistent.md", "inferred_title": "X",
                                "created_from_meta": None, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({}, plan)
        result = tool(action="migrate")
        assert result["total_failed"] == 1
        assert "nonexistent.md" in result["failed_paths"]

    def test_partial_failure_returns_partial_status(self):
        plan = {
            "status": "pending",
            "auto_captures": [
                {"path": "ok.md", "inferred_title": "OK", "created_from_meta": None, "auto_tags": []},
                {"path": "missing.md", "inferred_title": "Bad", "created_from_meta": None, "auto_tags": []},
            ],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"ok.md": "good content"}, plan)
        result = tool(action="migrate")
        assert result["status"] == "partial"
        assert result["total_migrated"] == 1
        assert result["total_failed"] == 1

    def test_return_is_summary_not_per_file_details(self):
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "a.md", "inferred_title": "A", "created_from_meta": None, "auto_tags": []},
                               {"path": "b.md", "inferred_title": "B", "created_from_meta": None, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"a.md": "content a", "b.md": "content b"}, plan)
        result = tool(action="migrate")
        assert "total_migrated" in result
        assert result["total_migrated"] == 2
        # No per-file migration list in result
        assert "migrated" not in result


# ---------------------------------------------------------------------------
# Todo conversion during migration
# ---------------------------------------------------------------------------

class TestTodoConversionDuringMigration:
    def _setup_with_plan(self, files, plan):
        all_files = {**files, ".brain/import-plan.json": json.dumps(plan)}
        adapter = MemoryAdapter(all_files)
        mcp = McpStub()
        register_init_tools(mcp, adapter)
        return adapter, mcp.tools["vault_init"]

    def test_completed_todos_become_strikethrough(self):
        content = "Notes\n- [x] Shipped side project feature\n- [x] Fixed bug"
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "Note",
                                "created_from_meta": None, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": content}, plan)
        tool(action="migrate")
        new_key = next(k for k in adapter.files if k.startswith("captures/"))
        post = frontmatter.loads(adapter.files[new_key])
        assert "~~Shipped side project feature~~" in post.content
        assert "~~Fixed bug~~" in post.content
        assert "[x]" not in post.content

    def test_pending_todos_become_plain_bullets(self):
        content = "- [ ] Pending task\n- [ ] Another task"
        plan = {
            "status": "pending",
            "auto_captures": [{"path": "loose/note.md", "inferred_title": "Note",
                                "created_from_meta": None, "auto_tags": []}],
            "auto_notes": [], "ambiguous": [],
        }
        adapter, tool = self._setup_with_plan({"loose/note.md": content}, plan)
        tool(action="migrate")
        new_key = next(k for k in adapter.files if k.startswith("captures/"))
        post = frontmatter.loads(adapter.files[new_key])
        assert "- Pending task" in post.content
        assert "[ ]" not in post.content


# ---------------------------------------------------------------------------
# Unknown action
# ---------------------------------------------------------------------------

class TestUnknownAction:
    def test_unknown_action_returns_error(self):
        _, tool = setup_init({})
        result = tool(action="invalid")
        assert result["status"] == "error"
        assert "invalid" in result["message"]
