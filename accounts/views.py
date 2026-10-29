from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Max, Q
from django.utils import timezone
import datetime
from .models import User, StudentType, Student, Role, PartnerInvestment, StudentMealRecord, NonSubscriptionMeal
from .forms import LoginForm, UserForm, StudentTypeForm, StudentForm, RoleForm, PartnerInvestmentForm, NonSubscriptionMealForm
from .permissions import admin_panel_required, partner_or_admin_required


def paginate_queryset(request, queryset, default_per_page=20, page_param='page'):
    """Helper to paginate any queryset with keyword search & custom variable page size."""
    try:
        per_page = int(request.GET.get('per_page', default_per_page))
        if per_page < 1:
            per_page = default_per_page
        elif per_page > 1000:
            per_page = 1000
    except (ValueError, TypeError):
        per_page = default_per_page

    page_number = request.GET.get(page_param)
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)
    return page_obj, per_page


# ---------------------------------------------------------------------------
# Authentication & Access Control
# ---------------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect('access_denied')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_student:
                return redirect('access_denied')
            role_display = user.role.name if user.role else "No Role"
            messages.success(request, f"Welcome back, {user.username} ({role_display})!")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'admin_panel/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')


@login_required
def access_denied_view(request):
    """Rendered when a student tries to access or perform operations in the admin panel."""
    return render(request, 'admin_panel/access_denied.html', status=403)


# ---------------------------------------------------------------------------
# Admin Panel Dashboard (Partners and Staff)
# ---------------------------------------------------------------------------
@admin_panel_required
def dashboard_view(request):
    total_users = User.objects.count()
    total_roles = Role.objects.count()
    total_student_types = StudentType.objects.count()
    total_students = Student.objects.count()
    total_partners = User.objects.filter(role__code='PARTNER').count()
    total_investments = PartnerInvestment.objects.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'total_users': total_users,
        'total_roles': total_roles,
        'total_student_types': total_student_types,
        'total_students': total_students,
        'total_partners': total_partners,
        'total_investments': total_investments,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ---------------------------------------------------------------------------
# User Role Management (List & Form - Partners & Admins Only)
# ---------------------------------------------------------------------------
@partner_or_admin_required
def role_list_view(request):
    q = request.GET.get('q', '').strip()
    roles = Role.objects.all()
    if q:
        roles = roles.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(description__icontains=q))
    roles = roles.order_by('name')
    page_obj, per_page = paginate_queryset(request, roles, default_per_page=20)
    return render(request, 'admin_panel/role_list.html', {
        'roles': page_obj,
        'page_obj': page_obj,
        'q': q,
        'per_page': per_page,
    })


@partner_or_admin_required
def role_create_view(request):
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            messages.success(request, f"User Role '{role.name}' [{role.code}] created successfully.")
            return redirect('role_list')
    else:
        form = RoleForm()
    return render(request, 'admin_panel/role_form.html', {'form': form, 'title': 'Create New User Role'})


@partner_or_admin_required
def role_edit_view(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, f"User Role '{role.name}' updated successfully.")
            return redirect('role_list')
    else:
        form = RoleForm(instance=role)
    return render(request, 'admin_panel/role_form.html', {'form': form, 'title': f'Edit User Role: {role.name}'})


@partner_or_admin_required
def role_delete_view(request, pk):
    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        name = role.name
        role.delete()
        messages.success(request, f"User Role '{name}' deleted successfully.")
        return redirect('role_list')
    return render(request, 'admin_panel/confirm_delete.html', {
        'item_name': f"User Role: {role.name} [{role.code}]",
        'cancel_url': 'role_list'
    })


# ---------------------------------------------------------------------------
# User Management (Restricted to Partners & Admins Only)
# ---------------------------------------------------------------------------
@partner_or_admin_required
def user_list_view(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.select_related('role').all()
    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q) |
            Q(role__name__icontains=q) |
            Q(role__code__icontains=q)
        )
    users = users.order_by('-date_joined')
    page_obj, per_page = paginate_queryset(request, users, default_per_page=20)
    return render(request, 'admin_panel/user_list.html', {
        'users': page_obj,
        'page_obj': page_obj,
        'q': q,
        'per_page': per_page,
    })


