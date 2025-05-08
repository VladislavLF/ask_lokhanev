accesslog = './gunicorn/logs/access.log'
port = 8000
workers = 2

bind = f'127.0.0.1:{port}'
wsgi_app = 'ask_lokhanev.wsgi'

backlog = 100
worker_connections = 500
max_requests = 50
timeout = 60