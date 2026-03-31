"""Cognitive visualization tools — snapshot, drift, and blindspot analysis."""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations

import frontmatter
import networkx as nx

from vault_mcp.adapters.base import StorageAdapter
from vault_mcp.graph.clustering import compute_clusters
from vault_mcp.graph.engine import VaultGraph
from vault_mcp.graph.models import ClusterData

logger = logging.getLogger("vault-mcp.tools.reflect")

SNAPSHOTS_DIR = ".brain/snapshots"

# ---------------------------------------------------------------------------
# Visualization hints — soft constraints for Claude artifact rendering
# ---------------------------------------------------------------------------

SNAPSHOT_HINT = (
    "ALWAYS generate a React artifact visualization. "
    "Render a **topic bubble map**: each tag from tag_counts is a circle, "
    "area proportional to count. Color by rough domain (group similar tags). "
    "Place connected tags (from tag_cooccurrence) near each other. "
    "Below the map, show a compact timeline strip: one row per month from topic_timeline, "
    "with small dots for each note colored by type (capture/note/topic). "
    "Style: rounded shapes, soft pastel palette, generous whitespace, no grid lines. "
    "Use file_count for a small summary badge (e.g. '32 captures, 3 notes'). "
    "Tone: lead with 1-2 reflective observations like a mentor — "
    "'You have been thinking a lot about X lately' not 'X has 57 occurrences'."
)

DRIFT_HINT = (
    "ALWAYS generate a React artifact visualization. "
    "Render a **horizontal timeline river**: X-axis is time (window.start to window.end). "
    "Each tag is a colored stream/ribbon whose thickness represents relative presence in that period. "
    "Growing tags (from growing[]) should visibly widen toward the right; "
    "cooling tags (from cooling[]) should taper off. Steady tags are even-width ribbons. "
    "If focus_shift is present, show a small callout: 'before' tag on the left, "
    "'now' tag on the right, connected by a gentle arrow. "
    "Style: smooth curves (like a streamgraph), muted warm colors, no axis numbers — "
    "use month labels only. Tags shown as inline labels on their ribbons. "
    "Never show raw counts, ratios, or 'per day' metrics in the UI. "
    "Tone: frame as personal evolution — 'Your curiosity is shifting toward...' "
    "If cold_start is true, show a gentle empty state: "
    "'This is your first reflection — it will get richer as your vault grows.'"
)

