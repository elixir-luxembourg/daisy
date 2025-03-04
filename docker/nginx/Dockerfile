FROM nginx:alpine
RUN rm /etc/nginx/nginx.conf
COPY server.key /etc/nginx/ssl/private/server.key
COPY server.crt /etc/nginx/ssl/certs/server.crt