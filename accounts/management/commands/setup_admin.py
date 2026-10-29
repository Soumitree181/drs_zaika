import datetime
from django.core.management.base import BaseCommand
from accounts.models import User, StudentType, Student, Role, PartnerInvestment


class Command(BaseCommand):
    help = "Sets up the initial User Roles, Admin, Student Types, and sample records"

    def handle(self, *args, **options):
        # 1. User Roles
        role_admin, _ = Role.objects.get_or_create(
            code="ADMIN",
            defaults={
                "name": "Administrator",
                "description": "Full system control, permissions, and settings",
                "can_access_admin": True,
                "can_manage_users": True,
            }
        )
        role_partner, _ = Role.objects.get_or_create(
            code="PARTNER",
            defaults={
                "name": "Partner / Investor",
                "description": "Canteen partners with access to financials, student schemes, and user management",
                "can_access_admin": True,
                "can_manage_users": True,
            }
        )
        role_staff, _ = Role.objects.get_or_create(
            code="STAFF",
            defaults={
                "name": "Canteen Staff",
                "description": "Operational canteen staff managing daily students and meal counters",
                "can_access_admin": True,
                "can_manage_users": False,
            }
        )
        role_student, _ = Role.objects.get_or_create(
            code="STUDENT",
            defaults={
                "name": "Student",
                "description": "Medical college students enrolled in canteen dining (no admin access)",
                "can_access_admin": False,
                "can_manage_users": False,
            }
        )
        self.stdout.write(self.style.SUCCESS(f"✔ User Roles ready: ADMIN, PARTNER, STAFF, STUDENT"))

        # 2. Admin User
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@canteen.com",
                "role": role_admin,
                "is_staff": True,
                "is_superuser": True,
            }
        )
        admin_user.role = role_admin
        admin_user.set_password("admin123")
        admin_user.save()
        self.stdout.write(self.style.SUCCESS(f"✔ Admin ready: admin / admin123"))

        # 3. Student Types
        monthly, _ = StudentType.objects.get_or_create(
            name="Monthly Basis",
            defaults={"description": "Monthly recurring meal subscription scheme"}
        )
        pay_meal, _ = StudentType.objects.get_or_create(
            name="Meal Basis (Pay-per-meal)",
            defaults={"description": "Pay individually per meal or token"}
        )
        self.stdout.write(self.style.SUCCESS(f"✔ Student Types ready: '{monthly.name}', '{pay_meal.name}'"))

        # 4. Sample Partners (3 Partners as required by specs)
        p1, _ = User.objects.get_or_create(
            username="partner_sharma",
            defaults={
                "first_name": "Alok",
                "last_name": "Sharma",
                "email": "sharma@partner.com",
                "role": role_partner,
                "phone": "+91 98111 22334"
            }
        )
        p1.role = role_partner
        p1.set_password("partner123")
        p1.save()

        p2, _ = User.objects.get_or_create(
            username="partner_patel",
            defaults={
                "first_name": "Priya",
                "last_name": "Patel",
                "email": "patel@partner.com",
                "role": role_partner,
                "phone": "+91 98111 33445"
            }
        )
        p2.role = role_partner
        p2.set_password("partner123")
        p2.save()

        p3, _ = User.objects.get_or_create(
            username="partner_verma",
            defaults={
                "first_name": "Vikram",
                "last_name": "Verma",
                "email": "verma@partner.com",
                "role": role_partner,
                "phone": "+91 98111 55667"
            }
        )
        p3.role = role_partner
        p3.set_password("partner123")
        p3.save()

        # Seed sample Partner Investments / Payments
        today = datetime.date.today()
        PartnerInvestment.objects.get_or_create(
            purpose="Monthly Rice, Wheat & Pulses Restock",
            defaults={
                "partner": p1,
                "amount": 35000.00,
                "category": "GROCERIES",
                "payment_mode": "BANK_TRANSFER",
                "payment_date": today - datetime.timedelta(days=12),
                "reference_number": "UTR-SBIN-892341",
                "notes": "Purchased from Metro Cash & Carry wholesale",
                "recorded_by": p1,
            }
        )
        PartnerInvestment.objects.get_or_create(
            purpose="Commercial Induction Counter & Rice Steam Cooker",
            defaults={
                "partner": p2,
                "amount": 48500.00,
                "category": "EQUIPMENT",
                "payment_mode": "UPI",
                "payment_date": today - datetime.timedelta(days=8),
                "reference_number": "UPI-GPay-90342",
                "notes": "Kitchen commercial appliance upgrade",
                "recorded_by": p2,
            }
        )
        PartnerInvestment.objects.get_or_create(
            purpose="Commercial LPG Gas 4 Cylinders Refill",
            defaults={
                "partner": p3,
                "amount": 8200.00,
                "category": "GAS_UTILITIES",
                "payment_mode": "UPI",
                "payment_date": today - datetime.timedelta(days=3),
                "reference_number": "INV-HPCL-7782",
                "notes": "HP Gas Commercial Distributor",
                "recorded_by": p3,
            }
        )
        PartnerInvestment.objects.get_or_create(
            purpose="Weekly Vegetables, Paneer & Fresh Milk Supplies",
            defaults={
                "partner": p1,
                "amount": 14250.00,
                "category": "VEGETABLES_DAIRY",
                "payment_mode": "CASH",
                "payment_date": today - datetime.timedelta(days=1),
                "reference_number": "BILL-MANDI-441",
                "notes": "Mandi wholesale market bulk procurement",
                "recorded_by": p1,
            }
        )

        staff, _ = User.objects.get_or_create(
            username="staff_ramesh",
            defaults={
                "first_name": "Ramesh",
                "last_name": "Kumar",
                "email": "ramesh@canteen.com",
                "role": role_staff,
                "phone": "+91 98222 33445"
            }
        )
        staff.role = role_staff
        staff.set_password("staff123")
        staff.save()

        student_user, _ = User.objects.get_or_create(
            username="student_arjun",
            defaults={
                "first_name": "Arjun",
                "last_name": "Gupta",
                "email": "arjun@medcollege.edu",
                "role": role_student,
                "phone": "+91 98333 44556"
            }
        )
        student_user.role = role_student
        student_user.set_password("student123")
        student_user.save()

        # 5. Sample Student record with StudentType assigned
        Student.objects.get_or_create(
            user=student_user,
            defaults={
                "student_type": monthly,
                "roll_number": "MBBS-2023-045",
                "department": "General Medicine",
                "batch": "MBBS 2023",
            }
        )
        self.stdout.write(self.style.SUCCESS("✔ Sample Users & Student records created successfully!"))
