## Запуск хука с пробросом порта по ssh

На удаленном сервере запущен nginx+letsencrypt с примерно следующим конфигом: 
```text
map $http_upgrade $connection_upgrade {
  default upgrade;
  '' close;
}

upstream port_pass {
    # 8760 порт для проброса
    server 127.0.0.1:8760 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    listen [::]:80;

    server_name $HOST_NAME;
    server_tokens off;

    location /.well-known/acme-challenge/ {
        root /data/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }    
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;

    server_name $HOST_NAME;
    
    ssl_certificate /etc/letsencrypt/live/$HOST_NAME/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$HOST_NAME/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_http_version 1.1;
        proxy_pass http://port_pass;

        # WebSocket
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
}
```

Локально запускаем приложение на 8760 порту или любом другом.
Для запуска SSH с пробросом локального порта 8760->8760

```bash
ssh -R 8760:localhost:8760 -o ServerAliveInterval=60 $SERVER_NAME
```
