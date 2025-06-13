from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime, date
from decimal import Decimal
import mysql.connector

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

# Clear relevant MongoDB collections
collections = [
    "hotel", "hotelpartnership", "customer", "booking", "contains", "room"
]
for col in collections:
    mongo_db[col].delete_many({})

def fix_types(record):
    for k, v in record.items():
        if isinstance(v, Decimal):
            record[k] = float(v)
        elif isinstance(v, date) and not isinstance(v, datetime):
            record[k] = datetime.combine(v, datetime.min.time())
    return record

# --- Customers
cursor.execute("SELECT * FROM Customer")
customers = cursor.fetchall()
customer_id_map = {}
for cust in customers:
    cleaned = fix_types(cust)
    old_id = cleaned.pop("CustomerID")
    result = mongo_db["customer"].insert_one(cleaned)
    customer_id_map[old_id] = result.inserted_id

# --- Hotels with embedded reviews
cursor.execute("SELECT * FROM Hotel")
hotels = cursor.fetchall()
hotel_id_map = {}
for hotel in hotels:
    hotel_id = hotel["HotelID"]
    hotel_clean = fix_types(hotel)
    hotel_clean.pop("HotelID")

    cursor.execute("SELECT * FROM Review WHERE HotelID = %s", (hotel_id,))
    reviews = cursor.fetchall()
    embedded_reviews = []
    for rev in reviews:
        rev_clean = fix_types(rev)
        rev_clean["CustomerID"] = customer_id_map.get(rev_clean.pop("CustomerID"))
        rev_clean.pop("HotelID", None)
        rev_clean.pop("ReviewNumber", None)
        embedded_reviews.append(rev_clean)

    hotel_clean["reviews"] = embedded_reviews
    result = mongo_db["hotel"].insert_one(hotel_clean)
    hotel_id_map[hotel_id] = result.inserted_id

# --- Rooms: create all rooms first
cursor.execute("SELECT * FROM Room")
all_rooms = cursor.fetchall()
room_id_map = {}
for r in all_rooms:
    cleaned = fix_types(r)
    old_hotel_id = cleaned.pop("HotelID")
    cleaned["HotelID"] = hotel_id_map[old_hotel_id]  # store HotelID as mongo _id
    # RoomNumber is kept as is
    result = mongo_db["room"].insert_one(cleaned)
    key = (old_hotel_id, cleaned["RoomNumber"])
    room_id_map[key] = result.inserted_id

# --- Embed SuiteRoom and DeluxeRoom info inside Room
# Add deluxe info
cursor.execute("SELECT * FROM DeluxeRoom")
for deluxe in cursor.fetchall():
    hotel_id = hotel_id_map[deluxe['HotelID']]
    room_number = deluxe['RoomNumber']
    deluxe_fields = {
        "PrivateBalcony": deluxe['PrivateBalcony'],
        "BonusServices": deluxe['BonusServices']
    }
    mongo_db["room"].update_one(
        {"HotelID": hotel_id, "RoomNumber": room_number},
        {"$set": {"deluxe": deluxe_fields}}
    )

# Add suite info
cursor.execute("SELECT * FROM SuiteRoom")
for suite in cursor.fetchall():
    hotel_id = hotel_id_map[suite['HotelID']]
    room_number = suite['RoomNumber']
    suite_fields = {
        "SeparateLivingRoom": suite['SeparateLivingRoom'],
        "Jacuzzi": suite['Jacuzzi']
    }
    mongo_db["room"].update_one(
        {"HotelID": hotel_id, "RoomNumber": room_number},
        {"$set": {"suite": suite_fields}}
    )

# --- HotelPartnership using MongoDB _id
cursor.execute("SELECT * FROM HotelPartnership")
partners = cursor.fetchall()
for p in partners:
    cleaned = fix_types(p)
    cleaned = {
        "Hotel1": hotel_id_map.get(cleaned["HotelID1"]),
        "Hotel2": hotel_id_map.get(cleaned["HotelID2"])
    }
    mongo_db["hotelpartnership"].insert_one(cleaned)

# --- Bookings with embedded Payments
cursor.execute("SELECT * FROM Booking")
bookings = cursor.fetchall()
booking_id_map = {}
for booking in bookings:
    old_bid = booking["BookingID"]
    booking_clean = fix_types(booking)
    booking_clean["CustomerID"] = customer_id_map.get(booking_clean["CustomerID"])
    
    cursor.execute("SELECT * FROM Payment WHERE BookingID = %s", (old_bid,))
    payments = cursor.fetchall()
    embedded_payments = []
    for pay in payments:
        pay_clean = fix_types(pay)
        pay_clean.pop("BookingID", None)
        pay_clean.pop("PaymentNumber", None)
        pay_clean["CustomerID"] = booking_clean["CustomerID"]
        embedded_payments.append(pay_clean)

    booking_clean["payments"] = embedded_payments
    booking_clean.pop("BookingID", None)
    result = mongo_db["booking"].insert_one(booking_clean)
    booking_id_map[old_bid] = result.inserted_id

# --- Contains mapper: store BookingID, RoomID, HotelID (Mongo _id), RoomNumber
cursor.execute("SELECT * FROM Contains")
contains = cursor.fetchall()
for c in contains:
    cleaned = fix_types(c)
    booking_oid = booking_id_map.get(cleaned["BookingID"])
    hotel_oid = hotel_id_map.get(cleaned["HotelID"])
    room_number = cleaned["RoomNumber"]
    room_oid = room_id_map.get((cleaned["HotelID"], room_number))
    doc = {
        "BookingID": booking_oid,
        "RoomID": room_oid,
        "HotelID": hotel_oid,
        "RoomNumber": room_number
    }
    mongo_db["contains"].insert_one(doc)

# Cleanup
cursor.close()
mariadb.close()
