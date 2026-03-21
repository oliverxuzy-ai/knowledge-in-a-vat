---
aliases: []
created: '2025-07-17T06:28:50+00:00'
promoted_to:
- notes/devops-and-deployment-practices.md
source: conversation
status: promoted
tags:
- programming
title: Graceful Degradation Beats Hard Failure
updated: '2025-07-17T06:28:50+00:00'
---

When a non-critical dependency fails, serve cached or default data rather than returning an error. Users prefer partial results to no results.