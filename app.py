from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
import os
import subprocess
import sys

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

def check_system_graphviz():
    """Проверяет наличие Graphviz в системе"""
    try:
        # Проверяем доступность dot
        result = subprocess.run(['which', 'dot'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            dot_path = result.stdout.strip()
            print(f"✓ Found Graphviz at: {dot_path}")
            
            # Проверяем версию
            version_result = subprocess.run(['dot', '-V'], capture_output=True, text=True, timeout=10)
            if version_result.returncode == 0:
                print(f"✓ Graphviz version: {version_result.stderr.strip()}")
                return True
            else:
                print("✗ Graphviz version check failed")
                return False
        else:
            print("✗ Graphviz not found in PATH")
            return False
            
    except Exception as e:
        print(f"✗ Graphviz check failed: {e}")
        return False

def install_graphviz_system():
    """Пытается установить Graphviz системными пакетами"""
    try:
        print("Attempting to install Graphviz via apt...")
        
        # Обновляем пакеты и устанавливаем graphviz
        commands = [
            ['apt-get', 'update'],
            ['apt-get', 'install', '-y', 'graphviz']
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"Command failed: {' '.join(cmd)}")
                print(f"Error: {result.stderr}")
                return False
        
        print("✓ Graphviz installed via apt")
        return check_system_graphviz()
        
    except Exception as e:
        print(f"✗ System installation failed: {e}")
        return False

# Проверяем и при необходимости устанавливаем Graphviz
print("=== GRAPHVIZ SETUP ===")
graphviz_available = check_system_graphviz()

if not graphviz_available:
    print("Graphviz not available, trying to install...")
    graphviz_available = install_graphviz_system()

print(f"=== GRAPHVIZ READY: {graphviz_available} ===")

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    if not graphviz_available:
        return jsonify({
            'error': 'Graphviz not available on server. Please check server logs.'
        }), 500
    
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
        
        print("=== GENERATING TREE ===")
        TreeElem.initialize_global_data(numbers1, numbers2, multiplier)

        # Создаем корневой элемент
        elem1 = TreeElem(0, 0, prev=None, used=[])
        
        # Генерируем PDF используя локальный Graphviz
        print("=== GENERATING PDF ===")
        pdf_data = elem1.dot.pipe(format='pdf')
        
        print(f"✓ PDF generated successfully, size: {len(pdf_data)} bytes")

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
        print(f"✗ Error: {str(e)}")
        return jsonify({'error': f'Ошибка генерации дерева: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'OK', 
        'message': 'Сервер работает',
        'graphviz_available': graphviz_available
    })

@app.route('/debug-graphviz', methods=['GET'])
def debug_graphviz():
    """Эндпоинт для отладки Graphviz"""
    try:
        # Проверяем доступность dot
        which_result = subprocess.run(['which', 'dot'], capture_output=True, text=True)
        dot_path = which_result.stdout.strip() if which_result.returncode == 0 else "Not found"
        
        # Проверяем версию
        version_result = subprocess.run(['dot', '-V'], capture_output=True, text=True)
        version = version_result.stderr.strip() if version_result.returncode == 0 else "Unknown"
        
        # Проверяем Python graphviz пакет
        try:
            import graphviz
            python_graphviz_version = graphviz.__version__
            python_graphviz_path = graphviz.__file__
        except ImportError:
            python_graphviz_version = "Not installed"
            python_graphviz_path = "N/A"
        
        return jsonify({
            'system': {
                'dot_path': dot_path,
                'version': version,
                'graphviz_available': graphviz_available
            },
            'python': {
                'graphviz_version': python_graphviz_version,
                'graphviz_path': python_graphviz_path
            },
            'environment': {
                'path': os.environ.get('PATH', '')
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)