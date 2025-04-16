from flask import render_template

from app import app


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html', title="Welcome")




if __name__ == '__main__':
    app.run(debug=True)