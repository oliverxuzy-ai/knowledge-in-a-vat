---
aliases: []
created: '2025-04-09T10:57:01+00:00'
source: conversation
status: capture
tags:
- programming
title: 'Lesson Learned: Pagination Should Use Cursor Not O'
updated: '2025-04-09T10:57:01+00:00'
---

Experience teaches that cursor-based pagination is stable under concurrent inserts and performs consistently regardless of page depth, unlike offset-based pagination.