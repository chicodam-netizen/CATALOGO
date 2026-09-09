---
name: apply-fixes-not-just-report
description: When validating stories, apply identified fixes directly to the story files — do not leave them as observations in the validation report
metadata:
  type: feedback
---

When a story validation surfaces required fixes, **write them into the story files themselves** (ACs, Tasks/Subtasks, Dev Notes, Change Log) before handing off. Listing them only in the final validation report is treated as incomplete work.

**Why:** In the first pass over the CATALOGO stories (6.2, 6.3, 1.1, 1.2, 1.3), I marked all five as `Ready` and logged should-fixes in the Change Log as narrative observations. The user pointed out that a story marked `Ready` is what @dev actually reads — anything left only in a chat report is invisible at implementation time and effectively lost.

**How to apply:**
- A verdict of GO with pending fixes is not done. Either apply the fixes or do not mark the story `Ready`.
- Resolve ambiguities decisively. If two ACs appear to conflict, pick the reading, state it as RESOLVED in Dev Notes with the criterion spelled out, and say explicitly that it is not an open question for the executor.
- Promote risks into executable scope (new Tasks/Subtasks), not prose. A risk described in Dev Notes but absent from the task list will not get done.
- Prefer edits that leave AC text intact; when an AC must change (e.g., a path invalidated by a prerequisite story), add a reconciliation note documenting the deliberate divergence from the epic.
- The Change Log is append-only. To close a pendency, append a new version row stating it is RESOLVED rather than rewriting the earlier row.

Related: [[catalogo-epic-story-traceability]]
