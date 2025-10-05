from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import tempfile
import os

app = Flask(__name__)
CORS(app)

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():

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

        # Импортируем здесь, чтобы избежать циклических импортов
        from solve import TreeElem
        # Использование вашего класса
        print(numbers1, numbers2, multiplier)
        TreeElem.initialize_global_data(numbers1, numbers2, multiplier)
        # Создаем корневой элемент
        elem1 = TreeElem(0, 0, prev=None, used=[])
        
        # Генерируем PDF
        pdf_data = elem1.dot.pipe(format='pdf')
        print("Дошли")

        # Создаем временный файл
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


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'message': 'Сервер работает'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)