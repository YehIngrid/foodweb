import re

with open('wireframe.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Define CSS Variables mapping
css_vars = '''<style>
:root {
  --color-background-primary: #ffffff;
  --color-background-secondary: #f8f5ee;
  --color-border-secondary: #ddd6c6;
  --color-border-tertiary: #ccc4b0;
  --color-text-primary: #1c1710;
  --color-text-secondary: #5c5040;
  --font-sans: 'Noto Sans TC', sans-serif;
  --font-mono: 'DM Mono', monospace;
  
  --green:     #2a6e3c;
  --green-bg:  rgba(42,110,60,.08);
  --green-bd:  rgba(42,110,60,.22);
  --gold:      #a07828;
  --gold-bg:   rgba(160,120,40,.09);
  --gold-bd:   rgba(160,120,40,.22);
  --orange:    #b53a18;
  --orange-bg: rgba(181,58,24,.08);
  --orange-bd: rgba(181,58,24,.22);
}
'''

content = content.replace('<style>', css_vars)

# Replace specific hex colors
replacements = {
    '#d4edda': 'var(--green-bg)',
    '#a3cdb0': 'var(--green-bd)',
    '#f5faf6': 'var(--color-background-secondary)',
    '#c8e0cc': 'var(--color-border-secondary)',
    '#1a5c30': 'var(--green)',
    '#faeeda': 'var(--gold-bg)',
    '#7a4d0c': 'var(--gold)',
    '#e8c87a': 'var(--gold-bd)',
    '#ba7517': 'var(--gold)',
    '#e0eee3': 'var(--color-border-tertiary)',
    '#e8f4ea': 'var(--green-bg)',
    '#fde8e0': 'var(--orange-bg)',
    '#8c2a0e': 'var(--orange)',
    '#e8a898': 'var(--orange-bd)',
    '#c95d2e': 'var(--orange)'
}

for old, new in replacements.items():
    content = content.replace(old, new)
    # Also handle uppercase if any
    content = content.replace(old.upper(), new)

with open('wireframe.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
