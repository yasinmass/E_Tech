from django.shortcuts import render, redirect, get_object_or_404
from .models import User, Site, Task, Attendance, WorkUpdate, Bill
from django.contrib.auth.decorators import login_required
from .views import role_required
from datetime import date

@role_required('admin')
def admin_workers(request):
    workers = User.objects.filter(role='worker')
    for worker in workers:
        tot = Attendance.objects.filter(worker=worker, is_present=True).count()
        worker.present_days = tot // 2
        worker.remaining_slots = tot % 2
        uq = Attendance.objects.filter(worker=worker).values('date').distinct().count()
        worker.absent_days = max(uq - worker.present_days, 0)
        worker.total_slots = tot
    return render(request, 'admin_workers.html', {'workers': workers})

@role_required('admin')
def admin_sites(request):
    return render(request, 'admin_sites.html', {'sites': Site.objects.all()})

@role_required('admin')
def admin_tasks(request):
    return render(request, 'admin_tasks.html', {'tasks': Task.objects.select_related('worker', 'site').order_by('-created_at')})

@role_required('admin')
def admin_all_attendance(request):
    return render(request, 'admin_attendance.html', {'attendances': Attendance.objects.select_related('worker').order_by('-date'), 'today': date.today()})

@role_required('admin')
def admin_updates(request):
    return render(request, 'admin_updates.html', {'updates': WorkUpdate.objects.select_related('worker', 'site').order_by('-created_at')})

@role_required('admin')
def admin_all_bills(request):
    return render(request, 'admin_bills.html', {'bills': Bill.objects.select_related('site', 'uploaded_by').order_by('-date')})

# --- WORKER VIEWS ---
@role_required('worker')
def worker_my_tasks(request):
    return render(request, 'worker_tasks.html', {'tasks': Task.objects.filter(worker=request.user).select_related('site').order_by('-created_at')})

@role_required('worker')
def worker_my_sites(request):
    return render(request, 'worker_sites.html', {'sites': request.user.assigned_sites.all()})

@role_required('worker')
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
    return render(request, 'customer_bills.html', {'bills': Bill.objects.filter(site__customer=request.user).order_by('-date')})
