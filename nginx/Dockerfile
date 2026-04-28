FROM nginx:1.25-alpine

RUN mkdir -p /var/cache/nginx/app_go /var/cache/nginx/app_python && \
    chown -R nginx:nginx /var/cache/nginx /var/run

COPY nginx.conf /etc/nginx/conf.d/default.conf

USER nginx
EXPOSE 80 81
