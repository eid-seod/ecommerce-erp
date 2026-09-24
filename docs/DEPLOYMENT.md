# Deployment

Run Gunicorn behind Nginx with HTTPS, a firewall, automatic OS security updates, a dedicated Unix user, and a writable `instance/` directory. Set a long random `SECRET_KEY`, `SESSION_COOKIE_SECURE=1`, and restrict database backups.
