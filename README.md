# 🏥 MediDine — Medical College Canteen Admin Panel

A Magento 2-inspired Admin Panel built for **Partners** and **Canteen Staff**, featuring **Dynamic Light & Dark Theme** switching, strict **Role-Based Access Control (RBAC)**, and medical campus management.

---

## 🌓 Dark and Light Mode Theming

- **One-Click Theme Toggle**: Located in the top header bar (`🌙 Dark / ☀️ Light`).
- **Instant Anti-FOUC Persistence**: User theme choice is stored in `localStorage` and loads immediately with zero screen flicker.
- **System Preference Detection**: Automatically defaults to system preferences (macOS / Windows dark or light mode) if no manual preference has been set yet.
- **Adaptive Tokens**:
  - **Light Mode**: Calming sterile hospital off-white (`#f8fafc`) with crisp white card surfaces (`#ffffff`) and surgical teal primary accents (`#0d9488`).
  - **Dark Mode**: Deep nocturnal clinical slate (`#07131a`) with midnight card surfaces (`#0d1e28`), subtle glowing teal borders, and reduced eye fatigue for evening canteen operations.

---

## 🛡️ Role-Based Access Control (RBAC) Matrix

| Operation / Section | Partner / Investor | Canteen Staff | Administrator | Student |
| :--- | :---: | :---: | :---: | :---: |
| **Admin Panel Login** | ✅ Granted | ✅ Granted | ✅ Granted | ❌ **Forbidden (403)** |
| **Dashboard** | ✅ View | ✅ View | ✅ View | ❌ **No Access** |
| **Manage Users & Assign Roles** | ✅ Full CRUD | ❌ Restricted *(Hidden)* | ✅ Full CRUD | ❌ **No Access** |
| **Manage User Roles** | ✅ Full CRUD | ❌ Restricted *(Hidden)* | ✅ Full CRUD | ❌ **No Access** |
| **Manage Student Types** | ✅ Full CRUD | ✅ Full CRUD | ✅ Full CRUD | ❌ **No Access** |
| **Manage Students & Assign Types**| ✅ Full CRUD | ✅ Full CRUD | ✅ Full CRUD | ❌ **No Access** |

---

## 🔑 Test Credentials

| Role | Username | Password | Accessible Sections |
| :--- | :--- | :--- | :--- |
| **Partner** | `partner_sharma` | `partner123` | Full access to Dashboard, Users, User Roles, Student Types, Students |
| **Staff** | `staff_ramesh` | `staff123` | Access to Dashboard, Student Types, Students *(Users & Roles hidden)* |
| **Student** | `student_arjun` | `student123` | ❌ **Blocked immediately with the 403 Restricted Screen** |
| **Admin** | `admin` | `admin123` | Full administrative control |

---

## 🚀 Running the Project

```bash
# Apply migrations
python3 manage.py migrate

# Seed sample users and roles
python3 manage.py setup_admin

# Run server
python3 manage.py runserver 127.0.0.1:8000
```

- **Login URL**: **[http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)**
- **Dashboard**: **[http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)**

---

## 🧪 Automated Test Suite
```bash
python3 manage.py test
```
All 5 tests verify Role CRUD, Role-based permission guards, and Student access blocking.
