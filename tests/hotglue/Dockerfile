# hotglue2 runs on plain PHP. GD reads image sizes, as on hotglue.me: without it, hotglue
# renders photos differently (an <img> without size, instead of the sized <img>/background).
FROM php:8.2-cli
RUN sed -i "s|http://|https://|g" /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y --no-install-recommends libpng-dev libjpeg-dev \
    && docker-php-ext-configure gd --with-jpeg && docker-php-ext-install gd \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
CMD ["php", "-d", "display_errors=0", "-S", "0.0.0.0:8000"]
