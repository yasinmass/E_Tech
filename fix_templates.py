"""
Fix all template issues:
1. Replace request.user with user in ALL templates
2. Fix split {{ }} tags across lines
3. Fix specific topbar username in base.html
"""
import os, re, glob

template_dir = os.path.join('core', 'templates')
fixed = []

for filepath in glob.glob(os.path.join(template_dir, '*.html')):
    with open(filepath, 'r', encoding='utf-8') as f:
        original = f.read()
    
    content = original
    
    # 1. Replace request.user. with user.
    content = content.replace('request.user.', 'user.')
    
    # 2. Fix split {{ variable }} tags ({{ on one line, variable on next)
    # Match {{ followed by whitespace+newline, then content, then }}
    content = re.sub(r'\{\{\s*\n\s*', '{{ ', content)
    # Match content then newline+whitespace then }}
    content = re.sub(r'\s*\n\s*\}\}', ' }}', content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        fixed.append(os.path.basename(filepath))

print(f"Fixed {len(fixed)} files: {', '.join(fixed) if fixed else 'none'}")

# Now verify base.html topbar specifically
base_path = os.path.join(template_dir, 'base.html')
with open(base_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and show the topbar username area
for i, line in enumerate(content.split('\n'), 1):
    if 'get_full_name' in line and 'default' in line:
        print(f"  base.html line {i}: {line.strip()}")
    if 'request.user' in line:
        print(f"  STILL HAS request.user at line {i}: {line.strip()}")

# Verify customer_dashboard.html
dash_path = os.path.join(template_dir, 'customer_dashboard.html')
with open(dash_path, 'r', encoding='utf-8') as f:
    content = f.read()

for i, line in enumerate(content.split('\n'), 1):
    if 'request.user' in line:
        print(f"  customer_dashboard.html STILL HAS request.user at line {i}: {line.strip()}")
    if 'site.address' in line:
        print(f"  customer_dashboard.html line {i}: {line.strip()}")

print("DONE")
