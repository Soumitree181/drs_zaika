from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. Partner / Investor, Canteen Staff, Student, Administrator")
    code = models.CharField(max_length=30, unique=True, help_text="Unique identifier code, e.g. PARTNER, STAFF, STUDENT, ADMIN")
    description = models.TextField(blank=True, null=True, help_text="Details about duties, privileges, or scope of this role")
    can_access_admin = models.BooleanField(default=True, help_text="Whether users with this role can log into the admin panel")
    can_manage_users = models.BooleanField(default=False, help_text="Whether users with this role can create/edit users and roles")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'

    def __str__(self):
        return f"{self.name} ({self.code})"


class User(AbstractUser):
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Assigned system role"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        role_name = self.role.name if self.role else "No Role"
        return f"{self.username} ({role_name})"

    def get_role_display(self) -> str:
        """Returns the human-readable name of the assigned Role or 'No Role Assigned'."""
        return self.role.name if self.role else "No Role Assigned"

    # -----------------------------------------------------------------------
    # Role & Permission Properties
    # -----------------------------------------------------------------------
    @property
    def is_partner(self) -> bool:
        if self.is_superuser:
            return True
        return bool(self.role and self.role.code == 'PARTNER')

    @property
    def is_canteen_staff(self) -> bool:
        return bool(self.role and self.role.code == 'STAFF')

    @property
    def is_student(self) -> bool:
        return bool(self.role and self.role.code == 'STUDENT')

    @property
    def can_access_admin_panel(self) -> bool:
        """Only users with can_access_admin (Staff, Partners, Admins) can access. Students are strictly barred."""
        if not self.is_authenticated:
            return False
        if self.is_superuser:
            return True
        return bool(self.role and self.role.can_access_admin)

    @property
    def can_manage_users(self) -> bool:
        """Only Partners and Admins with can_manage_users can manage user accounts and assign roles."""
        if not self.is_authenticated:
            return False
        if self.is_superuser:
            return True
        return bool(self.role and self.role.can_manage_users)

    @property
    def can_manage_students(self) -> bool:
        return self.can_access_admin_panel


