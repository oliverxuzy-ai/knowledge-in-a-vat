---
aliases:
- Database
- Data Architecture
confidence: 0.8
created: '2026-03-21T18:31:06.983859+00:00'
domain: programming
promoted_from:
- captures/2026-01-02-231153-key-insight-dependency-injection-makes.md
- captures/2026-02-02-224938-lesson-learned-twelve-factor-app.md
- captures/2025-10-25-085523-research-finding-code-review-is.md
status: note
tags:
- programming
title: Database and Data Architecture
topics:
- topics/software-architecture-and-design.md
- topics/software-testing-and-quality.md
updated: '2026-03-21T18:31:06.983859+00:00'
---

# Summary

[[Database and Data Architecture]] decisions — indexes, migrations, event sourcing — have long-term implications for system performance and auditability.

# Notes

1. **[[Database and Data Architecture]] indexes speed reads but slow writes**: Database indexes speed reads but slow writes — profile before adding

2. **Every migration should have a corresponding rollba**: Every migration should have a corresponding rollback strategy

3. **Event sourcing stores immutable events for complet**: Event sourcing stores immutable events for complete audit trail and time-travel debugging

# Links