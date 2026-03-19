path = 'c:/Users/Yasin/OneDrive/Desktop/construction_app/core/templates/base.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

history_link = '\r\n            <a href="{% url \'activity_history\' %}" class="menu-item {% if \'/history/\' in request.path %}active{% endif %}">\r\n                <span class="menu-icon"></span> <span style="margin-right:6px;">&#128220;</span>History\r\n            </a>'

marker = "{% url 'tools_list' %}"
pos = content.find(marker)
close = content.find('</a>', pos)
insert_after = close + len('</a>')

new_content = content[:insert_after] + history_link + content[insert_after:]
with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done.')