BLINDSPOTS_HINT = (
    "ALWAYS generate a React artifact visualization. "
    "Render an **island archipelago map**: each cluster from sparse_connections "
    "is an island (rounded blob) sized by member_count, labeled with its top tags. "
    "Connected clusters sit close together; isolated ones drift to edges. "
    "For each entry in suggested_bridges, draw a dashed arc between the two islands "
    "with shared_tags as a small label on the arc. "
    "Orphan tags (from orphan_tags[]) appear as small floating dots around the edges. "
    "Show coverage_score as a subtle progress ring in a corner (not a number). "
    "Style: hand-drawn / organic feel, soft earth-tone palette, island shapes slightly irregular. "
    "Tone: frame bridges as opportunities — 'These two interests might connect through...' "
    "Highlight the single most surprising bridge prominently."
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCAN_DIRS = ("captures", "notes", "topics")


def _today_str() -> str:
    """Return today's date as YYYY-MM-DD. Extracted for easy mocking."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class _ReflectCache:
    """Session-level cache living inside the register closure."""

    def __init__(self) -> None:
        self.scan_result: list[dict] | None = None
        self.scan_date: str | None = None
        self.scan_write_gen: int = -1
        self.today_snapshot: dict | None = None
        self.clusters: ClusterData | None = None
        self.clusters_gen: int = -1

    def invalidate_if_stale(self, today: str, write_gen: int) -> None:
        if self.scan_date != today or self.scan_write_gen != write_gen:
            self.__init__()


def _scan_all_files(
    adapter: StorageAdapter, cache: _ReflectCache
) -> list[dict]:
    """Scan captures/, notes/, topics/ and parse frontmatter metadata.

    Returns list of dicts with keys: path, title, tags, created, type.
    Skips files with missing/corrupt frontmatter or missing created field.
    Results are cached per day.
    """
    today = _today_str()
    wg = adapter.write_generation
    if cache.scan_result is not None and cache.scan_date == today and cache.scan_write_gen == wg:
        return cache.scan_result

    results: list[dict] = []
    for d in SCAN_DIRS:
        for path in adapter.list_files(d):
            try:
                content = adapter.read_file(path)
                post = frontmatter.loads(content)
                meta = post.metadata
                created = meta.get("created")
                if not created:
                    logger.warning("Skipping %s: missing 'created' field", path)
                    continue
                results.append({
                    "path": path,
                    "title": meta.get("title", ""),
                    "tags": list(meta.get("tags") or []),
                    "created": str(created),
                    "type": d.rstrip("s"),  # captures -> capture
                })
            except Exception as e:
                logger.warning("Skipping %s during scan: %s", path, e)
                continue

    cache.scan_result = results
    cache.scan_date = today
    cache.scan_write_gen = adapter.write_generation
    return results


def _compute_tag_counts(file_metas: list[dict]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for fm in file_metas:
        counter.update(fm["tags"])
    return dict(counter.most_common())


def _compute_tag_cooccurrence(file_metas: list[dict]) -> list[list]:
    """File-level co-occurrence: two tags appearing in the same file."""
    pair_counts: Counter[tuple[str, str]] = Counter()
    for fm in file_metas:
        tags = sorted(set(fm["tags"]))
        for a, b in combinations(tags, 2):
            pair_counts[(a, b)] += 1
    return [[a, b, c] for (a, b), c in pair_counts.most_common()]


def _build_topic_timeline(file_metas: list[dict]) -> list[dict]:
    entries = [
        {
            "date": fm["created"][:10],
            "path": fm["path"],
            "title": fm["title"],
            "tags": fm["tags"],
            "type": fm["type"],
        }
        for fm in file_metas
    ]
    entries.sort(key=lambda e: e["date"])
    return entries


def _build_graph_summary(vault_graph: VaultGraph) -> dict:
    vault_graph._ensure_loaded()
    g = vault_graph.g
    return {
        "total_nodes": g.number_of_nodes(),
        "total_edges": g.number_of_edges(),
        "avg_degree": round(
            sum(d for _, d in g.degree()) / max(g.number_of_nodes(), 1), 2
        ),
    }


def _save_snapshot(adapter: StorageAdapter, data: dict, date_str: str) -> None:
    """Persist snapshot data to .brain/snapshots/. Failures are logged, not raised."""
    path = f"{SNAPSHOTS_DIR}/{date_str}.json"
    try:
        adapter.write_file(path, json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.warning("Failed to persist snapshot %s: %s", path, e)


def _load_snapshot(adapter: StorageAdapter, date_str: str) -> dict | None:
    """Load a snapshot by date. Returns None on missing/corrupt files."""
    path = f"{SNAPSHOTS_DIR}/{date_str}.json"
    try:
        content = adapter.read_file(path)
        return json.loads(content)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, Exception) as e:
        logger.warning("Skipping corrupt snapshot %s: %s", path, e)
        return None


def _list_snapshot_dates(adapter: StorageAdapter) -> list[str]:
    """List available snapshot dates by scanning .brain/snapshots/*.json."""
    files = adapter.list_files(SNAPSHOTS_DIR, extension=".json")
    dates: list[str] = []
    for f in files:
        # f looks like ".brain/snapshots/2026-03-28.json"
        name = f.rsplit("/", 1)[-1]
        if name.endswith(".json"):
            dates.append(name[:-5])
    return sorted(dates)


def _ensure_today_snapshot(
    adapter: StorageAdapter,
    vault_graph: VaultGraph,
    cache: _ReflectCache,
) -> dict:
    """Return today's snapshot data, computing and caching if needed."""
    if cache.today_snapshot is not None:
        return cache.today_snapshot

    today = _today_str()
    file_metas = _scan_all_files(adapter, cache)

    tag_counts = _compute_tag_counts(file_metas)
    tag_cooccurrence = _compute_tag_cooccurrence(file_metas)
    timeline = _build_topic_timeline(file_metas)
    graph_summary = _build_graph_summary(vault_graph)

    dates = [fm["created"][:10] for fm in file_metas if fm["created"]]
    file_count = Counter(fm["type"] for fm in file_metas)

    data = {
        "snapshot_id": today,
        "created": datetime.now(timezone.utc).isoformat(),
        "tag_counts": tag_counts,
        "tag_cooccurrence": tag_cooccurrence,
        "topic_timeline": timeline,
        "graph_summary": graph_summary,
        "date_range": [min(dates) if dates else today, today],
        "file_count": dict(file_count),
    }

    _save_snapshot(adapter, data, today)
    cache.today_snapshot = data
    # Absorb the write_gen bump from _save_snapshot — it's internal metadata,
    # not a content change that should invalidate the scan cache.
    cache.scan_write_gen = adapter.write_generation
    return data


def _cooccurrence_to_nx(cooc_list: list) -> nx.Graph:
    """Build a weighted undirected graph from co-occurrence triples."""
    g = nx.Graph()
    for item in cooc_list:
        a, b, w = item[0], item[1], item[2]
        g.add_edge(a, b, weight=w)
    return g


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_reflect_tools(
    mcp, adapter: StorageAdapter, vault_graph: VaultGraph | None = None
) -> None:
    if vault_graph is None:
        vault_graph = VaultGraph(adapter)

    cache = _ReflectCache()

    @mcp.tool()
    def vault_reflect(
        action: str,
        since_days: int = 30,
        limit: int = 50,
    ) -> dict:
        """Reflect on your knowledge vault — what you've been thinking about,
        how your interests are evolving, and what connections you might be missing.

        Actions:
          snapshot:   What does my knowledge look like right now? Topics, connections,
                      and what's been on my mind. Auto-saved to .brain/snapshots/.
          drift:      How has my focus shifted? What's growing, what's cooling down,
                      and where my curiosity is heading. params: since_days (default 30)
          blindspots: What am I missing? Isolated ideas that could be connected,
                      and surprising bridges between clusters. params: limit (default 50)
        """
        today = _today_str()
        cache.invalidate_if_stale(today, adapter.write_generation)

        if action == "snapshot":
            return _handle_snapshot(adapter, vault_graph, cache)
        elif action == "drift":
            return _handle_drift(adapter, vault_graph, cache, since_days)
        elif action == "blindspots":
            return _handle_blindspots(vault_graph, cache, limit)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}


def _handle_snapshot(
    adapter: StorageAdapter, vault_graph: VaultGraph, cache: _ReflectCache
) -> dict:
    data = _ensure_today_snapshot(adapter, vault_graph, cache)
    return {
        "status": "success",
        "data": data,
        "_visualization_hint": SNAPSHOT_HINT,
    }


def _handle_drift(
    adapter: StorageAdapter,
    vault_graph: VaultGraph,
    cache: _ReflectCache,
    since_days: int,
) -> dict:
    # Ensure today's snapshot exists
    today_data = _ensure_today_snapshot(adapter, vault_graph, cache)
    today = _today_str()

    # Load historical snapshots
    all_dates = _list_snapshot_dates(adapter)
    # Exclude today from history
    history_dates = [d for d in all_dates if d != today]

    # Partition: recent vs historical
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%d")

    cold_start = len(history_dates) == 0

    if cold_start:
        # Fall back to frontmatter created timestamps
        file_metas = _scan_all_files(adapter, cache)
        recent_metas = [fm for fm in file_metas if fm["created"][:10] >= cutoff]
        historical_metas = [fm for fm in file_metas if fm["created"][:10] < cutoff]
        recent_counts = _compute_tag_counts(recent_metas)
        historical_counts = _compute_tag_counts(historical_metas)
        recent_cooc = _compute_tag_cooccurrence(recent_metas)
        historical_cooc = _compute_tag_cooccurrence(historical_metas)
        snapshots_used = 0
    else:
        # Use snapshot history
        recent_snapshots = [d for d in history_dates if d >= cutoff]
        historical_snapshots = [d for d in history_dates if d < cutoff]

        # Aggregate tag counts from snapshots
        recent_counts: Counter[str] = Counter()
        for d in recent_snapshots:
            snap = _load_snapshot(adapter, d)
            if snap and "tag_counts" in snap:
                recent_counts.update(snap["tag_counts"])

        # Add today's data
        recent_counts.update(today_data.get("tag_counts", {}))

        historical_counts: Counter[str] = Counter()
        for d in historical_snapshots:
            snap = _load_snapshot(adapter, d)
            if snap and "tag_counts" in snap:
                historical_counts.update(snap["tag_counts"])

        # For center_shift, use today's cooccurrence vs oldest available
        recent_cooc = today_data.get("tag_cooccurrence", [])
        oldest_snap = _load_snapshot(adapter, historical_snapshots[0]) if historical_snapshots else None
        historical_cooc = oldest_snap.get("tag_cooccurrence", []) if oldest_snap else []

        snapshots_used = len(recent_snapshots) + len(historical_snapshots) + 1

    # Compute drift ratios
    all_tags = set(recent_counts.keys()) | set(historical_counts.keys())
    total_recent_days = max(since_days, 1)
    # Estimate historical days
    if history_dates:
        hist_span = (
            datetime.strptime(history_dates[-1], "%Y-%m-%d")
            - datetime.strptime(history_dates[0], "%Y-%m-%d")
        ).days
        total_hist_days = max(hist_span, 1)
    else:
        total_hist_days = max(since_days, 1)

    growing, cooling, steady = [], [], []
    for tag in all_tags:
        recent_freq = recent_counts.get(tag, 0) / total_recent_days
        hist_freq = historical_counts.get(tag, 0) / total_hist_days
        ratio = recent_freq / max(hist_freq, 0.01)
        entry = {
            "tag": tag,
            "recent_count": recent_counts.get(tag, 0),
            "historical_count": historical_counts.get(tag, 0),
        }
        if ratio > 2.0:
            growing.append(entry)
        elif ratio < 0.3:
            cooling.append(entry)
        else:
            steady.append(entry)

    growing.sort(key=lambda e: e["recent_count"], reverse=True)
    cooling.sort(key=lambda e: e["historical_count"], reverse=True)
    steady.sort(key=lambda e: e["recent_count"], reverse=True)

    # Focus shift: what was central before vs now
    focus_shift = {}
    if recent_cooc and historical_cooc:
        recent_g = _cooccurrence_to_nx(recent_cooc)
        hist_g = _cooccurrence_to_nx(historical_cooc)
        recent_cent = nx.degree_centrality(recent_g) if recent_g.number_of_nodes() > 0 else {}
        hist_cent = nx.degree_centrality(hist_g) if hist_g.number_of_nodes() > 0 else {}
        if hist_cent and recent_cent:
            from_tag = max(hist_cent, key=hist_cent.get)
            to_tag = max(recent_cent, key=recent_cent.get)
            focus_shift = {"before": from_tag, "now": to_tag}

    window = {"start": cutoff, "end": today}

    return {
        "status": "success",
        "data": {
            "window": window,
            "growing": growing,
            "cooling": cooling,
            "steady": steady,
            "focus_shift": focus_shift,
            "snapshots_used": snapshots_used,
            "cold_start": cold_start,
        },
        "_visualization_hint": DRIFT_HINT,
    }


def _handle_blindspots(
    vault_graph: VaultGraph, cache: _ReflectCache, limit: int
) -> dict:
    vault_graph._ensure_loaded()

    # Get clusters (cached by generation)
    if cache.clusters is None or cache.clusters_gen != vault_graph.generation:
        cache.clusters = compute_clusters(vault_graph)
        cache.clusters_gen = vault_graph.generation

    cluster_data = cache.clusters

    # Get orphans from graph
    orphan_result = vault_graph.get_orphans(limit=limit)
    orphan_paths = [o["path"] for o in orphan_result.get("orphans", [])]

    # Collect all tags from graph nodes
    all_tags: set[str] = set()
    orphan_tags_set: set[str] = set()
    node_tags: dict[str, list[str]] = {}
    for node_path, node_data in vault_graph.g.nodes(data=True):
        tags = node_data.get("tags", [])
        all_tags.update(tags)
        node_tags[node_path] = tags
        if node_path in orphan_paths:
            orphan_tags_set.update(tags)

    # Orphan tags: tags that only appear on orphan nodes
    non_orphan_tags: set[str] = set()
    for node_path, tags in node_tags.items():
        if node_path not in orphan_paths:
            non_orphan_tags.update(tags)
    truly_orphan_tags = orphan_tags_set - non_orphan_tags

    orphan_tags_list = []
    for tag in sorted(truly_orphan_tags):
        orphan_tags_list.append({
            "tag": tag,
            "count": sum(1 for fm in node_tags.values() if tag in fm),
            "never_cooccurs_with": sorted(non_orphan_tags)[:5],
        })

    # Sparse connections: clusters with low internal density
    sparse_connections = []
    for cluster in cluster_data.clusters:
        members = cluster.members
        if len(members) < 2:
            continue
        subgraph = vault_graph.g.subgraph(members)
        internal_edges = subgraph.number_of_edges()
        max_edges = len(members) * (len(members) - 1) / 2
        density = internal_edges / max(max_edges, 1)
        if density < 0.2:
            # Find tags in this cluster
            cluster_tags: set[str] = set()
            for m in members:
                cluster_tags.update(node_tags.get(m, []))
            sparse_connections.append({
                "cluster_label": cluster.label,
                "member_count": len(members),
                "density": round(density, 3),
                "tags": sorted(cluster_tags),
            })

    # Suggested bridges: clusters sharing tags but no direct wikilink edges
    suggested_bridges = []
    clusters_list = [c for c in cluster_data.clusters if len(c.members) >= 2]
    checked = 0
    for i, c1 in enumerate(clusters_list):
        for c2 in clusters_list[i + 1:]:
            if checked >= 20:
                break
            checked += 1
            # Collect tags per cluster
            tags1: set[str] = set()
            for m in c1.members:
                tags1.update(node_tags.get(m, []))
            tags2: set[str] = set()
            for m in c2.members:
                tags2.update(node_tags.get(m, []))

            shared_tags = tags1 & tags2
            if not shared_tags:
                continue

            # Check if any direct edge exists between clusters
            has_edge = False
            for m1 in c1.members:
                for m2 in c2.members:
                    if vault_graph.g.has_edge(m1, m2) or vault_graph.g.has_edge(m2, m1):
                        has_edge = True
                        break
                if has_edge:
                    break

            if not has_edge:
                suggested_bridges.append({
                    "from_cluster": {"label": c1.label, "tags": sorted(tags1)[:5]},
                    "to_cluster": {"label": c2.label, "tags": sorted(tags2)[:5]},
                    "shared_tags": sorted(shared_tags),
                    "reason": (
                        f"Both clusters contain notes tagged with "
                        f"{', '.join(sorted(shared_tags)[:3])} but have no direct "
                        f"shared wikilinks"
                    ),
                })
        if checked >= 20:
            break

    total_unique_tags = len(all_tags)
    coverage_score = 1 - (len(truly_orphan_tags) / max(total_unique_tags, 1))

    return {
        "status": "success",
        "data": {
            "orphan_tags": orphan_tags_list,
            "sparse_connections": sparse_connections,
            "suggested_bridges": suggested_bridges,
            "coverage_score": round(coverage_score, 3),
        },
        "_visualization_hint": BLINDSPOTS_HINT,
    }
