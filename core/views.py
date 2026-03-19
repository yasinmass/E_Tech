from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
import json
from datetime import date
from .models import User, Site, Task, Attendance, WorkUpdate, Bill, WorkerProfile, Product, Tool, ActivityLog
from .forms import (
    AddWorkerForm, CustomerCreationForm, WorkerEditForm,
    SiteForm, SiteEditForm, TaskForm, AttendanceForm, WorkUpdateForm, BillForm,
    ProfileSettingsForm, ProductForm, ToolForm,
)

# ---------- Role helpers ----------
def role_required(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role != role:
                return HttpResponseForbidden("Access denied.")
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator

def log_activity(user, action, category):
    """Create an ActivityLog entry — silently ignores errors so it never breaks a view."""
    try:
        ActivityLog.objects.create(user=user, action=action, category=category)
    except Exception:
        pass

# ---------- Auth Views ----------
def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            log_activity(user, f"Logged in to the app", 'auth')
            return _redirect_by_role(user)
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
    return render(request, 'login.html')

def _redirect_by_role(user):
    if user.role == 'admin':
        return redirect('admin_dashboard')
    elif user.role == 'worker':
        return redirect('worker_dashboard')
    elif user.role == 'customer':
        return redirect('customer_dashboard')
    return redirect('login')

def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request.user, f"Logged out of the app", 'auth')
    logout(request)
    return redirect('login')

# ---------- Admin Views ----------
@role_required('admin')
def admin_dashboard(request):
    workers = User.objects.filter(role='worker')
    sites = Site.objects.prefetch_related('workers').all()
    tasks = Task.objects.select_related('worker', 'site').order_by('-created_at')
    updates = WorkUpdate.objects.select_related('worker', 'site').order_by('-created_at')
    bills = Bill.objects.select_related('site', 'uploaded_by').order_by('-date')
    attendances = Attendance.objects.select_related('worker').order_by('-date')
    customers = User.objects.filter(role='customer')

    # Add attendance calculations to each worker
    for worker in workers:
        total_slots = Attendance.objects.filter(worker=worker, is_present=True).count()
        present_days = total_slots // 2
        
        unique_dates = Attendance.objects.filter(worker=worker).values('date').distinct().count()
        absent_days = unique_dates - present_days
        if absent_days < 0:
            absent_days = 0
            
        worker.total_slots = total_slots
        worker.present_days = present_days
        worker.remaining_slots = total_slots % 2
        worker.absent_days = absent_days

    context = {
        'workers': workers,
        'sites': sites,
        'tasks': tasks,
        'updates': updates,
        'bills': bills,
        'attendances': attendances,
        'customers': customers,
        'today': date.today(),
    }
    return render(request, 'admin_dashboard.html', context)

@role_required('admin')
def add_worker(request):
    if request.method == 'POST':
        form = AddWorkerForm(request.POST, request.FILES)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['login_username'],
                password=form.cleaned_data['login_password'],
                role='worker',
            )
            full_name = form.cleaned_data['full_name']
            name_parts = full_name.strip().split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            user.phone = form.cleaned_data['phone']
            user.save()

            WorkerProfile.objects.create(
                user=user,
                age=form.cleaned_data['age'],
                phone=form.cleaned_data['phone'],
                family_phone=form.cleaned_data['family_phone'],
                address=form.cleaned_data['address'],
                id_proof=form.cleaned_data.get('id_proof'),
                photo=form.cleaned_data.get('photo'),
            )
            log_activity(request.user, f"Added new worker: {user.get_full_name() or user.username}", 'worker')
            return redirect('admin_workers')
    else:
        form = AddWorkerForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Add Worker'})

@role_required('admin')
def add_site(request):
    if request.method == 'POST':
        form = SiteForm(request.POST, request.FILES)
        if form.is_valid():
            site = form.save(commit=False)
            username = form.cleaned_data['owner_username']
            password = form.cleaned_data['owner_password']
            owner_name = form.cleaned_data.get('owner_name', '')
            owner_phone = form.cleaned_data.get('owner_phone', '')
            # Split owner_name into first/last
            name_parts = owner_name.strip().split(' ', 1)
            first = name_parts[0] if name_parts else ''
            last = name_parts[1] if len(name_parts) > 1 else ''
            user = User.objects.create_user(
                username=username,
                password=password,
                role='customer',
                first_name=first,
                last_name=last,
                phone=owner_phone,
            )
            site.customer = user
            site.status = 'In Progress'
            site.save()
            log_activity(request.user, f"Added new site: {site.name}", 'site')
            messages.success(request, f'Site "{site.name}" added and owner login created.')
            return redirect('admin_sites')
    else:
        form = SiteForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Add Site', 'back_url': 'admin_sites'})

