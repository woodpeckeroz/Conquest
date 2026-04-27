FROM nginx:1.25-alpine

RUN mkdir -p /var/cache/nginx/app_go /var/cache/nginx/app_python

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 81
