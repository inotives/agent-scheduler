# Market Close Summary

Generate a markdown market-close report for the assets and market close date supplied by the caller.

## Inputs

The caller prompt provides:

- `assets`: one or more ticker symbols
- `market_close_date`: the market session date to summarize

## Output

Create the report as markdown in this repository:

```text
outputs/market-close-summary/<market_close_date>/summary.md
```

For example, for `market_close_date` `2026-05-26`, write:

```text
outputs/market-close-summary/2026-05-26/summary.md
```

## Report Structure

Use this markdown structure:

```markdown
# Market Close Summary - <market_close_date>

## Assets

- <asset>

## Executive Summary

<concise summary>

## Per-Asset Notes

### <asset>

- Closing context
- Notable drivers
- Watch items for the next session

## Sources And Assumptions

- List any sources used.
- State when data was unavailable or inferred.
```

## Completion

After the markdown report is written, follow the caller's completion-signal instruction exactly.