@partner_or_admin_required
def user_create_view(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            role_name = user.role.name if user.role else "No Role"
            messages.success(request, f"User '{user.username}' with role '{role_name}' created successfully.")
            return redirect('user_list')
    else:
        form = UserForm()
    return render(request, 'admin_panel/user_form.html', {'form': form, 'title': 'Create New User'})


@partner_or_admin_required
def user_edit_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user.username}' updated successfully.")
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'admin_panel/user_form.html', {'form': form, 'title': f'Edit User: {user.username}', 'edit_mode': True})


@partner_or_admin_required
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f"User '{username}' deleted successfully.")
        return redirect('user_list')
    return render(request, 'admin_panel/confirm_delete.html', {
        'item_name': f"User: {user.username}",
        'cancel_url': 'user_list'
    })


# ---------------------------------------------------------------------------
# Student Type Management (Staff and Partners Can Manage)
# ---------------------------------------------------------------------------
@admin_panel_required
def student_type_list_view(request):
    q = request.GET.get('q', '').strip()
    student_types = StudentType.objects.all()
    if q:
        student_types = student_types.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q)
        )
    student_types = student_types.order_by('-created_at')
    page_obj, per_page = paginate_queryset(request, student_types, default_per_page=20)
    return render(request, 'admin_panel/student_type_list.html', {
        'student_types': page_obj,
        'page_obj': page_obj,
        'q': q,
        'per_page': per_page,
    })


@admin_panel_required
def student_type_create_view(request):
    if request.method == 'POST':
        form = StudentTypeForm(request.POST)
        if form.is_valid():
            st_type = form.save()
            messages.success(request, f"Student Type '{st_type.name}' created successfully.")
            return redirect('student_type_list')
    else:
        form = StudentTypeForm()
    return render(request, 'admin_panel/student_type_form.html', {'form': form, 'title': 'Create Student Type'})


@admin_panel_required
def student_type_edit_view(request, pk):
    st_type = get_object_or_404(StudentType, pk=pk)
    if request.method == 'POST':
        form = StudentTypeForm(request.POST, instance=st_type)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student Type '{st_type.name}' updated successfully.")
            return redirect('student_type_list')
    else:
        form = StudentTypeForm(instance=st_type)
    return render(request, 'admin_panel/student_type_form.html', {'form': form, 'title': f'Edit Student Type: {st_type.name}'})


@admin_panel_required
def student_type_delete_view(request, pk):
    st_type = get_object_or_404(StudentType, pk=pk)
    if request.method == 'POST':
        name = st_type.name
        st_type.delete()
        messages.success(request, f"Student Type '{name}' deleted successfully.")
        return redirect('student_type_list')
    return render(request, 'admin_panel/confirm_delete.html', {
        'item_name': f"Student Type: {st_type.name}",
        'cancel_url': 'student_type_list'
    })


# ---------------------------------------------------------------------------
# Student Management & Feeding Tracking (Staff and Partners Can Manage)
# ---------------------------------------------------------------------------
@admin_panel_required
def student_list_view(request):
    """
    List of all students with real-time feeding records:
    - Current month meals taken & days attended
    - All-time meals taken & days attended
    """
    today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
    q = request.GET.get('q', '').strip()
    students = Student.objects.select_related('user', 'student_type').annotate(
        curr_b=Count('meal_records', filter=Q(meal_records__date__year=today.year, meal_records__date__month=today.month, meal_records__breakfast=True)),
        curr_l=Count('meal_records', filter=Q(meal_records__date__year=today.year, meal_records__date__month=today.month, meal_records__lunch=True)),
        curr_d=Count('meal_records', filter=Q(meal_records__date__year=today.year, meal_records__date__month=today.month, meal_records__dinner=True)),
        curr_days=Count('meal_records', filter=Q(meal_records__date__year=today.year, meal_records__date__month=today.month) & (Q(meal_records__breakfast=True) | Q(meal_records__lunch=True) | Q(meal_records__dinner=True)), distinct=True),
        all_b=Count('meal_records', filter=Q(meal_records__breakfast=True)),
        all_l=Count('meal_records', filter=Q(meal_records__lunch=True)),
        all_d=Count('meal_records', filter=Q(meal_records__dinner=True)),
        all_days=Count('meal_records', filter=Q(meal_records__breakfast=True) | Q(meal_records__lunch=True) | Q(meal_records__dinner=True), distinct=True),
    )
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__username__icontains=q) |
            Q(roll_number__icontains=q) |
            Q(department__icontains=q) |
            Q(batch__icontains=q) |
            Q(user__phone__icontains=q) |
            Q(student_type__name__icontains=q)
        )

    students_data = []
    for s in students:
        s.curr_total_meals = s.curr_b + s.curr_l + s.curr_d
        s.all_total_meals = s.all_b + s.all_l + s.all_d
        students_data.append(s)

    page_obj, per_page = paginate_queryset(request, students_data, default_per_page=20)

    return render(request, 'admin_panel/student_list.html', {
        'students': page_obj,
        'page_obj': page_obj,
        'q': q,
        'per_page': per_page,
        'current_month_name': today.strftime('%B %Y'),
    })


