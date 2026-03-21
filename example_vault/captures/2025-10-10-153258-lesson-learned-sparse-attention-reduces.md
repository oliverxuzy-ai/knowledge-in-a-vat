---
aliases: []
created: '2025-10-10T15:32:58+00:00'
promoted_to:
- notes/advanced-prompt-engineering-techniques.md
source: conversation
status: promoted
tags:
- ai
- llm
title: 'Lesson Learned: Sparse Attention Reduces Quadratic'
updated: '2025-10-10T15:32:58+00:00'
---

Experience teaches that attention mechanisms that attend to only a subset of tokens (local + global) reduce memory from O(n^2) to O(n log n).