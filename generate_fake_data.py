import random
from faker import Faker
from datetime import timedelta
import mysql.connector

fake = Faker()

NUM_CUSTOMERS = 200
NUM_ROOMS = 200
NUM_BOOKINGS = 200
NUM_PAYMENTS = 200

conn = mysql.connector.connect(
    host="mariadb",
    user="root",
    password="root",
    database="hotelbooking"
)
cursor = conn.cursor()

print("✅ Veritabanına bağlantı başarılı, veri ekleniyor...")

# Hotel 
hotels = [
    (1, "Hotel Alpha", "Vienna", 4.5),
    (2, "Hotel Beta", "Salzburg", 4.2),
    (3, "Hotel Gamma", "Graz", 4.8)
]
cursor.executemany("INSERT IGNORE INTO Hotel (HotelID, Name, Location, Rating) VALUES (%s, %s, %s, %s)", hotels)

# Customer
for i in range(1, NUM_CUSTOMERS + 1):
    phone = fake.phone_number()[:20]  # Truncate to fit column limit
    cursor.execute(
        "INSERT INTO Customer (CustomerID, Username, Password, FirstName, LastName, Email, PhoneNumber) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (i, fake.unique.user_name(), fake.password(), fake.first_name(), fake.last_name(), fake.unique.email(), phone)
    )

# Room + SuiteRoom
for i in range(1, NUM_ROOMS + 1):
    room_number = f"R{i:03d}"
    cursor.execute(
        "INSERT INTO Room (RoomNumber, RoomFloor, PricePerNight, MaxGuests, Status, HotelID) VALUES (%s, %s, %s, %s, %s, %s)",
        (room_number, random.randint(1, 10), round(random.uniform(50, 300), 2),
         random.randint(1, 4), random.choice(['available', 'occupied', 'maintenance']),
         random.randint(1, 3))
    )
    if random.choice([True, False]):
        cursor.execute(
            "INSERT INTO SuiteRoom (RoomNumber, SeparateLivingRoom, Jacuzzi) VALUES (%s, %s, %s)",
            (room_number, random.randint(0, 1), random.randint(0, 1))
        )

# Booking + Contains
for i in range(1, NUM_BOOKINGS + 1):
    customer_id = random.randint(1, NUM_CUSTOMERS)
    checkin = fake.date_between(start_date='-6M', end_date='today')
    checkout = checkin + timedelta(days=random.randint(1, 10))
    total_price = round(random.uniform(200, 2000), 2)
    cursor.execute(
        "INSERT INTO Booking (BookingID, CheckInDate, CheckOutDate, TotalPrice, CustomerID) VALUES (%s, %s, %s, %s, %s)",
        (i, checkin, checkout, total_price, customer_id)
    )
    cursor.execute(
        "INSERT INTO Contains (BookingID, RoomNumber) VALUES (%s, %s)",
        (i, f"R{random.randint(1, NUM_ROOMS):03d}")
    )

# Payments
for i in range(1, NUM_PAYMENTS + 1):
    cursor.execute(
        "INSERT INTO Payment (PaymentNumber, PaymentMethod, PaymentDate, PaymentStatus, CardNumber, ExpiryDate, CVV, Amount, BookingID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            i,
            random.choice(['Credit Card', 'PayPal']),
            fake.date_between(start_date='-6M', end_date='today'),
            random.choice(['pending', 'completed', 'failed']),
            fake.credit_card_number(),
            fake.date_between(start_date='today', end_date='+3y'),
            str(random.randint(100, 999)),
            round(random.uniform(200, 2000), 2),
            i
        )
    )

conn.commit()
cursor.close()
conn.close()

print("✅")
