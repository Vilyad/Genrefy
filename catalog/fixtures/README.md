# Фикстуры данных для Genrefy

## Назначение
Фикстуры содержат демонстрационные данные для тестирования проекта без необходимости подключения к Spotify API.

## Файлы
- `demo.json` - основные демо-данные
- `exported_data.json` - автоматический экспорт (создаётся, нет в репозитории)

## Загрузка данных

### Команда загрузки
```bash
# Способ 1: Кастомная команда
python manage.py load_demo

# Способ 2: Стандартная команда Django
python manage.py loaddata demo.json 
```

## Экспорт текущих данных
```bash
python manage.py export_data
```

## Структура демо-данных

### Жанры (5)
1. Electronic - Электронная музыка
2. Rock - Рок-музыка
3. Hip Hop - Хип-хоп и рэп
4. Pop - Поп-музыка
5. Jazz - Джаз

### Артисты (5)
1. Daft Punk (Electronic)
2. The Beatles (Rock)
3. Kendrick Lamar (Hip Hop)
4. Taylor Swift (Pop)
5. Miles David (Jazz)

### Треки (2)
1. Get Lucky - Daft Punk (Electronic)
2. Hey Jude - The Beatles (Rock)

## Аудио-характеристики
Каждый трек содержит примерный audio_features для демонстрации:

| Характеристика   | Get Lucky | Hey Jude | Описание                 |
|------------------|-----------|----------|--------------------------|
| danceability     | 0.766     | 0.545    | Танцевальность (0-1)     |
| energy           | 0.674     | 0.445    | Энергичность (0-1)       |    
| valence          | 0.966     | 0.634    | Позитивность (0-1)       |      
| tempo            | 116.0     | 145.2    | Темп (BPM)               |     
| acousticness     | 0.0102    | 0.565    | Акустичность (0-1)       |    
| instrumentalness | 0.0214    | 0.0012   | Инструментальность (0-1) |

## Workflow разработки

### Для разработчика:
1. Клонируете проект
2. `python manage.py load_demo` - база готова
3. Работаете с данными

### Для продакшена:
1. Используете реальные данные из Spotify API
2. При необходимости: `python manage.py export_data` для бекапа

### Для тестирования:
```bash
# Очистить базу
python manage.py flush

#Загрузить демо
python manage.py load_demo
```

## Важно!
- demo.json - только для разработки
- Реальные данные получаются через Spotify API
- Не коммитить `exported_data.json` (он в .gitignore)