@admin_panel_required
def student_detail_view(request, pk):
    """
    Student View Page:
    - Complete student details & subscription info
    - Quick 3-meal checkbox logger (Breakfast, Lunch, Dinner) for today or any date
    - Current Month Feed Status (Summary metrics and breakdown)
    - Full historical records with month & date range filtering
    """
    student = get_object_or_404(Student.objects.select_related('user', 'student_type'), pk=pk)
    today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()

    # 1. Target date for meal logging (defaults to today or selected in URL)
    log_date_str = request.GET.get('log_date', str(today)).strip()
    try:
        selected_log_date = datetime.datetime.strptime(log_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        selected_log_date = today

    target_meal_record = StudentMealRecord.objects.filter(student=student, date=selected_log_date).first()

    # 2. Current Month Statistics
    curr_month_records = StudentMealRecord.objects.filter(
        student=student,
        date__year=today.year,
        date__month=today.month
    )
    curr_b_count = curr_month_records.filter(breakfast=True).count()
    curr_l_count = curr_month_records.filter(lunch=True).count()
    curr_d_count = curr_month_records.filter(dinner=True).count()
    curr_total_meals = curr_b_count + curr_l_count + curr_d_count
    curr_days_attended = curr_month_records.filter(
        Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
    ).count()

    # 3. All-Time Statistics
    all_records = StudentMealRecord.objects.filter(student=student)
    all_b_count = all_records.filter(breakfast=True).count()
    all_l_count = all_records.filter(lunch=True).count()
    all_d_count = all_records.filter(dinner=True).count()
    all_total_meals = all_b_count + all_l_count + all_d_count
    all_days_attended = all_records.filter(
        Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
    ).count()

    # 4. Old Records / Historical Filtering
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    selected_month = request.GET.get('month', '').strip()
    q = request.GET.get('q', '').strip()

    history_records = StudentMealRecord.objects.filter(student=student).select_related('recorded_by').order_by('-date')

    if q:
        history_records = history_records.filter(
            Q(notes__icontains=q) |
            Q(recorded_by__username__icontains=q) |
            Q(recorded_by__first_name__icontains=q)
        )
    if from_date:
        history_records = history_records.filter(date__gte=from_date)
    if to_date:
        history_records = history_records.filter(date__lte=to_date)
    if selected_month and selected_month != 'all':
        try:
            yr, mo = selected_month.split('-')
            history_records = history_records.filter(date__year=int(yr), date__month=int(mo))
        except (ValueError, IndexError):
            pass
    elif not from_date and not to_date:
        # Default to current month for clear and focused view
        history_records = history_records.filter(date__year=today.year, date__month=today.month)
        selected_month = today.strftime('%Y-%m')

    # Aggregates for the filtered period
    filtered_b = history_records.filter(breakfast=True).count()
    filtered_l = history_records.filter(lunch=True).count()
    filtered_d = history_records.filter(dinner=True).count()
    filtered_total_meals = filtered_b + filtered_l + filtered_d
    filtered_days_attended = history_records.filter(
        Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
    ).count()

    # Generate available months list for dropdown
    distinct_dates = list(StudentMealRecord.objects.filter(student=student).values_list('date', flat=True))
    months_set = {(d.year, d.month) for d in distinct_dates}
    months_set.add((today.year, today.month))
    available_months = []
    for yr, mo in sorted(months_set, reverse=True):
        m_date = datetime.date(yr, mo, 1)
        available_months.append({
            'val': f"{yr:04d}-{mo:02d}",
            'label': m_date.strftime('%B %Y')
        })

    # Paginate history records
    history_page_obj, history_per_page = paginate_queryset(request, history_records, default_per_page=15, page_param='history_page')

    context = {
        'student': student,
        'today': today,
        'selected_log_date': selected_log_date,
        'selected_log_date_str': selected_log_date.strftime('%Y-%m-%d'),
        'target_meal_record': target_meal_record,

        # Current month metrics
        'current_month_name': today.strftime('%B %Y'),
        'curr_total_meals': curr_total_meals,
        'curr_days_attended': curr_days_attended,
        'curr_b_count': curr_b_count,
        'curr_l_count': curr_l_count,
        'curr_d_count': curr_d_count,

        # All-time metrics
        'all_total_meals': all_total_meals,
        'all_days_attended': all_days_attended,
        'all_b_count': all_b_count,
        'all_l_count': all_l_count,
        'all_d_count': all_d_count,

        # Filtered history records & metrics
        'history_records': history_page_obj,
        'page_obj': history_page_obj,
        'page_param': 'history_page',
        'from_date': from_date,
        'to_date': to_date,
        'selected_month': selected_month,
        'available_months': available_months,
        'filtered_b': filtered_b,
        'filtered_l': filtered_l,
        'filtered_d': filtered_d,
        'filtered_total_meals': filtered_total_meals,
        'filtered_days_attended': filtered_days_attended,
        'q': q,
        'per_page': history_per_page,
    }
    return render(request, 'admin_panel/student_detail.html', context)


@admin_panel_required
def student_meal_log_view(request, pk):
    """
    Handle ticking or updating the 3 meal checkboxes (Breakfast, Lunch, Dinner).
    Supports standard form POST as well as JSON AJAX requests.
    """
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        date_str = request.POST.get('date', '').strip()
        today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
        try:
            log_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else today
        except (ValueError, TypeError):
            log_date = today

        breakfast = request.POST.get('breakfast') in ['on', 'true', '1', 'True']
        lunch = request.POST.get('lunch') in ['on', 'true', '1', 'True']
        dinner = request.POST.get('dinner') in ['on', 'true', '1', 'True']
        notes = request.POST.get('notes', '').strip()

        meal_record, created = StudentMealRecord.objects.get_or_create(
            student=student,
            date=log_date,
            defaults={
                'breakfast': breakfast,
                'lunch': lunch,
                'dinner': dinner,
                'notes': notes,
                'recorded_by': request.user,
            }
        )
        if not created:
            meal_record.breakfast = breakfast
            meal_record.lunch = lunch
            meal_record.dinner = dinner
            if notes:
                meal_record.notes = notes
            meal_record.recorded_by = request.user
            meal_record.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({
                'success': True,
                'date': str(log_date),
                'breakfast': meal_record.breakfast,
                'lunch': meal_record.lunch,
                'dinner': meal_record.dinner,
                'total_meals': meal_record.total_meals,
                'message': f"Meals updated for {log_date.strftime('%b %d, %Y')}."
            })

        messages.success(
            request,
            f"Logged meals for {student.user.get_full_name() or student.user.username} on {log_date.strftime('%b %d, %Y')}: "
            f"Breakfast={'✓' if breakfast else '✕'}, Lunch={'✓' if lunch else '✕'}, Dinner={'✓' if dinner else '✕'}."
        )
        return redirect(f"{reverse('student_detail', args=[student.pk])}?log_date={log_date}")

    return redirect('student_detail', pk=pk)


@admin_panel_required
def student_create_view(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"Student '{student.user.username}' created with Student Type '{student.student_type}'.")
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'admin_panel/student_form.html', {'form': form, 'title': 'Create Student Record'})


