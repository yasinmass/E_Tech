from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('worker', 'Worker'),
        ('customer', 'Customer'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')
    phone = models.CharField(max_length=15, blank=True)

class Site(models.Model):
    STATUS_CHOICES = [
        ('Not Started', 'Not Started'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=500, blank=True)
    owner_phone = models.CharField(max_length=20, blank=True)
    site_photo = models.ImageField(upload_to='sites/photos/', blank=True, null=True)
    owner_photo = models.ImageField(upload_to='sites/owners/', blank=True, null=True)
    customer = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_site'
    )
    workers = models.ManyToManyField(User, related_name='assigned_sites', limit_choices_to={'role': 'worker'}, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='In Progress')
    location = models.URLField(max_length=500, blank=True, null=True, verbose_name='Google Maps Link')
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks', limit_choices_to={'role': 'worker'})
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='tasks')
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.site.name})"

class Attendance(models.Model):
    SLOT_CHOICES = (
        ('early', 'Early Morning (5 AM - 8 AM)'),
        ('morning', 'Morning (9 AM - 1 PM)'),
        ('afternoon', 'Afternoon (1 PM - 6 PM)')
    )
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance', limit_choices_to={'role': 'worker'})
    date = models.DateField(auto_now_add=True)
    slot = models.CharField(max_length=20, choices=SLOT_CHOICES)
    is_present = models.BooleanField(default=True)

    class Meta:
        unique_together = ('worker', 'date', 'slot')

    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.worker.username} - {self.date} - {self.get_slot_display()} - {status}"

class WorkUpdate(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='updates')
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_updates', limit_choices_to={'role': 'worker'})
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to='updates/images/', blank=True, null=True)
    video = models.FileField(upload_to='updates/videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Update by {self.worker} at {self.site} on {self.created_at.date()}"

class Bill(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='bills')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='bills/', blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bill ₹{self.amount} - {self.site.name}"

class WorkerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker_profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    family_phone = models.CharField(max_length=20, blank=True, verbose_name='Family Contact Number')
    address = models.TextField(blank=True)
    id_proof = models.ImageField(upload_to='workers/id_proofs/', blank=True, null=True, verbose_name='ID Proof Photo')
    photo = models.ImageField(upload_to='workers/photos/', blank=True, null=True, verbose_name='Worker Photo')

class Product(models.Model):
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=0)
    size = models.CharField(max_length=100, blank=True)
    place = models.CharField(max_length=200, blank=True)
    photo = models.ImageField(upload_to='products/', blank=True, null=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_low_stock(self):
        return self.quantity <= 5

    def __str__(self):
        return self.name
