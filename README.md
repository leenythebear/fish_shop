# Бот для продажи рыбы в Telegram

## Как установить

1. Скачайте код
2. Для работы скрипта нужен Python версии не ниже 3.7
3. Установите зависимости, указанные в файле ``requirements.txt`` командой:

   ```pip install -r requirements.txt```
5. Создайте бота для работы в Telegram и получите его токен
6. Создайте базу данных в [Redis](https://redis.com/)
7. Создайте аккаунт в [Moltin](https://www.elasticpath.com/) и получите client_id и client_secret
8. Создайте в корне проекта файл ``.env`` и укажите в нем все вышеуказанные данные, по образцу:

```
TG_TOKEN=токен, полученный в п.5
DB_HOST=хост базы данных из п. 6 
DB_PORT=порт базы данных из п. 6 
DB_PASSWORD=пароль к базу данных из п. 6 
CLIENT_ID=client_id из п. 7
CLIENT_SECRET=client_secret из п. 7

```
## Начало работы
Для начала работы необходимо:
1. Создать товары в разделе [Products](https://euwest.cm.elasticpath.com/products)
2. Создать pricebook в разделе [Price Books](https://euwest.cm.elasticpath.com/pricebooks)
3. Опубликовать созданные товары в каталоге в разделе [Catalogs](https://euwest.cm.elasticpath.com/catalogs)

## Как запустить
- Telegram-бот запускается командой:

```python3 bot.py```

Попробовать ботa в действии можно по следующей ссылке:

[Telegram-бот](https://t.me/Want_some_fish_bot)

## Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).

## Автор проекта

Елена Иванова [Leeny_the_bear](https://github.com/leenythebear)

