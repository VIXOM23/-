from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
import os
import requests

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

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
        response = requests.get(
                'https://quickchart.io/graphviz',
                params={'format': 'pdf', 'graph': str(elem1.dot)},
                timeout=30
            )
        if response.status_code == 200:
            pdf_data =  response.content
        pdf_data = elem1.dot.pipe(format='pdf')

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