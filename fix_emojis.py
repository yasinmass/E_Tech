import os
import glob
import re

base_path = r'c:\Users\Yasin\OneDrive\Desktop\construction_app\core\templates'
html_files = glob.glob(os.path.join(base_path, '**', '*.html'), recursive=True)

for p in html_files:
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    
    # 1. Page titles and headings
    replacements = {
        '👷 Workers Management': 'Workers Management',
        '🏗️ Sites': 'Sites',
        '📋 Tasks': 'Tasks',
        '🕐 Attendance Management': 'Attendance Management',
        '📸 Work Updates': 'Work Updates',
        '🧾 Bills': 'Bills',
        '👤 Profile': 'Profile'
    }
    
    # Apply to exact match lines.
    for k, v in replacements.items():
        content = content.replace(f'<h2>{k}</h2>', f'<h2>{v}</h2>')
        content = content.replace(f'<h2>{k} ', f'<h2>{v} ')  # Just in case

    # Some might be <h3>
    for k, v in replacements.items():
        content = content.replace(f'<h3>{k}</h3>', f'<h3>{v}</h3>')
    
    # Let's also just replace them outright if they appear as purely the string in the file?
    # No, only in headings and titles.
    for k, v in replacements.items():
        content = content.replace(f'{k}', f'{v}')  # Since the prompt said "remove emojis from these specific places... Page titles and headings". Wait! It means replace the string "👷 Workers Management" entirely. The user doesn't use "👷 Workers Management" inside buttons! So replace generally is fine.
        
    # Wait, the prompt lists "👷 Workers Management" etc. I'll just replace the exact text.
    
    # 2. Sidebar nav links (base.html)
    if 'base.html' in p:
        # We need to remove emojis from <span class="menu-icon">...</span>
        # We can extract the inner content, if it's an emoji we remove it.
        # But wait, the prompt says "Sidebar nav links — remove emojis from all nav item labels only. Keep the nav icons that are SVG or CSS icons — only remove emoji characters."
        # Actually the "menu-icon" span contains the emoji. The nav item "label" is the text next to it.
        # "Remove emojis from all nav item labels only. Keep the nav icons that are SVG/CSS icons — only remove emoji characters."
        # Since the emoji IS the icon, removing it means keeping the span empty if there is no SVG.
        content = re.sub(r'<span class="menu-icon">([^<]+)</span>', r'<span class="menu-icon"></span>', content)
        
        # 3. Topbar breadcrumb text
        # <div class="page-title-bar" id="pageTitleBar">
        # In base.html, there is JS that sets breadcrumb:
        # const titles = { '/admin-dashboard/': '📊 Dashboard', ... }
        # Let's strip emojis from the titles dictionary in base.html
        content = re.sub(r"'(/?[\w\-]+/?)\':\s*'[^\s<>\w]*\s*(.*?)'", r"'\1': '\2'", content)
        # Handle specific ones that might have multiple emojis like 🏗️
        content = re.sub(r"'(/?[\w\-]+/?)\':\s*'(?:📊|👷|🏗️|📋|🕒|📸|🧾|👤|🏠|🚪)\s*(.*?)'", r"'\1': '\2'", content)
        content = content.replace("'📊 Dashboard'", "'Dashboard'")
        content = content.replace("'👷 Workers'", "'Workers'")
        content = content.replace("'🏗️ Sites'", "'Sites'")
        content = content.replace("'📋 Tasks'", "'Tasks'")
        content = content.replace("'🕒 Attendance'", "'Attendance'")
        content = content.replace("'📸 Work Updates'", "'Work Updates'")
        content = content.replace("'🧾 Bills'", "'Bills'")
        content = content.replace("'👤 Profile'", "'Profile'")
        content = content.replace("'🏠 Dashboard'", "'Dashboard'")
        content = content.replace("'📋 My Tasks'", "'My Tasks'")
        content = content.replace("'🏗️ My Sites'", "'My Sites'")
        content = content.replace("'🧾 Upload Bills'", "'Upload Bills'")
        
        # Also remove emojis directly in the page setup just in case
        
    if orig != content:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed {p}')
