# Quick Reference - New Statistics

Fast lookup for all the new statistics added to WhatsApp Unwrapped.

## Core Stats (in JSON export)

### BasicStats
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| `media_count` | int | Total media messages | 2451 |
| `deleted_count` | int | Total deleted messages | 57 |
| `link_count` | int | Total link messages | 323 |
| `links_per_person` | dict | Links per person | `{"Tim": 302, "Vita": 21}` |
| `deleted_per_person` | dict | Deleted per person | `{"Tim": 27, "Vita": 30}` |
| `media_ratio_per_person` | dict | Media % per person | `{"Tim": 0.118, "Vita": 0.068}` |
| `link_ratio_per_person` | dict | Link % per person | `{"Tim": 0.023, "Vita": 0.002}` |

### TemporalStats
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| `days_active` | int | Days with ≥1 message | 370 |
| `avg_messages_per_day` | float | Total msgs / total days | 61.93 |
| `avg_messages_per_active_day` | float | Total msgs / active days | 71.3 |
| `longest_streak_days` | int | Consecutive active days | 187 |
| `longest_gap_days` | int | Longest inactive period | 18 |
| `most_active_date` | str | Busiest date (YYYY-MM-DD) | "2024-12-27" |
| `busiest_hour` | int | Busiest hour (0-23) | 23 |

### ContentStats
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| `longest_messages` | list | Top 5 longest messages | `[{"sender": "Tim", "word_count": 2621, ...}]` |

### InteractionStats
| Field | Type | Description | Example Value |
|-------|------|-------------|---------------|
| `response_time_buckets` | dict | Bucketed response times | `{"Tim": {"<5m": 725, ...}}` |

**Buckets:** `<5m`, `5-30m`, `30-120m`, `>2h`

---

## Derived Stats (computed on-demand)

### Timeline
```python
derived['timeline']
```
- `total_days` - Days from first to last message
- `percentage_active` - % of days with messages
- `most_active_date_count` - Messages on busiest day
- `first_message_date` - Formatted start date
- `last_message_date` - Formatted end date

### Balance
```python
derived['balance']
```
- `per_person[name]` - Stats per person:
  - `message_percentage` - % of total messages
  - `word_percentage` - % of total words
- `most_talkative` - Person with most messages
- `most_verbose` - Person with most words

### Peak Times
```python
derived['peak_times']
```
- `busiest_hour_formatted` - "11 PM" format
- `busiest_weekday_name` - "Wednesday" etc.
- `busiest_weekday_count` - Messages on that day

### Response Speed
```python
derived['response_speed']
```
- `per_person[name]` - Stats per person:
  - `avg_response_time_formatted` - "34 minutes"
  - `fast_reply_percentage` - % under 5 minutes
  - `response_distribution` - Full bucket breakdown
- `fastest_responder` - Person with lowest avg

### Content Types
```python
derived['content_types']
```
- `per_person[name]` - Stats per person:
  - `media_percentage` - % of messages with media
  - `link_percentage` - % of messages with links

### Emoji Love
```python
derived['emoji_love']
```
- `per_person[name]` - Stats per person:
  - `favorite_emoji` - (emoji, count) tuple
  - `top_emojis` - Top 5 list

---

## Code Snippets

### Get Everything
```python
from output.presentation import compute_derived_stats, get_fun_facts

derived = compute_derived_stats(stats)
facts = get_fun_facts(stats)
```

### Access Specific Stats
```python
# Timeline
days = derived['timeline']['total_days']
streak = derived['timeline']['longest_streak_days']

# Balance
talkative = derived['balance']['most_talkative']

# Speed
fastest = derived['response_speed']['fastest_responder']
fast_pct = derived['response_speed']['per_person'][fastest]['fast_reply_percentage']

# Content
media_total = derived['content_types']['media_count']
```

### Display Copy Templates
```python
# Streak
f"🔥 {streak}-day messaging streak!"

# Activity
f"📅 Active {derived['timeline']['percentage_active']}% of days"

# Response
f"⚡ {fastest} replies within 5 minutes {fast_pct}% of the time"

# Media
f"📸 {media_total} photos and videos shared"

# Peak time
f"🌙 You both chat most at {derived['peak_times']['busiest_hour_formatted']}"
```

---

## File Locations

| What | Where |
|------|-------|
| Core stats models | `models.py` |
| Basic stats computation | `analysis/basic_stats.py` |
| Temporal stats computation | `analysis/temporal_stats.py` |
| Content stats computation | `analysis/content_stats.py` |
| Interaction stats computation | `analysis/interaction_stats.py` |
| **Presentation layer** | `output/presentation.py` |
| JSON export | `output/statistics.json` |

---

## Documentation Files

| File | Contents |
|------|----------|
| `NEW_STATS_SUMMARY.md` | Overview of core stats with examples |
| `STATS_USAGE_GUIDE.md` | How to use core stats for visualizations |
| `PRESENTATION_LAYER_GUIDE.md` | Complete guide to derived stats |
| `IMPLEMENTATION_COMPLETE.md` | Full implementation summary |
| `QUICK_REFERENCE.md` | This file! |

---

## Fun Facts Generator

```python
from output.presentation import get_fun_facts

facts = get_fun_facts(stats)
# Returns list of strings like:
# "📅 You've been chatting for 426 days (86.9% of days active)"
# "🔥 Longest streak: 187 days in a row!"
# "⚡ Vita replies within 5 minutes 31.5% of the time!"
```
