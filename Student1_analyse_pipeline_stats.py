from pymongo import MongoClient
from datetime import datetime, timedelta

# MongoDB'ye bağlan
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["hotel-booking-platform"]

# Tarih aralığını belirle
from_dt = datetime.today() - timedelta(days=30)
to_dt = datetime.today()

# Pipeline
pipeline = [
    {
        "$lookup": {
            "from": "contains",
            "localField": "_id",  # BookingID
            "foreignField": "BookingID",
            "as": "contains_data"
        }
    },
    {"$unwind": "$contains_data"},

    {
        "$lookup": {
            "from": "room",
            "let": {
                "rn": "$contains_data.RoomNumber",
                "hid": "$contains_data.HotelID"
            },
            "pipeline": [
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                { "$eq": ["$RoomNumber", "$$rn"] },
                                { "$eq": ["$HotelID", "$$hid"] }
                            ]
                        }
                    }
                }
            ],
            "as": "room_data"
        }
    },
    {"$unwind": "$room_data"},

    
    {
        "$addFields": {
            "IsSuite": {
                "$cond": [
                    {"$ifNull": ["$room_data.suite", False]}, 
                    1,
                    0
                ]
            }
        }
    },

    {
        "$addFields": {
            "DurationCategory": {
                "$cond": {
                    "if": {
                        "$gt": [
                            {
                                "$dateDiff": {
                                    "startDate": "$CheckinDate",
                                    "endDate": "$CheckOutDate",
                                    "unit": "day"
                                }
                            },
                            5
                        ]
                    },
                    "then": "More than 5 days",
                    "else": "5 days or less"
                }
            }
        }
    },

    {
        "$group": {
            "_id": "$DurationCategory",
            "TotalBookings": { "$sum": 1 },
            "NumSuiteBookings": {
                "$sum": {
                    "$cond": [{ "$eq": ["$IsSuite", 1] }, 1, 0]
                }
            }
        }
    },

    {
        "$sort": {
            "_id": 1
        }
    }
]

stats = db.command("explain", {
    "aggregate": "booking",
    "pipeline": pipeline,
    "cursor": {}
})

import pprint
pprint.pprint(stats)  
