from pymongo import MongoClient

mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["hotel-booking-platform"]

result1 = db.contains.create_index("BookingID")  
result2 = db.room.create_index([("RoomNumber", 1), ("HotelID", 1)])  

print("Indexes created successfully:")
print(result1)
print(result2)
