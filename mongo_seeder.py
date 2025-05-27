import random
from faker import Faker
from datetime import timedelta
from pymongo import MongoClient

fake = Faker()

NUM_CUSTOMERS = 200
NUM_ROOMS = 200
NUM_BOOKINGS = 200
NUM_PAYMENTS = 200

client = MongoClient("mongodb://mongo:27017/")  
db = client["hotel-booking-platform"]

db.hotel.delete_many({})
db.customer.delete_many({})
db.room.delete_many({})
db.suiteroom.delete_many({})
db.booking.delete_many({})
db.contains.delete_many({})
db.payment.delete_many({})

# Hotel (3 adet)
db.hotel.insert_many([
    {"HotelID": 1, "Name": "Hotel Alpha", "Location": "Vienna", "Rating": 4.5},
    {"HotelID": 2, "Name": "Hotel Beta", "Location": "Salzburg", "Rating": 4.2},
    {"HotelID": 3, "Name": "Hotel Gamma", "Location": "Graz", "Rating": 4.8}
])

# Customer
db.customer.insert_many([{
    "CustomerID": i,
    "Username": fake.unique.user_name(),
    "Password": fake.password(),
    "FirstName": fake.first_name(),
    "LastName": fake.last_name(),
    "Email": fake.unique.email(),
    "PhoneNumber": fake.phone_number()[:20]
} for i in range(1, NUM_CUSTOMERS + 1)])

# Room + SuiteRoom
rooms = []
suiterooms = []
for i in range(1, NUM_ROOMS + 1):
    room_number = f"R{i:03d}"
    rooms.append({
        "RoomNumber": room_number,
        "RoomFloor": random.randint(1, 10),
        "PricePerNight": round(random.uniform(50, 300), 2),
        "MaxGuests": random.randint(1, 4),
        "Status": random.choice(['available', 'occupied', 'maintenance']),
        "HotelID": random.randint(1, 3)
    })
    if random.choice([True, False]):
        suiterooms.append({
            "RoomNumber": room_number,
            "SeparateLivingRoom": bool(random.getrandbits(1)),
            "Jacuzzi": bool(random.getrandbits(1))
        })
db.room.insert_many(rooms)
db.suiteroom.insert_many(suiterooms)

# Booking + Contains
bookings = []
contains = []
for i in range(1, NUM_BOOKINGS + 1):
    checkin = fake.date_between(start_date='-6M', end_date='today')
    checkout = checkin + timedelta(days=random.randint(1, 10))
    bookings.append({
        "BookingID": i,
        "CheckInDate": checkin.isoformat(),
        "CheckOutDate": checkout.isoformat(),
        "TotalPrice": round(random.uniform(200, 2000), 2),
        "CustomerID": random.randint(1, NUM_CUSTOMERS)
    })
    contains.append({
        "BookingID": i,
        "RoomNumber": f"R{random.randint(1, NUM_ROOMS):03d}"
    })
db.booking.insert_many(bookings)
db.contains.insert_many(contains)

# Payment
db.payment.insert_many([{
    "PaymentNumber": i,
    "PaymentMethod": random.choice(['Credit Card', 'PayPal']),
    "PaymentDate": fake.date_between(start_date='-6M', end_date='today').isoformat(),
    "PaymentStatus": random.choice(['pending', 'completed', 'failed']),
    "CardNumber": fake.credit_card_number(),
    "ExpiryDate": fake.date_between(start_date='today', end_date='+3y').isoformat(),
    "CVV": str(random.randint(100, 999)),
    "Amount": round(random.uniform(200, 2000), 2),
    "BookingID": i
} for i in range(1, NUM_PAYMENTS + 1)])

print("✅")
client.close()
