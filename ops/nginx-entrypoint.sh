#!/bin/sh
set -eu
# Only substitute API_TOKEN: $host/$uri/$api_backend are Nginx runtime variables.
envsubst '${API_TOKEN}' < /etc/nginx/nginx.conf.template > /tmp/nginx.conf
nginx -t -c /tmp/nginx.conf
exec nginx -c /tmp/nginx.conf -g 'daemon off;'
