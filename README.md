# Videoflix Backend

Videoflix is a Django REST Framework backend for an authenticated video-streaming platform.

The backend provides user registration, account activation, JWT authentication through HttpOnly cookies, password reset functionality, responsive HTML emails, background video processing and adaptive HLS video streaming.

This repository contains the **backend only**. The provided Videoflix frontend is maintained separately and communicates with this backend through a REST API.

> Developed as part of the Developer Akademie GmbH advanced training program.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Implemented Features](#implemented-features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Main Workflows](#main-workflows)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Quickstart](#quickstart)
- [Environment Variables](#environment-variables)
- [Useful Commands](#useful-commands)
- [License](#license)

---

## Project Overview

The Videoflix backend handles authentication, video administration, background processing and protected video delivery.

New users are created as inactive accounts. After registration, the backend sends a styled HTML activation email containing a UID and token. The link opens the provided frontend, which forwards the activation data to the backend.

Authentication is implemented with JWT access and refresh tokens stored in HttpOnly cookies. Refresh tokens are rotated and blacklisted during logout.

Videos are uploaded through the Django administration interface. A Django RQ background task uses FFmpeg to create a thumbnail and HLS versions in 480p, 720p and 1080p. Generated manifests and segments are delivered only to authenticated users.

---

## Implemented Features

### User Management

- Registration with email address and password confirmation
- Prevention of duplicate accounts
- Inactive account creation before email activation
- Account activation through UID and token
- Responsive HTML emails for activation and password reset
- Embedded Videoflix logo in authentication emails
- Password-reset links with a 24-hour validity period
- Generic authentication and reset responses to reduce account enumeration
- JWT access and refresh tokens
- HttpOnly cookie-based authentication
- Refresh-token rotation and blacklisting
- Login, token refresh and logout endpoints

### Video Management

- Video administration through Django Admin
- Source-video and thumbnail storage
- Automatic background processing after upload
- Automatic thumbnail generation
- HLS conversion with 480p, 720p and 1080p variants
- HLS manifest and segment delivery
- Validation of resolutions and segment filenames
- Authenticated access to video resources
- HTTP 404 responses for unavailable media files

### Data and Performance

- PostgreSQL database
- Redis caching layer
- Cached video list
- Automatic cache invalidation after video changes
- Django RQ background processing
- Gunicorn application server
- WhiteNoise static-file handling
- Docker-based project setup

---

## Technology Stack

| Technology | Purpose |
| :--- | :--- |
| Python | Backend programming language |
| Django | Web framework and administration |
| Django REST Framework | REST API implementation |
| Simple JWT | JWT creation, refresh and blacklisting |
| PostgreSQL | Relational database |
| Redis | Cache and RQ message broker |
| Django RQ | Background task processing |
| FFmpeg | Thumbnail and HLS generation |
| Gunicorn | WSGI application server |
| WhiteNoise | Static-file handling |
| Docker | Containerized execution |
| Docker Compose | Multi-container orchestration |

FFmpeg is installed inside the backend Docker image. A separate FFmpeg installation on the host computer is not required when the project is started through Docker.

---

## Architecture

The backend is divided into two Django applications.

### `auth_app`

Responsible for:

- Registration and account activation
- Login, logout and token refresh
- JWT cookie handling
- Password reset
- HTML email rendering and delivery
- Authentication-related services and helpers

### `video_app`

Responsible for:

- Video model and administration
- Video API serialization
- Redis-backed video queries
- RQ task creation
- FFmpeg processing
- Thumbnail generation
- HLS manifests and segments

### Layer Responsibilities

- `api/views.py` handles HTTP requests and responses.
- `api/serializers.py` validates and serializes API data.
- `services.py` contains application logic.
- `email_service.py` renders and sends multipart authentication emails.
- `selectors.py` contains database queries and cached read operations.
- `tasks.py` contains background-processing tasks.
- `utils.py` contains reusable authentication, filesystem and FFmpeg helpers.
- `signals.py` reacts to video model changes.
- `authentication.py` reads JWT access tokens from HttpOnly cookies.

---

## Main Workflows

### Account Activation

```text
Registration
    |
    v
Inactive user is created
    |
    v
Backend sends an HTML activation email
    |
    v
Frontend receives UID and token
    |
    v
Frontend calls the backend activation endpoint
    |
    v
User account becomes active
```

### Password Reset

```text
Password-reset request
    |
    v
Backend sends an HTML reset email
    |
    v
Frontend receives UID and token
    |
    v
Frontend submits the new password to the backend
    |
    v
Password is updated
```

### Video Processing

```text
Video upload through Django Admin
    |
    v
Video model is saved
    |
    v
Django post-save signal
    |
    v
RQ task is queued after the database transaction
    |
    v
FFmpeg generates:
    - Thumbnail
    - 480p HLS
    - 720p HLS
    - 1080p HLS
```

Generated media follows this structure:

```text
media/
└── videos/
    ├── originals/
    ├── thumbnails/
    │   └── <video_id>.jpg
    └── hls/
        └── <video_id>/
            ├── 480p/
            │   ├── index.m3u8
            │   └── segment_000.ts
            ├── 720p/
            │   ├── index.m3u8
            │   └── segment_000.ts
            └── 1080p/
                ├── index.m3u8
                └── segment_000.ts
```

---

## API Endpoints

The backend is available locally at:

```text
http://localhost:8000
```

### Authentication

| Method | Endpoint | Authentication | Purpose |
| :---: | :--- | :---: | :--- |
| POST | `/api/register/` | No | Register an inactive user |
| GET | `/api/activate/<uidb64>/<token>/` | No | Activate a user account |
| POST | `/api/login/` | No | Authenticate a user and set JWT cookies |
| POST | `/api/token/refresh/` | Refresh cookie | Create a new access token |
| POST | `/api/logout/` | Refresh cookie | Blacklist the refresh token and delete cookies |
| POST | `/api/password_reset/` | No | Request a password-reset email |
| POST | `/api/password_confirm/<uidb64>/<token>/` | No | Set a new password |

Registration request:

```json
{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "confirmed_password": "SecurePassword123!"
}
```

Password-reset confirmation request:

```json
{
    "new_password": "NewSecurePassword123!",
    "confirm_password": "NewSecurePassword123!"
}
```

### Videos

All video endpoints require authentication.

| Method | Endpoint | Purpose |
| :---: | :--- | :--- |
| GET | `/api/video/` | Return available videos ordered by creation date |
| GET | `/api/video/<movie_id>/<resolution>/index.m3u8` | Return an HLS manifest |
| GET | `/api/video/<movie_id>/<resolution>/<segment>/` | Return an HLS segment |

Supported resolutions:

```text
480p
720p
1080p
```

### Administration

| Method | Endpoint | Purpose |
| :---: | :--- | :--- |
| GET | `/admin/` | Django administration |

---

## Project Structure

```text
.
├── auth_app/
│   ├── api/
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── migrations/
│   ├── authentication.py
│   ├── static/
│   │   └── auth_app/
│   │       └── email/
│   │           ├── videoflix_logo.svg
│   │           └── videoflix_logo.png
│   ├── templates/
│   │   └── auth_app/
│   │       └── emails/
│   │           ├── activation_email.html
│   │           └── password_reset_email.html
│   ├── email_service.py
│   ├── services.py
│   └── utils.py
├── video_app/
│   ├── api/
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── selectors.py
│   ├── services.py
│   ├── signals.py
│   ├── tasks.py
│   └── utils.py
├── core/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── backend.Dockerfile
├── backend.entrypoint.sh
├── docker-compose.yml
├── manage.py
├── requirements.txt
├── .env.template
├── LICENSE.md
└── README.md
```

The provided frontend is not included in this repository.

---

## Quickstart

### Prerequisites

Install:

- Docker Desktop
- Docker Compose
- Git

### 1. Create the Environment File

Using Git Bash, Linux or macOS:

```bash
cp .env.template .env
```

Using Windows PowerShell:

```powershell
Copy-Item .env.template .env
```

Review the generated `.env` file and replace placeholder values where required.

> The real `.env` file contains credentials and must not be committed to Git.

### 2. Build and Start the Project

```bash
docker compose up -d --build
```

The supplied Docker entrypoint:

- Waits for PostgreSQL
- Collects static files
- Creates and applies migrations
- Creates the configured superuser when required
- Starts Gunicorn
- Starts the Django RQ worker

> Keep `backend.Dockerfile`, `docker-compose.yml` and `backend.entrypoint.sh` unchanged.

### 3. Open the Backend

Backend:

```text
http://localhost:8000
```

Django administration:

```text
http://localhost:8000/admin/
```

Videos can be uploaded through Django Admin. After a new video is saved, processing runs automatically in the background.

---

## Environment Variables

The local `.env` file is based on `.env.template`.

| Variable | Purpose |
| :--- | :--- |
| `SECRET_KEY` | Django cryptographic key |
| `DEBUG` | Enable or disable debug mode |
| `ALLOWED_HOSTS` | Hosts accepted by Django |
| `CSRF_TRUSTED_ORIGINS` | Trusted frontend origins |
| `CORS_ALLOWED_ORIGINS` | Frontend origins allowed to access the API |
| `AUTH_COOKIE_SECURE` | Send authentication cookies only through HTTPS |
| `AUTH_COOKIE_SAMESITE` | SameSite policy for authentication cookies |
| `SECURE_SSL_REDIRECT` | Redirect HTTP requests to HTTPS |
| `SESSION_COOKIE_SECURE` | Send Django session cookies only through HTTPS |
| `CSRF_COOKIE_SECURE` | Send CSRF cookies only through HTTPS |
| `SECURE_HSTS_SECONDS` | Duration of the HTTP Strict Transport Security policy |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL database user |
| `DB_PASSWORD` | PostgreSQL database password |
| `DB_HOST` | PostgreSQL host or Docker service |
| `DB_PORT` | PostgreSQL port |
| `REDIS_LOCATION` | Redis cache URL |
| `REDIS_HOST` | Redis host or Docker service |
| `REDIS_PORT` | Redis port |
| `REDIS_DB` | Redis database used by RQ |
| `EMAIL_BACKEND` | Django email backend |
| `EMAIL_HOST` | SMTP server |
| `EMAIL_PORT` | SMTP server port |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password |
| `EMAIL_USE_TLS` | Enable SMTP TLS |
| `EMAIL_USE_SSL` | Enable SMTP SSL |
| `DEFAULT_FROM_EMAIL` | Sender address |
| `FRONTEND_ACTIVATION_URL` | Frontend account-activation page |
| `FRONTEND_PASSWORD_RESET_URL` | Frontend password-reset page |
| `DJANGO_SUPERUSER_USERNAME` | Automatically created admin username |
| `DJANGO_SUPERUSER_PASSWORD` | Automatically created admin password |
| `DJANGO_SUPERUSER_EMAIL` | Automatically created admin email |

For local development, the console email backend can be used. A configured SMTP backend is required for real email delivery.

---

## Useful Commands

Start or rebuild the project:

```bash
docker compose up -d --build
```

Follow backend and worker logs:

```bash
docker compose logs -f web
```

Run the Django system check:

```bash
docker compose exec web python manage.py check
```

Apply database migrations manually:

```bash
docker compose exec web python manage.py migrate
```

Stop the project:

```bash
docker compose down
```

Run an optional local code-quality check:

```bash
python -m pip install ruff
python -m ruff check .
```

---

## License

This project was developed for educational purposes as part of the Developer Akademie GmbH advanced training program.

The components supplied by Developer Akademie GmbH are subject to the included **Developer Akademie Learning License (Non-commercial)**.

The project may be presented for non-commercial portfolio, application and reference purposes in accordance with the conditions contained in `LICENSE.md`.

Do not publish real credentials, personal user data, private email passwords, production secrets or unlicensed video material.