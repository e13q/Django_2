#!/bin/bash
set -e
VENV_DIR="venv"
echo "Проверка наличия обновлений..."
git fetch
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})
BASE=$(git merge-base @ @{u})
if [ $LOCAL = $REMOTE ]; then
    echo "Нет новых обновлений в репозитории. Завершение скрипта."
    exit 0
fi
if [ $LOCAL = $BASE ]; then
    echo "Нужно обновить репозиторий."
else
    echo "Нужно слить изменения."
    exit 1
fi
echo "Обновление кода репозитория..."
git pull
COMMIT_HASH=$(git rev-parse HEAD)
echo "Хэш коммита: $COMMIT_HASH"
echo "Пересборка фронтенда..."
docker-compose run --rm frontend
echo "Пересборка статики Django..."
docker-compose run --rm backend python manage.py collectstatic --noinput
echo "Накат миграций..."
docker-compose run --rm backend python manage.py migrate
echo "Отправка уведомления в Rollbar..."
ROLLBAR_TOKEN=$(grep 'ROLLBAR_TOKEN' .env | cut -d '=' -f2)
export ROLLBAR_TOKEN
docker-compose up -d
curl https://api.rollbar.com/api/1/deploy/ \
    -F access_token="$ROLLBAR_TOKEN" \
    -F environment="production" \
    -F revision="$COMMIT_HASH" \
unset ROLLBAR_TOKEN
echo "Деплой успешно завершен!"