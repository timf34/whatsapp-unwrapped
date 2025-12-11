# High-Value Stats Usage Guide

Quick reference for using the new statistics in your Vita gift site or other visualizations.

## Accessing the Statistics

All statistics are available in the JSON output at `output/statistics.json`:

```python
import json

with open('output/statistics.json', 'r', encoding='utf-8') as f:
    stats = json.load(f)

basic = stats['basic']
temporal = stats['temporal']
content = stats['content']
interaction = stats['interaction']
```

## Fun Fact Templates

### 1. Activity & Consistency

```python
days_active = temporal['days_active']
longest_streak = temporal['longest_streak_days']
avg_per_active_day = temporal['avg_messages_per_active_day']

# "You've messaged on {days_active} different days, with a longest streak of {longest_streak} days in a row! 🔥"
# "When you chat, you average {avg_per_active_day} messages per day!"
```

### 2. Peak Times

```python
most_active_date = temporal['most_active_date']
busiest_hour = temporal['busiest_hour']
messages_on_best_day = temporal['messages_by_date'][most_active_date]

# "Your chattiest day was {most_active_date} with {messages_on_best_day} messages!"
# "You're both night owls 🦉 - peak hour is {busiest_hour}:00"
```

### 3. Media & Links

```python
media_count = basic['media_count']
deleted_count = basic['deleted_count']
link_count = basic['link_count']

tim_media_ratio = basic['media_ratio_per_person']['Tim Farrelly']
vita_media_ratio = basic['media_ratio_per_person']['Vita']

# "{media_count} photos and videos shared! 📸"
# "{deleted_count} messages deleted... what were they? 👀"
# "Tim shares media in {tim_media_ratio*100:.1f}% of messages, Vita in {vita_media_ratio*100:.1f}%"
```

### 4. Response Speed

```python
buckets_tim = interaction['response_time_buckets']['Tim Farrelly']
buckets_vita = interaction['response_time_buckets']['Vita']

tim_fast = buckets_tim['<5m']
tim_total = sum(buckets_tim.values())
tim_fast_pct = tim_fast / tim_total * 100

vita_fast = buckets_vita['<5m']
vita_total = sum(buckets_vita.values())
vita_fast_pct = vita_fast / vita_total * 100

# "Tim replies within 5 minutes {tim_fast_pct:.0f}% of the time ⚡"
# "Vita replies within 5 minutes {vita_fast_pct:.0f}% of the time ⚡"
```

### 5. Longest Messages

```python
longest = content['longest_messages'][0]  # Top message

sender = longest['sender']
word_count = longest['word_count']
timestamp = longest['timestamp']

# "{sender} once sent a {word_count}-word essay! 📚"
# "Longest message: {word_count} words on {timestamp}"
```

## Visualization Ideas

### 1. Streak Calendar Heatmap

```python
import matplotlib.pyplot as plt
import pandas as pd

# Convert messages_by_date to DataFrame
df = pd.DataFrame([
    {'date': date, 'count': count}
    for date, count in temporal['messages_by_date'].items()
])
df['date'] = pd.to_datetime(df['date'])

# Create heatmap with streak highlighting
# ... (use calplot or similar library)
```

### 2. Response Time Distribution

```python
import matplotlib.pyplot as plt

persons = list(interaction['response_time_buckets'].keys())
buckets = ['<5m', '5-30m', '30-120m', '>2h']

data = []
for person in persons:
    data.append([
        interaction['response_time_buckets'][person][bucket]
        for bucket in buckets
    ])

# Create stacked bar chart
fig, ax = plt.subplots()
# ... stacked bar implementation
```

### 3. Quote Cards (Longest Messages)

```html
<!-- For web display -->
<div class="quote-card">
  <div class="word-count">{word_count} words</div>
  <div class="sender">{sender}</div>
  <div class="preview">{text[:200]}...</div>
  <div class="timestamp">{timestamp}</div>
</div>
```

### 4. Media Usage Comparison

```python
import matplotlib.pyplot as plt

persons = list(basic['media_ratio_per_person'].keys())
media_ratios = [basic['media_ratio_per_person'][p] * 100 for p in persons]
link_ratios = [basic['link_ratio_per_person'][p] * 100 for p in persons]

# Grouped bar chart
fig, ax = plt.subplots()
x = range(len(persons))
width = 0.35
ax.bar([i - width/2 for i in x], media_ratios, width, label='Media %')
ax.bar([i + width/2 for i in x], link_ratios, width, label='Links %')
```

## Web Dashboard Copy Examples

### Hero Section
```
🎉 You've been chatting for {days_active} days
with a {longest_streak_days}-day streak!
```

### Stats Grid
```
┌─────────────────────┬─────────────────────┐
│   📸 {media_count}  │   🔗 {link_count}   │
│   Media Shared      │   Links Shared      │
├─────────────────────┼─────────────────────┤
│   ⚡ {fast_pct}%    │   🌙 Hour {hour}    │
│   Fast Replies      │   Peak Time         │
└─────────────────────┴─────────────────────┘
```

### Fun Facts Carousel
```
Slide 1: "Your chattiest day: {most_active_date} with {count} messages!"
Slide 2: "Tim sends {tim_media_ratio*100:.0f}% media, Vita {vita_media_ratio*100:.0f}%"
Slide 3: "Response time? You're both quick! 65% under 30 minutes ⚡"
Slide 4: "Only {deleted_count} deleted messages - you're confident! 💪"
Slide 5: "Longest message: {word_count} words. Someone had things to say! 📚"
```

## API Integration

If building a web API for the gift site:

```python
from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route('/api/stats')
def get_stats():
    with open('output/statistics.json', 'r', encoding='utf-8') as f:
        stats = json.load(f)
    return jsonify(stats)

@app.route('/api/fun-facts')
def get_fun_facts():
    with open('output/statistics.json', 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    temporal = stats['temporal']
    basic = stats['basic']
    
    return jsonify({
        'streak': {
            'days': temporal['longest_streak_days'],
            'fact': f"Longest streak: {temporal['longest_streak_days']} days! 🔥"
        },
        'deleted': {
            'count': basic['deleted_count'],
            'fact': f"Only {basic['deleted_count']} deleted messages - confident chatters! 💪"
        },
        # ... more facts
    })
```

## React Component Example

```jsx
function StatsCard({ stats }) {
  const { temporal, basic, interaction } = stats;
  
  return (
    <div className="stats-card">
      <h2>Your Chat Journey</h2>
      <div className="stat">
        <span className="number">{temporal.days_active}</span>
        <span className="label">Active Days</span>
      </div>
      <div className="stat">
        <span className="number">{temporal.longest_streak_days}</span>
        <span className="label">Longest Streak</span>
      </div>
      <div className="stat">
        <span className="number">{basic.media_count}</span>
        <span className="label">Media Shared</span>
      </div>
    </div>
  );
}
```

---

All these statistics are now live and ready to power your Vita gift site! 🎁

