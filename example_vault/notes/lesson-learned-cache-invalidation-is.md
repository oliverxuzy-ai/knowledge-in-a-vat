---
aliases: []
confidence: 0.67
created: '2026-03-21T18:31:07.006984+00:00'
domain: programming
promoted_from:
- captures/2026-01-25-180756-lesson-learned-cache-invalidation-is.md
- captures/2025-06-17-120544-lesson-learned-git-hooks-automate.md
- captures/2025-12-19-083157-dependency-injection-makes-code-testable.md
- captures/2025-06-03-153702-practical-application-graceful-degradation-beats.md
status: note
tags:
- programming
title: 'Lesson Learned: Cache Invalidation Is Genuinely Ha'
topics:
- topics/software-architecture-and-design.md
- topics/software-testing-and-quality.md
updated: '2026-03-21T18:31:07.006984+00:00'
---

# Summary

Synthesized insights on programming combining 4 related observations.

# Notes

1. **Experience teaches that most caching bugs come fro**: Experience teaches that most caching bugs come from stale data. Use TTL with cache-aside pattern, and always have a manu

2. **Experience teaches that pre-commit hooks running l**: Experience teaches that pre-commit hooks running linters, formatters, and type checkers catch issues before they enter t

3. **Injecting dependencies rather than hard-coding the**: Injecting dependencies rather than hard-coding them enables easy mocking in tests and flexible swapping of implementatio

4. **In practice, when a non-critical dependency fails,**: In practice, when a non-critical dependency fails, serve cached or default data rather than returning an error. Users pr

# Links