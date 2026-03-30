"""vault_init: Initialize a new vault or migrate existing Obsidian notes to vault-mcp format."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import frontmatter

from vault_mcp.adapters.base import StorageAdapter
from vault_mcp.tools.write import (
    _collect_existing_tags,
    _extract_auto_tags,
    _generate_slug,
    _load_tags_yaml,
)

logger = logging.getLogger("vault-mcp.tools.init")

# Template directory bundled with the package
TEMPLATE_DIR = Path(__file__).parent.parent / "template"

# Directories managed by vault-mcp — excluded from unmanaged scan
MANAGED_DIRS: frozenset[str] = frozenset({
    "captures", "notes", "topics", ".brain", "maps", "outputs", "templates",
})

# Regex for detecting daily/journal note filenames or parent directories
_DAILY_RE = re.compile(
    r"(^|[_\-\s])\d{4}-\d{2}-\d{2}([_\-\s]|$)|daily|日记|日志|journal",
    re.IGNORECASE,
)

_PLAN_PATH = ".brain/import-plan.json"

# Domain tags used for best-effort domain inference
_DOMAIN_PRIORITY = [
    "ai", "llm", "programming", "coding", "productivity", "learning",
    "writing", "health", "finance", "business", "philosophy", "psychology",
    "pkm", "prompt-engineering",
]


# ---------------------------------------------------------------------------
# Text processing helpers
# ---------------------------------------------------------------------------

def _convert_todo_syntax(body: str) -> str:
    """Convert Markdown todo checkboxes to plain prose.

    - [x] done  →  - ~~done~~  (completed, preserved as historical record)
    - [ ] todo  →  - todo      (open, preserved as plain bullet)
    """
    body = re.sub(r"^([-*+])\s+\[[xX]\]\s+(.+)$", r"\1 ~~\2~~", body, flags=re.MULTILINE)
    body = re.sub(r"^([-*+])\s+\[ \]\s+(.+)$", r"\1 \2", body, flags=re.MULTILINE)
    return body


def _infer_title(path: str, meta: dict, body: str) -> tuple[str, str]:
    """Infer title: frontmatter.title > first H1 heading > filename stem.

    Returns (title, source) where source ∈ {"frontmatter", "h1", "filename"}.
    """
    if meta.get("title"):
        return str(meta["title"]), "frontmatter"
    m = re.search(r"^#\s+(.+)", body, re.MULTILINE)
    if m:
        return m.group(1).strip(), "h1"
    stem = Path(path).stem
    title = re.sub(r"[-_]+", " ", stem).strip().title()
    return title, "filename"


def _count_words(text: str) -> int:
    return len(text.split())


def _is_managed(path: str) -> bool:
    """Return True if path belongs to a vault-mcp managed directory, hidden dir, or _archive."""
    first = path.split("/")[0]
    return first in MANAGED_DIRS or first.startswith(".") or first == ARCHIVE_DIR


def _classify_file(path: str, body: str) -> Literal["auto_capture", "auto_note", "ambiguous"]:
    """Server-side heuristic file classification."""
    filename = Path(path).stem
    parent = str(Path(path).parent)
    word_count = _count_words(body)
    has_h1 = bool(re.search(r"^#\s+.+", body, re.MULTILINE))
    h2_count = len(re.findall(r"^##\s+.+", body, re.MULTILINE))

    # Daily/journal notes → capture
    if _DAILY_RE.search(filename) or _DAILY_RE.search(parent):
        return "auto_capture"

    # Very short files → capture
    if word_count < 80:
        return "auto_capture"

    # No headings and medium-short → capture
    if not has_h1 and h2_count == 0 and word_count < 200:
        return "auto_capture"

    # Well-structured long files → note
    if has_h1 and word_count > 300:
        return "auto_note"
    if has_h1 and h2_count >= 2:
        return "auto_note"

    # Rich content even without H1 (logseq, project notes, research reports)
    if word_count > 500:
        return "auto_note"
    if h2_count >= 1 and word_count > 150:
        return "auto_note"

    return "ambiguous"


def _infer_domain(tags: list[str]) -> str:
    """Best-effort domain from auto-extracted tags."""
    for tag in _DOMAIN_PRIORITY:
        if tag in tags:
            return tag
    return tags[0] if tags else "general"


# ---------------------------------------------------------------------------
# Vault seeding (empty vault)
# ---------------------------------------------------------------------------

def _seed_vault(adapter: StorageAdapter) -> dict:
    """Copy template files into the adapter for a fresh vault."""
    if not TEMPLATE_DIR.exists():
        return {
            "status": "error",
            "message": f"Template directory not found: {TEMPLATE_DIR}",
        }

    files_created: list[str] = []
    for file_path in sorted(TEMPLATE_DIR.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.name == ".gitkeep" and file_path.stat().st_size == 0:
            # Write empty file to trigger directory creation, don't add to files_created list
            try:
                rel = file_path.relative_to(TEMPLATE_DIR).as_posix()
                adapter.write_file(rel, "")
            except Exception:
                pass
            continue
        rel = file_path.relative_to(TEMPLATE_DIR).as_posix()
        try:
            content = file_path.read_text(encoding="utf-8")
            adapter.write_file(rel, content)
            files_created.append(rel)
        except Exception as e:
            logger.warning("Failed to seed %s: %s", rel, e)

    return {
        "status": "seeded",
        "files_created": files_created,
        "next_step": "Vault initialized from template. Start capturing ideas with vault_capture.",
    }


# ---------------------------------------------------------------------------
# Vault scanning (non-empty vault)
# ---------------------------------------------------------------------------

def _scan_vault(adapter: StorageAdapter, unmanaged: list[str]) -> dict:
    """Scan unmanaged files, classify, persist plan, return summary + ambiguous."""
    tags_yaml = _load_tags_yaml(adapter)
    existing_tags = _collect_existing_tags(adapter)

    auto_captures: list[dict] = []
    auto_notes: list[dict] = []
    ambiguous_full: list[dict] = []   # persisted in plan (full data)
    ambiguous_return: list[dict] = [] # returned to Claude (lightweight)

    for path in unmanaged:
        try:
            raw = adapter.read_file(path)
            post = frontmatter.loads(raw)
            body = post.content
            meta = post.metadata

            title, title_source = _infer_title(path, meta, body)
            created_from_meta = str(meta["created"]) if meta.get("created") else None
            word_count = _count_words(body)
            has_h1 = bool(re.search(r"^#\s+.+", body, re.MULTILINE))
            auto_tags = _extract_auto_tags(body, tags_yaml, existing_tags)
            classification = _classify_file(path, body)

            base_entry = {
                "path": path,
                "inferred_title": title,
                "title_source": title_source,
                "created_from_meta": created_from_meta,
                "auto_tags": auto_tags,
            }

            if classification == "auto_capture":
                auto_captures.append(base_entry)
            elif classification == "auto_note":
                auto_notes.append({
                    **base_entry,
                    "inferred_domain": _infer_domain(auto_tags),
                })
            else:
                hint = (
                    "has H1 but body is short — likely note, verify"
                    if has_h1
                    else "medium length, no clear structure — verify"
                )
                full_entry = {
                    **base_entry,
                    "word_count": word_count,
                    "line_count": len(body.splitlines()),
                    "has_h1": has_h1,
                    "body_preview": body[:200],
                    "server_hint": hint,
                }
                ambiguous_full.append(full_entry)
                ambiguous_return.append({
                    k: full_entry[k]
                    for k in [
                        "path", "inferred_title", "title_source",
                        "word_count", "line_count", "has_h1",
                        "body_preview", "server_hint",
                    ]
                })
        except Exception as e:
            logger.warning("Error scanning %s: %s", path, e)
            continue

    # Persist full plan to .brain/import-plan.json
    plan = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "auto_captures": auto_captures,
        "auto_notes": auto_notes,
        "ambiguous": ambiguous_full,
    }
    try:
        adapter.write_file(_PLAN_PATH, json.dumps(plan, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.warning("Failed to write import plan: %s", e)

    total = len(auto_captures) + len(auto_notes) + len(ambiguous_full)
    return {
        "status": "scan_complete",
        "summary": {
            "total_files": total,
            "auto_captures": len(auto_captures),
            "auto_notes": len(auto_notes),
            "ambiguous": len(ambiguous_full),
        },
        "ambiguous_files": ambiguous_return,
        "plan_file": _PLAN_PATH,
        "message": (
            f"Found {total} unmanaged files: {len(auto_captures)} auto→capture, "
            f"{len(auto_notes)} auto→note, {len(ambiguous_full)} need review. "
            "Call migrate with manual_overrides to proceed."
        ),
    }


# ---------------------------------------------------------------------------
# Migration path generation
# ---------------------------------------------------------------------------

def _generate_capture_path(adapter: StorageAdapter, title: str, created_iso: str | None) -> str:
    """Generate captures/YYYY-MM-DD-HHMMSS-slug.md with collision avoidance."""
    if created_iso:
        try:
            dt = datetime.fromisoformat(created_iso)
        except (ValueError, TypeError):
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    ts = dt.strftime("%Y-%m-%d-%H%M%S")
    slug = _generate_slug(title)
    path = f"captures/{ts}-{slug}.md"
    counter = 2
    while True:
        try:
            adapter.read_file(path)
            path = f"captures/{ts}-{slug}-{counter}.md"
            counter += 1
        except FileNotFoundError:
            break
    return path


def _generate_note_path(adapter: StorageAdapter, title: str) -> str:
    """Generate notes/slug.md with collision avoidance."""
    slug = _generate_slug(title)
    path = f"notes/{slug}.md"
    counter = 2
    while True:
        try:
            adapter.read_file(path)
            path = f"notes/{slug}-{counter}.md"
            counter += 1
        except FileNotFoundError:
            break
    return path


# ---------------------------------------------------------------------------
# Single-file migration helpers
# ---------------------------------------------------------------------------

def _migrate_as_capture(
    adapter: StorageAdapter,
    path: str,
    title: str,
    created_from_meta: str | None,
    auto_tags: list[str],
    override: dict,
    keep_original: bool,
    now_iso: str,
    tags_yaml: dict,
    existing_tags: set,
) -> dict:
    """Migrate one file to captures/."""
    try:
        raw = adapter.read_file(path)
        post = frontmatter.loads(raw)
        body = _convert_todo_syntax(post.content)

        provided_tags = override.get("tags")
        if provided_tags is not None:
            tags = sorted(set(provided_tags))
        else:
            extra_tags = _extract_auto_tags(body, tags_yaml, existing_tags)
            tags = sorted(set(auto_tags) | set(extra_tags))

        # Clamp title to 50 chars (capture constraint)
        safe_title = title[:50] if len(title) > 50 else title
        created_iso = created_from_meta or now_iso
        source_type = override.get("source_type", "imported")

        new_meta = {
            "title": safe_title,
            "status": "capture",
            "created": created_iso,
            "updated": now_iso,
            "source": source_type,
            "tags": tags,
            "aliases": [],
        }
        new_post = frontmatter.Post(body, **new_meta)
        new_path = _generate_capture_path(adapter, title, created_from_meta)
        adapter.write_file(new_path, frontmatter.dumps(new_post))

        if not keep_original:
            try:
                adapter.delete_file(path)
            except Exception as e:
                logger.warning("Could not delete original %s: %s", path, e)

        existing_tags.update(t.lower() for t in tags)
        return {
            "original_path": path,
            "new_path": new_path,
            "target": "captures",
            "tags": tags,
            "kept_original": keep_original,
        }
    except Exception as e:
        logger.warning("migrate_as_capture failed for %s: %s", path, e)
        return {"original_path": path, "error": str(e)}


def _migrate_as_note(
    adapter: StorageAdapter,
    path: str,
    title: str,
    created_from_meta: str | None,
    auto_tags: list[str],
    override: dict,
    keep_original: bool,
    now_iso: str,
    tags_yaml: dict,
    existing_tags: set,
) -> dict:
    """Migrate one file to notes/."""
    try:
        raw = adapter.read_file(path)
        post = frontmatter.loads(raw)
        body = _convert_todo_syntax(post.content)

        provided_tags = override.get("tags")
        if provided_tags is not None:
            tags = sorted(set(provided_tags))
        else:
            extra_tags = _extract_auto_tags(body, tags_yaml, existing_tags)
            tags = sorted(set(auto_tags) | set(extra_tags))

        created_iso = created_from_meta or now_iso
        domain = override.get("domain") or _infer_domain(tags)
        confidence = override.get("confidence", 0.5)

        new_meta = {
            "title": title,
            "status": "note",
            "created": created_iso,
            "updated": now_iso,
            "domain": domain,
            "confidence": confidence,
            "tags": tags,
            "aliases": [],
            "promoted_from": [],
        }
        # Wrap body in note template structure (Summary / Notes / Links)
        structured_body = (
            "# Summary\n\n"
            "(imported — summary pending)\n\n"
            "# Notes\n\n"
            f"{body}\n\n"
            "# Links\n\n"
        )
        new_post = frontmatter.Post(structured_body, **new_meta)
        new_path = _generate_note_path(adapter, title)
        adapter.write_file(new_path, frontmatter.dumps(new_post))

        if not keep_original:
            try:
                adapter.delete_file(path)
            except Exception as e:
                logger.warning("Could not delete original %s: %s", path, e)

        existing_tags.update(t.lower() for t in tags)
        return {
            "original_path": path,
            "new_path": new_path,
            "target": "notes",
            "tags": tags,
            "kept_original": keep_original,
        }
    except Exception as e:
        logger.warning("migrate_as_note failed for %s: %s", path, e)
        return {"original_path": path, "error": str(e)}


# ---------------------------------------------------------------------------
# Post-migration cleanup
# ---------------------------------------------------------------------------

ARCHIVE_DIR = "_archive"


def _seed_missing_template_files(adapter: StorageAdapter) -> None:
    """Write template files that don't already exist in the vault.

    Used after migration to ensure the vault has the full example_vault
    structure (maps/, outputs/, topics/, templates/, tags.yaml, etc.).
    Skips files that already exist so it never overwrites user content.
    """
    if not TEMPLATE_DIR.exists():
        return

    for file_path in sorted(TEMPLATE_DIR.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(TEMPLATE_DIR).as_posix()
        try:
            adapter.read_file(rel)
            # File already exists — skip
        except FileNotFoundError:
            try:
                content = file_path.read_text(encoding="utf-8")
                adapter.write_file(rel, content)
            except Exception as e:
                logger.warning("Failed to seed missing template file %s: %s", rel, e)


def _cleanup_source_dirs(adapter: StorageAdapter) -> list[str]:
    """Move non-managed top-level directories and stray root files into _archive/.

    Only works with LocalStorageAdapter (requires vault_path on filesystem).
    Preserves all original content under _archive/ instead of deleting.
    """
    import shutil

    vault_path = getattr(adapter, "vault_path", None)
    if vault_path is None:
        return []

    archive_path = vault_path / ARCHIVE_DIR
    archive_path.mkdir(exist_ok=True)

    moved: list[str] = []
    KEEP_ROOT_FILES = {"tags.yaml", "README.md"}

    for item in list(vault_path.iterdir()):
        name = item.name
        if name.startswith(".") or name == ARCHIVE_DIR:
            continue  # Keep hidden dirs (.obsidian, .brain) and _archive itself

        if item.is_dir():
            if name not in MANAGED_DIRS:
                dest = archive_path / name
                try:
                    shutil.move(str(item), str(dest))
                    moved.append(f"{name}/")
                    logger.info("Archived source directory: %s", name)
                except Exception as e:
                    logger.warning("Could not archive directory %s: %s", name, e)
        elif item.is_file():
            if name not in KEEP_ROOT_FILES and not name.endswith(".md"):
                dest = archive_path / name
                try:
                    shutil.move(str(item), str(dest))
                    moved.append(name)
                    logger.info("Archived source file: %s", name)
                except Exception as e:
                    logger.warning("Could not archive file %s: %s", name, e)

    return moved


# ---------------------------------------------------------------------------
# Migration execution
# ---------------------------------------------------------------------------

def _handle_migrate(
    adapter: StorageAdapter,
    manual_overrides: list[dict],
    keep_original: bool,
) -> dict:
    """Execute migration from persisted plan + manual overrides."""
    try:
        plan_raw = adapter.read_file(_PLAN_PATH)
        plan = json.loads(plan_raw)
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "No import plan found. Run vault_init(action='setup') first.",
        }
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"Invalid import plan: {e}"}

    tags_yaml = _load_tags_yaml(adapter)
    existing_tags = _collect_existing_tags(adapter)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Build override lookup by path
    overrides: dict[str, dict] = {ov["path"]: ov for ov in manual_overrides}

    migrated: list[dict] = []
    failed: list[str] = []

    def _run(result: dict) -> None:
        if "error" in result:
            failed.append(result["original_path"])
            logger.warning("Migration failed for %s: %s", result["original_path"], result["error"])
        else:
            migrated.append(result)

    # auto_captures
    for entry in plan.get("auto_captures", []):
        _run(_migrate_as_capture(
            adapter, entry["path"], entry["inferred_title"],
            entry.get("created_from_meta"), entry.get("auto_tags", []),
            overrides.get(entry["path"], {}),
            keep_original, now_iso, tags_yaml, existing_tags,
        ))

    # auto_notes
    for entry in plan.get("auto_notes", []):
        base_override = {"domain": entry.get("inferred_domain", "general")}
        base_override.update(overrides.get(entry["path"], {}))
        _run(_migrate_as_note(
            adapter, entry["path"], entry["inferred_title"],
            entry.get("created_from_meta"), entry.get("auto_tags", []),
            base_override,
            keep_original, now_iso, tags_yaml, existing_tags,
        ))

    # ambiguous: use override target, default to captures
    for entry in plan.get("ambiguous", []):
        override = overrides.get(entry["path"], {})
        target = override.get("target", "captures")
        fn = _migrate_as_note if target == "notes" else _migrate_as_capture
        _run(fn(
            adapter, entry["path"],
            override.get("title", entry["inferred_title"]),
            entry.get("created_from_meta"), entry.get("auto_tags", []),
            override,
            keep_original, now_iso, tags_yaml, existing_tags,
        ))

    # Clean up plan file
    try:
        adapter.delete_file(_PLAN_PATH)
    except Exception:
        pass

    # Archive source directories and files when keep_original=False
    dirs_removed: list[str] = []
    if not keep_original:
        dirs_removed = _cleanup_source_dirs(adapter)

    # Seed template structure (maps/, outputs/, topics/, templates/, tags.yaml, etc.)
    # Only writes files that don't already exist
    _seed_missing_template_files(adapter)

    as_captures = sum(1 for r in migrated if r.get("target") == "captures")
    as_notes = sum(1 for r in migrated if r.get("target") == "notes")

    return {
        "status": "success" if not failed else "partial",
        "total_migrated": len(migrated),
        "as_captures": as_captures,
        "as_notes": as_notes,
        "total_failed": len(failed),
        "failed_paths": failed,
        "archived_to": f"{ARCHIVE_DIR}/" if dirs_removed else None,
        "archived_items": dirs_removed,
        "next_step": "Migration complete. Run vault_analyze to rebuild the knowledge graph.",
    }


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register_init_tools(mcp, adapter: StorageAdapter) -> None:

    @mcp.tool(annotations={"destructiveHint": True, "idempotentHint": False})
    def vault_init(
        action: str,
        manual_overrides: list[dict] | None = None,
        keep_original: bool = False,
    ) -> dict:
        """Initialize a new vault or migrate existing Obsidian notes to vault-mcp format.

        Actions:
          setup: Detect vault state and act accordingly.
            - Empty vault: seeds the vault with template structure
              (directory layout, .obsidian config, tags.yaml, templates/).
            - Non-empty vault with unmanaged files: scans all unmanaged .md
              files, classifies them into auto_captures / auto_notes / ambiguous
              using server-side heuristics, persists a plan to
              .brain/import-plan.json, and returns ONLY the ambiguous files for
              review. Claude should NOT call migrate until the user confirms.
            - Already-initialized vault: returns status "already_initialized".

          migrate: Execute the migration from the persisted import plan.
            params: manual_overrides (list[dict], optional — each dict must have
                    "path" key to identify the file; supported override fields:
                    target ("captures"|"notes"), title, tags (list[str]),
                    source_type (captures), domain/confidence (notes)),
                    keep_original (bool, default False — if True, source files
                    are preserved after migration)

        WORKFLOW:
          For setup:
            CALL vault_init(action="setup").
            Empty vault → vault seeded from template. Done.
            Non-empty vault → review summary + ambiguous_files.
              1. Present summary counts to user.
              2. For ambiguous files, decide target with user if needed.
              3. CONFIRM full plan, then call migrate.

          For migrate:
            CONFIRM: Show user the counts and ambiguous decisions before calling.
            auto-classified files will be migrated automatically.
            CALL vault_init(action="migrate", manual_overrides=[...],
                            keep_original=False).

        Todo conversion (applied automatically during migration):
          - [ ] pending task  →  - pending task      (plain bullet)
          - [x] done task     →  - ~~done task~~     (strikethrough, history preserved)
        """
        if action == "setup":
            all_md = adapter.list_files()
            unmanaged = [p for p in all_md if not _is_managed(p)]

            if not all_md:
                return _seed_vault(adapter)
            elif not unmanaged:
                return {
                    "status": "already_initialized",
                    "message": "All .md files are already in managed directories. Nothing to migrate.",
                }
            else:
                return _scan_vault(adapter, unmanaged)

        elif action == "migrate":
            return _handle_migrate(adapter, manual_overrides or [], keep_original)

        else:
            return {
                "status": "error",
                "message": f"Unknown action '{action}'. Valid: setup, migrate",
            }
