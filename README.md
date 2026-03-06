# ☕ Coffee Bean Simple Reflex Agent

A rule-based AI agent that recommends coffee beans from natural language descriptions.

> **Example:** *"cheap chocolatey medium roast from Ethiopia"* → returns matching beans with tasting notes, origin, roast, price, and rating.

---

## Overview

This project implements a **Simple Reflex Agent** — an AI agent that selects actions using condition-action rules, without memory or learning. The agent accepts a short natural language description of desired coffee and returns up to 5 matching beans from a cleaned coffee dataset.

### Agent Pipeline

```
User Input → Sensing → Rule Matching → Action → Response
```

1. **Sensing** — Extract keywords and two-word phrases from user input
2. **Rule Matching** — Apply the first matching rule from a fixed ordered rule set
3. **Action** — Return the bean(s) associated with the matched rule

---

## Rule Set

Rules are evaluated in priority order. The first matching rule fires.

| Priority | Rule | Condition | Action |
|----------|------|-----------|--------|
| 1 | **Bean Name** | Input contains a full bean name | Return all exact-match beans |
| 2 | **Taste Keyword** | Input contains a tasting keyword | Filter by matching tasting notes |
| 3 | **Origin** | Input contains a country/region | Filter by origin field |
| 4 | **Roast** | Input mentions light / medium / dark | Filter by roast group |
| 5 | **Price** | Input mentions a price preference | Filter by price level |
| 6 | **Rating** | Input mentions "best", "top-rated", etc. | Sort by descending rating |
| — | **Fallback** | No keywords matched, or all filters empty | Return 5 random top-rated beans |

The fallback rule ensures the agent always returns a meaningful result rather than an empty response or raw dataset rows.

---

## Keyword Bank

### Tasting Notes
| Category | Keywords |
|----------|----------|
| Chocolate | `dark chocolate`, `milk chocolate`, `chocolate`, `chocolatey` |
| Acidity | `low acidity`, `high acidity`, `acidity` |
| Nuts & Caramel | `caramel`, `nutty`, `hazelnut` |
| Fruit & Berry | `fruit`, `fruity`, `berry`, `dark cherry`, `cherry` |
| Body & Sweetness | `sweet`, `rich`, `syrupy`, `full body`, `medium body`, `light body`, `body` |

### Roast
`light`, `light roast`, `medium`, `medium roast`, `dark`, `dark roast`

### Price
`cheap`, `budget`, `inexpensive`, `medium price`, `mid price`, `expensive`, `premium`

### Rating
`best`, `top`, `top-rated`, `highly rated`

---

## Response Format

Each result returns the following fields:

- **Bean name**
- **Origin**
- **Roast**
- **Price level**
- **Rating**
- **Tasting notes**

Up to **5 beans** are returned per query, unless the user names a specific bean (in which case all exact matches are returned).

---

## Dataset

The agent operates on a cleaned coffee bean dataset with normalized fields for origin, roast group, price level, tasting keywords, and ratings.
