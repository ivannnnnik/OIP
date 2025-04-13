#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import math
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
from tqdm import tqdm

# Пути к файлам
TOKENS_PATH = "../Задание2/tokens.txt"
LEMMAS_PATH = "../Задание2/lemmas.txt"
PAGES_DIR = "../Задание_1/crawler/data/pages"
INVERTED_INDEX_PATH = "../Задание3/inverted_index.json"
OUTPUT_DIR = "./results"

# Создаем директорию для результатов, если её нет
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_tokens():
    """Чтение списка токенов из файла"""
    with open(TOKENS_PATH, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def read_lemmas():
    """Чтение словаря лемм из файла"""
    lemmas_dict = {}  # словарь вида {word_form: lemma}
    lemma_to_forms = {}  # словарь вида {lemma: [word_forms]}
    
    with open(LEMMAS_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(':')
            if len(parts) != 2:
                continue
                
            lemma = parts[0].strip()
            forms = parts[1].strip().split()
            
            lemma_to_forms[lemma] = forms
            
            # Добавляем саму лемму как форму
            lemmas_dict[lemma] = lemma
            
            # Каждой форме соответствует лемма
            for form in forms:
                lemmas_dict[form] = lemma
    
    return lemmas_dict, lemma_to_forms

def read_inverted_index():
    """Чтение инвертированного индекса из файла"""
    with open(INVERTED_INDEX_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_page_files():
    """Получение списка файлов страниц"""
    return [f for f in os.listdir(PAGES_DIR) if f.endswith('.html')]

def extract_text_from_html(file_path):
    """Извлечение текста из HTML-файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.extract()
            
        # Получаем текст
        text = soup.get_text(separator=' ')
        
        # Чистка текста
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        print(f"Ошибка при чтении {file_path}: {e}")
        return ""

def calculate_tf(term, text_tokens):
    """Расчет TF для термина"""
    term_count = text_tokens.count(term)
    return term_count / len(text_tokens) if len(text_tokens) > 0 else 0

def calculate_idf(term, total_docs, term_docs):
    """Расчет IDF для термина"""
    # Если термин не встречается ни в одном документе, возвращаем 0
    if term not in term_docs or term_docs[term] == 0:
        return 0
    return math.log10(total_docs / term_docs[term])

def process_documents():
    """Обработка документов и подсчет TF-IDF"""
    print("Чтение данных...")
    tokens = read_tokens()
    lemmas_dict, lemma_to_forms = read_lemmas()
    inverted_index = read_inverted_index()
    page_files = get_page_files()
    
    # Считаем количество документов, в которых встречается каждый термин
    token_docs = defaultdict(int)
    lemma_docs = defaultdict(int)
    
    # Для каждого токена из inverted_index считаем количество документов
    for token, doc_ids in inverted_index.items():
        token_docs[token] = len(doc_ids)
        
        # Если токен есть в словаре лемм, увеличиваем счетчик для соответствующей леммы
        if token in lemmas_dict:
            lemma = lemmas_dict[token]
            lemma_docs[lemma] += 1
    
    # Общее количество документов
    total_docs = len(page_files)
    
    print(f"Обработка {total_docs} документов...")
    
    # Обработка каждого документа
    for page_file in tqdm(page_files):
        file_path = os.path.join(PAGES_DIR, page_file)
        page_id = int(page_file.split('_')[1].split('.')[0])  # Извлекаем ID страницы
        
        # Извлекаем текст из HTML
        text = extract_text_from_html(file_path)
        
        # Токенизация текста (простой подход - разбиение по пробелам)
        text_tokens = text.lower().split()
        
        # Подсчитываем частоту каждого токена в документе
        token_counts = Counter(text_tokens)
        total_tokens = len(text_tokens)
        
        # Счетчики для лемматизированных форм
        lemma_counts = defaultdict(int)
        
        # Заполняем счетчики лемм
        for token, count in token_counts.items():
            if token in lemmas_dict:
                lemma = lemmas_dict[token]
                lemma_counts[lemma] += count
        
        # Результаты TF-IDF для токенов
        token_results = []
        
        # Вычисляем TF-IDF для каждого токена из списка
        for token in tokens:
            if token in token_counts:
                tf = token_counts[token] / total_tokens
                idf = calculate_idf(token, total_docs, token_docs)
                tf_idf = tf * idf
                token_results.append((token, idf, tf_idf))
        
        # Результаты TF-IDF для лемм
        lemma_results = []
        
        # Вычисляем TF-IDF для каждой леммы
        for lemma in lemma_to_forms:
            if lemma in lemma_counts:
                tf = lemma_counts[lemma] / total_tokens
                idf = calculate_idf(lemma, total_docs, lemma_docs)
                tf_idf = tf * idf
                lemma_results.append((lemma, idf, tf_idf))
        
        # Сортируем результаты по убыванию tf-idf
        token_results.sort(key=lambda x: x[2], reverse=True)
        lemma_results.sort(key=lambda x: x[2], reverse=True)
        
        # Сохраняем результаты в файлы
        with open(os.path.join(OUTPUT_DIR, f"tokens_tf_idf_{page_id}.txt"), 'w', encoding='utf-8') as f:
            for token, idf, tf_idf in token_results:
                f.write(f"{token} {idf:.6f} {tf_idf:.6f}\n")
        
        with open(os.path.join(OUTPUT_DIR, f"lemmas_tf_idf_{page_id}.txt"), 'w', encoding='utf-8') as f:
            for lemma, idf, tf_idf in lemma_results:
                f.write(f"{lemma} {idf:.6f} {tf_idf:.6f}\n")
    
    print("Обработка завершена.")
    print(f"Результаты сохранены в директории: {OUTPUT_DIR}")

if __name__ == "__main__":
    process_documents() 