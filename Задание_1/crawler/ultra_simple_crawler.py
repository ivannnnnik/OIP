#!/usr/bin/env python3
import os
import time
import random
import requests
from typing import List
from bs4 import BeautifulSoup

# Файл со списком URL
urls_file = "config/urls.txt"

# Директория для сохранения страниц
pages_dir = "data/pages"

# Файл индекса
index_file = "data/index.txt"

# Создаем директории, если их нет
os.makedirs(pages_dir, exist_ok=True)
os.makedirs(os.path.dirname(index_file), exist_ok=True)

# Загрузка URL из файла
def load_urls(file_path: str) -> List[str]:
    urls = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith('#'):
                urls.append(url)
    print(f"Загружено {len(urls)} URL из файла {file_path}")
    return urls

# Скачивание страницы
def download_page(url: str) -> str:
    try:
        print(f"Загрузка страницы {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Ошибка при загрузке {url}: статус {response.status_code}")
            return ""
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")
        return ""

# Сохранение страницы в файл
def save_page(content: str, file_id: int) -> str:
    filename = f"page_{file_id:03d}.html"
    file_path = os.path.join(pages_dir, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path

# Основная функция
def main():
    # Загрузка URL
    urls = load_urls(urls_file)
    
    # Создание индексного файла
    with open(index_file, 'w', encoding='utf-8') as index:
        # Скачивание и сохранение страниц
        for i, url in enumerate(urls, 1):
            if i > 100:  # Ограничение на 100 страниц
                break
                
            # Скачивание страницы
            content = download_page(url)
            
            # Если страница не скачалась, пропускаем
            if not content:
                continue
                
            # Сохранение страницы
            file_path = save_page(content, i)
            print(f"Сохранена страница {i}: {url} -> {file_path}")
            
            # Запись в индексный файл
            index.write(f"{i} {url}\n")
            
            # Задержка между запросами
            delay = random.uniform(1.0, 3.0)
            time.sleep(delay)
    
    print("Краулинг завершен")

if __name__ == "__main__":
    main() 