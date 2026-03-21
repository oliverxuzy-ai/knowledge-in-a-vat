---
aliases:
- API Design
- System Design
confidence: 0.85
created: '2026-03-21T18:31:06.978674+00:00'
domain: programming
promoted_from:
- captures/2025-05-15-181522-lesson-learned-dependency-injection-makes.md
- captures/2025-07-01-095510-practical-application-dependency-injection-makes.md
- captures/2025-03-02-112751-key-insight-graph-databases-model.md
status: note
tags:
- programming
title: API and System Design Patterns
topics:
- topics/software-architecture-and-design.md
- topics/software-testing-and-quality.md
updated: '2026-03-21T18:31:06.978674+00:00'
---

# Summary

Well-designed APIs follow conventions, use cursor-based pagination, and separate read/write models for high-throughput systems.

# Notes

1. **RESTful APIs should use standard HTTP methods, sta**: RESTful APIs should use standard HTTP methods, status codes, and naming conventions

2. **Cursor-based pagination is stable under concurrent**: Cursor-based pagination is stable under concurrent inserts unlike offset-based

3. **CQRS separates read and write models for independe**: CQRS separates read and write models for independent optimization

# Links