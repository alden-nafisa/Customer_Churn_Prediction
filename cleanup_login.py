#!/usr/bin/env python3
"""Clean up orphaned login function code."""

import re

file_path = "app_lapisai.py"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove orphaned CSS code between line markers
# The orphaned code starts with indented CSS (lines from 213 onwards)
# and ends before the score_frame function definition

# Remove orphaned CSS block
# Look for the pattern: spaces + --brand-blue-dark: ... ending before def score_frame
pattern = r'\n(\s+--brand-blue-dark.*?)\ndef score_frame'

# Use a more specific pattern to match the orphaned CSS
# We need to find the lines starting with indentation (CSS) and ending before score_frame
pattern = r'\n\s+--brand-blue-dark:[^\n]*\n(?:.*?\n)*?\s+\.login-caption strong,\n\s+\.login-caption b \{[^\}]*\}\n\n\ndef score_frame'

# Actually, let's use a simpler approach - just find the pattern of orphaned CSS and remove it
# The orphaned CSS starts with --brand-blue-dark and ends with .login-caption styles

lines = content.split('\n')
new_lines = []
skip_until_score_frame = False
i = 0

while i < len(lines):
    line = lines[i]
    
    # Check if we've hit the orphaned CSS start (indented --brand-blue-dark)
    if '--brand-blue-dark:' in line and i > 200 and i < 450:
        # Skip until we find def score_frame
        skip_until_score_frame = True
        i += 1
        while i < len(lines) and not lines[i].startswith('def score_frame'):
            i += 1
        # Don't increment i here since we want to process the def score_frame line
        continue
    
    # Add the line
    new_lines.append(line)
    i += 1

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print("✓ Orphaned login CSS code removed successfully")
