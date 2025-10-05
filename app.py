from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
import os
import requests
import os
import requests
import zipfile
import tarfile
import subprocess
from pathlib import Path

def install_graphviz():
    """Устанавливает Graphviz бинарники в папку проекта"""
    graphviz_path = Path("./graphviz")
    
    if graphviz_path.exists():
        return str(graphviz_path)
    
    # Создаем папку
    graphviz_path.mkdir(exist_ok=True)
    
    # Скачиваем бинарники для Linux (Render использует Ubuntu)
    if os.name == 'posix':
        print("Downloading Graphviz for Linux...")
        
        # Способ 1: Скачать с официального сайта
        graphviz_url = "https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/9.0.0/graphviz-9.0.0.tar.gz"
        
        # Способ 2: Альтернативный источник
        # graphviz_url = "https://www2.graphviz.org/Packages/stable/portable_source/graphviz-9.0.0.tar.gz"
        
        try:
            # Скачиваем
            response = requests.get(graphviz_url, timeout=60)
            tar_path = graphviz_path / "graphviz.tar.gz"
            
            with open(tar_path, 'wb') as f:
                f.write(response.content)
            
            # Распаковываем
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(graphviz_path)
            
            # Находим путь к бинарникам
            extracted_dir = list(graphviz_path.glob("graphviz-*"))[0]
            bin_path = extracted_dir / "bin"
            
            # Добавляем в PATH
            os.environ["PATH"] = str(bin_path) + ":" + os.environ["PATH"]
            
            print(f"Graphviz installed to: {bin_path}")
            return str(bin_path)
            
        except Exception as e:
            print(f"Graphviz installation failed: {e}")
            return None

# Устанавливаем Graphviz при запуске приложения
graphviz_bin_path = install_graphviz()
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

def convert_dot_to_pdf_online(dot_source):
    """Конвертирует DOT source в PDF используя онлайн сервис"""
    try:
        response = requests.get(
            'https://quickchart.io/graphviz',
            params={'format': 'pdf', 'graph': dot_source},
            timeout=30
        )
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"QuickChart error: {response.status_code}")
    except Exception as e:
        raise Exception(f"Online conversion failed: {str(e)}")

# Главная страница - отдаем HTML
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# API endpoint для генерации PDF
@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.json
        
        # Получаем данные из запроса
        numbers_line1 = data.get('numbers1', '')
        numbers_line2 = data.get('numbers2', '')
        multiplier = data.get('multiplier', 1)
        
        # Валидация данных
        if not numbers_line1 or not numbers_line2:
            return jsonify({'error': 'Обе строки чисел обязательны'}), 400
        
        try:
            numbers1 = list(map(int, numbers_line1.split()))
            numbers2 = list(map(int, numbers_line2.split()))
            multiplier = int(multiplier)
        except ValueError as e:
            return jsonify({'error': f'Ошибка в данных: {str(e)}'}), 400
        
        # Проверяем размер входных данных
        if len(numbers1) > 10 or len(numbers2) > 10:
            return jsonify({'error': 'Слишком много чисел. Используйте не более 10 чисел в каждой строке.'}), 400
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from solve import TreeElem
        
        # Использование
        TreeElem.initialize_global_data(numbers1, numbers2, multiplier)

        # Создаем корневой элемент (prev=None для корня)
        elem1 = TreeElem(0, 0, prev=None, used=[])
        
        # Получаем DOT source разными способами
        dot_source = None
        
        # Способ 1: через атрибут source
        if hasattr(elem1.dot, 'source'):
            dot_source = elem1.dot.source
        # Способ 2: через строковое представление
        elif hasattr(elem1.dot, '__str__'):
            dot_source = str(elem1.dot)
        else:
            raise Exception("Cannot extract DOT source from graphviz object")
        
        # Используем онлайн конвертацию вместо локального Graphviz
        pdf_data = convert_dot_to_pdf_online(dot_source)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_data)
            tmp_file_path = tmp_file.name
        
        # Отправляем файл
        return send_file(
            tmp_file_path,
            as_attachment=True,
            download_name='knapsack_tree.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': f'Ошибка генерации дерева: {str(e)}'}), 500

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'message': 'Сервер работает'})

# Отдаем статические файлы (CSS, JS, images)
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)