class StudentType(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Monthly Basis, Meal Basis (Pay-per-meal)")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Student Type'
        verbose_name_plural = 'Student Types'

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_record'
    )
    student_type = models.ForeignKey(
        StudentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    roll_number = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    batch = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        st_type = self.student_type.name if self.student_type else "No Type"
        return f"{self.user.username} ({self.roll_number}) - {st_type}"

    @property
    def is_monthly_subscriber(self) -> bool:
        if not self.student_type:
            return False
        return 'month' in self.student_type.name.lower()


class StudentMealRecord(models.Model):
    """
    Tracks daily meal consumption (Breakfast, Lunch, Dinner) for students,
    particularly monthly subscribers receiving 3 meals a day.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='meal_records',
        help_text="Student receiving the meals"
    )
    date = models.DateField(
        default=timezone.now,
        db_index=True,
        help_text="Date of meal service"
    )
    breakfast = models.BooleanField(
        default=False,
        help_text="Morning Meal / Breakfast taken"
    )
    lunch = models.BooleanField(
        default=False,
        help_text="Afternoon Meal / Lunch taken"
    )
    dinner = models.BooleanField(
        default=False,
        help_text="Night Meal / Dinner taken"
    )
    notes = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Optional remarks or dietary notes"
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_student_meals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date', '-created_at']
        verbose_name = 'Student Meal Record'
        verbose_name_plural = 'Student Meal Records'

    def __str__(self):
        return f"{self.student.roll_number} on {self.date}: B={int(self.breakfast)} L={int(self.lunch)} D={int(self.dinner)}"

    @property
    def total_meals(self) -> int:
        return int(self.breakfast) + int(self.lunch) + int(self.dinner)

    @property
    def has_any_meal(self) -> bool:
        return self.breakfast or self.lunch or self.dinner


class PartnerInvestment(models.Model):
    CATEGORY_CHOICES = [
        ('GROCERIES', 'Raw Groceries & Cooking Ingredients'),
        ('VEGETABLES_DAIRY', 'Vegetables, Milk & Dairy'),
        ('EQUIPMENT', 'Kitchen Equipment & Appliances'),
        ('GAS_UTILITIES', 'LPG Gas, Electricity & Utilities'),
        ('SALARIES', 'Staff Salaries & Advance Wages'),
        ('MAINTENANCE', 'Canteen Repairs & Maintenance'),
        ('PACKAGING', 'Packaging, Disposables & Cutlery'),
        ('CAPITAL', 'Working Capital / Cash Infusion'),
        ('OTHER', 'Other Operational Expenses'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('UPI', 'UPI (GPay / PhonePe / Paytm / QR)'),
        ('CASH', 'Cash Payment'),
        ('BANK_TRANSFER', 'Bank Transfer (NEFT / IMPS / RTGS)'),
        ('CARD', 'Debit / Credit Card'),
        ('CHEQUE', 'Cheque Payment'),
    ]

    partner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='investments',
        help_text="Partner who contributed this investment/expense"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount in ₹"
    )
    purpose = models.CharField(
        max_length=200,
        help_text="Item / Service paid for, e.g. Monthly Grocery Restock, Commercial Mixer Grinder, LPG Refill"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='GROCERIES',
        help_text="Category of expenditure/investment"
    )
    payment_mode = models.CharField(
        max_length=30,
        choices=PAYMENT_MODE_CHOICES,
        default='UPI',
        help_text="Payment method used"
    )
    payment_date = models.DateField(
        default=timezone.now,
        help_text="Date when payment was made"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Invoice / Bill number or UPI transaction UTR"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Vendor name, shop details, or additional remarks"
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_partner_investments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Partner Investment'
        verbose_name_plural = 'Partner Investments'

    def __str__(self):
        return f"₹{self.amount} by {self.partner.username} - {self.purpose} ({self.payment_date})"


class NonSubscriptionMeal(models.Model):
    """
    Daily register for non-subscription walk-in students purchasing individual meals:
    Records Batch, Roll number, Veg/Non-veg, Price, Last 3 digits of Mobile, and Payment mode.
    """
    DIET_CHOICES = [
        ('VEG', 'Veg'),
        ('NON_VEG', 'Non-Veg'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('ONLINE', 'Online (UPI / QR / Net Banking)'),
        ('CASH', 'Cash'),
    ]

    MEAL_TYPE_CHOICES = [
        ('BREAKFAST', 'Breakfast'),
        ('LUNCH', 'Lunch'),
        ('DINNER', 'Dinner'),
        ('SNACKS', 'Snacks / Refreshment'),
    ]

    date = models.DateField(
        default=timezone.now,
        db_index=True,
        help_text="Date of meal service"
    )
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_TYPE_CHOICES,
        default='LUNCH',
        help_text="Breakfast, Lunch, Dinner, or Snacks"
    )
    batch = models.CharField(
        max_length=50,
        help_text="Student Batch (e.g. MBBS 2023, BDS 2022)"
    )
    roll_number = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Student Roll Number"
    )
    diet = models.CharField(
        max_length=10,
        choices=DIET_CHOICES,
        default='VEG',
        help_text="Veg or Non-Veg"
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Meal price in ₹"
    )
    mobile_last_3 = models.CharField(
        max_length=3,
        help_text="Last 3 digits of student mobile number"
    )
    payment_mode = models.CharField(
        max_length=10,
        choices=PAYMENT_MODE_CHOICES,
        default='ONLINE',
        help_text="Mode of Payment (Online or Cash)"
    )
    notes = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Optional remarks, item details, or UPI transaction ref"
    )
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_non_sub_meals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Non-Subscription Register'
        verbose_name_plural = 'Non-Subscription Student Register'

    def __str__(self):
        return f"{self.roll_number} [{self.batch}] - {self.get_diet_display()} ₹{self.price} ({self.get_payment_mode_display()})"

