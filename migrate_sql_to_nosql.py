import mysql.connector
from pymongo import MongoClient
from decimal import Decimal
from bson import ObjectId
from datetime import date, datetime
from bson import ObjectId

# Connect to MariaDB
mariadb = mysql.connector.connect(
    host="mariadb",
    user="user",
    password="upass",
    database="hotelbooking"
)
cursor = mariadb.cursor(dictionary=True)

# Connect to MongoDB
mongo = MongoClient("mongodb://mongo:27017/")
mongo_db = mongo["hotel-booking-platform"]

# List of collections to clear
collections = [
    "hotel", "hotelpartnership", "customer", "room",
    "suiteroom", "deluxeroom", "booking", "contains",
    "payment", "review"
]

# Clear MongoDB collections
for col in collections:
    mongo_db[col].delete_many({})

# Helper: Convert Decimal → float for MongoDB
def fix_types(record):
    for key, value in record.items():
        if isinstance(value, Decimal):
            record[key] = float(value)
        elif isinstance(value, date) and not isinstance(value, datetime):
            # Convert date to datetime (at midnight)
            record[key] = datetime.combine(value, datetime.min.time())
        elif isinstance(value, ObjectId):
            record[key] = str(value)
        elif isinstance(value, bytes):
            record[key] = value.decode("utf-8")
    return record

# Migration helper
def migrate_table(sql_table, mongo_collection):
    cursor.execute(f"SELECT * FROM {sql_table}")
    records = cursor.fetchall()
    if records:
        cleaned = [fix_types(r) for r in records]
        mongo_db[mongo_collection].insert_many(cleaned)

# Migrate Bookings with Embedded Payments
cursor.execute("SELECT * FROM Booking")
bookings = cursor.fetchall()

for booking in bookings:
    # Find all payments for this booking
    cursor.execute("SELECT * FROM Payment WHERE BookingID = %s", (booking['BookingID'],))
    payments = cursor.fetchall()
    # Clean types for MongoDB
    booking_clean = fix_types(booking)
    payments_clean = [fix_types(p) for p in payments]
    booking_clean['payments'] = payments_clean
    mongo_db['booking'].insert_one(booking_clean)

# Migrate other tables as before
migrate_table("Hotel", "hotel")
migrate_table("HotelPartnership", "hotelpartnership")
migrate_table("Customer", "customer")
migrate_table("Room", "room")
migrate_table("SuiteRoom", "suiteroom")
migrate_table("DeluxeRoom", "deluxeroom")
migrate_table("Contains", "contains")
migrate_table("Review", "review")

# Cleanup
cursor.close()
mariadb.close()

print("Data successfully migrated from MariaDB to MongoDB.")
