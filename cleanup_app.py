#!/usr/bin/env python3
"""Clean up orphaned login CSS from app_lapisai.py"""

import re

file_path = "app_lapisai.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and remove orphaned CSS (lines with login CSS that are not inside a function)
# Looking for lines between line 209 and line 425 that are CSS/orphaned code

lines = content.split('\n')
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Skip orphaned CSS block (the mess between load_assets and score_frame)
    if i >= 209 and i <= 425 and (
        line.strip().startswith('--brand') or 
        line.strip().startswith('.stApp') or
        line.strip().startswith('header[') or
        line.strip().startswith('[data-testid') or
        line.strip().startswith('#MainMenu') or
        line.strip().startswith('.login-') or
        line.strip().startswith('.blue-grid') or
        line.strip().startswith('.wave') or
        line.strip().startswith('.orbit') or
        line.strip().startswith('.brand-mark') or
        line.strip().startswith('animation:') or
        line.strip().startswith('@keyframes') or
        line.strip().startswith('font-') or
        line.strip().startswith('background') or
        line.strip().startswith('color:') or
        line.strip().startswith('border') or
        line.strip().startswith('padding') or
        line.strip().startswith('margin') or
        line.strip().startswith('width') or
        line.strip().startswith('height') or
        line.strip().startswith('position') or
        line.strip().startswith('display') or
        line.strip().startswith('z-index') or
        line.strip().startswith('opacity') or
        line.strip().startswith('transform') or
        line.strip().startswith('left') or
        line.strip().startswith('right') or
        line.strip().startswith('top') or
        line.strip().startswith('bottom') or
        line.strip() == '}' or
        line.strip().startswith('content:') or
        line.strip().startswith('filter:') or
        line.strip().startswith('overflow:') or
        line.strip().startswith('isolation:') or
        line.strip().startswith('pointer-events:') or
        line.strip().startswith('box-shadow:') or
        line.strip().startswith('border-radius:') or
        line.strip().startswith('inset:') or
        line.strip().startswith('gap:') or
        line.strip().startswith('align-items:') or
        line.strip().startswith('justify-content:') or
        line.strip().startswith('flex-') or
        line.strip().startswith('line-height:') or
        line.strip().startswith('letter-spacing:') or
        line.strip().startswith('text-') or
        line.strip().startswith('cursor:') or
        line.strip().startswith('font-weight:') or
        line.strip().startswith('font-size:') or
        line.strip().startswith('mix-blend-mode:') or
        line.strip().startswith('will-change:') or
        line.strip().startswith('mask-image:') or
        line.strip().startswith('max-width:') or
        line.strip().startswith('min-height:') or
        line.strip().startswith('radial-gradient') or
        line.strip().startswith('linear-gradient') or
        line.strip().startswith('rgba(') or
        line.strip() == '' and new_lines and new_lines[-1].strip() == ''
    ):
        # Skip this line (orphaned CSS)
        i += 1
        continue
    
    new_lines.append(line)
    i += 1

# Clean up multiple blank lines at that orphaned section
final_content = '\n'.join(new_lines)

# Replace multiple newlines with proper ones
final_content = re.sub(r'\n\n\n+', '\n\n', final_content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"✓ Cleaned up {file_path}")
print(f"  Removed orphaned CSS and login page code")
