# Page 13 Review Prompt Assets

These files are sample inputs for the custom Tier 3 review workflow.

- `scout.md`: scout-only instructions for the run
- `specialists_common.md`: shared specialist block for the run
- `specialists.json`: custom specialist set with per-specialist instructions

Use them with:

```bash
export STRUAI_REVIEW_SCOUT_FILE=/absolute/path/to/examples/prompts/page13_review/scout.md
export STRUAI_REVIEW_SPECIALISTS_COMMON_FILE=/absolute/path/to/examples/prompts/page13_review/specialists_common.md
export STRUAI_REVIEW_SPECIALISTS_FILE=/absolute/path/to/examples/prompts/page13_review/specialists.json
```
