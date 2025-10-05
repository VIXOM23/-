from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
import tempfile
import os
import subprocess

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

def check_graphviz():
    """Проверяет доступность Graphviz"""
    try:
        result = subprocess.run(
            ['dot', '-V'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            print(f"✓ Graphviz available: {result.stderr.strip()}")
            return True
        else:
            print("✗ Graphviz not working")
            return False
    except Exception as e:
        print(f"✗ Graphviz check failed: {e}")
        return False

# Проверяем Graphviz при старте
graphviz_available = check_graphviz()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    if not graphviz_available:
        return jsonify({
            'error': 'Graphviz not available. Please use Docker deployment.'
        }), 500
    
    try:
        data = request.json
        
        numbers_line1 = data.get('numbers1', '')
        numbers_line2 = data.get('numbers2', '')
        multiplier = data.get('multiplier', 1)
        
        if not numbers_line1 or not numbers_line2:
            return jsonify({'error': 'Обе строки чисел обязательны'}), 400
        
        try:
            numbers1 = list(map(int, numbers_line1.split()))
            numbers2 = list(map(int, numbers_line2.split()))
            multiplier = int(multiplier)
        except ValueError as e:
            return jsonify({'error': f'Ошибка в данных: {str(e)}'}), 400
        
        if len(numbers1) > 10 or len(numbers2) > 10:
            return jsonify({'error': 'Слишком много чисел. Используйте не более 10 чисел в каждой строке.'}), 400
        
        from solve import TreeElem
        
        print("=== GENERATING TREE ===")
        TreeElem.initialize_global_data(numbers1, numbers2, multiplier)
        elem1 = TreeElem(0, 0, prev=None, used=[])
        
        print("=== GENERATING PDF ===")
        pdf_data = elem1.dot.pipe(format='pdf')
        print(f"✓ PDF size: {len(pdf_data)} bytes")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_data)
            tmp_file_path = tmp_file.name
        
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

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)