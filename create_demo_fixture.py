import json
import os

fixture_data = [
    {
        "model": "catalog.genre",
        "pk": 1,
        "fields": {
            "name": "Electronic",
            "description": "Электронная музыка",
            "parent": None,
            "spotify_genre_id": "",
        }
    },
    {
        "model": "catalog.genre",
        "pk": 2,
        "fields": {
            "name": "Rock",
            "description": "Рок-музыка",
            "parent": None,
            "spotify_genre_id": "",
        }
    },
    {
        "model": "catalog.genre",
        "pk": 3,
        "fields": {
            "name": "Hip Hop",
            "description": "Хип-хоп и рэп",
            "parent": None,
            "spotify_genre_id": "",
        }
    },
    {
        "model": "catalog.genre",
        "pk": 4,
        "fields": {
            "name": "Pop",
            "description": "Поп-музыка",
            "parent": None,
            "spotify_genre_id": "",
        }
    },
    {
        "model": "catalog.genre",
        "pk": 5,
        "fields": {
            "name": "Jazz",
            "description": "Джаз",
            "parent": None,
            "spotify_genre_id": "",
        }
    },
    {
        "model": "catalog.artist",
        "pk": 1,
        "fields": {
            "name": "Daft Punk",
            "spotify_id": "4tZwfgrHOc3mvqYlEYSvVi",
            "genres": [1],
        }
    },
    {
        "model": "catalog.artist",
        "pk": 2,
        "fields": {
            "name": "The Beatles",
            "spotify_id": "3WrFJ7ztbogyGnTHbHJFl2",
            "genres": [2],
        }
    },
    {
        "model": "catalog.artist",
        "pk": 3,
        "fields": {
            "name": "Kendrick Lamar",
            "spotify_id": "2YZyLoL8N0Wb9xBt1NhZWg",
            "genres": [3],
        }
    },
    {
        "model": "catalog.artist",
        "pk": 4,
        "fields": {
            "name": "Taylor Swift",
            "spotify_id": "06HL4z0CvFAxyc27GXpf02",
            "genres": [4],
        }
    },
    {
        "model": "catalog.artist",
        "pk": 5,
        "fields": {
            "name": "Miles Davis",
            "spotify_id": "0kbYTNQb4Pb1rPbbaF0pT4",
            "genres": [5],
        }
    },
    {
        "model": "catalog.track",
        "pk": 1,
        "fields": {
            'title': 'Get Lucky',
            'artist': 1,
            'spotify_id': '69kOkLUCkxIZYexIgSG8rq',
            "preview_url": "",
            'audio_features': {
                'danceability': 0.766,
                'energy': 0.674,
                'valence': 0.966,
                'tempo': 116.0,
                'acousticness': 0.0102,
                'instrumentalness': 0.0214,
            }
        }
    },
    {
        "model": "catalog.track",
        "pk": 2,
        "fields": {
            'title': 'Hey Jude',
            'artist': 2,
            'spotify_id': '0aym2LBJBk9DAYuHHutrIl',
            "preview_url": "",
            'audio_features': {
                'danceability': 0.766,
                'energy': 0.674,
                'valence': 0.966,
                'tempo': 116.0,
                'acousticness': 0.0102,
                'instrumentalness': 0.0214,
            }
        }
    },
]

os.makedirs('catalog/fixtures', exist_ok=True)

with open('catalog/fixtures/demo.json', 'w', encoding='utf-8') as f:
    json.dump(fixture_data, f, indent=2, ensure_ascii=False)

print("Файл demo.json создан с кодировкой UTF-8")
print("Путь: catalog/fixtures/demo.json")