from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, StudentType, Student, Role


class RoleAndPermissionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Roles
        self.role_admin = Role.objects.create(
            name='Administrator', code='ADMIN', can_access_admin=True, can_manage_users=True
        )
        self.role_partner = Role.objects.create(
            name='Partner', code='PARTNER', can_access_admin=True, can_manage_users=True
        )
        self.role_staff = Role.objects.create(
            name='Staff', code='STAFF', can_access_admin=True, can_manage_users=False
        )
        self.role_student = Role.objects.create(
            name='Student', code='STUDENT', can_access_admin=False, can_manage_users=False
        )

        # 1. Admin
        self.admin = User.objects.create_user(
            username='admin',
            password='password123',
            role=self.role_admin,
            is_staff=True,
            is_superuser=True
        )

        # 2. Partner
        self.partner = User.objects.create_user(
            username='partner_user',
            password='password123',
            role=self.role_partner,
            first_name='Partner'
        )

        # 3. Staff
        self.staff = User.objects.create_user(
            username='staff_user',
            password='password123',
            role=self.role_staff,
            first_name='Staff'
        )

        # 4. Student
        self.student = User.objects.create_user(
            username='student_user',
            password='password123',
            role=self.role_student,
            first_name='Student'
        )

        # Student Type & Record
        self.type_monthly = StudentType.objects.create(name='Monthly Basis')
        self.student_record = Student.objects.create(
            user=self.student,
            student_type=self.type_monthly,
            roll_number='MBBS-2023-001'
        )

    def test_role_crud_by_partner(self):
        """Partners can view, create, and update User Roles."""
        self.client.login(username='partner_user', password='password123')

        # List roles
        res = self.client.get(reverse('role_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Administrator')
        self.assertContains(res, 'Partner')
        self.assertContains(res, 'Staff')
        self.assertContains(res, 'Student')

        # Create new role
        res = self.client.post(reverse('role_create'), {
            'name': 'Accountant',
            'code': 'ACCOUNTANT',
            'description': 'Handles daily bookkeeping and invoices',
            'can_access_admin': True,
            'can_manage_users': False,
        })
        self.assertRedirects(res, reverse('role_list'))
        self.assertTrue(Role.objects.filter(code='ACCOUNTANT').exists())

    def test_role_management_blocked_for_staff(self):
        """Staff members cannot manage user roles."""
        self.client.login(username='staff_user', password='password123')

        res = self.client.get(reverse('role_list'))
        self.assertRedirects(res, reverse('admin_dashboard'))

        res = self.client.post(reverse('role_create'), {
            'name': 'Hacker',
            'code': 'HACKER'
        })
        self.assertRedirects(res, reverse('admin_dashboard'))

    def test_student_cannot_access_any_admin_panel_operations(self):
        """Students must be strictly blocked from viewing or operating in the admin panel."""
        self.client.login(username='student_user', password='password123')

        # Dashboard -> redirects to access-denied
        res = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(res, reverse('access_denied'), target_status_code=403)

        # Roles List -> redirects to access-denied
        res = self.client.get(reverse('role_list'))
        self.assertRedirects(res, reverse('access_denied'), target_status_code=403)

        # User List -> redirects to access-denied
        res = self.client.get(reverse('user_list'))
        self.assertRedirects(res, reverse('access_denied'), target_status_code=403)

        # Student Types -> redirects to access-denied
        res = self.client.get(reverse('student_type_list'))
        self.assertRedirects(res, reverse('access_denied'), target_status_code=403)

        # Students -> redirects to access-denied
        res = self.client.get(reverse('student_list'))
        self.assertRedirects(res, reverse('access_denied'), target_status_code=403)

    def test_staff_permissions(self):
        """Staff can access dashboard, student types, and students, but cannot manage users or roles."""
        self.client.login(username='staff_user', password='password123')

        # Can access dashboard, student types, students
        self.assertEqual(self.client.get(reverse('admin_dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('student_type_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('student_list')).status_code, 200)

        # CANNOT access user management
        self.assertRedirects(self.client.get(reverse('user_list')), reverse('admin_dashboard'))
        self.assertRedirects(self.client.get(reverse('role_list')), reverse('admin_dashboard'))

    def test_partner_permissions(self):
        """Partners can access dashboard, manage users, user roles, student types, and students."""
        self.client.login(username='partner_user', password='password123')

        self.assertEqual(self.client.get(reverse('admin_dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('user_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('role_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('student_type_list')).status_code, 200)
        self.assertEqual(self.client.get(reverse('student_list')).status_code, 200)

    def test_partner_list_and_investment_crud(self):
        """Partners and Admins can access clean Partners list, Partner View Page with date filter, and record spends."""
        from accounts.models import PartnerInvestment
        import datetime

        self.client.login(username='partner_user', password='password123')

        # 1. Partner list view (Clean with Add Partner & Add Spend options)
        res = self.client.get(reverse('partner_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '+ Add Partner')
        self.assertContains(res, '+ Add Spend')
        self.assertContains(res, 'partner_user')
        self.assertContains(res, reverse('partner_detail', args=[self.partner.id]))

        # 2. Add spend for partner
        res = self.client.post(reverse('investment_create'), {
            'partner': self.partner.id,
            'amount': '25000.00',
            'purpose': 'Bulk Rice and Pulses restock for Canteen',
            'category': 'GROCERIES',
            'payment_mode': 'UPI',
            'payment_date': str(datetime.date.today()),
            'reference_number': 'UPI-TEST-12345',
            'notes': 'Test investment',
        })
        self.assertRedirects(res, reverse('partner_detail', args=[self.partner.id]))
        self.assertEqual(PartnerInvestment.objects.count(), 1)
        inv = PartnerInvestment.objects.first()
        self.assertEqual(inv.amount, 25000.00)
        self.assertEqual(inv.partner, self.partner)

        # 3. View respective partner view page
        res = self.client.get(reverse('partner_detail', args=[self.partner.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Bulk Rice and Pulses restock')
        self.assertContains(res, '25000.00')
        self.assertContains(res, 'All-Time Total Spend')

        # 4. Date filter on partner view page
        res = self.client.get(reverse('partner_detail', args=[self.partner.id]) + f"?from_date={datetime.date.today()}&to_date={datetime.date.today()}")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Bulk Rice and Pulses restock')

        # Filter outside range -> empty
        old_date = str(datetime.date.today() - datetime.timedelta(days=30))
        res = self.client.get(reverse('partner_detail', args=[self.partner.id]) + f"?from_date={old_date}&to_date={old_date}")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'No spends recorded')

        # 5. Student is barred from partner list & partner detail
        self.client.login(username='student_user', password='password123')
        self.assertRedirects(self.client.get(reverse('partner_list')), reverse('access_denied'), target_status_code=403)
        self.assertRedirects(self.client.get(reverse('partner_detail', args=[self.partner.id])), reverse('access_denied'), target_status_code=403)

    def test_all_spends_page_with_partner_and_date_filters(self):
        """All Spends page displays all partner spends and properly supports Partner and Date filters."""
        from accounts.models import PartnerInvestment
        import datetime

        # Create a second partner
        partner_two = User.objects.create_user(
            username='partner_two',
            password='password123',
            role=self.role_partner,
            first_name='Second Partner'
        )

        today = datetime.date.today()
        ten_days_ago = today - datetime.timedelta(days=10)

        # Spend 1: Partner 1 today (Groceries)
        inv1 = PartnerInvestment.objects.create(
            partner=self.partner,
            amount=15000.00,
            purpose='Vegetables & Dairy Restock',
            category='GROCERIES',
            payment_mode='UPI',
            payment_date=today,
            reference_number='UPI-001',
            recorded_by=self.partner
        )

        # Spend 2: Partner 2 ten days ago (Equipment)
        inv2 = PartnerInvestment.objects.create(
            partner=partner_two,
            amount=42000.00,
            purpose='New Industrial Microwave Oven',
            category='EQUIPMENT',
            payment_mode='BANK_TRANSFER',
            payment_date=ten_days_ago,
            reference_number='IMPS-002',
            recorded_by=self.partner
        )

        self.client.login(username='partner_user', password='password123')

        # 1. Unfiltered page shows all spends and total sum (15000 + 42000 = 57000)
        res = self.client.get(reverse('all_spends'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Vegetables &amp; Dairy Restock')
        self.assertContains(res, 'New Industrial Microwave Oven')
        self.assertContains(res, '15000.00')
        self.assertContains(res, '42000.00')
        self.assertContains(res, '57000.00')
        self.assertContains(res, 'Filter by Partner:')
        self.assertContains(res, 'From Date:')
        self.assertContains(res, 'To Date:')

        # 2. Partner Filter: filter by partner_two only
        res = self.client.get(reverse('all_spends') + f"?partner_id={partner_two.id}")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'New Industrial Microwave Oven')
        self.assertContains(res, '42000.00')
        self.assertNotContains(res, 'Vegetables &amp; Dairy Restock')

        # 3. Date Filter: filter by today only (should only include inv1)
        res = self.client.get(reverse('all_spends') + f"?from_date={today}&to_date={today}")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Vegetables &amp; Dairy Restock')
        self.assertContains(res, '15000.00')
        self.assertNotContains(res, 'New Industrial Microwave Oven')

        # 4. Combined Filter: Partner 1 + Today
        res = self.client.get(reverse('all_spends') + f"?partner_id={self.partner.id}&from_date={today}&to_date={today}&category=GROCERIES")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Vegetables &amp; Dairy Restock')
        self.assertContains(res, '15000.00')
        self.assertNotContains(res, 'New Industrial Microwave Oven')

        # 5. Student cannot access /spends/
        self.client.login(username='student_user', password='password123')
        res = self.client.get(reverse('all_spends'))
        self.assertRedirects(res, reverse('access_denied'), target_status_code=403)

    def test_student_meal_tracking_and_detail_view(self):
        """Staff and Partners can log 3-time meals, view current month feed status and old records."""
        from accounts.models import StudentMealRecord
        import datetime

        self.client.login(username='staff_user', password='password123')

        # 1. Student List shows View button & feeding records
        res = self.client.get(reverse('student_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'View')
        self.assertContains(res, reverse('student_detail', args=[self.student_record.id]))
        self.assertContains(res, 'MBBS-2023-001')

        # 2. Student Detail View loads successfully with 3-meal logger
        detail_url = reverse('student_detail', args=[self.student_record.id])
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Daily Meal Logger (3 Meals / Day)')
        self.assertContains(res, 'Breakfast (Morning)')
        self.assertContains(res, 'Lunch (Afternoon)')
        self.assertContains(res, 'Dinner (Night)')
        self.assertContains(res, 'Current Month Feeding Status')

        # 3. Log 3 meals for today
        today = datetime.date.today()
        log_url = reverse('student_meal_log', args=[self.student_record.id])
        res = self.client.post(log_url, {
            'date': str(today),
            'breakfast': 'on',
            'lunch': 'on',
            'dinner': 'on',
            'notes': 'All 3 meals taken',
        })
        self.assertRedirects(res, f"{detail_url}?log_date={today}")

        # Verify meal record created
        record = StudentMealRecord.objects.get(student=self.student_record, date=today)
        self.assertTrue(record.breakfast)
        self.assertTrue(record.lunch)
        self.assertTrue(record.dinner)
        self.assertEqual(record.total_meals, 3)

        # 4. Create an older meal record from 5 days ago (Breakfast & Lunch only)
        five_days_ago = today - datetime.timedelta(days=5)
        res = self.client.post(log_url, {
            'date': str(five_days_ago),
            'breakfast': 'on',
            'lunch': 'on',
            'notes': 'Dinner skipped',
        })
        self.assertRedirects(res, f"{detail_url}?log_date={five_days_ago}")

        past_record = StudentMealRecord.objects.get(student=self.student_record, date=five_days_ago)
        self.assertTrue(past_record.breakfast)
        self.assertTrue(past_record.lunch)
        self.assertFalse(past_record.dinner)
        self.assertEqual(past_record.total_meals, 2)

        # 5. Check student detail reflects updated totals (3 + 2 = 5 meals across 2 days)
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '5') # Total meals

        # 6. Test JSON AJAX meal logger endpoint
        res = self.client.post(log_url, {
            'date': str(today),
            'breakfast': 'on',
            'lunch': 'on',
            'dinner': '',  # Uncheck dinner
            'ajax': '1',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        json_data = res.json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['total_meals'], 2)

        # 7. Test searching students list by roll number
        self.client.login(username='staff_user', password='password123')
        res = self.client.get(reverse('student_list') + f"?q={self.student_record.roll_number}")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.student_record.roll_number)

        # 8. Student user is blocked from viewing detail view
        self.client.login(username='student_user', password='password123')
        res = self.client.get(detail_url)
        self.assertRedirects(res, reverse('access_denied'), target_status_code=403)

    def test_pagination_across_listings(self):
        """Pagination controls correctly split items across pages and preserve query parameters."""
        from accounts.models import PartnerInvestment
        import datetime

        self.client.login(username='partner_user', password='password123')

        # Create 15 Partner Investments to test 10-item pagination
        today = datetime.date.today()
        for i in range(15):
            PartnerInvestment.objects.create(
                partner=self.partner,
                amount=1000.00 + i,
                purpose=f"Expense item #{i+1}",
                category='GROCERIES',
                payment_mode='UPI',
                payment_date=today,
                reference_number=f"REF-{i+1:03d}",
                recorded_by=self.partner
            )

        # 1. Page 1 with per_page=10 shows 10 items, 15 records found, and next page control
        res = self.client.get(reverse('all_spends') + '?per_page=10')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Showing <strong>1</strong> to <strong>10</strong> of <strong>15</strong> entries')
        self.assertContains(res, '15</strong> records found')
        self.assertContains(res, 'per page')
        self.assertContains(res, 'Search by keyword')
        self.assertContains(res, 'page=2')
        self.assertContains(res, 'Expense item #1')

        # 2. Page 2 shows remaining 5 items and previous page link
        res = self.client.get(reverse('all_spends') + '?per_page=10&page=2')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Showing <strong>11</strong> to <strong>15</strong> of <strong>15</strong> entries')
        self.assertContains(res, 'page=1')

        # 3. Pagination preserves query parameters like category filter
        res = self.client.get(reverse('all_spends') + '?category=GROCERIES&per_page=10&page=1')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'category=GROCERIES')
        self.assertContains(res, 'page=2')

        # 4. Keyword search filters listing dynamically
        res = self.client.get(reverse('all_spends') + '?q=REF-015')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Expense item #15')
        self.assertNotContains(res, 'Expense item #14')
        self.assertContains(res, '1</strong> records found')

        # 5. Verify removed options: Filters, Default View, Columns, Actions are NOT present
        self.assertNotContains(res, 'Default View')
        self.assertNotContains(res, '>Columns<')
        self.assertNotContains(res, '<option value="">Actions</option>')

        # 6. Verify custom page size option works properly (e.g. per_page=7)
        res = self.client.get(reverse('all_spends') + '?per_page=7')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Showing <strong>1</strong> to <strong>7</strong> of <strong>15</strong> entries')
        self.assertContains(res, '7 (Custom)')
        self.assertContains(res, 'Custom...')

    def test_non_subscription_students_register(self):
        """Test maintaining daily register for non-subscription walk-in students."""
        from accounts.models import NonSubscriptionMeal
        import datetime

        self.client.login(username='staff_user', password='password123')
        today = datetime.date.today()

        # 1. Create a non-sub meal record via POST
        create_url = reverse('non_sub_create')
        res = self.client.post(create_url, {
            'date': str(today),
            'meal_type': 'LUNCH',
            'batch': 'MBBS 2023',
            'roll_number': 'MBBS-045',
            'diet': 'VEG',
            'price': '80.00',
            'mobile_last_3': '849',
            'payment_mode': 'ONLINE',
            'notes': 'UPI payment via GPay',
        })
        self.assertRedirects(res, reverse('non_sub_register'))

        meal = NonSubscriptionMeal.objects.get(roll_number='MBBS-045')
        self.assertEqual(meal.batch, 'MBBS 2023')
        self.assertEqual(meal.diet, 'VEG')
        self.assertEqual(meal.price, 80.00)
        self.assertEqual(meal.mobile_last_3, '849')
        self.assertEqual(meal.payment_mode, 'ONLINE')
        self.assertEqual(meal.recorded_by, self.staff)

        # 2. Validation: mobile_last_3 must be exactly 3 numeric digits
        res = self.client.post(create_url, {
            'date': str(today),
            'meal_type': 'DINNER',
            'batch': 'BDS 2022',
            'roll_number': 'BDS-012',
            'diet': 'NON_VEG',
            'price': '120.00',
            'mobile_last_3': '12', # Invalid: 2 digits
            'payment_mode': 'CASH',
        })
        self.assertEqual(res.status_code, 200)
        self.assertFormError(res.context['form'], 'mobile_last_3', 'Must be exactly 3 numeric digits (e.g. 849).')

        # 3. Create a second valid record (Non-Veg, Cash)
        res = self.client.post(create_url, {
            'date': str(today),
            'meal_type': 'DINNER',
            'batch': 'BDS 2022',
            'roll_number': 'BDS-012',
            'diet': 'NON_VEG',
            'price': '120.00',
            'mobile_last_3': '789',
            'payment_mode': 'CASH',
        })
        self.assertRedirects(res, reverse('non_sub_register'))

        # 4. View register list page
        reg_url = reverse('non_sub_register')
        res = self.client.get(reg_url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'MBBS-045')
        self.assertContains(res, 'BDS-012')
        self.assertContains(res, '849')
        self.assertContains(res, '789')
        self.assertContains(res, '200.00') # 80 + 120 = 200

        # 5. Filter by Diet: VEG only
        res = self.client.get(reg_url + '?diet=VEG')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'MBBS-045')
        self.assertNotContains(res, 'BDS-012')

        # 6. Filter by Payment Mode: CASH only
        res = self.client.get(reg_url + '?payment_mode=CASH')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'BDS-012')
        self.assertNotContains(res, 'MBBS-045')

        # 7. Keyword search: search by last 3 digits of mobile '849'
        res = self.client.get(reg_url + '?q=849')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'MBBS-045')
        self.assertNotContains(res, 'BDS-012')

        # 8. Edit register entry
        edit_url = reverse('non_sub_edit', args=[meal.id])
        res = self.client.post(edit_url, {
            'date': str(today),
            'meal_type': 'LUNCH',
            'batch': 'MBBS 2023',
            'roll_number': 'MBBS-045',
            'diet': 'NON_VEG', # Changed to NON_VEG
            'price': '110.00', # Changed to 110
            'mobile_last_3': '849',
            'payment_mode': 'ONLINE',
            'notes': 'Upgraded to chicken thali',
        })
        self.assertRedirects(res, reverse('non_sub_register'))
        meal.refresh_from_db()
        self.assertEqual(meal.diet, 'NON_VEG')
        self.assertEqual(meal.price, 110.00)

        # 9. Students cannot access the register
        self.client.login(username='student_user', password='password123')
        res = self.client.get(reg_url)
        self.assertRedirects(res, reverse('access_denied'), target_status_code=403)





