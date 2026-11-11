# 📦 Project Setup

---

# 🧩 1. Install Homebrew (Mac Only)

> Skip this step if you're on Windows.

Homebrew is a package manager for macOS.  
You’ll use it to easily install Git, Python, Docker, etc.

**Install Homebrew:**

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Verify Homebrew:**

```bash
brew --version
```

If you see a version number, you're good to go.

---

# 🧩 2. Install and Configure Git

## Install Git

- **MacOS (using Homebrew)**

```bash
brew install git
```

- **Windows**

Download and install [Git for Windows](https://git-scm.com/download/win).  
Accept the default options during installation.

**Verify Git:**

```bash
git --version
```

---

## Configure Git Globals

Set your name and email so Git tracks your commits properly:

```bash
git config --global user.name "Your Name"
git config --global user.email "your_email@example.com"
```

Confirm the settings:

```bash
git config --list
```

---

## Generate SSH Keys and Connect to GitHub

> Only do this once per machine.

1. Generate a new SSH key:

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

(Press Enter at all prompts.)

2. Start the SSH agent:

```bash
eval "$(ssh-agent -s)"
```

3. Add the SSH private key to the agent:

```bash
ssh-add ~/.ssh/id_ed25519
```

4. Copy your SSH public key:

- **Mac/Linux:**

```bash
cat ~/.ssh/id_ed25519.pub | pbcopy
```

- **Windows (Git Bash):**

```bash
cat ~/.ssh/id_ed25519.pub | clip
```

5. Add the key to your GitHub account:
   - Go to [GitHub SSH Settings](https://github.com/settings/keys)
   - Click **New SSH Key**, paste the key, save.

6. Test the connection:

```bash
ssh -T git@github.com
```

You should see a success message.

---

# 🧩 3. Clone the Repository

Now you can safely clone the course project:

```bash
git clone <repository-url>
cd <repository-directory>
```

---

# 🛠️ 4. Install Python 3.11+

## Install Python

- **MacOS (Homebrew)**

```bash
brew install python
```

- **Windows**

Download and install [Python for Windows](https://www.python.org/downloads/).  
✅ Make sure you **check the box** `Add Python to PATH` during setup.

**Verify Python:**

```bash
python3 --version
```
or
```bash
python --version
```

---

## Create and Activate a Virtual Environment

(Optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate.bat  # Windows
```

### Install Required Packages

```bash
pip install -r requirements.txt
```

### Running tests

GitHub Actions starts an isolated PostgreSQL 17 service and runs the unit,
database integration, and browser tests. PostgreSQL tests create temporary
schemas and require a test database user with permission to create schemas.
To run them locally, set `TEST_DATABASE_URL` to a disposable PostgreSQL
database, install Chromium with `python -m playwright install chromium`,
and run `python -m pytest tests/unit/ tests/integration/ tests/e2e/`.
When `TEST_DATABASE_URL` is not set, PostgreSQL-specific tests are skipped.
Do not use a production database for tests.

---

# 🐳 5. (Optional) Docker Setup

> Skip if Docker isn't used in this module.

## Install Docker

- [Install Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
- [Install Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)

## Docker Hub

The image repository is [cmp59/module10-is601](https://hub.docker.com/r/cmp59/module10-is601).
After tests and the image security scan pass, GitHub Actions publishes the
image on pushes to `main`. Configure the `DOCKERHUB_USERNAME` and
`DOCKERHUB_TOKEN` repository secrets before deploying.

## Build Docker Image

```bash
docker build -t <image-name> .
```

## Run Docker Container

```bash
docker run -it --rm <image-name>
```

---

# 🚀 6. Running the Project

## PostgreSQL connection

Start Docker Desktop, then from the project directory run:

```bash
docker compose up --build
```

Compose supplies the web service with connection settings for the PostgreSQL
`db` service. Visit `http://localhost:8000/health` to check the connection; it
returns HTTP 503 when the database is unavailable. The calculator routes
do not require a database connection.

The Compose database credentials are development defaults, not production
secrets. `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` can be set
in the environment before starting Compose. Existing PostgreSQL volumes
retain their original credentials and database; changing these variables
does not update an already initialized volume.

When running the app outside Docker, set `DATABASE_URL` to a PostgreSQL URL,
for example `postgresql+psycopg://USER:PASSWORD@localhost:5432/fastapi_db`
(percent-encode URL-special characters in the username and password).
Alternatively, supply `DATABASE_HOST`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
and `POSTGRES_DB` (port 5432). Setting up the connection does not create or
modify any tables.

The SQLAlchemy `User` model is defined in `app/models.py`. Usernames and
emails are unique. The model does not hash passwords or create tables
automatically.

### Migrating a Module 9 database

The Module 9 `users` table has no `password_hash` column. Before using the
model with an existing Module 9 database, back it up, select the intended
database in pgAdmin, and run `sql/06_migrate_users_password_hash.sql` in
the Query Tool. This adds a nullable column without deleting users or
calculations. It is safe to run again. For a fresh database, first create
the Module 9 tables with `sql/01_create_tables.sql`, then run the migration.

Existing users will have a NULL password hash, not a usable password. They
must not be authenticated until a secure password setup process is added.
The database permits NULL so legacy records can be preserved; user creation
requires and hashes passwords for all new users.

`app/schemas.py` defines `UserCreate` and `UserRead`. New-user input requires
a username, valid email, and nonempty password; the username and normalized
email must fit the database column lengths. `UserRead` can serialize existing
SQLAlchemy users without exposing their password hashes. `app/security.py`
provides Argon2 password hashing and verification. A legacy user with no
password hash cannot pass verification.

### Creating a user

After creating and migrating the tables as described above, use
`http://localhost:8000/docs` to call `POST /users` with a username, email,
and password. A successful response has status 201 and includes the user ID,
username, email, and creation time, but no password or hash. Invalid inputs
return 400; duplicate usernames or emails return 409. User registration does
not implement login or password recovery.

- **Without Docker**:

```bash
python main.py
```

(or update this if the main script is different.)

- **With Docker**:

```bash
docker run -it --rm <image-name>
```

---

# 📝 7. Submission Instructions

After finishing your work:

```bash
git add .
git commit -m "Complete Module X"
git push origin main
```

Then submit the GitHub repository link as instructed.

---

# 🔥 Useful Commands Cheat Sheet

| Action                         | Command                                          |
| ------------------------------- | ------------------------------------------------ |
| Install Homebrew (Mac)          | `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` |
| Install Git                     | `brew install git` or Git for Windows installer |
| Configure Git Global Username  | `git config --global user.name "Your Name"`      |
| Configure Git Global Email     | `git config --global user.email "you@example.com"` |
| Clone Repository                | `git clone <repo-url>`                          |
| Create Virtual Environment     | `python3 -m venv venv`                           |
| Activate Virtual Environment   | `source venv/bin/activate` / `venv\Scripts\activate.bat` |
| Install Python Packages        | `pip install -r requirements.txt`               |
| Build Docker Image              | `docker build -t <image-name> .`                |
| Run Docker Container            | `docker run -it --rm <image-name>`               |
| Push Code to GitHub             | `git add . && git commit -m "message" && git push` |

---

# 📋 Notes

- Install **Homebrew** first on Mac.
- Install and configure **Git** and **SSH** before cloning.
- Use **Python 3.11+** and **virtual environments** for Python projects.
- **Docker** is optional depending on the project.

---

# 📎 Quick Links

- [Homebrew](https://brew.sh/)
- [Git Downloads](https://git-scm.com/downloads)
- [Python Downloads](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [GitHub SSH Setup Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
