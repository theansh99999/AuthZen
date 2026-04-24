# 🔐 AuthZen — Identity & Access Management Service
![FastAPI](https://img.shields.io/badge/FastAPI-0.100-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![Status](https://img.shields.io/badge/Status-In%20Progress-orange)
> ⚠️ **This project is currently IN PROGRESS. Features are being actively developed and things may change.**

A production-ready, multi-tenant **IAM (Identity & Access Management)** service built with **FastAPI** and **PostgreSQL**. Designed to be a reusable authentication and authorization backbone for multiple applications.

---

## 🧩 Project Phases

| Phase | Feature | Status |
|------|--------|--------|
| Phase 1 | Authentication (JWT) | ✅ |
| Phase 2 | RBAC (Roles & Permissions) | ✅ |
| Phase 3 | IAM APIs (validate-token, check-permission) | ✅ |
| Phase 4 | Multi-Application Support | ✅ |
| Phase 5 | Advanced Security (JWT, Lock, Rate Limit basics) | ✅ |
| Phase 6 | Admin Dashboard (UI + Management) | ✅ |
| Phase 7 | Audit Logs & Tracking | ✅ |
| Phase 8 | Application Registration (app_id, api_key, redirect_uri) | ✅ |
| Phase 9 | Redirect-based Authentication (/authorize flow) | ✅ |
| Phase 10 | Secure Token Exchange (code → JWT) | ✅ |
| Phase 11 | External App Integration Flow | ✅ |
| Phase 12 | App-scoped RBAC Enforcement | ✅ |
| Phase 13 | App Access Control (no role → no entry) | ✅ |
| Phase 14 | Security & Optimization (perm_version, rate limit, validation) | ⏳ Planned |

## ✨ Features (So Far)

- 🔑 **JWT Authentication** — Secure signup, login, and token-based auth
- 👥 **RBAC** — Roles (`admin`, `user`) and permissions (`read`, `write`, `delete`)
- 🏢 **Multi-Application Support** — Same user, different roles per application
- 🔒 **Permission-based Access Control** — Reusable dependency injection guards
- 📋 **Audit Logs** — Track login attempts, role changes, permission checks
- 🖥️ **Admin Dashboard** — Basic HTML UI for managing users, roles, permissions
- 🛡️ **Data Isolation** — Strict `app_id` scoping to prevent cross-app leakage

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Templates | Jinja2 |
| Config | Pydantic Settings, python-dotenv |

---

## 📁 Project Structure

```
ad fastapi/
├── app/
│   ├── core/          # Config, security utilities
│   ├── db/            # Database session & base
│   ├── middleware/    # Custom middleware
│   ├── models/        # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── permission.py
│   │   ├── application.py
│   │   ├── audit_log.py
│   │   └── associations.py
│   ├── routes/        # API route handlers
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── roles.py
│   │   ├── permissions.py
│   │   ├── applications.py
│   │   ├── audit_logs.py
│   │   └── pages.py
│   ├── schemas/       # Pydantic request/response models
│   ├── services/      # Business logic layer
│   ├── utils/         # Helper functions
│   └── main.py        # FastAPI app entry point
├── templates/         # Jinja2 HTML templates (Admin UI)
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚡ Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/theansh99999/AuthZen.git
cd "ad fastapi"
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup environment variables

```bash
copy .env.example .env
```

Edit `.env` with your actual values:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/iam_db
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_NAME=IAM Service
DEBUG=False
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

App will be live at: **http://localhost:8000**

Interactive API docs: **http://localhost:8000/docs**

---

## 🔗 Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/signup` | Register a new user |
| `POST` | `/auth/login` | Login & get JWT token |
| `GET` | `/auth/validate-token` | Validate a JWT token |
| `POST` | `/auth/check-permission` | Check user permission |
| `GET` | `/users/` | List all users |
| `GET` | `/roles/` | List all roles |
| `POST` | `/roles/` | Create a new role |
| `POST` | `/users/{id}/assign-role` | Assign role to user |
| `GET` | `/permissions/` | List all permissions |
| `GET` | `/applications/` | List all applications |
| `POST` | `/applications/` | Create a new application |
| `GET` | `/audit-logs/` | View audit logs |

---

## 🔒 Authentication Flow

```
User → POST /auth/login → JWT Token
                              ↓
         Token in Authorization header (Bearer)
                              ↓
         Protected Route → Dependency checks token
                              ↓
         Permission Check → Role → Application Scope
```

---

## 🗺️ Roadmap

- [ ] Refresh Token system
- [ ] Account lockout after failed login attempts
- [ ] Rate limiting on auth endpoints
- [ ] Full Admin Dashboard with role/permission management UI
- [ ] OAuth2 / SSO flow for external app login
- [ ] Docker support
- [ ] CI/CD pipeline

---

## 🤝 Contributing

This project is in active development. Feel free to open issues or PRs once the core is stable.

---

## 📄 License

This project is for personal/learning purposes. License TBD.

---

> Built with ❤️ using FastAPI | **IN PROGRESS — stay tuned!**