@role_required('admin')
def assign_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = TaskForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Assign Task', 'back_url': 'admin_dashboard'})

@role_required('admin')
def admin_mark_attendance(request):
    if request.method == "POST":
        form = AttendanceForm(request.POST)
        if form.is_valid():
            att = form.save(commit=False)
            # Prevent duplicate attendance for same worker+day+slot
            existing = Attendance.objects.filter(worker=att.worker, date=date.today(), slot=att.slot).first()
            if existing:
                existing.is_present = att.is_present
                existing.save()
            else:
                att.save()
            return redirect('admin_dashboard')
    else:
        form = AttendanceForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Mark Attendance', 'back_url': 'admin_dashboard'})

@role_required('admin')
def upload_bill(request):
    if request.method == "POST":
        form = BillForm(request.POST, request.FILES)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.uploaded_by = request.user
            bill.save()
            log_activity(request.user, f"Uploaded bill: ₹{bill.amount} — {bill.site.name}", 'bill')
            return redirect('admin_dashboard')
    else:
        form = BillForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Upload Bill', 'back_url': 'admin_dashboard'})

# ---------- Worker Views ----------
@role_required('worker')
def worker_dashboard(request):
    attendances_today = Attendance.objects.filter(worker=request.user, date=date.today())
    marked_slots = {att.slot: att.is_present for att in attendances_today}
    
    # Calculate summary
    # Present Days = total_slots // 2
    # Absent Days = total working days - present days (we can find total working days by counting unique dates)
    all_atts = Attendance.objects.filter(worker=request.user)
    total_slots = all_atts.filter(is_present=True).count()
    present_days = total_slots // 2
    
    unique_dates = all_atts.values('date').distinct().count()
    absent_days = unique_dates - present_days
    if absent_days < 0:
        absent_days = 0 
    
    attendance_percentage = 0
    if unique_dates > 0:
        attendance_percentage = int((present_days / (present_days + absent_days)) * 100) if (present_days + absent_days) > 0 else 0

    tasks = Task.objects.filter(assigned_workers=request.user).select_related('site').order_by('-created_at')
    pending_tasks = tasks.filter(is_completed=False).count()
    sites = request.user.assigned_sites.all()
    updates = WorkUpdate.objects.filter(worker=request.user).order_by('-created_at')[:10]
    history = all_atts.order_by('-date')[:30]
    bills = Bill.objects.filter(uploaded_by=request.user).order_by('-date')[:10]
    context = {
        'marked_slots': marked_slots,
        'present_days': present_days,
        'absent_days': absent_days,
        'attendance_percentage': attendance_percentage,
        'tasks': tasks,
        'pending_tasks': pending_tasks,
        'sites': sites,
        'updates': updates,
        'history': history,
        'bills': bills,
        'today': date.today(),
    }
    return render(request, 'worker_dashboard.html', context)

@role_required('worker')
def worker_mark_attendance(request):
    if request.method == "POST":
        slot = request.POST.get('slot')
        is_present = request.POST.get('is_present') == 'true'
        existing = Attendance.objects.filter(worker=request.user, date=date.today(), slot=slot).first()
        if existing:
            # Feature 3: Block re-submission — attendance already marked for this slot today
            slot_label = dict(Attendance.SLOT_CHOICES).get(slot, slot)
            messages.error(request, f'Attendance for "{slot_label}" has already been marked for today.')
        else:
            Attendance.objects.create(worker=request.user, slot=slot, is_present=is_present)
            log_activity(request.user, f"Marked own attendance — {slot} — {'Present' if is_present else 'Absent'}", 'attendance')
    return redirect('worker_dashboard')

@role_required('worker')
def worker_mark_task_complete(request, task_id):
    if request.method == "POST":
        task = get_object_or_404(Task, id=task_id)
        if request.user in task.assigned_workers.all():
            task.status = 'Done'
            task.is_completed = True
            task.save()
    return redirect('worker_my_tasks')


@role_required('worker')
def worker_upload_update(request):
    if request.method == "POST":
        form = WorkUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            update = form.save(commit=False)
            update.worker = request.user
            update.save()
            log_activity(request.user, f"Uploaded work update for site: {update.site.name}", 'update')
            return redirect('worker_dashboard')
    else:
        form = WorkUpdateForm()
        form.fields['site'].queryset = request.user.assigned_sites.all()
    return render(request, 'form_template.html', {'form': form, 'title': 'Upload Work Update', 'back_url': 'worker_dashboard'})