@admin_panel_required
def student_edit_view(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student '{student.user.username}' updated successfully.")
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'admin_panel/student_form.html', {'form': form, 'title': f'Edit Student: {student.user.username}'})


@admin_panel_required
def student_delete_view(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        username = student.user.username
        student.delete()
        messages.success(request, f"Student record for '{username}' deleted successfully.")
        return redirect('student_list')
    return render(request, 'admin_panel/confirm_delete.html', {
        'item_name': f"Student: {student.user.username} ({student.roll_number})",
        'cancel_url': 'student_list'
    })


# ---------------------------------------------------------------------------
# Partner & Investment Management (Restricted to Partners & Admins)
# ---------------------------------------------------------------------------
@partner_or_admin_required
def partner_list_view(request):
    """
    Clean, simple Partner list with options to:
    1. '+ Add Partner'
    2. '+ Add Spend'
    3. 'View' -> goes to Partner View Page showing respective partner's spends with date filter
    """
    q = request.GET.get('q', '').strip()
    partners = User.objects.filter(role__code='PARTNER')
    if q:
        partners = partners.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )
    partners = partners.order_by('first_name', 'username')

    partners_data = []
    for p in partners:
        inv_agg = p.investments.aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        partners_data.append({
            'user': p,
            'total_spend': inv_agg['total'] or 0,
            'spend_count': inv_agg['count'] or 0,
        })

    page_obj, per_page = paginate_queryset(request, partners_data, default_per_page=20)

    return render(request, 'admin_panel/partner_list.html', {
        'partners_data': page_obj,
        'page_obj': page_obj,
        'q': q,
        'per_page': per_page,
    })


