# Re‑Photo Booth

Re‑Photo Booth is an open‑source photobooth platform designed to run on
recycled iPads or tablets installed in repurposed Tritan Hearing kiosks.  It
allows guests to take photos at weddings, events, festivals, conferences and
public spaces.  The application is built with Django and runs entirely on
commodity hardware without relying on third‑party cloud services.

## Features

- **Event branding:** configure logos, backgrounds, overlay frames and colour
  themes per event via the admin interface.
- **Capture flow:** guests select their event, choose a filter and mode
  (single or photo strip), watch a countdown and capture photos using the
  built‑in camera.
- **Client‑side processing:** brightness, contrast and saturation filters are
  applied in the browser.  Multiple photos are combined into a vertical
  strip for “photo strip” mode.
- **QR code delivery:** each photo generates a unique URL and QR code so
  guests can download their images instantly.
- **Email delivery:** optional email collection sends the photo directly to
  the guest with the image attached.
- **Printing:** integration with CUPS allows photos to be printed on a
  configured printer.  Printing can be disabled if no printer is configured.
- **Offline mode:** if the booth loses connectivity the captured image is
  stored in the browser’s local storage and uploaded automatically when
  connectivity returns.
- **Gallery and analytics:** staff can browse captured photos, search by
  email and view basic analytics such as photo counts and top events.

## Installation

1. Clone this repository and install the Python dependencies.  A virtual
   environment is recommended:

   ```sh
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and customise it for your environment.  At a
   minimum you must set `SECRET_KEY` and configure `ALLOWED_HOSTS`.

3. Create the database and run migrations:

   ```sh
   python manage.py migrate
   ```

4. Create a superuser to access the Django admin:

   ```sh
   python manage.py createsuperuser
   ```

5. Run the development server:

   ```sh
   python manage.py runserver
   ```

6. Visit `http://localhost:8000/admin/` to log in and create your first
   Theme, Event and Booth.  Then navigate to the root URL to test the
   photobooth flow.

## Production deployment

For production use it is recommended to run the application with a WSGI
server such as Gunicorn behind a reverse proxy (e.g. Nginx) and to serve
static and media files from a dedicated storage provider.  An example
`docker-compose.yml` file can be added to orchestrate the web server and a
database.  Ensure that the `PHOTOBOOTH_PRINTER` environment variable is set
to the name of your CUPS printer if printing is enabled.

## Running tests

The project includes a minimal test suite.  To run the tests, execute:

```sh
python manage.py test
```

## Contributing

Contributions are welcome!  Please open issues or pull requests to propose
improvements or new features.