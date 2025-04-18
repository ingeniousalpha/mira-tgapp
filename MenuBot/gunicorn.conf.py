import multiprocessing

bind = '0.0.0.0:8000'
backlog = 2048
workers = multiprocessing.cpu_count() * 2 + 1
threads = 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2
chdir = '/menubot'
wsgi_app = 'MenuBot.wsgi'
reload = True