#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import math
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Any
import numpy as np
from bs4 import BeautifulSoup

class SearchEngine:
    """
    Векторная поисковая система на основе TF-IDF
    """
    def __init__(self, 
                 index_path: str = '../Задание3/inverted_index.json',
                 tokens_path: str = '../Задание2/tokens.txt',
                 lemmas_path: str = '../Задание2/lemmas.txt',
                 pages_dir: str = '../Задание_1/crawler/data/pages',
                 tf_idf_dir: str = '../Задание4/results'):
        """
        Инициализация поисковой системы
        
        :param index_path: путь к инвертированному индексу
        :param tokens_path: путь к файлу с токенами
        :param lemmas_path: путь к файлу с леммами
        :param pages_dir: директория с HTML-страницами
        :param tf_idf_dir: директория с TF-IDF метриками
        """
        self.index_path = index_path
        self.tokens_path = tokens_path
        self.lemmas_path = lemmas_path
        self.pages_dir = pages_dir
        self.tf_idf_dir = tf_idf_dir
        
        # Загрузка данных
        print("Загрузка данных...")
        self.inverted_index = self._load_inverted_index()
        self.tokens = self._load_tokens()
        self.lemmas_dict, self.lemma_to_forms = self._load_lemmas()
        self.page_files = self._get_page_files()
        self.documents_count = len(self.page_files)
        
        # Загрузка TF-IDF значений для документов
        self.documents_tf_idf = self._load_documents_tf_idf()
        
        # Словарь для быстрого доступа к документам по ID
        self.document_id_to_path = {
            int(f.split('_')[1].split('.')[0]): os.path.join(self.pages_dir, f)
            for f in self.page_files
        }
        
        print(f"Загружено {self.documents_count} документов")
        print(f"Загружено {len(self.tokens)} токенов")
        print(f"Загружено {len(self.lemmas_dict)} лемматизированных форм")
    
    def _load_inverted_index(self) -> Dict[str, List[int]]:
        """Загрузка инвертированного индекса из JSON файла"""
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке инвертированного индекса: {e}")
            return {}
    
    def _load_tokens(self) -> List[str]:
        """Загрузка списка токенов из файла"""
        try:
            with open(self.tokens_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Ошибка при загрузке токенов: {e}")
            return []
    
    def _load_lemmas(self) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
        """Загрузка словаря лемм и их форм"""
        lemmas_dict = {}  # словарь вида {word_form: lemma}
        lemma_to_forms = {}  # словарь вида {lemma: [word_forms]}
        
        try:
            with open(self.lemmas_path, 'r', encoding='utf-8') as f:
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
        except Exception as e:
            print(f"Ошибка при загрузке лемм: {e}")
        
        return lemmas_dict, lemma_to_forms
    
    def _get_page_files(self) -> List[str]:
        """Получение списка файлов страниц"""
        try:
            return [f for f in os.listdir(self.pages_dir) if f.endswith('.html')]
        except Exception as e:
            print(f"Ошибка при получении списка файлов: {e}")
            return []
    
    def _load_documents_tf_idf(self) -> Dict[int, Dict[str, float]]:
        """Загрузка TF-IDF значений для документов"""
        documents_tf_idf = {}
        
        # Проверяем, существует ли директория с TF-IDF
        if not os.path.exists(self.tf_idf_dir):
            print(f"Директория с TF-IDF не найдена: {self.tf_idf_dir}")
            return documents_tf_idf
        
        # Получаем список файлов с TF-IDF для токенов
        tf_idf_files = [f for f in os.listdir(self.tf_idf_dir) if f.startswith('tokens_tf_idf_')]
        
        for file_name in tf_idf_files:
            # Извлекаем ID документа из имени файла
            doc_id = int(file_name.split('_')[-1].split('.')[0])
            documents_tf_idf[doc_id] = {}
            
            # Загружаем TF-IDF значения для токенов
            file_path = os.path.join(self.tf_idf_dir, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            token = parts[0]
                            tf_idf = float(parts[2])
                            documents_tf_idf[doc_id][token] = tf_idf
            except Exception as e:
                print(f"Ошибка при загрузке TF-IDF для документа {doc_id}: {e}")
        
        return documents_tf_idf
    
    def extract_text_from_html(self, file_path: str) -> str:
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
    
    def get_document_snippet(self, doc_id: int, query_terms: List[str], 
                             max_snippet_length: int = 200) -> str:
        """
        Получение фрагмента документа с выделенными терминами запроса
        
        :param doc_id: ID документа
        :param query_terms: термины запроса
        :param max_snippet_length: максимальная длина фрагмента
        :return: фрагмент документа с выделенными терминами
        """
        if doc_id not in self.document_id_to_path:
            return ""
        
        # Получаем текст документа
        file_path = self.document_id_to_path[doc_id]
        text = self.extract_text_from_html(file_path)
        
        # Находим первое вхождение любого из терминов запроса
        best_pos = -1
        
        for term in query_terms:
            term_lower = term.lower()
            pos = text.lower().find(term_lower)
            if pos != -1 and (best_pos == -1 or pos < best_pos):
                best_pos = pos
        
        # Если ни один термин не найден, берем начало документа
        if best_pos == -1:
            start_pos = 0
        else:
            # Ищем начало предложения или параграфа
            start_pos = max(0, best_pos - 50)
            while start_pos > 0 and text[start_pos] not in '.!?\n':
                start_pos -= 1
            if start_pos > 0:
                start_pos += 1
        
        # Определяем конец фрагмента
        end_pos = min(len(text), start_pos + max_snippet_length)
        
        # Обрезаем до конца предложения, если возможно
        if end_pos < len(text):
            next_sentence_end = text.find('.', end_pos)
            if next_sentence_end != -1 and next_sentence_end - end_pos < 30:
                end_pos = next_sentence_end + 1
        
        # Получаем фрагмент текста
        snippet = text[start_pos:end_pos].strip()
        
        # Добавляем многоточие, если фрагмент не с начала текста
        if start_pos > 0:
            snippet = "..." + snippet
        
        # Добавляем многоточие, если фрагмент не до конца текста
        if end_pos < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    def get_document_title(self, doc_id: int) -> str:
        """
        Получение заголовка документа
        
        :param doc_id: ID документа
        :return: заголовок документа
        """
        if doc_id not in self.document_id_to_path:
            return f"Документ {doc_id}"
        
        # Получаем текст документа
        file_path = self.document_id_to_path[doc_id]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Пытаемся найти заголовок
            title = soup.title
            if title and title.string:
                return title.string.strip()
            
            # Если заголовок не найден, ищем первый h1
            h1 = soup.find('h1')
            if h1 and h1.get_text():
                return h1.get_text().strip()
            
            # Если ничего не найдено, возвращаем имя файла
            return f"Документ {doc_id}"
        except Exception as e:
            print(f"Ошибка при чтении заголовка {file_path}: {e}")
            return f"Документ {doc_id}"
    
    def tokenize_query(self, query: str) -> List[str]:
        """
        Токенизация запроса
        
        :param query: текст запроса
        :return: список токенов
        """
        # Преобразуем в нижний регистр и разбиваем на слова
        return [word.lower() for word in re.findall(r'\b\w+\b', query.lower())]
    
    def lemmatize_query(self, query_tokens: List[str]) -> List[str]:
        """
        Лемматизация токенов запроса
        
        :param query_tokens: токены запроса
        :return: лемматизированные токены
        """
        lemmatized_tokens = []
        
        for token in query_tokens:
            # Если токен есть в словаре лемм, используем лемму
            if token in self.lemmas_dict:
                lemmatized_tokens.append(self.lemmas_dict[token])
            else:
                lemmatized_tokens.append(token)
        
        return lemmatized_tokens
    
    def compute_query_vector(self, query_tokens: List[str]) -> Dict[str, float]:
        """
        Вычисление вектора запроса
        
        :param query_tokens: токены запроса
        :return: вектор запроса в виде {токен: вес}
        """
        # Считаем частоту каждого токена в запросе
        token_counts = Counter(query_tokens)
        
        # Нормализуем веса
        query_length = sum(token_counts.values())
        
        if query_length == 0:
            return {}
        
        # Вычисляем TF для каждого токена (TF = частота / общее количество)
        query_vector = {}
        
        for token, count in token_counts.items():
            tf = count / query_length
            
            # Если токен есть в инвертированном индексе, учитываем его IDF
            if token in self.inverted_index:
                idf = math.log10(self.documents_count / len(self.inverted_index[token]))
                query_vector[token] = tf * idf
            else:
                # Если токена нет в индексе, даем ему небольшой вес
                query_vector[token] = tf * 0.1
        
        # Нормализуем вектор запроса
        vector_length = math.sqrt(sum(w * w for w in query_vector.values()))
        
        if vector_length > 0:
            for token in query_vector:
                query_vector[token] /= vector_length
        
        return query_vector
    
    def compute_cosine_similarity(self, query_vector: Dict[str, float], doc_id: int) -> float:
        """
        Вычисление косинусного сходства между вектором запроса и документа
        
        :param query_vector: вектор запроса
        :param doc_id: ID документа
        :return: косинусное сходство
        """
        if doc_id not in self.documents_tf_idf:
            return 0.0
        
        doc_vector = self.documents_tf_idf[doc_id]
        
        # Вычисляем скалярное произведение векторов
        dot_product = sum(query_vector.get(token, 0) * doc_vector.get(token, 0) 
                          for token in query_vector)
        
        # Длина вектора документа
        doc_length = math.sqrt(sum(w * w for w in doc_vector.values()))
        
        # Длина вектора запроса (должна быть 1, так как мы уже нормализовали)
        # query_length = math.sqrt(sum(w * w for w in query_vector.values()))
        
        # Косинусное сходство = скалярное произведение / (длина вектора запроса * длина вектора документа)
        if doc_length > 0:
            return dot_product / doc_length
        
        return 0.0
    
    def search(self, query: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Поиск документов по запросу
        
        :param query: текст запроса
        :param top_n: количество возвращаемых результатов
        :return: список найденных документов с метаданными
        """
        if not query.strip():
            return []
        
        # Токенизация запроса
        query_tokens = self.tokenize_query(query)
        
        if not query_tokens:
            return []
        
        # Лемматизация запроса
        lemmatized_tokens = self.lemmatize_query(query_tokens)
        
        # Вычисление вектора запроса
        query_vector = self.compute_query_vector(lemmatized_tokens)
        
        if not query_vector:
            return []
        
        # Вычисление косинусного сходства для всех документов
        document_scores = []
        
        for doc_id in self.documents_tf_idf:
            similarity = self.compute_cosine_similarity(query_vector, doc_id)
            
            if similarity > 0:
                document_scores.append({
                    'id': doc_id,
                    'score': similarity,
                    'title': self.get_document_title(doc_id),
                    'snippet': self.get_document_snippet(doc_id, query_tokens)
                })
        
        # Сортировка результатов по релевантности (убыванию косинусного сходства)
        document_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Возвращаем top_n результатов
        return document_scores[:top_n] 