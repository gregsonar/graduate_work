import multiprocessing

wsgi_app = 'admin.wsgi:application'

bind = '0.0.0.0:8000'

workers = multiprocessing.cpu_count() * 2 + 1

threads = 2

timeout = 120

reload = False

loglevel = 'info'

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}
