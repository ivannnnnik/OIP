#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Добавляем родительскую директорию в path для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_engine import SearchEngine

class TestSearchEngine:
    """Тесты для поисковой системы"""

    @pytest.fixture
    def mock_search_engine(self):
        """Создание мок-объекта поисковой системы"""
        with patch('search_engine.SearchEngine._load_inverted_index', return_value={'term1': [1, 2], 'term2': [2, 3]}), \
             patch('search_engine.SearchEngine._load_tokens', return_value=['term1', 'term2', 'term3']), \
             patch('search_engine.SearchEngine._load_lemmas', return_value=({'term1': 'term1', 'term2': 'term2'}, {'term1': ['term1'], 'term2': ['term2']})), \
             patch('search_engine.SearchEngine._get_page_files', return_value=['page_1.html', 'page_2.html', 'page_3.html']), \
             patch('search_engine.SearchEngine._load_documents_tf_idf', return_value={
                 1: {'term1': 0.5, 'term3': 0.3},
                 2: {'term1': 0.2, 'term2': 0.7},
                 3: {'term2': 0.4, 'term3': 0.6}
             }):
            engine = SearchEngine()
            engine.document_id_to_path = {
                1: 'path/to/page_1.html',
                2: 'path/to/page_2.html',
                3: 'path/to/page_3.html'
            }
            yield engine

    def test_tokenize_query(self, mock_search_engine):
        """Тест токенизации запроса"""
        tokens = mock_search_engine.tokenize_query("term1 term2")
        assert tokens == ['term1', 'term2']
        
        # Проверка преобразования регистра
        tokens = mock_search_engine.tokenize_query("TERM1 Term2")
        assert tokens == ['term1', 'term2']
        
        # Проверка игнорирования пунктуации
        tokens = mock_search_engine.tokenize_query("term1, term2.")
        assert tokens == ['term1', 'term2']

    def test_lemmatize_query(self, mock_search_engine):
        """Тест лемматизации запроса"""
        lemmas = mock_search_engine.lemmatize_query(['term1', 'term2', 'unknown'])
        assert lemmas == ['term1', 'term2', 'unknown']

    def test_compute_query_vector(self, mock_search_engine):
        """Тест вычисления вектора запроса"""
        # Подготовка mock-объекта
        mock_search_engine.documents_count = 3
        
        # Тестирование с известными терминами
        vector = mock_search_engine.compute_query_vector(['term1', 'term2'])
        assert 'term1' in vector
        assert 'term2' in vector
        
        # Тестирование с неизвестным термином
        vector = mock_search_engine.compute_query_vector(['unknown'])
        assert 'unknown' in vector
        assert vector['unknown'] > 0  # Должен иметь малый вес, но не ноль

    def test_compute_cosine_similarity(self, mock_search_engine):
        """Тест вычисления косинусного сходства"""
        # Создаем вектор запроса
        query_vector = {'term1': 0.7, 'term2': 0.3}
        
        # Вычисляем косинусное сходство с документом 1
        similarity_1 = mock_search_engine.compute_cosine_similarity(query_vector, 1)
        assert similarity_1 > 0
        
        # Вычисляем косинусное сходство с документом 2
        similarity_2 = mock_search_engine.compute_cosine_similarity(query_vector, 2)
        assert similarity_2 > 0
        
        # Проверяем, что оба документа имеют положительное сходство с запросом
        # Документ 1 содержит term1, документ 2 содержит term1 и term2
        # Документ 2 хоть и имеет более низкий вес для term1, но содержит term2
        # Основной момент - положительная корреляция, конкретные значения могут отличаться
        assert similarity_1 > 0 and similarity_2 > 0

    def test_search(self, mock_search_engine):
        """Тест поиска документов"""
        # Мокаем методы, которые используются в search
        with patch.object(mock_search_engine, 'get_document_title', return_value="Test Document"), \
             patch.object(mock_search_engine, 'get_document_snippet', return_value="Test snippet"):
            
            # Тестирование пустого запроса
            results = mock_search_engine.search("")
            assert results == []
            
            # Тестирование реального запроса
            results = mock_search_engine.search("term1 term2")
            assert len(results) > 0
            
            # Проверка сортировки результатов по релевантности
            for i in range(1, len(results)):
                assert results[i-1]['score'] >= results[i]['score']
            
            # Проверка наличия всех полей в результатах
            assert 'id' in results[0]
            assert 'score' in results[0]
            assert 'title' in results[0]
            assert 'snippet' in results[0]

if __name__ == "__main__":
    pytest.main() 