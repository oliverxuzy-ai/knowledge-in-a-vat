---
aliases: []
created: '2025-06-03T15:37:02+00:00'
promoted_to:
- notes/lesson-learned-cache-invalidation-is.md
source: conversation
status: promoted
tags:
- programming
title: 'Practical Application: Graceful Degradation Beats '
updated: '2025-06-03T15:37:02+00:00'
---

In practice, when a non-critical dependency fails, serve cached or default data rather than returning an error. Users prefer partial results to no results.