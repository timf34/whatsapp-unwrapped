"""Constants used throughout the application."""

import re

# Timestamp pattern: DD/MM/YYYY, HH:MM
# Example: "10/10/2024, 14:05"
TIMESTAMP_PATTERN = re.compile(r"^(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}) - (.+)$")

# System message patterns (messages without a sender)
SYSTEM_MESSAGE_PATTERNS = [
    re.compile(r"^Messages and calls are end-to-end encrypted", re.IGNORECASE),
    re.compile(r".+ created group .+", re.IGNORECASE),
    re.compile(r".+ added .+", re.IGNORECASE),
    re.compile(r".+ left$", re.IGNORECASE),
    re.compile(r".+ removed .+", re.IGNORECASE),
    re.compile(r".+ changed the subject to .+", re.IGNORECASE),
    re.compile(r".+ changed the group description", re.IGNORECASE),
    re.compile(r".+ changed this group's icon", re.IGNORECASE),
    re.compile(r"^Missed voice call$", re.IGNORECASE),
    re.compile(r"^Missed video call$", re.IGNORECASE),
    re.compile(r".+ joined using this group's invite link", re.IGNORECASE),
    re.compile(r".+ changed their phone number", re.IGNORECASE),
    re.compile(r"^You're now an admin$", re.IGNORECASE),
    re.compile(r".+ is now an admin", re.IGNORECASE),
]

# Deleted message patterns
DELETED_MESSAGE_PATTERNS = [
    re.compile(r"^You deleted this message$", re.IGNORECASE),
    re.compile(r"^This message was deleted$", re.IGNORECASE),
]

# Media placeholder
MEDIA_PLACEHOLDER = "<Media omitted>"

# URL pattern for link detection
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)

# Mention pattern (handles Unicode directional isolates)
# WhatsApp uses U+2068 (FIRST STRONG ISOLATE) and U+2069 (POP DIRECTIONAL ISOLATE)
MENTION_PATTERN = re.compile(r"@[\u2068]?([^\u2069@\s]+)[\u2069]?")
