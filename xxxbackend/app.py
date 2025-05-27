from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host='mariadb',
        user='root',
        password='root',
        database='hotelbooking'
    )

@app.route('/')
def home():
    return 'Backend API is running! Try /api/hotels or others.'

@app.route('/api/hotels')
def hotels():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Hotel")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/customers')
def customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Customer")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/rooms')
def rooms():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Room")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/suite-rooms')
def suite_rooms():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM SuiteRoom")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/bookings')
def bookings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Booking")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/contains')
def contains():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Contains")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route('/api/payments')
def payments():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Payment")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
