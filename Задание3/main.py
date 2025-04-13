#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Задание 3: Создание инвертированного индекса и булев поиск
# Суть: 
# 1. Создаем инвертированный индекс из токенов файлов
# 2. Реализуем булев поиск с операторами AND, OR, NOT
# 3. Обрабатываем сложные запросы со скобками

import os
import re
import json
from collections import defaultdict

# Путь к директории с HTML-файлами
DATA_DIR = "../Задание_1/crawler/data/pages"
# Путь к файлу с токенами из Задания 2
TOKENS_FILE = "../Задание2/tokens.txt"
# Путь для сохранения индекса
INDEX_FILE = "inverted_index.json"

# В этом списке будем хранить все наши токены
all_tokens = []

# Инвертированный индекс - словарь, где ключ - токен, значение - список doc_id
inverted_index = defaultdict(list)

# Читаем токены из файла
print("Чтение токенов из файла...")
try:
    with open(TOKENS_FILE, 'r', encoding='utf-8') as file:
        all_tokens = [line.strip() for line in file.readlines()]
    print(f"Прочитано {len(all_tokens)} токенов.")
except FileNotFoundError:
    print(f"Файл {TOKENS_FILE} не найден.")
    all_tokens = []

# Проверяем, что токены были прочитаны
if not all_tokens:
    print("Токены не найдены, будем индексировать файлы напрямую.")
    
    # Проверяем существование директории с данными
    if not os.path.exists(DATA_DIR):
        print(f"Ошибка: директория {DATA_DIR} не существует")
        exit(1)
        
    # Получаем список HTML файлов
    html_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.html')]
    print(f"Найдено {len(html_files)} HTML файлов.")
    
    # Для каждого HTML файла извлекаем токены и создаем индекс
    for filename in html_files:
        doc_id = int(filename.split('_')[1].split('.')[0])  # Извлекаем ID документа из имени файла
        file_path = os.path.join(DATA_DIR, filename)
        
        # Читаем содержимое файла
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', ' ', content)
        
        # Разбиваем на слова, приводим к нижнему регистру
        words = re.findall(r'\b[а-яА-Яa-zA-Z]+\b', text.lower())
        
        # Добавляем токены в индекс
        for word in words:
            if word not in inverted_index[word]:
                inverted_index[word].append(doc_id)
                if word not in all_tokens:
                    all_tokens.append(word)
else:
    # Если токены уже есть, просто строим инвертированный индекс
    # Для каждого HTML файла проверяем наличие токенов
    html_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.html')]
    
    print("Создание инвертированного индекса...")
    for filename in html_files:
        doc_id = int(filename.split('_')[1].split('.')[0])  # Извлекаем ID документа из имени файла
        file_path = os.path.join(DATA_DIR, filename)
        
        # Читаем содержимое файла
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Удаляем HTML теги
        text = re.sub(r'<[^>]+>', ' ', content)
        text = text.lower()
        
        # Проверяем каждый токен
        for token in all_tokens:
            # Если токен есть в тексте, добавляем doc_id в индекс
            if re.search(r'\b' + re.escape(token) + r'\b', text):
                if doc_id not in inverted_index[token]:
                    inverted_index[token].append(doc_id)

# Сортируем doc_id в каждом списке
for token in inverted_index:
    inverted_index[token].sort()

# Сохраняем индекс в JSON файл
print(f"Сохранение индекса в файл {INDEX_FILE}...")
with open(INDEX_FILE, 'w', encoding='utf-8') as file:
    json.dump(inverted_index, file, ensure_ascii=False, indent=2)

print(f"Индекс создан и сохранен. Всего уникальных токенов: {len(inverted_index)}")

# Функции для парсинга и обработки булевых запросов

