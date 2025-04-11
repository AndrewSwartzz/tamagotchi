from flask import render_template

from app import app


@app.route('/')
def home():
    return render_template('home.html')

@app.rout('/pixel_test')
def pixel_test():
    return render_template('pixelTest.html')


if __name__ == '__main__':
    app.run(debug=True)