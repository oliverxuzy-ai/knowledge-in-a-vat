---
aliases: []
created: '2025-01-06T23:17:51+00:00'
promoted_to:
- notes/research-finding-premature-optimization-is.md
source: flash
status: promoted
tags:
- programming
title: 'Lesson Learned: Database Indexes Are Not Free'
updated: '2025-01-06T23:17:51+00:00'
---

Experience teaches that each index speeds reads but slows writes and consumes storage. Profile query patterns before adding indexes; remove unused ones.