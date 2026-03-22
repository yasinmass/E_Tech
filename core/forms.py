from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Site, Task, Attendance, WorkUpdate, Bill, WorkerProfile, Product, Tool

# ── Existing: Worker creation ─────────────────────────────────────────────────
class AddWorkerForm(forms.ModelForm):
    full_name = forms.CharField(max_length=200, label='Full Name')
    age = forms.IntegerField(label='Age')
    phone = forms.CharField(max_length=20, label='Phone Number')
    family_phone = forms.CharField(max_length=20, label='Family Contact Number')
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Address')
    photo = forms.ImageField(label='Worker Photo', required=False)
    id_proof = forms.ImageField(label='ID Proof Photo', required=False)
    login_username = forms.CharField(max_length=150, label='Login Username')
    login_password = forms.CharField(widget=forms.PasswordInput, label='Login Password')

    class Meta:
        model = User
        fields = []
        
    def clean_login_username(self):
        login_username = self.cleaned_data['login_username']
        if User.objects.filter(username=login_username).exists():
            raise forms.ValidationError('This username is already taken.')
        return login_username

# ── NEW: Customer creation ────────────────────────────────────────────────────
class CustomerCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'customer'
        if commit:
            user.save()
        return user

# ── NEW: Worker edit (no username change, optional password) ──────────────────
class WorkerEditForm(forms.ModelForm):
    full_name = forms.CharField(max_length=200, label='Full Name')
    age = forms.IntegerField(label='Age')
    phone = forms.CharField(max_length=20, label='Phone Number')
    family_phone = forms.CharField(max_length=20, label='Family Contact Number')
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Address')
    photo = forms.ImageField(label='Worker Photo', required=False)
    id_proof = forms.ImageField(label='ID Proof Photo', required=False)
    new_username = forms.CharField(max_length=150, label='Login Username', required=False)
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep current'}),
        label='New Password',
        help_text='Leave blank to keep the existing password.'
    )

    class Meta:
        model = User
        fields = []

    def clean_new_username(self):
        new_username = self.cleaned_data.get('new_username')
        if new_username:
            if User.objects.filter(username=new_username).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('This username is already taken.')
        return new_username

# ── Existing: Site, Task, Attendance ─────────────────────────────────────────
# ── Site: Add (creates customer login automatically) ─────────────────────────
class SiteForm(forms.ModelForm):
    owner_username = forms.CharField(max_length=150, label='Owner Login Username')
    owner_password = forms.CharField(widget=forms.PasswordInput, label='Owner Login Password')

    class Meta:
        model = Site
        fields = ['name', 'address', 'site_photo', 'owner_name', 'owner_phone', 'owner_photo', 'location']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Enforce display order
        field_order = ['name', 'address', 'location', 'site_photo', 'owner_name', 'owner_phone', 'owner_photo',
                       'owner_username', 'owner_password']
        self.fields = {k: self.fields[k] for k in field_order if k in self.fields}

    def clean_owner_username(self):
        username = self.cleaned_data['owner_username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

# ── Site: Edit ───────────────────────────────────────────────────────────────
class SiteEditForm(forms.ModelForm):
    owner_name_field   = forms.CharField(max_length=200, label='Owner Name', required=False)
    owner_phone_field  = forms.CharField(max_length=20, label='Owner Phone', required=False)
    new_username       = forms.CharField(max_length=150, label='Owner Username', required=False)
    new_password       = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep current'}),
        label='New Owner Password', required=False
    )
    status = forms.ChoiceField(
        choices=[('Not Started', 'Not Started'), ('In Progress', 'In Progress'), ('Completed', 'Completed')],
        label='Site Status'
    )

    class Meta:
        model = Site
        fields = ['name', 'address', 'location', 'site_photo', 'owner_photo', 'status']

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'site', 'assigned_workers', 'priority', 'due_date', 'status']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['worker', 'slot', 'is_present']

# ── Existing + File Size Validation: WorkUpdate ──────────────────────────────
class WorkUpdateForm(forms.ModelForm):
    class Meta:
        model = WorkUpdate
        fields = ['site', 'text', 'image']
        labels = {
            'site': 'Select Site',
            'text': 'Caption / Description',
            'image': 'Upload Image',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show all sites in dropdown
        self.fields['site'].queryset = Site.objects.all().order_by('name')
        self.fields['site'].empty_label = 'Select a site...'

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            if image.size > 10 * 1024 * 1024:  # 10 MB
                raise forms.ValidationError('Image file is too large. Maximum allowed size is 10 MB.')
        return image

# ── Existing + File Size Validation: Bill ────────────────────────────────────
class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['site', 'amount', 'description', 'image']
        labels = {
            'site': 'Select Site',
            'amount': 'Amount (₹)',
            'description': 'Description / Notes',
            'image': 'Bill Photo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['site'].queryset = Site.objects.all().order_by('name')
        self.fields['site'].empty_label = 'Select a site...'

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            if image.size > 10 * 1024 * 1024:  # 10 MB
                raise forms.ValidationError('Bill photo is too large. Maximum allowed size is 10 MB.')
        return image

# ── NEW: Profile Settings ─────────────────────────────────────────────────────
class ProfileSettingsForm(forms.Form):
    first_name    = forms.CharField(max_length=150, required=False, label='First Name')
    last_name     = forms.CharField(max_length=150, required=False, label='Last Name')
    phone         = forms.CharField(max_length=15,  required=False, label='Phone Number')
    current_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='Current Password',
        help_text='Required only if you want to change your password.'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='New Password',
        help_text='Leave blank to keep your current password.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        label='Confirm New Password'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        new_pw      = cleaned.get('new_password')
        confirm_pw  = cleaned.get('confirm_password')
        current_pw  = cleaned.get('current_password')

        if new_pw:
            if self.user.role in ['worker', 'customer'] and not self.user.is_superuser:
                raise forms.ValidationError('You do not have permission to change your password.')
            if not current_pw:
                raise forms.ValidationError('Please enter your current password to set a new one.')
            if not self.user.check_password(current_pw):
                raise forms.ValidationError('Current password is incorrect.')
            if new_pw != confirm_pw:
                raise forms.ValidationError('New passwords do not match.')
        return cleaned

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'quantity', 'size', 'place']
        labels = {
            'name': 'Product Name',
            'quantity': 'Quantity',
            'size': 'Size (e.g. 2 inch x 10ft)',
            'place': 'Storage Place / Location',
        }

class ToolForm(forms.ModelForm):
    class Meta:
        model = Tool
        fields = ['name', 'location', 'description', 'photo']
        labels = {
            'name': 'Tool Name',
            'location': 'Storage Location',
            'description': 'Description (optional)',
            'photo': 'Tool Photo',
        }