@role_required('worker')
def worker_upload_bill(request):
    if request.method == "POST":
        form = BillForm(request.POST, request.FILES)
        if form.is_valid():
            bill = form.save(commit=False)
            bill.uploaded_by = request.user
            bill.save()
            return redirect('worker_dashboard')
    else:
        form = BillForm()
        form.fields['site'].queryset = request.user.assigned_sites.all()
    return render(request, 'form_template.html', {'form': form, 'title': 'Upload Bill', 'back_url': 'worker_dashboard'})

# ---------- Customer Views ----------
@role_required('customer')
def customer_dashboard(request):
    sites = Site.objects.filter(customer=request.user).prefetch_related('workers')
    updates = WorkUpdate.objects.filter(site__in=sites).select_related('worker', 'site').order_by('-created_at')
    bills = Bill.objects.filter(site__in=sites).select_related('site').order_by('-date')
    context = {'sites': sites, 'updates': updates, 'bills': bills}
    return render(request, 'customer_dashboard.html', context)


@role_required('admin')
def admin_workers(request):
    workers = User.objects.filter(role='worker')
    for worker in workers:
        today_att = Attendance.objects.filter(worker=worker, date=date.today())
        worker.today_early = "true" if today_att.filter(slot='early', is_present=True).exists() else "false" if today_att.filter(slot='early', is_present=False).exists() else "none"
        worker.today_morning = "true" if today_att.filter(slot='morning', is_present=True).exists() else "false" if today_att.filter(slot='morning', is_present=False).exists() else "none"
        worker.today_afternoon = "true" if today_att.filter(slot='afternoon', is_present=True).exists() else "false" if today_att.filter(slot='afternoon', is_present=False).exists() else "none"

    return render(request, 'admin_workers.html', {'workers': workers, 'today': date.today()})

@role_required('admin')
def admin_mark_worker_ajax(request):
    if request.method == "POST":
        data = json.loads(request.body)
        worker_id = data.get('worker_id')
        worker = get_object_or_404(User, id=worker_id, role='worker')
        
        slots_data = data.get('slots', {}) # {'early': True/False, 'morning': True...}
        
        for slot_key, is_present in slots_data.items():
            if is_present is not None:
                Attendance.objects.update_or_create(
                    worker=worker, 
                    date=date.today(), 
                    slot=slot_key,
                    defaults={'is_present': is_present}
                )
                log_activity(request.user, f"Marked attendance for {worker.get_full_name() or worker.username} — {slot_key} — {'Present' if is_present else 'Absent'}", 'attendance')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'invalid request'}, status=400)

@role_required('admin')
def admin_sites(request):
    sites = Site.objects.all().order_by('-created_at')
    for site in sites:
        tasks = Task.objects.filter(site=site)
        total_tasks = tasks.count()
        done_tasks = tasks.filter(status='Done').count()
        inprogress_tasks = tasks.filter(status='In Progress').count()
        pending_tasks = tasks.filter(status='Pending').count()
        pct = round((done_tasks / total_tasks * 100)) if total_tasks > 0 else 0
        site.total_tasks = total_tasks
        site.done_tasks = done_tasks
        site.inprogress_tasks = inprogress_tasks
        site.pending_tasks = pending_tasks
        site.task_pct = pct
    return render(request, 'admin_sites.html', {'sites': sites})

@role_required('admin')
def admin_tasks(request):
    return render(request, 'admin_tasks.html', {'tasks': Task.objects.select_related('site').prefetch_related('assigned_workers').order_by('-created_at')})

@role_required('admin')
def admin_all_attendance(request):
    from datetime import timedelta
    workers = User.objects.filter(role='worker')
    worker_data = []
    for w in workers:
        records = Attendance.objects.filter(worker=w).order_by('date')
        present = records.filter(is_present=True).count()
        absent = records.filter(is_present=False).count()
        total = present + absent
        pct = round((present / total) * 100) if total > 0 else 0
        dates_map = {}
        for r in records:
            key = r.date
            if key not in dates_map:
                dates_map[key] = {'early': None, 'morning': None, 'afternoon': None}
            dates_map[key][r.slot] = r.is_present
        day_rows = []
        if dates_map:
            start = min(dates_map.keys())
            end = date.today()
            d = start
            idx = 1
            while d <= end:
                slots = dates_map.get(d, {'early': None, 'morning': None, 'afternoon': None})
                day_present = sum(1 for v in slots.values() if v is True)
                day_rows.append({'idx': idx, 'date': d, 'day': d.strftime('%a'), 'early': slots['early'], 'morning': slots['morning'], 'afternoon': slots['afternoon'], 'day_present': day_present})
                idx += 1
                d += timedelta(days=1)
        worker_data.append({'worker': w, 'present': present, 'absent': absent, 'total': total, 'pct': pct, 'rows': day_rows})
    return render(request, 'admin_attendance.html', {'worker_data': worker_data, 'today': date.today()})

