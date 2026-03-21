---
aliases: []
confidence: 0.8
created: '2026-03-21T18:31:07.106881+00:00'
domain: ai
promoted_from:
- captures/2025-05-13-004329-temperature-controls-output-randomness.md
- captures/2025-11-11-142058-practical-application-kv-cache-optimization.md
- captures/2025-08-29-230819-lesson-learned-chain-of-thought.md
- captures/2025-11-05-095635-practical-application-embedding-models-capture.md
status: note
tags:
- ai
- llm
- prompt-engineering
title: Temperature Controls Output Randomness
topics:
- topics/ai-assisted-development.md
- topics/prompt-engineering-mastery.md
- topics/large-language-model-architecture.md
updated: '2026-03-21T18:31:07.106881+00:00'
---

# Summary

Synthesized insights on ai combining 4 related observations.

# Notes

1. **Setting temperature to 0 makes LLM output determin**: Setting temperature to 0 makes LLM output deterministic. Higher values increase creativity but risk incoherence above 1.

2. **In practice, caching key-value pairs from previous**: In practice, caching key-value pairs from previous tokens avoids redundant computation during autoregressive generation,

3. **Experience teaches that asking a model to think st**: Experience teaches that asking a model to think step by step before answering improves accuracy on math and logic tasks 

4. **In practice, text embeddings map sentences to high**: In practice, text embeddings map sentences to high-dimensional vectors where semantic similarity correlates with cosine 

# Links