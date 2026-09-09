---
name: catalogo-epic-story-traceability
description: CATALOGO stories copy ACs literally from docs/prd/epic-*.md, so epic Risk Mitigation sections must be checked for requirements that never got transposed
metadata:
  type: project
---

In the CATALOGO (Data Catalog & Profiler) project, stories under `docs/stories/` copy their Acceptance Criteria **literally** from the epics in `docs/prd/`. Requirements living outside the epic's numbered AC list — especially the **Risk Mitigation**, **Rollback Plan**, and **Compatibility Requirements** sections — are routinely dropped during story drafting.

**Why:** Story 1.1 inherited "migration verified by row count" from Epic 1's Risk Mitigation but silently dropped the paired "manual backup of the file before execution" from the same sentence. Row counting only *detects* data loss after the fact; the backup is what makes it *recoverable*. The half that protected against irreversible loss of a consultant's real client glossary was the half that got lost.

**How to apply:**
- When validating any CATALOGO story, read the full source epic, not just its AC list. Cross-check Risk Mitigation / Rollback Plan / Compatibility Requirements against the story's ACs and Tasks.
- Literal AC copying also freezes assumptions in time: an AC can reference a path or state that a prerequisite story invalidates (Story 1.2 AC3 cited `metadata.db` in the project root, which Story 1.1 relocates to `data/workspaces/{slug}/`). Verify AC references against the state *after* prerequisite stories, following the execution order in `docs/prd/README.md` §3.
- Adding an AC sourced from the epic body is not invention (Constitution Article IV is satisfied) — cite the epic section in a note so traceability survives.

Related: [[apply-fixes-not-just-report]]
