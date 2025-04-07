from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('test.html')


@app.route('/update_pixel', methods=['POST'])
def update_pixel():
    data = request.get_json()
    row = data['row']
    col = data['col']
    color = data['color']
    # Here you would add logic to store the pixel data, e.g., in a list or databas
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)