@role_required('admin')
def admin_updates(request):
    return render(request, 'admin_updates.html', {'updates': WorkUpdate.objects.select_related('worker', 'site').order_by('-created_at')})

@role_required('admin')
def admin_all_bills(request):
    return render(request, 'admin_bills.html', {'bills': Bill.objects.select_related('site', 'uploaded_by').order_by('-date')})

# --- WORKER VIEWS ---
@role_required('worker')
def worker_my_tasks(request):
    return render(request, 'worker_tasks.html', {'tasks': Task.objects.filter(assigned_workers=request.user).select_related('site').order_by('-created_at')})

@role_required('worker')
def worker_my_sites(request):
    sites = Site.objects.all().order_by('-created_at')
    return render(request, 'worker_sites.html', {'sites': sites})

@role_required('worker')
def worker_my_attendance(request):
    from datetime import date, timedelta
    records = Attendance.objects.filter(worker=request.user).order_by('date')
    
    present_slots = records.filter(is_present=True).count()
    absent_slots = records.filter(is_present=False).count()
    total_slots = present_slots + absent_slots
    attendance_pct = round((present_slots / total_slots * 100), 1) if total_slots > 0 else 0

    day_rows = []
    if records.exists():
        first_date = records.first().date
        today = date.today()
        current = first_date
        while current <= today:
            day_records = records.filter(date=current)
            
            def get_slot_info(slot_name):
                r = day_records.filter(slot=slot_name).first()
                if not r:
                    return {'sym': 'NT', 'color': '#BDBDBD', 'is_p': False}
                sym = 'P' if r.is_present else 'A'
                color = '#2E7D32' if r.is_present else '#C62828'
                return {'sym': sym, 'color': color, 'is_p': r.is_present}
            
            e = get_slot_info('early')
            m = get_slot_info('morning')
            a = get_slot_info('afternoon')
            dp = sum([1 for s in [e, m, a] if s['is_p']])

            if dp == 3:
                badge = 'badge-done'
            elif dp >= 1:
                badge = 'badge-pending'
            else:
                badge = 'badge-absent'

            day_rows.append({
                'date': current.strftime('%b %d, %Y'),
                'day_name': current.strftime('%a'),
                'early': e['sym'],
                'early_color': e['color'],
                'morning': m['sym'],
                'morning_color': m['color'],
                'afternoon': a['sym'],
                'afternoon_color': a['color'],
                'day_present': dp,
                'day_badge': badge,
                'is_today': current == today,
            })
            current += timedelta(days=1)
    
    day_rows.reverse()

    return render(request, 'worker_attendance.html', {
        'present_slots': present_slots,
        'absent_slots': absent_slots,
        'total_slots': total_slots,
        'attendance_pct': attendance_pct,
        'day_rows': day_rows,
    })

@role_required('worker')
def worker_my_updates(request):
    return render(request, 'worker_updates.html', {'updates': WorkUpdate.objects.filter(worker=request.user).order_by('-created_at')})

@role_required('worker')
def worker_my_bills(request):
    return render(request, 'worker_bills.html', {'bills': Bill.objects.filter(uploaded_by=request.user).order_by('-date')})

# --- CUSTOMER VIEWS ---
@role_required('customer')
def customer_sites(request):
    return render(request, 'customer_sites.html', {'sites': Site.objects.filter(customer=request.user)})

@role_required('customer')
def customer_updates(request):
    return render(request, 'customer_updates.html', {'updates': WorkUpdate.objects.filter(site__customer=request.user).order_by('-created_at')})

@role_required('customer')
def customer_bills(request):
    return redirect('customer_dashboard')


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — Customer Management
# ═══════════════════════════════════════════════════════════════════════════════

@role_required('admin')
def admin_customers(request):
    customers = User.objects.filter(role='customer')
    return render(request, 'admin_customers.html', {'customers': customers})


