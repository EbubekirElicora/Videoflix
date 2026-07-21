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
- [Environment Profiles](#environment-profiles)
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

This guide is written for users who have no previous knowledge of this
repository.

Follow every step in the exact order shown below.

### 1. Install the Required Programs

Install the following programs before continuing:

- Git
- Docker Desktop
- Docker Compose
- Visual Studio Code
- The Live Server extension for Visual Studio Code

Python, PostgreSQL, Redis and FFmpeg do not need to be installed separately.
They are provided through Docker.

Start Docker Desktop before continuing.

Verify that Docker is available:

```bash
docker --version
docker compose version
```

Both commands must display a version number.

If one of the commands fails, Docker Desktop is either not installed or not
running.

### 2. Clone the Backend Repository

Open Git Bash, Windows PowerShell or another terminal.

Run:

```bash
git clone https://github.com/EbubekirElicora/Videoflix.git
cd Videoflix
```

All following Docker commands must be executed from inside the cloned
`Videoflix` directory.

The supplied frontend is maintained separately and is not included in this
backend repository.

### 3. Create the Local Environment File

The repository contains a file named:

```text
.env.template
```

This is an example configuration without real credentials.

Create a copy named `.env`.

Using Git Bash, Linux or macOS:

```bash
cp .env.template .env
```

Using Windows PowerShell:

```powershell
Copy-Item .env.template .env
```

After running the command, the project directory must contain both files:

```text
.env.template
.env
```

Open the newly created `.env` file in Visual Studio Code.

Important:

- Edit `.env`, not `.env.template`.
- The real `.env` file may contain passwords.
- Never commit `.env` to GitHub.
- Lines beginning with `#` are comments and are ignored.
- The default values are prepared for local Docker development.
- PostgreSQL and Redis values can remain unchanged for the first local setup.

### 4. Choose the Email Delivery Method

Videoflix uses emails for:

- Account activation after registration
- Password reset

There are two possible email configurations.

Choose exactly one option.

---

#### Option A: Display Emails in the Docker Logs

This option is active by default.

The active line in `.env` is:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

With this backend:

- No real email is sent.
- Nothing arrives in an email inbox.
- The complete activation or password-reset email is printed in the Docker
  logs.
- SMTP credentials are not required.

Keep this line active:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Keep the SMTP backend commented out:

```env
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

After registering a user, display the email with:

```bash
docker compose logs -f web
```

The logs contain:

- The recipient email address
- The email subject
- The complete activation or password-reset link

Copy the link from the logs and open it in the browser.

Press:

```text
Ctrl + C
```

to stop following the logs.

This does not stop the Docker containers.

---

#### Option B: Send Real Emails Through SMTP

Choose this option when activation and password-reset emails must arrive in a
real email inbox.

Open `.env`.

Comment out the console backend:

```env
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Activate the SMTP backend:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

There must be exactly one active `EMAIL_BACKEND` line.

Replace the example SMTP values with the values supplied by your own email
provider:

```env
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=your_email@example.com
```

Explanation:

| Variable | Required value |
| :--- | :--- |
| `EMAIL_HOST` | SMTP server from the email provider |
| `EMAIL_PORT` | Usually `587` for TLS or `465` for SSL |
| `EMAIL_HOST_USER` | Usually the complete email address |
| `EMAIL_HOST_PASSWORD` | Email password or app password |
| `DEFAULT_FROM_EMAIL` | Sender address permitted by the SMTP provider |

For SMTP port `587`, normally use:

```env
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
```

For SMTP port `465`, normally use:

```env
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
```

Important:

- `EMAIL_USE_TLS` and `EMAIL_USE_SSL` must never both be `True`.
- Some providers require an app password when two-factor authentication is
  enabled.
- In that case, use the generated app password instead of the normal account
  password.
- Real SMTP credentials belong only in `.env`.
- Never place real credentials in `.env.template`, `README.md` or GitHub.

### 5. Check the Frontend Port

The default configuration expects the supplied frontend to run through Live
Server on port `5500`.

The active email URLs are:

```env
FRONTEND_ACTIVATION_URL=http://127.0.0.1:5500/pages/auth/activate.html
FRONTEND_PASSWORD_RESET_URL=http://127.0.0.1:5500/pages/auth/confirm_password.html
```

The allowed local frontend origins are:

```env
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:5501,http://127.0.0.1:5501
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:5501,http://127.0.0.1:5501
```

When Live Server starts the frontend on port `5501`, change the email URLs to:

```env
FRONTEND_ACTIVATION_URL=http://127.0.0.1:5501/pages/auth/activate.html
FRONTEND_PASSWORD_RESET_URL=http://127.0.0.1:5501/pages/auth/confirm_password.html
```

The port in the activation and password-reset URLs must match the actual
frontend port.

### 6. Review the PostgreSQL Configuration

The default local PostgreSQL values are:

```env
DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=videoflix_local_password
DB_HOST=db
DB_PORT=5432
```

These values work directly with `docker-compose.yml`.

Do not change:

```env
DB_HOST=db
```

to:

```env
DB_HOST=localhost
```

Inside the Docker network, `db` is the PostgreSQL service name.

### 7. Review the Redis Configuration

The default Redis values are:

```env
REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0
```

Do not change:

```env
REDIS_HOST=redis
```

to:

```env
REDIS_HOST=localhost
```

Inside the Docker network, `redis` is the Redis service name.

### 8. Build and Start the Backend

Make sure Docker Desktop is running.

Run this command from inside the backend repository:

```bash
docker compose up -d --build
```

During the first startup, Docker:

- Downloads the required images
- Builds the Django backend image
- Starts PostgreSQL
- Starts Redis
- Waits until PostgreSQL is ready
- Collects static files
- Creates and applies database migrations
- Creates the configured Django administrator when required
- Starts the Django RQ worker
- Starts Gunicorn

The first build can take several minutes.

Keep these supplied files unchanged:

```text
backend.Dockerfile
docker-compose.yml
backend.entrypoint.sh
```

### 9. Verify That the Containers Are Running

Run:

```bash
docker compose ps
```

The output must show these containers as running:

```text
videoflix_backend
videoflix_database
videoflix_redis
```

Inspect the latest backend logs:

```bash
docker compose logs --tail=100 web
```

A successful startup should not contain:

- A Python traceback
- A PostgreSQL connection error
- A Redis connection error
- A missing environment-file error

Run the Django system check:

```bash
docker compose exec web python manage.py check
```

Expected result:

```text
System check identified no issues
```

### 10. Open the Backend

The backend is available at:

```text
http://localhost:8000
```

The Django administration interface is available at:

```text
http://localhost:8000/admin/
```

The default local administrator is:

```text
Username: admin
Password: adminpassword
```

These credentials are intended only for local development.

### 11. Start the Supplied Frontend

Open the separately supplied frontend folder in Visual Studio Code.

Open its main `index.html` file.

Start the file with the Live Server extension.

The frontend address is normally:

```text
http://127.0.0.1:5500
```

or:

```text
http://127.0.0.1:5501
```

Check the port shown by Live Server.

When the port differs from the values in `.env`, update:

- `FRONTEND_ACTIVATION_URL`
- `FRONTEND_PASSWORD_RESET_URL`
- `CSRF_TRUSTED_ORIGINS`
- `CORS_ALLOWED_ORIGINS`

After editing `.env`, recreate the containers:

```bash
docker compose down
docker compose up -d
```

These commands preserve the existing Docker volumes and database data.

### 12. Test Registration and Account Activation

Open the frontend registration page.

Register with an email address that has not already been used.

The backend creates the new account as inactive.

The user cannot log in until the activation link has been opened.

#### Using the Console Email Backend

Run:

```bash
docker compose logs -f web
```

Find the activation email in the logs.

Copy the complete activation URL and open it in the browser.

No real email arrives when the console backend is active.

#### Using the SMTP Email Backend

Check the inbox of the address entered during registration.

Also check:

- Spam
- Junk
- Unwanted email

Open the activation link from the received email.

After successful activation, log in through the frontend.

### 13. Test SMTP Independently

This test is only required when the SMTP backend is active.

Replace `receiver@example.com` with a real recipient address:

```bash
docker compose exec web python manage.py shell -c \
"from django.conf import settings; from django.core.mail import send_mail; send_mail('Videoflix SMTP Test', 'Email delivery works.', settings.DEFAULT_FROM_EMAIL, ['receiver@example.com'], fail_silently=False)"
```

Expected command result:

```text
1
```

A result of `1` means Django handed one email to the SMTP server.

Also check the recipient inbox and spam folder.

### 14. Test Password Reset

Open the password-reset page in the frontend.

Enter the email address of an active account.

Depending on the selected email backend:

- Read the password-reset link from `docker compose logs -f web`, or
- Open the real password-reset email in the recipient inbox

Open the link.

Enter and confirm a new password.

Verify that login works with the new password.

### 15. Upload and Process a Video

Open Django Admin:

```text
http://localhost:8000/admin/
```

Log in with the configured administrator.

Create a new video entry and upload a video file.

After saving, the Django RQ worker automatically generates:

- A thumbnail
- A 480p HLS version
- A 720p HLS version
- A 1080p HLS version

Follow the processing output with:

```bash
docker compose logs -f web
```

Video processing can temporarily use significant CPU resources.

After processing finishes, test:

- Video playback
- Sound
- Seeking
- 480p
- 720p
- 1080p

---

## Environment Profiles

The `.env.template` file contains one active local-development configuration
and commented examples for staging and production.

Only one value for each environment variable may be active at the same time.

### Local Development

The active default configuration is intended for local development through
Docker and an HTTP frontend started with Live Server.

```env
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
AUTH_COOKIE_SECURE=False
AUTH_COOKIE_SAMESITE=Lax
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
```

The console email backend is active by default:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

This configuration does not send real emails. Activation and password-reset
emails are displayed with:

```bash
docker compose logs -f web
```

Real SMTP delivery can also be enabled during local development by following
the email instructions in the Quickstart section.

### Staging

The staging example is commented out in `.env.template`.

To activate staging:

1. Comment out the corresponding local-development values.
2. Uncomment the staging values.
3. Replace every example domain with the real staging domain.
4. Replace the development secret key and passwords.
5. Configure real SMTP credentials.
6. Use HTTPS.

Example:

```env
DEBUG=False
ALLOWED_HOSTS=staging.example.com
CSRF_TRUSTED_ORIGINS=https://staging.example.com
CORS_ALLOWED_ORIGINS=https://staging.example.com
AUTH_COOKIE_SECURE=True
AUTH_COOKIE_SAMESITE=Lax
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=3600
FRONTEND_ACTIVATION_URL=https://staging.example.com/pages/auth/activate.html
FRONTEND_PASSWORD_RESET_URL=https://staging.example.com/pages/auth/confirm_password.html
```

### Production

The production example is also commented out in `.env.template`.

Before using production:

1. Set `DEBUG=False`.
2. Replace the example domain with the real production domain.
3. Generate a long random `SECRET_KEY`.
4. Replace the database credentials.
5. Replace the administrator password.
6. Activate the SMTP email backend.
7. Enter real SMTP credentials.
8. Enable secure cookies and HTTPS redirection.
9. Never commit the production `.env` file.

Example:

```env
DEBUG=False
ALLOWED_HOSTS=videoflix.example.com
CSRF_TRUSTED_ORIGINS=https://videoflix.example.com
CORS_ALLOWED_ORIGINS=https://videoflix.example.com
AUTH_COOKIE_SECURE=True
AUTH_COOKIE_SAMESITE=Lax
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=3600
FRONTEND_ACTIVATION_URL=https://videoflix.example.com/pages/auth/activate.html
FRONTEND_PASSWORD_RESET_URL=https://videoflix.example.com/pages/auth/confirm_password.html
```

The real production values belong only in the private `.env` file.

---


## Environment Variables

The local `.env` file is based on `.env.template`.

| Variable | Purpose |
| :--- | :--- |
| `SECRET_KEY` | Django cryptographic key |
| `DEBUG` | Enable or disable debug mode |
| `ALLOWED_HOSTS` | Hosts accepted by Django |
| `CSRF_TRUSTED_ORIGINS` | Trusted frontend origins |
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

Run local code-quality checks:

```bash
python -m ruff check .
```

---

## License

This project was developed for educational purposes as part of the Developer Akademie GmbH advanced training program.

The components supplied by Developer Akademie GmbH are subject to the included **Developer Akademie Learning License (Non-commercial)**.

The project may be presented for non-commercial portfolio, application and reference purposes in accordance with the conditions contained in `LICENSE.md`.

Do not publish real credentials, personal user data, private email passwords, production secrets or unlicensed video material.