with open('c:/Users/Yasin/OneDrive/Desktop/construction_app/core/views.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    'log_activity(user, f"Logged in to the app", \'auth\')',
    'log_activity(user, f"Logged in as {user.role}", \'auth\')'
)

code = code.replace(
    'def customer_sites(request):\n    return render',
    'def customer_sites(request):\n    log_activity(request.user, f"Viewed site details", \'site\')\n    return render'
)

code = code.replace(
    'def customer_updates(request):\n    return render',
    'def customer_updates(request):\n    log_activity(request.user, f"Viewed work updates for their site", \'update\')\n    return render'
)

c_tasks_target = """def customer_tasks(request):
    if request.user.role != 'customer':
        return redirect('login')
    try:"""
c_tasks_replace = """def customer_tasks(request):
    if request.user.role != 'customer':
        return redirect('login')
    log_activity(request.user, f"Viewed tasks for their site", 'task')
    try:"""
code = code.replace(c_tasks_target, c_tasks_replace)

ah_target = """    online_threshold = timezone.now() - timedelta(minutes=3)
    online_users = User.objects.filter(
        last_seen__gte=online_threshold,
        role__in=['worker', 'customer']
    )
    
    recent_threshold = timezone.now() - timedelta(minutes=30)
    recent_users = User.objects.filter(
        last_seen__gte=recent_threshold,
        last_seen__lt=online_threshold,
        role__in=['worker', 'customer']
    )"""
ah_replace = """    online_threshold = timezone.now() - timedelta(minutes=3)
    online_users = User.objects.filter(
        last_seen__gte=online_threshold
    ).exclude(role='admin').order_by('-last_seen')
    
    recent_threshold = timezone.now() - timedelta(minutes=30)
    recent_users = User.objects.filter(
        last_seen__gte=recent_threshold,
        last_seen__lt=online_threshold
    ).exclude(role='admin').order_by('-last_seen')"""
code = code.replace(ah_target, ah_replace)

ah_target_rn = ah_target.replace('\n', '\r\n')
ah_replace_rn = ah_replace.replace('\n', '\r\n')
code = code.replace(ah_target_rn, ah_replace_rn)

c_tasks_target_rn = c_tasks_target.replace('\n', '\r\n')
c_tasks_replace_rn = c_tasks_replace.replace('\n', '\r\n')
code = code.replace(c_tasks_target_rn, c_tasks_replace_rn)

code = code.replace(
    'def customer_sites(request):\r\n    return render',
    'def customer_sites(request):\r\n    log_activity(request.user, f"Viewed site details", \'site\')\r\n    return render'
)

code = code.replace(
    'def customer_updates(request):\r\n    return render',
    'def customer_updates(request):\r\n    log_activity(request.user, f"Viewed work updates for their site", \'update\')\r\n    return render'
)


with open('c:/Users/Yasin/OneDrive/Desktop/construction_app/core/views.py', 'w', encoding='utf-8') as f:
    f.write(code)
