---
aliases: []
created: '2026-01-15T00:00:01+00:00'
promoted_to:
- notes/software-architecture-principles.md
source: conversation
status: promoted
tags:
- programming
title: 'Key Insight: Graceful Degradation Beats Hard Failu'
updated: '2026-01-15T00:00:01+00:00'
---

The key realization is that when a non-critical dependency fails, serve cached or default data rather than returning an error. Users prefer partial results to no results.