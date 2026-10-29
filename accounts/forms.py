from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, StudentType, Student, Role, PartnerInvestment, NonSubscriptionMeal


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'autocomplete': 'current-password'
        })
    )


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'code', 'description', 'can_access_admin', 'can_manage_users']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Partner / Investor'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. PARTNER'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe duties and rights for this role'}),
            'can_access_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        return code


class UserForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank to keep unchanged (if editing)'}),
        help_text="Required when creating a new user."
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. dr_sharma'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].empty_label = "-- Select User Role --"

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.instance.pk and not password:
            raise forms.ValidationError("Password is required for a new user.")
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class StudentTypeForm(forms.ModelForm):
    class Meta:
        model = StudentType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Monthly Basis'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of this student type scheme'}),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['user', 'student_type', 'roll_number', 'department', 'batch']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'student_type': forms.Select(attrs={'class': 'form-control'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MBBS-2023-045'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. General Medicine'}),
            'batch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MBBS 2023'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student_type'].empty_label = "-- Select Student Type --"
        self.fields['user'].empty_label = "-- Select User Account --"


class PartnerInvestmentForm(forms.ModelForm):
    class Meta:
        model = PartnerInvestment
        fields = [
            'partner',
            'amount',
            'purpose',
            'category',
            'payment_mode',
            'payment_date',
            'reference_number',
            'notes'
        ]
        widgets = {
            'partner': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'style': 'padding-left: 28px;'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Monthly Grocery Restock / Kitchen Appliances / LPG Gas'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UPI UTR / Invoice / Bill Ref No.'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional vendor info, shop address, or split notes'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        partner_users = User.objects.filter(role__code='PARTNER')
        self.fields['partner'].queryset = partner_users
        self.fields['partner'].empty_label = "-- Select Partner --"

        if user and user.is_partner and not self.initial.get('partner'):
            self.initial['partner'] = user.id


class NonSubscriptionMealForm(forms.ModelForm):
    class Meta:
        model = NonSubscriptionMeal
        fields = [
            'date',
            'meal_type',
            'batch',
            'roll_number',
            'diet',
            'price',
            'mobile_last_3',
            'payment_mode',
            'notes',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'meal_type': forms.Select(attrs={'class': 'form-control'}),
            'batch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MBBS 2023, BDS 2022'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MBBS-2023-045'}),
            'diet': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '80.00', 'step': '0.50', 'style': 'padding-left: 28px;'}),
            'mobile_last_3': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 849', 'maxlength': '3', 'pattern': '[0-9]{3}', 'title': 'Enter last 3 digits of student mobile'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional remarks, item details, UPI ref'}),
        }

    def clean_mobile_last_3(self):
        val = self.cleaned_data.get('mobile_last_3', '').strip()
        if not val.isdigit() or len(val) != 3:
            raise forms.ValidationError("Must be exactly 3 numeric digits (e.g. 849).")
        return val

    def clean_roll_number(self):
        return self.cleaned_data.get('roll_number', '').strip().upper()