@role_required('admin')
def add_customer(request):
    if request.method == 'POST':
        form = CustomerCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer account created successfully.')
            return redirect('admin_customers')
    else:
        form = CustomerCreationForm()
    return render(request, 'form_template.html', {
        'form': form, 'title': 'Add Customer', 'back_url': 'admin_customers'
    })


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 2 — Edit & Delete: Workers
# ═══════════════════════════════════════════════════════════════════════════════

@role_required('admin')
def edit_worker(request, worker_id):
    worker = get_object_or_404(User, id=worker_id, role='worker')
    profile, created = WorkerProfile.objects.get_or_create(user=worker)
    
    if request.method == 'POST':
        form = WorkerEditForm(request.POST, request.FILES, instance=worker)
        if form.is_valid():
            worker = form.save(commit=False)
            
            full_name = form.cleaned_data['full_name']
            name_parts = full_name.strip().split(' ', 1)
            worker.first_name = name_parts[0]
            worker.last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            worker.phone = form.cleaned_data['phone']
            
            new_username = form.cleaned_data.get('new_username')
            if new_username:
                worker.username = new_username
                
            new_pw = form.cleaned_data.get('new_password')
            if new_pw:
                worker.set_password(new_pw)
                
            worker.save()
            
            profile.age = form.cleaned_data['age']
            profile.phone = form.cleaned_data['phone']
            profile.family_phone = form.cleaned_data['family_phone']
            profile.address = form.cleaned_data['address']
            
            if form.cleaned_data.get('photo'):
                profile.photo = form.cleaned_data['photo']
            if form.cleaned_data.get('id_proof'):
                profile.id_proof = form.cleaned_data['id_proof']
                
            profile.save()
            messages.success(request, f'Worker updated successfully.')
            return redirect('admin_workers')
    else:
        initial = {
            'full_name': worker.get_full_name() or worker.username,
            'age': profile.age,
            'phone': profile.phone or worker.phone,
            'family_phone': profile.family_phone,
            'address': profile.address,
            'new_username': worker.username,
        }
        form = WorkerEditForm(instance=worker, initial=initial)
    return render(request, 'form_template.html', {
        'form': form,
        'title': f'Edit Worker — {worker.get_full_name() or worker.username}',
        'back_url': 'admin_workers'
    })


@role_required('admin')
def delete_worker(request, worker_id):
    worker = get_object_or_404(User, id=worker_id, role='worker')
    if request.method == 'POST':
        name = worker.get_full_name() or worker.username
        worker.delete()
        messages.success(request, f'Worker "{name}" deleted.')
        return redirect('admin_workers')
    return render(request, 'confirm_delete.html', {
        'object_name': worker.get_full_name() or worker.username,
        'object_type': 'Worker',
        'back_url': 'admin_workers',
    })

@role_required('admin')
def worker_detail(request, worker_id):
    worker = get_object_or_404(User, id=worker_id, role='worker')
    profile, created = WorkerProfile.objects.get_or_create(user=worker)
    attendances = Attendance.objects.filter(worker=worker).order_by('-date')[:30]
    total_slots = Attendance.objects.filter(worker=worker, is_present=True).count()
    present_days = total_slots // 2
    unique_dates = Attendance.objects.filter(worker=worker).values('date').distinct().count()
    absent_days = max(0, unique_dates - present_days)
    attendance_stats = {
        'present': present_days,
        'absent': absent_days,
        'total': unique_dates,
    }
    return render(request, 'admin_worker_detail.html', {
        'worker': worker,
        'profile': profile,
        'attendances': attendances,
        'attendance_stats': attendance_stats,
    })


# ── Edit & Delete: Sites ───────────────────────────────────────────────────────

