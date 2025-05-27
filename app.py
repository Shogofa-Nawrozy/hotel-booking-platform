from flask import Flask, render_template, jsonify
from pymongo import MongoClient
import subprocess



app = Flask(__name__)


client = MongoClient("mongodb://mongo:27017/")
db = client["hotel-booking-platform"]


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



# BACKEND API ROUTES (JSON Endpoints for all collections)

@app.route('/api/hotels')
def api_hotels():
    data = list(db.hotel.find())
    for d in data:
        d['_id'] = str(d['_id'])  # Convert ObjectId to string
    return jsonify(data)

@app.route('/api/customers')
def api_customers():
    data = list(db.customer.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/rooms')
def api_rooms():
    data = list(db.room.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/suiterooms')
def api_suiterooms():
    data = list(db.suiteroom.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/bookings')
def api_bookings():
    data = list(db.booking.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/contains')
def api_contains():
    data = list(db.contains.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

@app.route('/api/payments')
def api_payments():
    data = list(db.payment.find())
    for d in data:
        d['_id'] = str(d['_id'])
    return jsonify(data)

# ROUTE TO TRIGGER MONGODB DATA SEEDING
@app.route('/import-mongo')
def import_mongo():
    """
    Run the mongo_seeder.py script to populate MongoDB with random data.
    Displays success or error message on a simple HTML page.
    """
    try:
        result = subprocess.run(["python", "mongo_seeder.py"], capture_output=True, text=True)
        if result.returncode == 0:
            return render_template("mongo-import.html", message="✅ MongoDB data imported successfully.")
        else:
            return render_template("mongo-import.html", message=f"❌ Error occurred: {result.stderr}")
    except Exception as e:
        return render_template("mongo-import.html", message=f"❌ Exception: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")