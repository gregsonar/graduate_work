# AhoyStream

### Запуск бекенда

Из корневой директории проекта выполнить команду:

```
docker compose -f docker-compose.main.yaml up --build
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
Админка нотификаций:
```
http://localhost:8080/admin
```

### Запуск фронтенда

Из директории `front` выполнить команду:

```
npm install
npm run dev
```
