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

# Map MariaDB BookingID to MongoDB _id for reference in Contains
booking_id_map = {}

for booking in bookings:
    original_booking_id = booking['BookingID']  # Save before cleaning
    cursor.execute("SELECT * FROM Payment WHERE BookingID = %s", (original_booking_id,))
    payments = cursor.fetchall()
    booking_clean = fix_types(booking)
    payments_clean = []
    for p in payments:
        p_clean = fix_types(p)
        p_clean.pop('BookingID', None)  # Remove BookingID from payment
        payments_clean.append(p_clean)
    booking_clean['payments'] = payments_clean
    booking_clean.pop('BookingID', None)
    result = mongo_db['booking'].insert_one(booking_clean)
    booking_id_map[original_booking_id] = result.inserted_id  # Use saved value

# Migrate Contains, referencing booking _id
cursor.execute("SELECT * FROM Contains")
contains_records = cursor.fetchall()
contains_cleaned = []
for c in contains_records:
    c_clean = fix_types(c)
    # Replace BookingID with MongoDB _id
    c_clean['BookingID'] = booking_id_map.get(c['BookingID'])
    contains_cleaned.append(c_clean)
if contains_cleaned:
    mongo_db['contains'].insert_many(contains_cleaned)

# Migrate other tables as before (no change needed)
migrate_table("Hotel", "hotel")
migrate_table("HotelPartnership", "hotelpartnership")
migrate_table("Customer", "customer")
migrate_table("Room", "room")
migrate_table("SuiteRoom", "suiteroom")
migrate_table("DeluxeRoom", "deluxeroom")
migrate_table("Review", "review")

# Cleanup
cursor.close()
mariadb.close()

# Run this in a Python shell or script with your MongoDB connection
for booking in mongo_db.booking.find():
    payments = booking.get("payments", [])
    changed = False
    for p in payments:
        if "BookingID" in p:
            p.pop("BookingID")
            changed = True
    if changed:
        mongo_db.booking.update_one({"_id": booking["_id"]}, {"$set": {"payments": payments}})

print("Data successfully migrated from MariaDB to MongoDB.")
