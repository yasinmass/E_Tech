file_path = r'core\views.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old = """@role_required('worker')
def worker_my_attendance(request):
    all_atts = Attendance.objects.filter(worker=request.user)
    tot = all_atts.filter(is_present=True).count()
    pd = tot // 2
    uq = all_atts.values('date').distinct().count()
    ad = max(uq - pd, 0)
    pct = int((pd / (pd + ad)) * 100) if (pd + ad) > 0 else 0
    return render(request, 'worker_attendance.html', {
        'history': all_atts.order_by('-date')[:30],
        'present_days': pd, 'absent_days': ad, 'attendance_percentage': pct, 'today': date.today(),
        'marked_slots': {att.slot: att.is_present for att in Attendance.objects.filter(worker=request.user, date=date.today())}
    })"""

new = """@role_required('worker')
def worker_my_attendance(request):
    from datetime import timedelta
    records = Attendance.objects.filter(worker=request.user).order_by('date')
    present_slots = records.filter(is_present=True).count()
    absent_slots = records.filter(is_present=False).count()
    total_slots = present_slots + absent_slots
    pct = round((present_slots / total_slots) * 100, 1) if total_slots > 0 else 0

    # Build date-wise map
    dates_map = {}
    for r in records:
        key = r.date
        if key not in dates_map:
            dates_map[key] = {'early': None, 'morning': None, 'afternoon': None}
        dates_map[key][r.slot] = r.is_present

    # Fill all dates from first entry to today
    day_rows = []
    if dates_map:
        start = min(dates_map.keys())
        end = date.today()
        d = start
        idx = 1
        while d <= end:
            slots = dates_map.get(d, {'early': None, 'morning': None, 'afternoon': None})
            day_present = sum(1 for v in slots.values() if v is True)
            day_rows.append({
                'idx': idx, 'date': d, 'day': d.strftime('%a'),
                'early': slots['early'], 'morning': slots['morning'], 'afternoon': slots['afternoon'],
                'day_present': day_present,
            })
            idx += 1
            d += timedelta(days=1)
    day_rows.reverse()  # newest first

    marked_slots = {att.slot: att.is_present for att in Attendance.objects.filter(worker=request.user, date=date.today())}

    return render(request, 'worker_attendance.html', {
        'present_slots': present_slots,
        'absent_slots': absent_slots,
        'total_slots': total_slots,
        'pct': pct,
        'day_rows': day_rows,
        'today': date.today(),
        'marked_slots': marked_slots,
    })"""

# Normalize line endings for matching
content_normalized = content.replace('\r\n', '\n')

if old in content_normalized:
    content_normalized = content_normalized.replace(old, new)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content_normalized)
    print('SUCCESS')
else:
    print('NOT FOUND')
    idx = content_normalized.find('worker_my_attendance')
    print(repr(content_normalized[idx:idx+300]))
