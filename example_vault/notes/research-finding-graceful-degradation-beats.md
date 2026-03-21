---
aliases: []
confidence: 0.71
created: '2026-03-21T18:31:07.041096+00:00'
domain: programming
promoted_from:
- captures/2025-03-22-111516-research-finding-graceful-degradation-beats.md
- captures/2025-03-25-203315-lesson-learned-contract-testing-validates.md
- captures/2025-10-20-143402-premature-optimization-is-still-the.md
- captures/2025-04-28-060259-research-finding-infrastructure-as-code.md
status: note
tags:
- programming
title: 'Research Finding: Graceful Degradation Beats Hard '
topics:
- topics/software-architecture-and-design.md
- topics/software-testing-and-quality.md
updated: '2026-03-21T18:31:07.041096+00:00'
---

# Summary

Synthesized insights on programming combining 4 related observations.

# Notes

1. **Studies show that when a non-critical dependency f**: Studies show that when a non-critical dependency fails, serve cached or default data rather than returning an error. Use

2. **Experience teaches that consumer-driven contracts **: Experience teaches that consumer-driven contracts verify that service changes don't break callers, without the fragility

3. **Profile before optimizing. Most performance assump**: Profile before optimizing. Most performance assumptions are wrong. The hot path is usually not where you expect it to be

4. **Studies show that defining infrastructure in versi**: Studies show that defining infrastructure in version-controlled code ensures environments are reproducible, auditable, a

# Links