@role_required('admin')
def edit_site(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    customer = site.customer
    if request.method == 'POST':
        form = SiteEditForm(request.POST, request.FILES, instance=site)
        if form.is_valid():
            site = form.save(commit=False)
            site.owner_name = form.cleaned_data.get('owner_name_field', site.owner_name)
            site.owner_phone = form.cleaned_data.get('owner_phone_field', site.owner_phone)
            site.save()
            log_activity(request.user, f"Edited site: {site.name}", 'site')
            # Update linked customer user
            if customer:
                new_username = form.cleaned_data.get('new_username', '').strip()
                new_password = form.cleaned_data.get('new_password', '').strip()
                owner_name = form.cleaned_data.get('owner_name_field', '').strip()
                owner_phone = form.cleaned_data.get('owner_phone_field', '').strip()
                if new_username and new_username != customer.username:
                    if not User.objects.filter(username=new_username).exclude(pk=customer.pk).exists():
                        customer.username = new_username
                if new_password:
                    customer.set_password(new_password)
                if owner_name:
                    parts = owner_name.split(' ', 1)
                    customer.first_name = parts[0]
                    customer.last_name = parts[1] if len(parts) > 1 else ''
                if owner_phone:
                    customer.phone = owner_phone
                customer.save()
            messages.success(request, f'Site "{site.name}" updated.')
            return redirect('admin_sites')
    else:
        initial = {}
        if customer:
            initial['new_username'] = customer.username
            initial['owner_name_field'] = customer.get_full_name() or site.owner_name
            initial['owner_phone_field'] = customer.phone or site.owner_phone
        form = SiteEditForm(instance=site, initial=initial)
    return render(request, 'form_template.html', {
        'form': form, 'title': f'Edit Site — {site.name}', 'back_url': 'admin_sites',
        'delete_url': f'/mgmt/sites/{site.id}/delete/',
        'delete_label': 'Delete Site',
    })


@role_required('admin')
def delete_site(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == 'POST':
        name = site.name
        site.delete()
        log_activity(request.user, f"Deleted site: {name}", 'site')
        messages.success(request, f'Site "{name}" deleted.')
        return redirect('admin_sites')
    return render(request, 'confirm_delete.html', {
        'object_name': site.name, 'object_type': 'Site', 'back_url': 'admin_sites',
    })


# ── Edit & Delete: Tasks ───────────────────────────────────────────────────────

@role_required('admin')
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated.')
            return redirect('admin_tasks')
    else:
        form = TaskForm(instance=task)
    return render(request, 'form_template.html', {
        'form': form, 'title': f'Edit Task — {task.title}', 'back_url': 'admin_tasks'
    })


@role_required('admin')
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        name = task.title
        task.delete()
        messages.success(request, f'Task "{name}" deleted.')
        return redirect('admin_tasks')
    return render(request, 'confirm_delete.html', {
        'object_name': task.title, 'object_type': 'Task', 'back_url': 'admin_tasks',
    })


# ── Edit & Delete: Bills ───────────────────────────────────────────────────────

@role_required('admin')
def edit_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    if request.method == 'POST':
        form = BillForm(request.POST, request.FILES, instance=bill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bill updated successfully.')
            return redirect('admin_all_bills')
    else:
        form = BillForm(instance=bill)
    return render(request, 'form_template.html', {
        'form': form, 'title': f'Edit Bill — {bill.site.name}', 'back_url': 'admin_all_bills'
    })


@role_required('admin')
def delete_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    if request.method == 'POST':
        label = f'₹{bill.amount} — {bill.site.name}'
        bill.delete()
        messages.success(request, f'Bill "{label}" deleted.')
        return redirect('admin_all_bills')
    return render(request, 'confirm_delete.html', {
        'object_name': f'₹{bill.amount} — {bill.site.name}',
        'object_type': 'Bill',
        'back_url': 'admin_all_bills',
    })


# ═══════════════════════════════════════════════════════════════════════════════
# FEATURE 5 — Profile Settings (all roles)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def profile_settings(request):
    is_admin = request.user.role == 'admin' or request.user.is_superuser
    if request.method == 'POST':
        if not is_admin:
            messages.error(request, 'You do not have permission to edit your profile.')
            return redirect('profile_settings')
            
        form = ProfileSettingsForm(request.user, request.POST)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name  = form.cleaned_data['last_name']
            user.phone      = form.cleaned_data['phone']
            new_pw = form.cleaned_data.get('new_password')
            if new_pw:
                user.set_password(new_pw)
                update_session_auth_hash(request, user)   # keeps session alive
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_settings')
    else:
        form = ProfileSettingsForm(request.user, initial={
            'first_name': request.user.first_name,
            'last_name':  request.user.last_name,
            'phone':      request.user.phone,
        })
    return render(request, 'profile_settings.html', {'form': form})

# ---------- Product / Inventory Views ----------
@login_required
def products_list(request):
    query = request.GET.get('q', '')
    products = Product.objects.all().order_by('-created_at')
    if query:
        products = products.filter(name__icontains=query) | Product.objects.filter(place__icontains=query).order_by('-created_at')
        products = products.distinct()
    total = products.count()
    in_stock = products.filter(quantity__gt=5).count()
    low_stock = products.filter(quantity__lte=5).count()
    return render(request, 'products.html', {
        'products': products,
        'query': query,
        'total': total,
        'in_stock': in_stock,
        'low_stock': low_stock,
    })

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.added_by = request.user
            product.save()
            log_activity(request.user, f"Added product: {product.name} (qty: {product.quantity})", 'product')
            return redirect('products_list')
    else:
        form = ProductForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Add Product', 'back_url': 'products_list'})

@login_required
def edit_product(request, product_id):
    if request.user.role != 'admin':
        return redirect('products_list')
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('products_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'form_template.html', {'form': form, 'title': 'Edit Product', 'back_url': 'products_list'})

@login_required
def update_product_qty(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        try:
            qty = int(request.POST.get('qty', 1))
        except ValueError:
            qty = 1
        if action == 'add':
            product.quantity += qty
        elif action == 'remove':
            product.quantity = max(0, product.quantity - qty)
        product.save()
        log_activity(request.user, f"{'Added' if action == 'add' else 'Removed'} {qty} units of {product.name}", 'product')
    return redirect('products_list')

@login_required
def delete_product(request, product_id):
    if request.user.role != 'admin':
        return redirect('products_list')
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('products_list')

# ---------- Tool Views ----------
@login_required
def tools_list(request):
    from django.db.models import Q
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    tools = Tool.objects.all().order_by('is_available', '-created_at')
    if query:
        tools = Tool.objects.filter(
            Q(name__icontains=query) | Q(location__icontains=query)
        ).order_by('is_available', '-created_at')
    if status == 'available':
        tools = tools.filter(is_available=True)
    elif status == 'inuse':
        tools = tools.filter(is_available=False)
    total = Tool.objects.count()
    available = Tool.objects.filter(is_available=True).count()
    in_use = Tool.objects.filter(is_available=False).count()
    return render(request, 'tools.html', {
        'tools': tools,
        'query': query,
        'status': status,
        'total': total,
        'available': available,
        'in_use': in_use,
    })

@login_required
def add_tool(request):
    if request.user.role != 'admin':
        return redirect('tools_list')
    if request.method == 'POST':
        form = ToolForm(request.POST, request.FILES)
        if form.is_valid():
            tool = form.save(commit=False)
            tool.added_by = request.user
            tool.save()
            return redirect('tools_list')
    else:
        form = ToolForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Add Tool', 'back_url': 'tools_list'})

@login_required
def take_tool(request, tool_id):
    from django.utils import timezone
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST' and tool.is_available:
        tool.is_available = False
        tool.taken_by = request.user
        tool.taken_at = timezone.now()
        tool.save()
        log_activity(request.user, f"Took tool: {tool.name}", 'tool')
    return redirect('tools_list')

@login_required
def return_tool(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        if request.user == tool.taken_by or request.user.role == 'admin':
            tool.is_available = True
            tool.taken_by = None
            tool.taken_at = None
            tool.save()
            log_activity(request.user, f"Returned tool: {tool.name}", 'tool')
    return redirect('tools_list')

@login_required
def delete_tool(request, tool_id):
    if request.user.role != 'admin':
        return redirect('tools_list')
    tool = get_object_or_404(Tool, id=tool_id)
    tool.delete()
    return redirect('tools_list')

@login_required
def edit_tool(request, tool_id):
    if request.user.role != 'admin':
        return redirect('tools_list')
    tool = get_object_or_404(Tool, id=tool_id)
    if request.method == 'POST':
        form = ToolForm(request.POST, request.FILES, instance=tool)
        if form.is_valid():
            form.save()
            return redirect('tools_list')
    else:
        form = ToolForm(instance=tool)
    return render(request, 'form_template.html', {'form': form, 'title': 'Edit Tool', 'back_url': 'tools_list'})


# ═══════════════════════════════════════════════════════════════════════════════
# Assign Task for Site (Admin only — called from Sites page modal)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def assign_task_for_site(request):
    if request.method == 'POST' and request.user.role == 'admin':
        site_id = request.POST.get('site_id')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 'Medium')
        due_date = request.POST.get('due_date') or None
        worker_ids = request.POST.getlist('worker_ids')
        site = get_object_or_404(Site, id=site_id)
        task = Task.objects.create(
            title=title,
            description=description,
            site=site,
            priority=priority,
            due_date=due_date,
        )
        if worker_ids:
            task.assigned_workers.set(worker_ids)
        log_activity(request.user, f"Assigned task '{task.title}' to site: {site.name}", 'task')
        messages.success(request, f'Task "{title}" assigned successfully.')
    return redirect('admin_sites')


@login_required
def search_workers_api(request):
    query = request.GET.get('q', '')
    from django.db.models import Q
    workers = User.objects.filter(role='worker').filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:10]
    data = []
    for w in workers:
        designation = 'Worker'
        if hasattr(w, 'worker_profile'):
            designation = getattr(w.worker_profile, 'designation', 'Worker') or 'Worker'
        data.append({'id': w.id, 'name': w.get_full_name() or w.username, 'role': designation})
    return JsonResponse({'workers': data})


# ═══════════════════════════════════════════════════════════════════════════════
# Site Tasks — Admin view of tasks for a specific site
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def site_tasks(request, site_id):
    if request.user.role != 'admin':
        return redirect('login')
    site = get_object_or_404(Site, id=site_id)
    tasks = Task.objects.filter(site=site).prefetch_related('assigned_workers').order_by('-created_at')
    return render(request, 'site_tasks.html', {'site': site, 'tasks': tasks})


@login_required
def edit_task(request, task_id):
    if request.user.role != 'admin':
        return redirect('login')
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        task.title = request.POST.get('title', task.title)
        task.description = request.POST.get('description', task.description)
        task.priority = request.POST.get('priority', task.priority)
        task.status = request.POST.get('status', task.status)
        task.due_date = request.POST.get('due_date') or None
        worker_ids = request.POST.getlist('worker_ids')
        task.save()
        if worker_ids:
            task.assigned_workers.set(worker_ids)
        messages.success(request, f'Task "{task.title}" updated.')
        return redirect('site_tasks', site_id=task.site.id)
    workers = User.objects.filter(role='worker')
    return render(request, 'edit_task.html', {'task': task, 'workers': workers})


@login_required
def delete_task(request, task_id):
    if request.user.role != 'admin':
        return redirect('login')
    task = get_object_or_404(Task, id=task_id)
    site_id = task.site.id if task.site else None
    task.delete()
    messages.success(request, 'Task deleted.')
    if site_id:
        return redirect('site_tasks', site_id=site_id)
    return redirect('admin_sites')


# ═══════════════════════════════════════════════════════════════════════════════
# Worker: Update Task Status
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user in task.assigned_workers.all():
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'In Progress', 'Done']:
            task.status = new_status
            task.is_completed = (new_status == 'Done')
            task.save()
            log_activity(request.user, f"Updated task '{task.title}' status to {new_status}", 'task')
    return redirect('worker_my_tasks')


# ═══════════════════════════════════════════════════════════════════════════════
# Customer: Tasks for their site
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def customer_tasks(request):
    if request.user.role != 'customer':
        return redirect('login')
    try:
        site = Site.objects.get(customer=request.user)
        tasks = Task.objects.filter(site=site).prefetch_related(
            'assigned_workers',
            'assigned_workers__worker_profile',
        ).order_by('-created_at')
    except Site.DoesNotExist:
        site = None
        tasks = []
    return render(request, 'customer_tasks.html', {'tasks': tasks, 'site': site})


# ═══════════════════════════════════════════════════════════════════════════════
# Activity History / Audit Log
# ═══════════════════════════════════════════════════════════════════════════════

ACTIVITY_CATEGORIES = [
    ('', 'All'),
    ('attendance', '🕐 Attendance'),
    ('task', '📋 Task'),
    ('site', '🏗️ Site'),
    ('worker', '👷 Worker'),
    ('bill', '🧾 Bill'),
    ('update', '📸 Updates'),
    ('tool', '🔧 Tool'),
    ('product', '📦 Product'),
    ('auth', '🔐 Login / Logout'),
]

@login_required
def activity_history(request):
    if request.user.role != 'admin':
        return redirect('login')
    category = request.GET.get('category', '')
    logs = ActivityLog.objects.all().select_related('user').order_by('-timestamp')
    if category:
        logs = logs.filter(category=category)
        
    from django.utils import timezone
    from datetime import timedelta
    
    online_threshold = timezone.now() - timedelta(minutes=10)
    online_users = User.objects.filter(last_seen__gte=online_threshold).exclude(role='admin')
    
    recent_threshold = timezone.now() - timedelta(hours=1)
    recent_users = User.objects.filter(
        last_seen__gte=recent_threshold,
        last_seen__lt=online_threshold
    ).exclude(role='admin')
    
    return render(request, 'history.html', {
        'logs': logs,
        'category': category,
        'categories': ACTIVITY_CATEGORIES,
        'online_users': online_users,
        'recent_users': recent_users,
    })
