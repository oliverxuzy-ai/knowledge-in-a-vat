---
aliases: []
created: '2025-12-25T10:00:43+00:00'
source: conversation
status: capture
tags:
- programming
title: 'Key Insight: Pagination Should Use Cursor Not Offs'
updated: '2025-12-25T10:00:43+00:00'
---

The key realization is that cursor-based pagination is stable under concurrent inserts and performs consistently regardless of page depth, unlike offset-based pagination.