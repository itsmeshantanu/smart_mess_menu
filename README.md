# Smart Mess Menu Finder

A Django full-stack web application for students to discover mess menus, rate messes, and manage favorites — and for mess owners to manage their listings.

---

## Quick Setup

### 1. Install Django
```bash
pip install django
```

### 2. Apply Migrations
```bash
python manage.py migrate
```

### 3. Seed Demo Data (optional)
```bash
python seed.py
```

### 4. Run Server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## Demo Accounts (after seed.py)

| Role    | Username    | Password    |
|---------|-------------|-------------|
| Admin   | admin       | admin123    |
| Owner   | messowner   | owner123    |
| Student | student1    | student123  |

Admin panel: http://127.0.0.1:8000/admin/

---

## Project Structure

```
smart_mess_menu/
├── manage.py
├── seed.py
├── db.sqlite3          (created after migrate)
├── smart_mess/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── mess/
│   ├── models.py       — Mess, Menu, Dish, Rating, Favorite, OwnerInquiry
│   ├── views.py        — All feature views
│   ├── auth_views.py   — Login, Logout (POST), Register
│   ├── forms.py        — All forms with validation
│   ├── urls.py         — App URL patterns
│   ├── auth_urls.py    — Auth URL patterns
│   ├── admin.py        — Admin registrations
│   └── templates/mess/
│       ├── homepage.html
│       ├── mess_list.html
│       ├── mess_detail.html
│       ├── owner_inquiry.html
│       ├── owner_inquiry_success.html
│       ├── owner_dashboard.html
│       ├── mess_form.html
│       ├── menu_form.html
│       ├── manage_menu.html
│       ├── my_favorites.html
│       ├── login.html
│       └── register.html
└── templates/
    └── base.html       — Shared layout + navbar
```

---

## Features

### Students
- Browse all messes with average ratings
- View today's Lunch, Dinner & General menu per mess
- Rate any mess (1–5), update rating anytime
- Add/remove favorites (login required)
- View all favorited messes

### Mess Owners
- Register inquiry (no login required)
- Login → Dashboard to manage messes
- Create / edit messes
- Create menus (General / Lunch / Dinner)
  - Duplicate prevention enforced (mess + date + type unique)
- Add / delete dishes per menu

### Auth
- Register, Login, Logout (POST-only, CSRF protected)
- LOGIN_REDIRECT_URL → /mess/
- LOGOUT_REDIRECT_URL → /
- @login_required guards all owner & student actions

---

## Key Design Decisions

- **POST → REDIRECT → GET** everywhere (no form resubmit on refresh)
- **Rating validation**: MinValueValidator(1) + MaxValueValidator(5) at model + form level
- **Duplicate menu**: Checked explicitly in view before save + `unique_together` at DB level
- **Logout**: POST only via form with CSRF token
- **Favorites**: `get_or_create` → toggle delete pattern
- **Ratings**: `update_or_create` for idempotent upsert
