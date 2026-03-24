"""Shared state and constants for MyVNKey."""

# Mutable shared state
vietnamese_mode = True
use_clipboard_mode = False

# Characters that break a word (reset the buffer)
WORD_BREAK_CHARS = set(' \t\n\r,.;:!?/\\()[]{}<>@#$%^&*-+=~`\'"0123456789')
