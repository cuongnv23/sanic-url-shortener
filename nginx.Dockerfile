FROM nginx:alpine

COPY app/static /var/www/static
COPY nginx/url.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
