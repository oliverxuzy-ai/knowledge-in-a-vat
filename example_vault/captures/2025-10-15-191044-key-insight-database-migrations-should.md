---
aliases: []
created: '2025-10-15T19:10:44+00:00'
promoted_to:
- notes/lesson-learned-database-migrations-should.md
source: conversation
status: promoted
tags:
- programming
title: 'Key Insight: Database Migrations Should Be Reversi'
updated: '2025-10-15T19:10:44+00:00'
---

The key realization is that every migration should have a corresponding rollback. Irreversible migrations (dropping columns) need careful data backup strategies.