@partner_or_admin_required
def partner_create_view(request):
    """Clean shortcut to create a new Partner user."""
    role_partner = Role.objects.filter(code='PARTNER').first()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Partner '{user.get_full_name() or user.username}' added successfully.")
            return redirect('partner_list')
    else:
        initial = {'role': role_partner.id if role_partner else None}
        form = UserForm(initial=initial)
    return render(request, 'admin_panel/user_form.html', {
        'form': form,
        'title': 'Add New Partner',
    })


@partner_or_admin_required
def partner_detail_view(request, pk):
    """
    Respective Partner View Page:
    - Partner's details (Name, Contact, Total spend)
    - Respective partner's spend history only
    - Date filter (from_date, to_date)
    """
    partner = get_object_or_404(User, pk=pk, role__code='PARTNER')

    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    q = request.GET.get('q', '').strip()

    spends = partner.investments.all()
    if q:
        spends = spends.filter(
            Q(purpose__icontains=q) |
            Q(reference_number__icontains=q) |
            Q(category__icontains=q) |
            Q(notes__icontains=q) |
            Q(payment_mode__icontains=q)
        )
    if from_date:
        spends = spends.filter(payment_date__gte=from_date)
    if to_date:
        spends = spends.filter(payment_date__lte=to_date)

    agg = spends.aggregate(total=Sum('amount'), count=Count('id'))
    all_time_total = partner.investments.aggregate(total=Sum('amount'))['total'] or 0

    page_obj, per_page = paginate_queryset(request, spends, default_per_page=20)

    context = {
        'partner': partner,
        'spends': page_obj,
        'page_obj': page_obj,
        'total_filtered_amount': agg['total'] or 0,
        'filtered_count': agg['count'] or 0,
        'all_time_total': all_time_total,
        'from_date': from_date,
        'to_date': to_date,
        'q': q,
        'per_page': per_page,
        'active_filters_count': (1 if from_date else 0) + (1 if to_date else 0),
    }
    return render(request, 'admin_panel/partner_detail.html', context)


