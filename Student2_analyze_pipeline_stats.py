from pymongo import MongoClient
from datetime import datetime, timedelta

# Connect to MongoDB
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["hotel-booking-platform"]

# Use your actual pipeline (copy-paste from app.py)
from_dt = datetime.today() - timedelta(days=30)
to_dt = datetime.today()

pipeline = [
    {"$match": {"CheckInDate": {"$gte": from_dt, "$lte": to_dt}}},
    {"$lookup": {
        "from": "contains",
        "localField": "_id",
        "foreignField": "BookingID",
        "as": "contains"
    }},
    {"$unwind": "$contains"},
    {"$match": {"contains.HotelID": {"$exists": True}}},
    {"$addFields": {
        "TotalPaid": {"$sum": {
            "$map": {
                "input": "$payments",
                "as": "pay",
                "in": {
                    "$cond": [
                        {"$eq": ["$$pay.PaymentStatus", "completed"]},
                        "$$pay.Amount",
                        0
                    ]
                }
            }
        }}
    }},
    {"$group": {
        "_id": "$contains.HotelID",
        "NumCustomers": {"$addToSet": "$CustomerID"},
        "NumBookings": {"$addToSet": "$_id"},
        "NumRooms": {"$sum": 1},
        "TotalSpent": {"$sum": "$TotalPaid"}
    }},
    {"$addFields": {
        "NumCustomers": {"$size": "$NumCustomers"},
        "NumBookings": {"$size": "$NumBookings"}
    }},
    {"$lookup": {
        "from": "hotel",
        "localField": "_id",
        "foreignField": "_id",
        "as": "hotel"
    }},
    {"$unwind": "$hotel"},
    {"$addFields": {
        "HotelName": "$hotel.Name",
        "AvgBookingValue": {
            "$cond": [
                {"$eq": ["$NumBookings", 0]},
                0,
                {"$divide": ["$TotalSpent", "$NumBookings"]}
            ]
        }
    }},
    {"$project": {
        "_id": 0,
        "HotelName": 1,
        "NumCustomers": 1,
        "NumBookings": 1,
        "NumRooms": 1,
        "TotalSpent": 1,
        "AvgBookingValue": 1
    }},
    {"$sort": {"HotelName": 1}}
]

# Run the aggregation with explain
stats = db.command("explain", {
    "aggregate": "booking",
    "pipeline": pipeline,
    "cursor": {}
})

import pprint; pprint.pprint(stats)
