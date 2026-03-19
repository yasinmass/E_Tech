from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ── Admin core ────────────────────────────────────────────────────────────
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('mgmt/workers/', views.admin_workers, name='admin_workers'),
    path('mgmt/workers/<int:worker_id>/', views.worker_detail, name='worker_detail'),
    path('mgmt/workers/ajax-mark/', views.admin_mark_worker_ajax, name='admin_mark_worker_ajax'),
    path('mgmt/sites/', views.admin_sites, name='admin_sites'),
    path('mgmt/tasks/', views.admin_tasks, name='admin_tasks'),
    path('mgmt/attendance/', views.admin_all_attendance, name='admin_all_attendance'),
    path('mgmt/updates/', views.admin_updates, name='admin_updates'),
    path('mgmt/bills/', views.admin_all_bills, name='admin_all_bills'),

    # ── Admin: Create ─────────────────────────────────────────────────────────
    path('mgmt/add-worker/', views.add_worker, name='add_worker'),
    path('mgmt/add-site/', views.add_site, name='add_site'),
    path('mgmt/assign-task/', views.assign_task, name='assign_task'),
    path('mgmt/mark-attendance/', views.admin_mark_attendance, name='admin_mark_attendance'),
    path('mgmt/upload-bill/', views.upload_bill, name='admin_upload_bill'),

    # ── Admin: Customers (Feature 1) ──────────────────────────────────────────
    path('mgmt/customers/', views.admin_customers, name='admin_customers'),
    path('mgmt/add-customer/', views.add_customer, name='add_customer'),

    # ── Admin: Edit & Delete — Workers (Feature 2) ────────────────────────────
    path('mgmt/workers/<int:worker_id>/edit/', views.edit_worker, name='edit_worker'),
    path('mgmt/workers/<int:worker_id>/delete/', views.delete_worker, name='delete_worker'),

    # ── Admin: Edit & Delete — Sites (Feature 2) ──────────────────────────────
    path('mgmt/sites/<int:site_id>/edit/', views.edit_site, name='edit_site'),
    path('mgmt/sites/<int:site_id>/delete/', views.delete_site, name='delete_site'),
    path('mgmt/sites/assign-task/', views.assign_task_for_site, name='assign_task_for_site'),
    path('mgmt/api/search-workers/', views.search_workers_api, name='search_workers_api'),

    # ── Admin: Edit & Delete — Tasks (Feature 2) ──────────────────────────────
    path('mgmt/tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('mgmt/tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('mgmt/sites/<int:site_id>/tasks/', views.site_tasks, name='site_tasks'),

    # ── Admin: Edit & Delete — Bills (Feature 2) ──────────────────────────────
    path('mgmt/bills/<int:bill_id>/edit/', views.edit_bill, name='edit_bill'),
    path('mgmt/bills/<int:bill_id>/delete/', views.delete_bill, name='delete_bill'),

    # ── Worker core ───────────────────────────────────────────────────────────
    path('worker-dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('worker/my-tasks/', views.worker_my_tasks, name='worker_my_tasks'),
    path('worker/my-sites/', views.worker_my_sites, name='worker_my_sites'),
    path('worker/my-attendance/', views.worker_my_attendance, name='worker_my_attendance'),
    path('worker/my-updates/', views.worker_my_updates, name='worker_my_updates'),
    path('worker/my-bills/', views.worker_my_bills, name='worker_my_bills'),

    # ── Worker: Actions ───────────────────────────────────────────────────────
    path('worker/task-complete/<int:task_id>/', views.worker_mark_task_complete, name='worker_mark_task_complete'),
    path('worker/task-status/<int:task_id>/', views.update_task_status, name='update_task_status'),
    path('worker/mark-attendance/', views.worker_mark_attendance, name='worker_mark_attendance'),
    path('worker/upload-update/', views.worker_upload_update, name='worker_upload_update'),
    path('worker/upload-bill/', views.worker_upload_bill, name='worker_upload_bill'),

    # ── Customer core ─────────────────────────────────────────────────────────
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/sites/', views.customer_sites, name='customer_sites'),
    path('customer/updates/', views.customer_updates, name='customer_updates'),
    path('customer/bills/', views.customer_bills, name='customer_bills'),
    path('customer/tasks/', views.customer_tasks, name='customer_tasks'),

    # ── Profile Settings — all roles (Feature 5) ──────────────────────────────
    path('profile/', views.profile_settings, name='profile_settings'),
    path('history/', views.activity_history, name='activity_history'),


    # ── Products / Inventory ───────────────────────────────────────────────────
    path('products/', views.products_list, name='products_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:product_id>/qty/', views.update_product_qty, name='update_product_qty'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),

    # ── Tools / Equipment ─────────────────────────────────────────────────────
    path('tools/', views.tools_list, name='tools_list'),
    path('tools/add/', views.add_tool, name='add_tool'),
    path('tools/<int:tool_id>/take/', views.take_tool, name='take_tool'),
    path('tools/<int:tool_id>/return/', views.return_tool, name='return_tool'),
    path('tools/<int:tool_id>/delete/', views.delete_tool, name='delete_tool'),
    path('tools/<int:tool_id>/edit/', views.edit_tool, name='edit_tool'),
]