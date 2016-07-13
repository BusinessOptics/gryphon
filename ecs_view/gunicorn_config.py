import os

reload = (os.environ.get('DEV_MODE', 0) == '1')
user = 'www-data'
bind = '0.0.0.0:3000'
workers = 6
# Requires eventlet >= 0.9.7
worker_class = 'sync'
worker_connections = 1024
# The number of seconds to wait for requests on a Keep-Alive connection.
# Set higher than default to deal with latency.
keepalive = 90
# How max time worker can handle request after got restart signal.
# If the time is up worker will be force killed.
graceful_timeout = 30
# If a worker does not notify the master process in this number of seconds it is
# killed and a new worker is spawned to replace it.
#
# For the non sync workers it just means that the worker  process is still
# communicating and is not tied to the length of time required to handle a single
# request.
timeout = 600
loglevel = 'debug'
log_file = '-'
# "-" means log to stdout
accesslog = '-'
errorlog = '-'
# Sets the process title
proc_name = 'gunicorn'