import os
import re

path = 'core/templates'
print("Scanning " + path)

# We want to match text blocks that look exactly like the subtitles across the views.
# Example 1: <p style="font-size:13px;color:#5A6A85;">Full audit log of all actions across the app.</p>
# Example 2: <div style="font-size:13px;color:#5A6A85;margin-top:2px;">All site work progress updates.</div>
# We should cautiously match <p or <div with exactly style="font-size:13px;color:#5A6A85..."

pattern_p = re.compile(r'<p\s+style="font-size:13px;color:#5A6A85;[^>]*>.*?</p>', re.DOTALL)
pattern_div = re.compile(r'<div\s+style="font-size:13px;color:#5A6A85;[^>]*>.*?</div>', re.DOTALL)

replacement = '{% if subtitle %}<p class="page-subtitle" style="font-size:13px;color:#5A6A85;margin-top:2px;">{{ subtitle }}</p>{% endif %}'

for file in os.listdir(path):
    if file.endswith('.html'):
        fpath = os.path.join(path, file)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content = pattern_p.sub(replacement, content)
        new_content = pattern_div.sub(replacement, new_content)

        if new_content != content:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {file}")
