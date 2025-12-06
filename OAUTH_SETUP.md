# OAuth 2.0 Setup Guide

## Проблема: redirect_uri не совпадает

Если вы видите ошибку:
```
Error: invalid_request
Description: The "redirect_uri" parameter does not match...
```

Это значит, что в настройках вашего Whoop приложения не добавлен redirect URI.

## Решение

### Шаг 1: Зайдите в Developer Dashboard

1. Откройте https://developer.whoop.com/
2. Войдите в свой аккаунт
3. Перейдите в "My Applications" или "Developer Dashboard"

### Шаг 2: Настройте приложение

1. Найдите ваше приложение (с Client ID: `8b1dd617-41e6-4e3a-bca3-9a9c072460de`)
2. Нажмите "Edit" или "Settings"
3. Найдите секцию "Redirect URIs" или "OAuth 2.0 Redirect URLs"
4. Добавьте: `http://localhost:8000/callback`
5. Сохраните изменения

### Шаг 3: Запустите авторизацию

После добавления redirect URI:

```bash
uv run python -m whoop_obsidian.auth_helper
```

Это должно:
1. Открыть браузер
2. Попросить вас войти в Whoop
3. Запросить разрешения
4. Перенаправить на localhost:8000
5. Показать ваш access token

## Альтернативный способ (если localhost не работает)

Если у вас проблемы с localhost, вы можете получить токен вручную:

### Вариант 1: Через Whoop Developer Portal

1. Зайдите в https://developer.whoop.com/
2. В разделе вашего приложения найдите "Generate Token" или "Test Token"
3. Скопируйте токен
4. Экспортируйте: `export WHOOP_API_TOKEN="ваш_токен"`

### Вариант 2: Вручную через OAuth Flow

1. Откройте в браузере:
```
https://api.prod.whoop.com/oauth/oauth2/auth?client_id=8b1dd617-41e6-4e3a-bca3-9a9c072460de&response_type=code&redirect_uri=http://localhost:8000/callback&scope=read:recovery+read:cycles+read:sleep+read:workout+read:profile+read:body_measurement
```

2. После авторизации вас перенаправит на URL вида:
```
http://localhost:8000/callback?code=AUTHORIZATION_CODE
```

3. Скопируйте `AUTHORIZATION_CODE` из URL

4. Обменяйте код на токен:
```bash
curl -X POST https://api.prod.whoop.com/oauth/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code=AUTHORIZATION_CODE" \
  -d "client_id=8b1dd617-41e6-4e3a-bca3-9a9c072460de" \
  -d "client_secret=d221daaa4edeede3bab128edf65a5e72816a4c1ed9ab48cda4421127c70fb646" \
  -d "redirect_uri=http://localhost:8000/callback"
```

5. Ответ будет содержать `access_token`:
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "..."
}
```

6. Экспортируйте токен:
```bash
export WHOOP_API_TOKEN="access_token_из_ответа"
```

## Проверка токена

После получения токена проверьте его:

```bash
# Экспортируйте токен
export WHOOP_API_TOKEN="ваш_токен"

# Протестируйте API
uv run python test_api.py
```

Это покажет ваши данные из Whoop API!

## Troubleshooting

### Токен истёк
Токены Whoop обычно действуют 1 час. Используйте refresh_token для получения нового:

```python
from whoop_obsidian.oauth import WhoopOAuth

oauth = WhoopOAuth(client_id, client_secret)
new_token = oauth.refresh_access_token(refresh_token)
```

### Ошибка 401 Unauthorized
- Проверьте что токен правильно экспортирован
- Проверьте что токен не истёк
- Получите новый токен

### Нет данных
- Убедитесь что у вас есть данные в Whoop за последние дни
- Проверьте что вы носите Whoop strap
- Данные могут появляться с задержкой
