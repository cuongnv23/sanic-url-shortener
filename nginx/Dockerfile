FROM nginx:alpine

COPY static /var/www/static
COPY url.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
