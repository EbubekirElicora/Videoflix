# Videoflix Backend

Videoflix is a Django REST Framework backend for an authenticated video-streaming platform.

The application provides user registration, account activation, JWT authentication through HttpOnly cookies, password reset functionality, background video processing and adaptive HLS video streaming.

This repository contains the **backend only**. The provided Videoflix frontend is maintained and deployed separately and communicates with this backend through a REST API.

> Developed as part of the Developer Akademie GmbH advanced training program.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Implemented Features](#implemented-features)
- [Technology Stack](#technology-stack)
- [Application Architecture](#application-architecture)
- [Video Processing](#video-processing)
- [API Endpoints](#api-endpoints)
  - [Authentication](#authentication)
  - [Videos](#videos)
  - [Django Administration](#django-administration)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quickstart](#quickstart)
  - [1. Create the Environment File](#1-create-the-environment-file)
  - [2. Build and Start the Project](#2-build-and-start-the-project)
  - [3. Open the Backend](#3-open-the-backend)
- [Uploading and Processing Videos](#uploading-and-processing-videos)
- [Useful Docker Commands](#useful-docker-commands)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [Dependencies](#dependencies)
- [Original Docker Setup Reference](#original-docker-setup-reference)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Project Overview

The Videoflix backend handles authentication, video administration, background processing and video delivery.

Registered users must activate their accounts through an activation link before they can log in. Authentication is implemented with JSON Web Tokens stored in secure HttpOnly cookies.

Videos are uploaded through the Django administration interface. After a new video has been saved, a Django RQ background task automatically starts the FFmpeg processing pipeline.

The generated video files are delivered as HTTP Live Streaming resources.

---

## Implemented Features

### User Management

- Registration with email address and password
- Password confirmation validation
- Prevention of duplicate accounts
- Inactive user creation before email activation
- Account activation through a UID and token
- Secure login responses with generic error messages
- JWT access and refresh tokens
- Authentication through HttpOnly cookies
- Refresh token rotation
- Refresh token blacklisting during logout
- Password reset request
- Password reset confirmation
- Generic password-reset responses to prevent account enumeration

### Video Management

- Video model with title, description, source video and thumbnail
- Video administration through the Django admin panel
- Automatic background processing after upload
- Automatic thumbnail generation
- Automatic HLS conversion
- Supported HLS resolutions:
  - 480p
  - 720p
  - 1080p
- HLS manifest delivery
- HLS segment delivery
- Validation of supported resolutions
- Validation of HLS segment filenames
- Authenticated access to video resources
- HTTP 404 responses for unavailable video files

### Performance

- Redis as caching layer
- Cached video list
- Automatic cache invalidation after video creation, modification or deletion
- Django RQ for background processing
- PostgreSQL instead of SQLite
- Gunicorn as application server
- WhiteNoise for static files

---

## Technology Stack

| Technology | Purpose |
| :--- | :--- |
| Python | Backend programming language |
| Django | Web framework and administration |
| Django REST Framework | REST API implementation |
| Simple JWT | JWT authentication and token blacklisting |
| PostgreSQL | Relational database |
| Redis | Cache and RQ message broker |
| Django RQ | Background task processing |
| FFmpeg | Thumbnail and HLS generation |
| Gunicorn | WSGI application server |
| WhiteNoise | Static-file delivery |
| Docker | Containerized development and project evaluation |
| Docker Compose | Multi-container orchestration |

FFmpeg is installed inside the backend Docker image. A separate global FFmpeg installation on the host computer is therefore not required when the project is started through Docker.

---

## Application Architecture

The backend is divided into separate Django applications and layers.

### `auth_app`

Responsible for:

- User registration
- Account activation
- Login
- JWT cookie handling
- Token refresh
- Logout
- Password reset
- Authentication services

### `video_app`

Responsible for:

- Video model
- Video administration
- Video serialization
- Video API endpoints
- Redis caching
- RQ task creation
- FFmpeg processing
- HLS manifests and segments

### Layer Responsibilities

- `api/views.py` handles requests and responses.
- `api/serializers.py` validates and serializes API data.
- `services.py` contains application logic.
- `selectors.py` contains database queries and cached read operations.
- `tasks.py` contains background-processing tasks.
- `utils.py` contains filesystem and FFmpeg helpers.
- `signals.py` reacts to video model changes.
- `authentication.py` handles JWT authentication through cookies.

---

## Video Processing

The processing workflow starts automatically after a video has been uploaded through the Django admin panel.

```text
Video upload
    |
    v
Video model is saved
    |
    v
Django post_save signal
    |
    v
RQ task is added after the database transaction is committed
    |
    v
Django RQ worker starts processing
    |
    +--> Thumbnail is generated
    |
    +--> 480p HLS version is generated
    |
    +--> 720p HLS version is generated
    |
    +--> 1080p HLS version is generated
```

The generated media structure follows this pattern:

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
            │   ├── segment_000.ts
            │   └── ...
            ├── 720p/
            │   ├── index.m3u8
            │   ├── segment_000.ts
            │   └── ...
            └── 1080p/
                ├── index.m3u8
                ├── segment_000.ts
                └── ...
```

---

## API Endpoints

The backend is available locally at:

```text
http://localhost:8000
```

### Authentication

#### Register User

```http
POST /api/register/
```

Creates an inactive user and sends an account-activation email.

Example request:

```json
{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "confirmed_password": "SecurePassword123!"
}
```

---

#### Activate Account

```http
GET /api/activate/<uidb64>/<token>/
```

Activates a previously registered account.

---

#### Login

```http
POST /api/login/
```

Authenticates an active user and stores JWT tokens in HttpOnly cookies.

Example request:

```json
{
    "email": "user@example.com",
    "password": "SecurePassword123!"
}
```

---

#### Refresh Access Token

```http
POST /api/token/refresh/
```

Creates a new access token by using the refresh token stored in the HttpOnly cookie.

---

#### Logout

```http
POST /api/logout/
```

Blacklists the refresh token and removes the authentication cookies.

---

#### Request Password Reset

```http
POST /api/password_reset/
```

Example request:

```json
{
    "email": "user@example.com"
}
```

The response remains generic regardless of whether the email address exists.

---

#### Confirm Password Reset

```http
POST /api/password_confirm/<uidb64>/<token>/
```

Example request:

```json
{
    "new_password": "NewSecurePassword123!",
    "confirmed_password": "NewSecurePassword123!"
}
```

---

### Videos

All video endpoints require authentication.

#### Video List

```http
GET /api/video/
```

Returns the available videos ordered by creation date.

The result is cached in Redis for improved performance.

---

#### HLS Manifest

```http
GET /api/video/<movie_id>/<resolution>/index.m3u8
```

Example:

```http
GET /api/video/1/720p/index.m3u8
```

Supported resolutions:

```text
480p
720p
1080p
```

---

#### HLS Segment

```http
GET /api/video/<movie_id>/<resolution>/<segment>/
```

Example:

```http
GET /api/video/1/720p/segment_000.ts
```

Only segment filenames matching the expected format are accepted.

---

### Django Administration

```http
GET /admin/
```

The administration interface can be used to:

- Create videos
- Edit video metadata
- Delete videos
- View generated thumbnail information
- Manage users

The Docker entrypoint automatically creates a superuser from the configured environment variables when the account does not already exist.

---

## Project Structure

```text
.
├── auth_app/
│   ├── api/
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── authentication.py
│   ├── services.py
│   ├── tokens.py
│   ├── urls.py
│   └── utils.py
├── video_app/
│   ├── api/
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── views.py
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
│   └── wsgi.py
├── backend.Dockerfile
├── backend.entrypoint.sh
├── docker-compose.yml
├── manage.py
├── requirements.txt
├── .env.template
└── README.md
```

---

## Prerequisites

The following software must be installed:

- **Docker Desktop**
- **Docker Compose**
- **Git**

Docker installation:

[Docker Compose installation documentation](https://docs.docker.com/compose/install/)

Git installation:

[Git download page](https://git-scm.com/downloads)

The project is fully containerized. Python, PostgreSQL, Redis, Gunicorn, Django RQ and FFmpeg are provided through Docker.

---

## Quickstart

> [!CAUTION]
> Keep the provided Docker configuration unchanged.
>
> Do not modify the fundamental configuration of:
>
> - `backend.Dockerfile`
> - `docker-compose.yml`
> - `backend.entrypoint.sh`
>
> Environment-variable values may be adjusted, but the existing variable names should not be deleted.

### 1. Create the Environment File

Create a `.env` file from `.env.template`.

Using Git Bash, Linux or macOS:

```bash
cp .env.template .env
```

Using Windows PowerShell:

```powershell
Copy-Item .env.template .env
```

Review the generated `.env` file and replace placeholder values where required.

The real `.env` file contains credentials and must not be committed to Git.

---

### 2. Build and Start the Project

Run:

```bash
docker compose up --build
```

To run the containers in the background:

```bash
docker compose up -d --build
```

Older Docker Compose installations may require:

```bash
docker-compose up --build
```

The Docker entrypoint automatically:

- Waits for PostgreSQL
- Collects static files
- Creates migrations when necessary
- Applies database migrations
- Creates the configured superuser when necessary
- Starts Gunicorn
- Starts the Django RQ worker

---

### 3. Open the Backend

Backend:

```text
http://localhost:8000
```

Django administration:

```text
http://localhost:8000/admin/
```

Django RQ administration:

```text
http://localhost:8000/django-rq/
```

---

## Uploading and Processing Videos

1. Start the Docker containers.
2. Open the Django administration interface.
3. Log in with the superuser credentials from `.env`.
4. Open the video administration.
5. Create a new video.
6. Enter a title and description.
7. Select a source video file.
8. Save the video.

After the database transaction has been committed, the video is added to the default RQ queue.

The worker then generates:

- One thumbnail
- One 480p HLS version
- One 720p HLS version
- One 1080p HLS version

Processing may take some time depending on:

- Video duration
- Source resolution
- File size
- Available CPU performance

RQ worker activity can be inspected with:

```bash
docker compose logs -f web
```

Generated files are stored below:

```text
media/videos/
```

---

## Useful Docker Commands

### Show Running Containers

```bash
docker compose ps
```

### Follow Backend Logs

```bash
docker compose logs -f web
```

### Show Recent Backend Logs

```bash
docker compose logs --tail=250 web
```

### Run the Django System Check

```bash
docker compose exec web python manage.py check
```

### Open a Shell in the Backend Container

```bash
docker compose exec web sh
```

### Stop the Containers

```bash
docker compose down
```

### Rebuild the Containers

```bash
docker compose up -d --build
```

### Restart the Backend Service

```bash
docker compose restart web
```

---

## Environment Variables

All required environment variables are stored in the local `.env` file.

> [!IMPORTANT]
> Do not rename or delete the existing variables from the supplied configuration.
>
> Use secure values and never publish the real `.env` file.

The `backend.entrypoint.sh` script creates a superuser based on:

- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_PASSWORD`
- `DJANGO_SUPERUSER_EMAIL`

| Name | Type | Description | Default | Mandatory |
| :--- | :---: | :--- | :--- | :---: |
| `DJANGO_SUPERUSER_USERNAME` | str | Username for the automatically created Django administrator | `admin` | |
| `DJANGO_SUPERUSER_PASSWORD` | str | Password for the Django administrator | `adminpassword` | |
| `DJANGO_SUPERUSER_EMAIL` | str | Email address of the Django administrator | `admin@example.com` | |
| `SECRET_KEY` | str | Secret cryptographic Django key | | Yes |
| `DEBUG` | bool | Enables or disables Django debug mode | `True` | |
| `ALLOWED_HOSTS` | List[str] | Hosts and domains accepted by Django | `localhost` | |
| `CSRF_TRUSTED_ORIGINS` | List[str] | Trusted frontend origins for CSRF protection | `http://localhost:4200` | |
| `DB_NAME` | str | PostgreSQL database name | `your_database_name` | Yes |
| `DB_USER` | str | PostgreSQL database user | `your_database_user` | Yes |
| `DB_PASSWORD` | str | PostgreSQL database password | `your_database_password` | Yes |
| `DB_HOST` | str | PostgreSQL host or Docker service name | `db` | |
| `DB_PORT` | int | PostgreSQL port | `5432` | |
| `REDIS_LOCATION` | str | Redis cache connection URL | `redis://redis:6379/1` | |
| `REDIS_HOST` | str | Redis host or Docker service name | `redis` | |
| `REDIS_PORT` | int | Redis port | `6379` | |
| `REDIS_DB` | int | Redis database used by RQ | `0` | |
| `EMAIL_HOST` | str | SMTP server address | `smtp.example.com` | Yes |
| `EMAIL_PORT` | int | SMTP server port | `587` | |
| `EMAIL_USE_TLS` | bool | Enables TLS for email delivery | `True` | |
| `EMAIL_USE_SSL` | bool | Enables SSL for email delivery | `False` | |
| `EMAIL_HOST_USER` | str | SMTP account username | `your_email_user` | Yes |
| `EMAIL_HOST_PASSWORD` | str | SMTP account password | `your_email_password` | Yes |
| `DEFAULT_FROM_EMAIL` | str | Sender address used by Django | `EMAIL_HOST_USER` | |

---

## Database Migrations

### Create Migrations

```bash
docker compose exec web python manage.py makemigrations
```

### Apply Migrations

```bash
docker compose exec web python manage.py migrate
```

The supplied Docker entrypoint also applies migrations automatically when the backend container starts.

Migration files must remain part of the Git repository so that the project database can be reproduced on another computer.

---

## Dependencies

The Python dependencies are listed in:

```text
requirements.txt
```

When a dependency is added or changed, rebuild the backend image:

```bash
docker compose up -d --build
```

To inspect installed top-level packages inside the container:

```bash
docker compose exec web pip list --not-required
```

---

## Original Docker Setup Reference

The supplied Docker setup was provided to simplify local development and project evaluation.

> [!CAUTION]
> Follow the supplied Docker instructions carefully.
>
> Changing the fundamental configuration may prevent the project from starting.
>
> Existing variables in `.env.template` must not be deleted.
>
> Do not modify:
>
> - `backend.Dockerfile`
> - `docker-compose.yml`
> - `backend.entrypoint.sh`
>
> Additional Python packages may be installed when required. Update `requirements.txt` whenever a runtime dependency is added.

### Original Settings Reference

The project uses environment-based Django configuration.

Example imports:

```python
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
```

Environment-based security configuration:

```python
SECRET_KEY = os.getenv("SECRET_KEY")
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    default="localhost",
).split(",")

CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:4200",
).split(",")
```

Installed Django RQ application:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_rq",
]
```

WhiteNoise middleware:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

PostgreSQL configuration:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get(
            "DB_NAME",
            default="videoflix_db",
        ),
        "USER": os.environ.get(
            "DB_USER",
            default="videoflix_user",
        ),
        "PASSWORD": os.environ.get(
            "DB_PASSWORD",
            default="supersecretpassword",
        ),
        "HOST": os.environ.get(
            "DB_HOST",
            default="db",
        ),
        "PORT": os.environ.get(
            "DB_PORT",
            default=5432,
        ),
    }
}
```

Redis cache configuration:

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get(
            "REDIS_LOCATION",
            default="redis://redis:6379/1",
        ),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "videoflix",
    }
}
```

Django RQ configuration:

```python
RQ_QUEUES = {
    "default": {
        "HOST": os.environ.get(
            "REDIS_HOST",
            default="redis",
        ),
        "PORT": os.environ.get(
            "REDIS_PORT",
            default=6379,
        ),
        "DB": os.environ.get(
            "REDIS_DB",
            default=0,
        ),
        "DEFAULT_TIMEOUT": 900,
        "REDIS_CLIENT_KWARGS": {},
    },
}
```

Static and media configuration:

```python
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

---

## Troubleshooting

### Docker Cannot Connect to Docker Desktop

Example error:

```text
unable to get image 'postgres:latest': error during connect:
open //./pipe/dockerDesktopLinuxEngine:
The system cannot find the file specified.
```

Solution:

Make sure Docker Desktop is running before starting the project.

---

### Entrypoint File Cannot Be Found

Example error:

```text
videoflix_backend | exec ./backend.entrypoint.sh:
no such file or directory
```

Solution:

Ensure that `backend.entrypoint.sh` uses the Unix line-ending format:

```text
LF
```

In Visual Studio Code, the current line-ending format is displayed in the bottom-right corner.

Do not save the entrypoint file with Windows `CRLF` line endings.

---

### Database Migration Fails During Container Startup

Create migrations manually:

```bash
docker compose run --rm web python manage.py makemigrations
```

Apply them manually:

```bash
docker compose run --rm web python manage.py migrate
```

Afterwards, rebuild and start the project:

```bash
docker compose up -d --build
```

---

### Video Processing Does Not Start

Inspect the backend and worker logs:

```bash
docker compose logs -f web
```

Check whether:

- PostgreSQL is ready
- Redis is running
- The RQ worker is listening on the default queue
- The video file exists
- FFmpeg reports an encoding error
- The video was created as a new database entry

---

### HLS Manifest Returns HTTP 404

Check whether the processing task has completed.

The expected path is:

```text
media/videos/hls/<video_id>/<resolution>/index.m3u8
```

Supported resolution values are:

```text
480p
720p
1080p
```

---

### HLS Segment Returns HTTP 404

The segment name must match this format:

```text
segment_000.ts
```

Examples of valid names:

```text
segment_000.ts
segment_001.ts
segment_002.ts
```

---

### Authentication Returns HTTP 401

Check whether:

- The account has been activated
- Login was successful
- The client accepts and sends cookies
- The access token has expired
- The refresh endpoint has been called when required

---

### Static Files Are Missing

Run:

```bash
docker compose exec web python manage.py collectstatic --noinput
```

Then restart the backend:

```bash
docker compose restart web
```

---

## License

This project was developed for educational purposes as part of the Developer Akademie GmbH advanced training program.

The components supplied by Developer Akademie GmbH are subject to the included **Developer Akademie Learning License (Non-commercial)**.

The project may be presented for non-commercial portfolio, application and reference purposes in accordance with the conditions contained in the `LICENSE.md` file.

Do not publish:

- Real credentials
- The local `.env` file
- Personal user data
- Private email passwords
- Production secrets
- Unlicensed video material