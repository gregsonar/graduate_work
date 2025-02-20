import multiprocessing

wsgi_app = 'main:app'

bind = '0.0.0.0:8000'

workers = multiprocessing.cpu_count() * 2 + 1

worker_class = 'uvicorn.workers.UvicornWorker'

threads = 2

timeout = 120

reload = False

loglevel = 'info'

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}

preload_app = True

max_requests = 1000
max_requests_jitter = 50

graceful_timeout = 30

limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
