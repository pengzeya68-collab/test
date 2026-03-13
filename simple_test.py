from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        return jsonify({
            'message': 'Registration successful',
            'user': data
        }), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
