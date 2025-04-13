#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify
from search_engine import SearchEngine
import time

app = Flask(__name__)

# Инициализация поисковой системы
search_engine = None

@app.route('/')
def index():
    """Главная страница с формой поиска"""
    return render_template('index.html')

@app.route('/search')
def search():
    """Обработка поискового запроса"""
    # Получаем поисковый запрос из параметров
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search_results.html', query='', results=[], time=0)
    
    # Замеряем время выполнения поиска
    start_time = time.time()
    
    # Выполняем поиск
    results = search_engine.search(query)
    
    # Вычисляем время выполнения
    search_time = time.time() - start_time
    
    # Возвращаем шаблон с результатами поиска
    return render_template('search_results.html', 
                          query=query, 
                          results=results, 
                          time=search_time)

@app.route('/api/search')
def api_search():
    """API для поискового запроса"""
    # Получаем поисковый запрос из параметров
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query is empty'})
    
    # Выполняем поиск
    results = search_engine.search(query)
    
    # Возвращаем результаты в формате JSON
    return jsonify({
        'query': query,
        'results': results
    })

def init_search_engine():
    """Инициализация поисковой системы"""
    global search_engine
    search_engine = SearchEngine()

if __name__ == '__main__':
    print("Инициализация поисковой системы...")
    init_search_engine()
    print("Запуск веб-сервера...")
    app.run(debug=True) 