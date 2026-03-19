import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'etech.settings')
django.setup()

from core.models import User, Site

def seed_data():
    print("Seeding database...")

    # Admin
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@etech.com', 'admin')
        admin.role = 'admin'
        admin.first_name = 'Admin'
        admin.save()
        print("Created admin user: admin / admin")
    else:
        # Fix role if empty
        admin = User.objects.get(username='admin')
        if not admin.role:
            admin.role = 'admin'
            admin.save()
        print("Admin user already exists (role:", admin.role, ")")

    # Worker
    if not User.objects.filter(username='worker1').exists():
        worker = User.objects.create_user('worker1', 'worker@etech.com', 'worker')
        worker.role = 'worker'
        worker.first_name = 'John'
        worker.last_name = 'Doe'
        worker.phone = '9876543210'
        worker.save()
        print("Created worker: worker1 / worker")
    else:
        print("worker1 already exists")

    # Customer
    if not User.objects.filter(username='customer1').exists():
        customer = User.objects.create_user('customer1', 'customer@etech.com', 'customer')
        customer.role = 'customer'
        customer.first_name = 'Alice'
        customer.last_name = 'Smith'
        customer.save()
        print("Created customer: customer1 / customer")
    else:
        print("customer1 already exists")

    # Site
    customer = User.objects.get(username='customer1')
    worker = User.objects.get(username='worker1')
    if not Site.objects.filter(name='Oceanview Villa').exists():
        site = Site.objects.create(
            name='Oceanview Villa',
            customer=customer,
            address='123 Beach Road, Kozhikode, Kerala',
            owner_name='Alice Smith',
            owner_phone='9876543210',
        )
        site.workers.add(worker)
        print("Created site: Oceanview Villa")
    else:
        print("Site already exists")

    print("\n=== Login Credentials ===")
    print("Admin:    admin    / admin")
    print("Worker:   worker1  / worker")
    print("Customer: customer1/ customer")
    print("\nServer: http://127.0.0.1:8000/")

if __name__ == "__main__":
    seed_data()
