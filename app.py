from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')  # Existing home route

# NEW: create a route for pixelTest
@app.route('/pixelTest')
def pixel_test():
    return render_template('pixelTest.html')

if __name__ == '__main__':
    app.run(debug=True)