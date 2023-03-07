# Photography Backend

Photography Backend is a RESTful API server built using the Django Rest Framework (DRF) and token-based authentication using JSON Web Tokens (JWTs). It provides endpoints for managing users, photos, and categories.

## Features

- User authentication and registration using JWTs
- CRUD endpoints for managing users, photos, and categories
- Pagination and filtering options for endpoints
- Support for media files (uploaded photos)

## Technologies Used

- Django
- Django Rest Framework
- MySQL
- JSON Web Tokens (JWTs)
- uWSGI and Nginx (for production deployment)

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/ECarry/Photography_Backend.git
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Create a MySQL database and update the DATABASES setting in settings.py:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '<your-database-name>',
        'USER': '<your-database-user>',
        'PASSWORD': '<your-database-password>',
        'HOST': '<your-database-host>',
        'PORT': '<your-database-port>',
    }
}
```

4. Run database migrations:

```bash
python manage.py migrate
```

5. Create a superuser account:

```bash
python manage.py createsuperuser
```

6. Start the development server:

```bash
python manage.py runserver
```

7. Access the API at http://localhost:8000/api/.

## API Endpoints

### Authentication

- POST `/api/token/`: obtain a JWT token by providing valid credentials
- POST `/api/token/refresh/`: refresh a JWT token


### Photos
- GET `/api/photos/`: retrieve a list of photos
- POST `/api/photos/`: upload a new photo
- GET `/api/photos/{id}/`: retrieve a single photo by ID
- PUT `/api/photos/{id}/`: update a single photo by ID
- DELETE `/api/photos/{id}/`: delete a single photo by ID

### Categories
- GET `/api/category/`: retrieve a list of categories
- POST `/api/category/`: create a new category
- GET `/api/category/{id}/`: retrieve a single category by ID
- PUT `/api/category/{id}/`: update a single category by ID
- DELETE `/api/category/{id}/`: delete a single category by ID

## Deployment

To deploy the application in a production environment, follow these steps:

1. Install uWSGI and Nginx on your server.
2. Configure Nginx to proxy requests to the uWSGI server.
3. Update the ALLOWED_HOSTS setting in settings.py to include your server's domain name.
4. Collect static files using python manage.py collectstatic.
5. Start the uWSGI server with the following command:
```bash
uwsgi --http :8000 --module <path-to-uwsgi-config-file>
```

## Contributing

Contributions to the project are welcome. If you find a bug or have a feature request, please create an issue on the repository. If you would like to contribute code, please create a pull request and include a detailed description of your changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.