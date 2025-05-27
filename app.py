from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about-us.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/rooms')
def rooms():
    return render_template('rooms.html')

@app.route('/room-details')
def rooms_details():
    return render_template('room-details.html')

@app.route('/bookings')
def bookings():
    return render_template('bookings.html')

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/blog-details')
def blog_details():
    return render_template('blog-details.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
