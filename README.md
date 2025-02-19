# AhoyStream

### Запуск бекенда

Из корневой директории проекта выполнить команду:

```
docker compose -f docker-compose.main.yaml up subscriptions_api --build
```

### Swagger адреса: 

Подписки:
```url
http://localhost/api/subscriptions/api/openapi
```
Auth: 
```
http://localhost/api/openapi
```

### Запуск фронтенда

Из директории `front` выполнить команду:

```
npm install
npm run dev
```
