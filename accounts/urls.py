from django.urls import path
from . import views

urlpatterns = [
    # Auth & Access Control
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('access-denied/', views.access_denied_view, name='access_denied'),

    # Admin Panel Dashboard (Staff & Partners)
    path('', views.dashboard_view, name='admin_dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Partner Management & Spend Ledger (Partners & Admins Only)
    path('partners/', views.partner_list_view, name='partner_list'),
    path('partners/add/', views.partner_create_view, name='partner_create'),
    path('partners/<int:pk>/', views.partner_detail_view, name='partner_detail'),
    path('spends/', views.all_spends_view, name='all_spends'),
    path('partners/investments/', views.investment_list_view, name='investment_list'),
    path('partners/investments/add/', views.investment_create_view, name='investment_create'),
    path('partners/investments/<int:pk>/edit/', views.investment_edit_view, name='investment_edit'),
    path('partners/investments/<int:pk>/delete/', views.investment_delete_view, name='investment_delete'),

    # User Role Management (Partners & Admins Only)
    path('roles/', views.role_list_view, name='role_list'),
    path('roles/add/', views.role_create_view, name='role_create'),
    path('roles/<int:pk>/edit/', views.role_edit_view, name='role_edit'),
    path('roles/<int:pk>/delete/', views.role_delete_view, name='role_delete'),

    # User Management (Partners & Admins Only)
    path('users/', views.user_list_view, name='user_list'),
    path('users/add/', views.user_create_view, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),

    # Student Type Management (Staff & Partners)
    path('student-types/', views.student_type_list_view, name='student_type_list'),
    path('student-types/add/', views.student_type_create_view, name='student_type_create'),
    path('student-types/<int:pk>/edit/', views.student_type_edit_view, name='student_type_edit'),
    path('student-types/<int:pk>/delete/', views.student_type_delete_view, name='student_type_delete'),

    # Student Management & Meal Tracking (Staff & Partners)
    path('students/', views.student_list_view, name='student_list'),
    path('students/add/', views.student_create_view, name='student_create'),
    path('students/<int:pk>/', views.student_detail_view, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit_view, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete_view, name='student_delete'),
    path('students/<int:pk>/meals/log/', views.student_meal_log_view, name='student_meal_log'),

    # Non-Subscription Students Register (Staff & Partners)
    path('non-sub-register/', views.non_sub_register_view, name='non_sub_register'),
    path('non-sub-register/add/', views.non_sub_create_view, name='non_sub_create'),
    path('non-sub-register/<int:pk>/edit/', views.non_sub_edit_view, name='non_sub_edit'),
    path('non-sub-register/<int:pk>/delete/', views.non_sub_delete_view, name='non_sub_delete'),
]
