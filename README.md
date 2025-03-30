# Duty Scheduler

## Description

This Django application allows you to create and manage duty schedules for your team. The system supports three types of duty scheduling based on the chosen duty duration:
All generated assignments are created only for dates up to December 31 of the current year.

## Additional Features

- **REST API:**  
  CRUD operations for duty configurations and individual assignments are available via Django REST Framework.  
  A custom API endpoint allows updating an assignment based on a combination of `config_id` and date.

- **Automatic Recalculation:**  
  A management command automatically recalculates all schedules on January 1 each year, removing outdated assignments and generating new ones for the new calendar year (from January 1 to December 31).

- **CI/CD:**  
  A GitLab CI/CD pipeline is configured with testing and build stages (the deploy stage is currently disabled).

## Requirements

- Python 3.11  
- Django (4.2.2 or later recommended)  
- Django REST Framework  
- Additional packages (e.g. django-filter, if used)  
- Docker and Docker Compose (optional, for containerization)

## Installation and Setup

1. **Clone the repository:**

   ```bash
   git clone <repository_url>
   cd DUTYPROJECT

2. **Create and activate a virtual environment:**
  On Unix/macOS:

    python -m venv env
    source env/bin/activate

  On Windows:

    python -m venv env
    env\Scripts\activate

3. **Install dependencies:**

  pip install -r requirements.txt

4. **Apply migrations:**

  python manage.py makemigrations
  python manage.py migrate

5. **Run the development server:**

    python manage.py runserver

  The application will be available at http://127.0.0.1:8000/.

## API Endpoints

    /api/configs/ — Manage duty configurations.
    /api/assignments/ — Manage individual duty assignments.
    A custom endpoint (/api/assignments/update-by-config-date/) allows updating a specific assignment based on config_id and date.

## CI/CD

The GitLab CI/CD pipeline is defined in the .gitlab-ci.yml file with stages for testing and building the Docker image.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request with your improvements or bug fixes.
