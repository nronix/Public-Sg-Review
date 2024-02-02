FROM httpd:2.4.54-alpine

COPY web /usr/local/apache2/htdocs
COPY .httpasswd /usr/local/apache2/conf/.htpasswd
COPY auth.conf /usr/local/apache2/conf/extra/auth_basic.conf
RUN echo "Include conf/extra/auth_basic.conf" >> /usr/local/apache2/conf/httpd.conf
EXPOSE 80