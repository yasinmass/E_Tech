file_path = r'core\views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = """            day_rows.append({
                'idx': idx, 'date': d, 'day': d.strftime('%a'),
                'early': slots['early'], 'morning': slots['morning'], 'afternoon': slots['afternoon'],
                'day_present': day_present,
                'day_badge': day_badge,
                'is_today': (d == date.today()),
            })"""

new_block = """            def get_symbol(val):
                if val is True: return 'P'
                if val is False: return 'A'
                return '—'

            day_rows.append({
                'idx': idx, 'date': d, 'day': d.strftime('%a'),
                'early_sym': get_symbol(slots['early']),
                'morning_sym': get_symbol(slots['morning']),
                'afternoon_sym': get_symbol(slots['afternoon']),
                'early_color': '#2E7D32' if slots['early'] is True else ('#C62828' if slots['early'] is False else '#BDBDBD'),
                'morning_color': '#2E7D32' if slots['morning'] is True else ('#C62828' if slots['morning'] is False else '#BDBDBD'),
                'afternoon_color': '#2E7D32' if slots['afternoon'] is True else ('#C62828' if slots['afternoon'] is False else '#BDBDBD'),
                'day_present': day_present,
                'day_badge': day_badge,
                'is_today': (d == date.today()),
                'is_early_p': slots['early'] is True,
                'is_morning_p': slots['morning'] is True,
                'is_afternoon_p': slots['afternoon'] is True,
            })"""

# Use normalized line endings for replacement
content = content.replace('\r\n', '\n')
if old_block in content:
    content = content.replace(old_block, new_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS')
else:
    print('NOT FOUND')
    print(repr(content[content.find('day_rows.append'):content.find('day_rows.append')+300]))