def tokenize_query(query):
    """Разбивает запрос на токены"""
    tokens = []
    i = 0
    while i < len(query):
        if query[i].isspace():
            i += 1
            continue
        elif query[i:i+3] == 'AND':
            tokens.append('AND')
            i += 3
        elif query[i:i+2] == 'OR':
            tokens.append('OR')
            i += 2
        elif query[i:i+3] == 'NOT':
            tokens.append('NOT')
            i += 3
        elif query[i] == '(':
            tokens.append('(')
            i += 1
        elif query[i] == ')':
            tokens.append(')')
            i += 1
        else:
            # Извлекаем термин
            start = i
            while i < len(query) and not query[i].isspace() and query[i] not in '()' and not query[i:i+3] in ['AND', 'OR', 'NOT']:
                i += 1
            term = query[start:i]
            tokens.append(term.lower())  # Приводим к нижнему регистру для регистронезависимого поиска
    return tokens

def evaluate_query(query, inverted_index, all_doc_ids):
    """Оценивает булев запрос, возвращает список doc_id"""
    tokens = tokenize_query(query)
    return evaluate_expression(tokens, 0, len(tokens), inverted_index, all_doc_ids)[0]

def evaluate_expression(tokens, start, end, inverted_index, all_doc_ids):
    """Рекурсивно оценивает выражение, возвращает (результат, новая_позиция)"""
    if start >= end:
        return [], start
    
    result = []
    i = start
    last_operator = 'OR'  # По умолчанию используем OR
    first_term = True
    next_is_not = False  # Флаг, чтобы обработать случай, когда NOT - первый оператор
    
    while i < end:
        if tokens[i] == '(':
            # Обрабатываем вложенное выражение
            sub_result, i = evaluate_expression(tokens, i + 1, end, inverted_index, all_doc_ids)
            
            # Применяем оператор к текущему результату
            if first_term:
                # Если это первый терм, просто присваиваем результат
                if next_is_not:
                    result = list(set(all_doc_ids) - set(sub_result))
                    next_is_not = False
                else:
                    result = sub_result
                first_term = False
            else:
                if last_operator == 'AND':
                    result = list(set(result) & set(sub_result))
                elif last_operator == 'OR':
                    result = list(set(result) | set(sub_result))
                elif last_operator == 'NOT':
                    result = list(set(result) - set(sub_result))
        elif tokens[i] == ')':
            # Конец вложенного выражения
            return result, i + 1
        elif tokens[i] == 'AND':
            last_operator = 'AND'
            i += 1
        elif tokens[i] == 'OR':
            last_operator = 'OR'
            i += 1
        elif tokens[i] == 'NOT':
            if first_term:
                # Если NOT - первый оператор, запоминаем это
                next_is_not = True
            else:
                last_operator = 'NOT'
            i += 1
        else:
            # Обрабатываем терм
            term = tokens[i]
            term_docs = inverted_index.get(term, [])
            
            # Применяем оператор к текущему результату
            if first_term:
                # Если это первый терм, просто присваиваем результат
                if next_is_not:
                    result = list(set(all_doc_ids) - set(term_docs))
                    next_is_not = False
                else:
                    result = term_docs
                first_term = False
            else:
                if last_operator == 'AND':
                    result = list(set(result) & set(term_docs))
                elif last_operator == 'OR':
                    result = list(set(result) | set(term_docs))
                elif last_operator == 'NOT':
                    # NOT должен работать с result, а не с all_doc_ids
                    result = list(set(result) - set(term_docs))
            
            i += 1
    
    return result, i

def print_search_results(doc_ids):
    """Выводит результаты поиска"""
    if not doc_ids:
        print("Ничего не найдено.")
        return
    
    print(f"Найдено документов: {len(doc_ids)}")
    for doc_id in sorted(doc_ids):
        print(f"Документ: page_{doc_id:03d}.html")

# Получаем список всех doc_id
all_doc_ids = []
for filename in os.listdir(DATA_DIR):
    if filename.endswith('.html'):
        doc_id = int(filename.split('_')[1].split('.')[0])
        all_doc_ids.append(doc_id)

# Цикл для поиска
print("\nБулев поиск (для выхода введите 'q')")
print("Примеры запросов:")
print("  python AND язык")
print("  (python OR html) AND NOT javascript")
print("  python OR (html AND css)")

while True:
    query = input("\nВведите запрос: ")
    if query.lower() == 'q':
        break
    
    try:
        result_doc_ids = evaluate_query(query, inverted_index, all_doc_ids)
        print_search_results(result_doc_ids)
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        print("Пожалуйста, проверьте синтаксис запроса.") 