@partner_or_admin_required
def all_spends_view(request):
    """
    All Spends Page:
    Displays all canteen expenditures/investments across all partners.
    Filterable by:
    - Partner Filter
    - Date Filter (from_date, to_date)
    - Category Filter
    """
    spends = PartnerInvestment.objects.select_related('partner', 'recorded_by').all()
    
    partner_id = request.GET.get('partner_id', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    category = request.GET.get('category', '').strip()
    q = request.GET.get('q', '').strip()

    if q:
        spends = spends.filter(
            Q(purpose__icontains=q) |
            Q(reference_number__icontains=q) |
            Q(category__icontains=q) |
            Q(notes__icontains=q) |
            Q(payment_mode__icontains=q) |
            Q(partner__first_name__icontains=q) |
            Q(partner__last_name__icontains=q) |
            Q(partner__username__icontains=q)
        )
    if partner_id and partner_id.isdigit():
        spends = spends.filter(partner_id=int(partner_id))
    if from_date:
        spends = spends.filter(payment_date__gte=from_date)
    if to_date:
        spends = spends.filter(payment_date__lte=to_date)
    if category:
        spends = spends.filter(category=category)

    total_filtered_amount = spends.aggregate(total=Sum('amount'))['total'] or 0
    total_count = spends.count()
    partners = User.objects.filter(role__code='PARTNER').order_by('first_name', 'username')

    page_obj, per_page = paginate_queryset(request, spends, default_per_page=20)

    active_filters_count = (1 if partner_id else 0) + (1 if from_date else 0) + (1 if to_date else 0) + (1 if category else 0)

    context = {
        'spends': page_obj,
        'page_obj': page_obj,
        'total_filtered_amount': total_filtered_amount,
        'total_count': total_count,
        'partners': partners,
        'categories': PartnerInvestment.CATEGORY_CHOICES,
        'selected_partner_id': int(partner_id) if partner_id and partner_id.isdigit() else None,
        'from_date': from_date,
        'to_date': to_date,
        'selected_category': category,
        'q': q,
        'per_page': per_page,
        'active_filters_count': active_filters_count,
    }
    return render(request, 'admin_panel/all_spends.html', context)


# Alias for compatibility
investment_list_view = all_spends_view


@partner_or_admin_required
def investment_create_view(request):
    """Add spend / investment form."""
    initial_data = {}
    partner_id = request.GET.get('partner_id')
    if partner_id and partner_id.isdigit():
        initial_data['partner'] = int(partner_id)

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = PartnerInvestmentForm(request.POST, user=request.user)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.recorded_by = request.user
            inv.save()
            partner_name = inv.partner.get_full_name() or inv.partner.username
            messages.success(
                request,
                f"Spend of ₹{inv.amount:,.2f} by {partner_name} for '{inv.purpose}' added successfully."
            )
            if next_url:
                return redirect(next_url)
            return redirect('partner_detail', pk=inv.partner.id)
    else:
        form = PartnerInvestmentForm(initial=initial_data, user=request.user)

    return render(request, 'admin_panel/investment_form.html', {
        'form': form,
        'title': 'Add Spend',
        'next_url': next_url,
    })


@partner_or_admin_required
def investment_edit_view(request, pk):
    investment = get_object_or_404(PartnerInvestment, pk=pk)
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = PartnerInvestmentForm(request.POST, instance=investment, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Spend entry #{investment.id} updated successfully.")
            if next_url:
                return redirect(next_url)
            return redirect('partner_detail', pk=investment.partner.id)
    else:
        form = PartnerInvestmentForm(instance=investment, user=request.user)

    return render(request, 'admin_panel/investment_form.html', {
        'form': form,
        'title': f'Edit Spend Entry #{investment.id}',
        'edit_mode': True,
        'next_url': next_url,
    })


@partner_or_admin_required
def investment_delete_view(request, pk):
    investment = get_object_or_404(PartnerInvestment, pk=pk)
    partner_id = investment.partner.id
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        desc = f"₹{investment.amount:,.2f} for '{investment.purpose}'"
        investment.delete()
        messages.success(request, f"Spend record ({desc}) deleted successfully.")
        if next_url:
            return redirect(next_url)
        return redirect('partner_detail', pk=partner_id)

    cancel_url = next_url if next_url else f"/partners/{partner_id}/"
    return render(request, 'admin_panel/confirm_delete.html', {
        'item_name': f"Spend of ₹{investment.amount:,.2f} by {investment.partner.username} for '{investment.purpose}'",
        'cancel_url': 'partner_list'
    })


# ---------------------------------------------------------------------------
# Non-Subscription Student Register (Staff, Partners & Admins)
# ---------------------------------------------------------------------------
@admin_panel_required
def non_sub_register_view(request):
    """
    Register and live ledger for non-subscription walk-in students purchasing individual meals:
    Tracks Batch, Roll number, Veg/Non-Veg, Price, Mobile Last 3 digits, Payment Mode (Cash/Online).
    """
    q = request.GET.get('q', '').strip()
    selected_date = request.GET.get('date', '').strip()
    selected_diet = request.GET.get('diet', '').strip()
    selected_payment_mode = request.GET.get('payment_mode', '').strip()
    selected_meal_type = request.GET.get('meal_type', '').strip()

    meals = NonSubscriptionMeal.objects.select_related('recorded_by').all()

    if selected_date:
        meals = meals.filter(date=selected_date)
    if selected_diet:
        meals = meals.filter(diet=selected_diet)
    if selected_payment_mode:
        meals = meals.filter(payment_mode=selected_payment_mode)
    if selected_meal_type:
        meals = meals.filter(meal_type=selected_meal_type)

    if q:
        meals = meals.filter(
            Q(roll_number__icontains=q) |
            Q(batch__icontains=q) |
            Q(mobile_last_3__icontains=q) |
            Q(notes__icontains=q) |
            Q(recorded_by__username__icontains=q)
        )

    # Statistics / Summary Metrics
    total_count = meals.count()
    total_amount = meals.aggregate(total=Sum('price'))['total'] or 0.0
    veg_count = meals.filter(diet='VEG').count()
    non_veg_count = meals.filter(diet='NON_VEG').count()
    online_total = meals.filter(payment_mode='ONLINE').aggregate(total=Sum('price'))['total'] or 0.0
    cash_total = meals.filter(payment_mode='CASH').aggregate(total=Sum('price'))['total'] or 0.0

    # Today's stats for quick pill
    today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
    today_meals = NonSubscriptionMeal.objects.filter(date=today)
    today_count = today_meals.count()
    today_revenue = today_meals.aggregate(total=Sum('price'))['total'] or 0.0

    page_obj, per_page = paginate_queryset(request, meals, default_per_page=20)

    # Quick Add Form for direct entry on top of register
    quick_form = NonSubscriptionMealForm(initial={'date': today, 'meal_type': 'LUNCH', 'diet': 'VEG', 'payment_mode': 'ONLINE'})

    context = {
        'meals': page_obj,
        'page_obj': page_obj,
        'per_page': per_page,
        'q': q,
        'selected_date': selected_date,
        'selected_diet': selected_diet,
        'selected_payment_mode': selected_payment_mode,
        'selected_meal_type': selected_meal_type,
        'total_count': total_count,
        'total_amount': total_amount,
        'veg_count': veg_count,
        'non_veg_count': non_veg_count,
        'online_total': online_total,
        'cash_total': cash_total,
        'today_count': today_count,
        'today_revenue': today_revenue,
        'today_str': str(today),
        'quick_form': quick_form,
        'diet_choices': NonSubscriptionMeal.DIET_CHOICES,
        'payment_mode_choices': NonSubscriptionMeal.PAYMENT_MODE_CHOICES,
        'meal_type_choices': NonSubscriptionMeal.MEAL_TYPE_CHOICES,
    }
    return render(request, 'admin_panel/non_sub_register.html', context)


@admin_panel_required
def non_sub_create_view(request):
    """Log a new non-subscription walk-in student meal purchase."""
    if request.method == 'POST':
        form = NonSubscriptionMealForm(request.POST)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.recorded_by = request.user
            meal.save()
            messages.success(
                request,
                f"Recorded: {meal.roll_number} ({meal.batch}) — {meal.get_diet_display()} ₹{meal.price} [{meal.get_payment_mode_display()}]"
            )
            return redirect('non_sub_register')
    else:
        today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
        form = NonSubscriptionMealForm(initial={'date': today, 'meal_type': 'LUNCH', 'diet': 'VEG', 'payment_mode': 'ONLINE'})

    return render(request, 'admin_panel/non_sub_form.html', {
        'form': form,
        'title': 'New Non-Subscription Student Register Entry',
        'edit_mode': False,
    })


@admin_panel_required
def non_sub_edit_view(request, pk):
    """Edit an existing register record."""
    meal = get_object_or_404(NonSubscriptionMeal, pk=pk)
    if request.method == 'POST':
        form = NonSubscriptionMealForm(request.POST, instance=meal)
        if form.is_valid():
            meal = form.save()
            messages.success(request, f"Register entry #{meal.id} for {meal.roll_number} updated successfully.")
            return redirect('non_sub_register')
    else:
        form = NonSubscriptionMealForm(instance=meal)

    return render(request, 'admin_panel/non_sub_form.html', {
        'form': form,
        'title': f'Edit Register Entry #{meal.id} ({meal.roll_number})',
        'edit_mode': True,
        'meal': meal,
    })


@admin_panel_required
def non_sub_delete_view(request, pk):
    """Delete a register record with confirmation."""
    meal = get_object_or_404(NonSubscriptionMeal, pk=pk)
    if request.method == 'POST':
        desc = f"{meal.roll_number} ({meal.batch}) ₹{meal.price}"
        meal.delete()
        messages.success(request, f"Register entry ({desc}) deleted successfully.")
        return redirect('non_sub_register')

    return render(request, 'admin_panel/confirm_delete.html', {
        'item_name': f"Non-Sub Entry: {meal.roll_number} [{meal.batch}] - {meal.get_diet_display()} ₹{meal.price} on {meal.date}",
        'cancel_url': 'non_sub_register',
    })


