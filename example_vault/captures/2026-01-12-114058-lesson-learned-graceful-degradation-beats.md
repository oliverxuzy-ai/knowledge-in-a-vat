---
aliases: []
created: '2026-01-12T11:40:58+00:00'
promoted_to:
- notes/observability-and-operational-excellence.md
source: conversation
status: promoted
tags:
- programming
title: 'Lesson Learned: Graceful Degradation Beats Hard Fa'
updated: '2026-01-12T11:40:58+00:00'
---

Experience teaches that when a non-critical dependency fails, serve cached or default data rather than returning an error. Users prefer partial results to no results.