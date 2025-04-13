#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Добавляем родительскую директорию в path для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app

@pytest.fixture
def client():
    """Создание тестового клиента Flask"""
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client

@pytest.fixture
def mock_search_engine():
    """Мок поисковой системы"""
    mock_engine = MagicMock()
    # Устанавливаем результат для метода search
    mock_engine.search.return_value = [
        {
            'id': 1,
            'score': 0.8,
            'title': 'Test Document 1',
            'snippet': 'This is a test snippet 1'
        },
        {
            'id': 2,
            'score': 0.6,
            'title': 'Test Document 2',
            'snippet': 'This is a test snippet 2'
        }
    ]
    
    with patch('app.search_engine', mock_engine):
        yield mock_engine

def test_index_route(client):
    """Тест главной страницы"""
    response = client.get('/')
    assert response.status_code == 200
    # Используем decode для правильной работы с UTF-8 строками
    data = response.data.decode('utf-8')
    assert '<title>Поисковая система</title>' in data
    assert '<form action="/search"' in data

def test_search_route_empty_query(client):
    """Тест страницы поиска с пустым запросом"""
    response = client.get('/search')
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert '<title>Результаты поиска: </title>' in data

def test_search_route_with_query(client, mock_search_engine):
    """Тест страницы поиска с запросом"""
    response = client.get('/search?q=test+query')
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert '<title>Результаты поиска: test query</title>' in data
    assert 'Test Document 1' in data
    assert 'Test Document 2' in data
    
    # Проверяем, что метод search был вызван с правильным аргументом
    mock_search_engine.search.assert_called_once_with('test query')

def test_api_search_route_empty_query(client):
    """Тест API поиска с пустым запросом"""
    response = client.get('/api/search')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'error' in json_data

def test_api_search_route_with_query(client, mock_search_engine):
    """Тест API поиска с запросом"""
    response = client.get('/api/search?q=test+query')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'query' in json_data
    assert json_data['query'] == 'test query'
    assert 'results' in json_data
    assert len(json_data['results']) == 2
    
    # Проверяем, что метод search был вызван с правильным аргументом
    mock_search_engine.search.assert_called_once_with('test query') 