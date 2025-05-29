import mysql.connector
from pymongo import MongoClient

# Connect to MariaDB
mariadb = mysql.connector.connect(
    host="mariadb",
    user="your_user",
    password="your_password",
    database="hotel"
)
cursor = mariadb.cursor(dictionary=True)

# Connect to MongoDB
mongo = MongoClient("mongodb://mongo:27017/")
mongo_db = mongo["hotel-booking-platform"]

# Clear all collections
mongo_db.hotel.delete_many({})
mongo_db.customer.delete_many({})
mongo_db.room.delete_many({})
mongo_db.booking.delete_many({})
# etc...

# Example: Migrate customers
cursor.execute("SELECT * FROM customer")
customers = cursor.fetchall()
mongo_db.customer.insert_many(customers)

# Migrate more tables similarly...
cursor.execute("SELECT * FROM hotel")
mongo_db.hotel.insert_many(cursor.fetchall())

cursor.close()
mariadb.close()
