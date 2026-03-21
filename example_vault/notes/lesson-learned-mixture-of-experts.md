---
aliases: []
confidence: 0.77
created: '2026-03-21T18:31:07.009231+00:00'
domain: ai
promoted_from:
- captures/2026-02-24-135504-lesson-learned-mixture-of-experts.md
- captures/2025-12-10-081803-practical-application-long-context-models.md
- captures/2026-01-05-215205-research-finding-prompt-chaining-breaks.md
- captures/2025-01-17-024323-research-finding-embedding-models-capture.md
status: note
tags:
- ai
- llm
- prompt-engineering
title: 'Lesson Learned: Mixture of Experts Reduces Compute'
topics:
- topics/ai-assisted-development.md
- topics/prompt-engineering-mastery.md
- topics/large-language-model-architecture.md
updated: '2026-03-21T18:31:07.009231+00:00'
---

# Summary

Synthesized insights on ai combining 4 related observations.

# Notes

1. **Experience teaches that moE architectures activate**: Experience teaches that moE architectures activate only a subset of parameters per token, achieving larger model capacit

2. **In practice, models with 100K+ token context windo**: In practice, models with 100K+ token context windows can process entire books, eliminating the need for complex chunking

3. **Studies show that decomposing a complex prompt int**: Studies show that decomposing a complex prompt into a chain of simpler prompts yields better results than one monolithic

4. **Studies show that text embeddings map sentences to**: Studies show that text embeddings map sentences to high-dimensional vectors where semantic similarity correlates with co

# Links