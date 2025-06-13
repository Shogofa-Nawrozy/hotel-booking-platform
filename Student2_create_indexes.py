from pymongo import MongoClient

# Connect to MongoDB (adjust connection string if needed)
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["hotel-booking-platform"]

# Create indexes
result1 = db.booking.create_index("CheckInDate")
result2 = db.contains.create_index("BookingID")
result3 = db.contains.create_index("HotelID")

print("Indexes created successfully:")
print(result1)
print(result2)
print(result3)
