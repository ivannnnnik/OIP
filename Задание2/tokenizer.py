#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
from bs4 import BeautifulSoup
from pymystem3 import Mystem
from collections import defaultdict

DATA_DIR = "../Задание_1/crawler/data/pages"
OUTPUT_DIR = "."

TOKEN_PATTERN = re.compile(r'^[а-яА-Яa-zA-Z]+$')
MIN_TOKEN_LENGTH = 3

STOP_WORDS = {
    'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то', 'все', 'она', 'так',
    'его', 'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было',
    'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже', 'ну', 'вдруг',
    'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж',
    'вам', 'ведь', 'там', 'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть',
    'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб', 'без', 'будто', 'чего',
    'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда', 'кто', 'этот', 'того', 'потому', 'этого',
    'какой', 'совсем', 'этом', 'этой', 'этот', 'при', 'об', 'the', 'of', 'and', 'to', 'in', 'a',
    'is', 'that', 'for', 'it', 'as', 'was', 'with', 'be', 'by', 'are', 'this', 'an', 'на', 'то',
    'не', 'как', 'над', 'под', 'от', 'pro', 'по', 'со', 'из',
    'am', 'has', 'have', 'had', 'do', 'does', 'did', 'but', 'if', 'or', 'because', 'as', 'until',
    'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
    'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
    'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
    'will', 'just', 'don', 'should', 'now'
}

def extract_text_from_html(html_content):
    """Извлекает текст из HTML-файла, удаляя теги и JavaScript"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Удаляем все скрипты и стили
    for script in soup(["script", "style"]):
        script.extract()
    
    # Получаем текст
    text = soup.get_text()
    
    # Удаляем лишние пробелы и переносы строк
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def tokenize_text(text):
    """Разбивает текст на отдельные слова (токены)"""
    # Приводим к нижнему регистру и разбиваем на слова
    words = text.lower().split()
    
    # Фильтруем токены
    filtered_tokens = []
    for word in words:
        # Проверяем, что токен содержит только буквы и имеет достаточную длину
        if (TOKEN_PATTERN.match(word) and 
            len(word) >= MIN_TOKEN_LENGTH and 
            word not in STOP_WORDS):
            filtered_tokens.append(word)
    
    # Удаляем дубликаты, сохраняя порядок
    unique_tokens = []
    seen = set()
    for token in filtered_tokens:
        if token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    
    return unique_tokens

def lemmatize_tokens(tokens):
    """Лемматизирует список токенов с помощью Mystem"""
    # Инициализируем лемматизатор
    mystem = Mystem()
    
    # Словарь для хранения лемм и их форм
    lemmas_dict = defaultdict(set)
    
    # Лемматизируем каждый токен
    for token in tokens:
        lemmas = mystem.analyze(token)
        if lemmas and 'analysis' in lemmas[0] and lemmas[0]['analysis']:
            lemma = lemmas[0]['analysis'][0]['lex']
            lemmas_dict[lemma].add(token)
        else:
            # Если не удалось лемматизировать, используем сам токен как лемму
            lemmas_dict[token].add(token)
    
    return lemmas_dict

def process_html_files():
    """Обрабатывает все HTML-файлы в директории"""
    all_tokens = []
    
    # Проверяем существование директории с данными
    if not os.path.exists(DATA_DIR):
        print(f"Ошибка: директория {DATA_DIR} не существует")
        sys.exit(1)
    
    # Обрабатываем все HTML-файлы
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.html'):
            file_path = os.path.join(DATA_DIR, filename)
            
            # Читаем файл
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Извлекаем текст
            text = extract_text_from_html(html_content)
            
            # Токенизируем текст
            tokens = tokenize_text(text)
            
            # Добавляем в общий список
            all_tokens.extend(tokens)
    
    # Удаляем дубликаты
    unique_tokens = []
    seen = set()
    for token in all_tokens:
        if token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    
    # Лемматизируем токены
    lemmas_dict = lemmatize_tokens(unique_tokens)
    
    return unique_tokens, lemmas_dict

def save_tokens(tokens, filename="tokens.txt"):
    """Сохраняет список токенов в файл"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        for token in tokens:
            file.write(f"{token}\n")
    
    print(f"Токены сохранены в файл {file_path}")

def save_lemmas(lemmas_dict, filename="lemmas.txt"):
    """Сохраняет словарь лемм в файл"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    with open(file_path, 'w', encoding='utf-8') as file:
        for lemma, forms in lemmas_dict.items():
            forms_str = ' '.join(forms)
            file.write(f"{lemma}: {forms_str}\n")
    
    print(f"Леммы сохранены в файл {file_path}")

def main():
    """Основная функция программы"""
    print("Начинаем обработку HTML-файлов...")
    
    # Обрабатываем HTML-файлы
    tokens, lemmas_dict = process_html_files()
    
    print(f"Получено {len(tokens)} уникальных токенов")
    print(f"Получено {len(lemmas_dict)} уникальных лемм")
    
    # Сохраняем результаты
    save_tokens(tokens, "tokens.txt")
    save_lemmas(lemmas_dict, "lemmas.txt")
    
    print("Обработка завершена!")

if __name__ == "__main__":
    main() 