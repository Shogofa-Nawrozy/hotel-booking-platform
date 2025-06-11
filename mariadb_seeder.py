from faker import Faker
import mysql.connector
from datetime import timedelta
import random

fake = Faker()

NUM_CUSTOMERS = 200
NUM_HOTELS = 3
NUM_ROOMS_PER_HOTEL = 50
NUM_BOOKINGS = 200
MAX_ROOMS_PER_BOOKING = 3
MAX_PAYMENTS_PER_BOOKING = 2
MAX_REVIEWS_PER_CUSTOMER = 3

# SQL statement list
seed_sql = []

# ✅ Disable foreign key checks & fully clear data
seed_sql.append("SET FOREIGN_KEY_CHECKS = 0;")
tables = [
    "Review",
    "Payment",
    "Contains",
    "Booking",
    "SuiteRoom",
    "DeluxeRoom",
    "Room",
    "HotelPartnership",
    "Customer",
    "Hotel"
]
for table in tables:
    seed_sql.append(f"TRUNCATE TABLE {table};")  # better than DELETE for full reset
seed_sql.append("SET FOREIGN_KEY_CHECKS = 1;")

# ✅ Insert Hotels
hotels = [(i+1, f"Hotel {chr(65+i)}", fake.city(), round(random.uniform(3.0, 5.0), 1)) for i in range(NUM_HOTELS)]
seed_sql.append("-- Insert Hotels")
for h in hotels:
    seed_sql.append(f"INSERT INTO Hotel (HotelID, Name, Location, Rating) VALUES ({h[0]}, '{h[1]}', '{h[2]}', {h[3]});")

# ✅ Hotel Partnerships
seed_sql.append("-- Insert Hotel Partnerships")
for i in range(NUM_HOTELS):
    for j in range(i+1, NUM_HOTELS):
        seed_sql.append(f"INSERT INTO HotelPartnership (HotelID1, HotelID2) VALUES ({hotels[i][0]}, {hotels[j][0]});")

# ✅ Insert Customers
seed_sql.append("-- Insert Customers")
for i in range(1, NUM_CUSTOMERS + 1):
    seed_sql.append(f"""
    INSERT INTO Customer (CustomerID, Username, Password, FirstName, LastName, Email, PhoneNumber)
    VALUES (
        {i},
        '{fake.unique.user_name()}',
        '{fake.password()}',
        '{fake.first_name()}',
        '{fake.last_name()}',
        '{fake.unique.email()}',
        '{fake.phone_number()[:20]}'
    );
    """)

# ✅ Insert Rooms and Subtypes
seed_sql.append("-- Insert Rooms and Room Subtypes")
room_numbers = {}
room_price_lookup = {}  # Lookup for room prices
for hotel_id in range(1, NUM_HOTELS + 1):
    room_numbers[hotel_id] = []
    for room_index in range(1, NUM_ROOMS_PER_HOTEL + 1):
        room_num = f"R{hotel_id}{room_index:03d}"  # guaranteed unique per hotel
        room_numbers[hotel_id].append(room_num)
        floor = random.randint(1, 10)
        price = round(random.uniform(80, 500), 2)
        guests = random.randint(1, 4)
        status = random.choice(['available', 'occupied', 'maintenance'])

        seed_sql.append(f"""
        INSERT INTO Room (HotelID, RoomNumber, RoomFloor, PricePerNight, MaxGuests, Status)
        VALUES ({hotel_id}, '{room_num}', {floor}, {price}, {guests}, '{status}');
        """)

        # Add to room price lookup
        room_price_lookup[(hotel_id, room_num)] = price

        if random.choice([True, False]):
            seed_sql.append(f"""
            INSERT INTO SuiteRoom (HotelID, RoomNumber, SeparateLivingRoom, Jacuzzi)
            VALUES ({hotel_id}, '{room_num}', {random.randint(0,1)}, {random.randint(0,1)});
            """)
        else:
            seed_sql.append(f"""
            INSERT INTO DeluxeRoom (HotelID, RoomNumber, PrivateBalcony, BonusServices)
            VALUES ({hotel_id}, '{room_num}', {random.randint(0,1)}, 'Bonus {fake.word()}');
            """)

# ✅ Bookings, Contains, Payments
seed_sql.append("-- Insert Bookings, Contains, Payments")
used_room_combos = set()
for booking_id in range(1, NUM_BOOKINGS + 1):
    customer_id = random.randint(1, NUM_CUSTOMERS)
    checkin = fake.date_between(start_date='-6M', end_date='-1d')
    num_nights = random.randint(1, 10)
    checkout = checkin + timedelta(days=num_nights)

    # Pick rooms for this booking
    room_choices = []
    for _ in range(random.randint(1, MAX_ROOMS_PER_BOOKING)):
        while True:
            hid = random.randint(1, NUM_HOTELS)
            rnum = random.choice(room_numbers[hid])
            combo = (booking_id, hid, rnum)
            if combo not in used_room_combos:
                used_room_combos.add(combo)
                room_choices.append((hid, rnum))
                break

    # Calculate total price: sum of all room prices per night × number of nights
    room_prices = [room_price_lookup[(hid, rnum)] for hid, rnum in room_choices]
    total_price = round(sum(room_prices) * num_nights, 2)

    seed_sql.append(f"""
    INSERT INTO Booking (BookingID, CheckInDate, CheckOutDate, TotalPrice, CustomerID)
    VALUES ({booking_id}, '{checkin}', '{checkout}', {total_price}, {customer_id});
    """)

    for hid, rnum in room_choices:
        seed_sql.append(f"""
        INSERT INTO Contains (BookingID, HotelID, RoomNumber)
        VALUES ({booking_id}, {hid}, '{rnum}');
        """)

    # Payment logic: randomly choose full or installment
    is_installment = random.choice([True, False])
    if is_installment:
        # Two payments, each half the total price
        half_amount = round(total_price / 2, 2)
        # First payment: completed
        method = random.choice(['Credit Card', 'Debit Card'])
        pay_date = fake.date_between(start_date=checkin, end_date=checkout)
        card = fake.credit_card_number()
        exp = fake.date_between(start_date='today', end_date='+3y')
        cvv = str(random.randint(100, 999))
        seed_sql.append(f"""
        INSERT INTO Payment (BookingID, PaymentNumber, PaymentMethod, PaymentDate, PaymentStatus,
        CardNumber, ExpiryDate, CVV, Amount)
        VALUES ({booking_id}, 1, '{method}', '{pay_date}', 'completed', '{card}', '{exp}', '{cvv}', {half_amount});
        """)
        # Second payment: pending, no card info yet
        seed_sql.append(f"""
        INSERT INTO Payment (BookingID, PaymentNumber, PaymentMethod, PaymentDate, PaymentStatus,
        CardNumber, ExpiryDate, CVV, Amount)
        VALUES ({booking_id}, 2, '{method}', NULL, 'pending', NULL, NULL, NULL, {half_amount});
        """)
    else:
        # Full payment, one row
        method = random.choice(['Credit Card', 'Debit Card'])
        pay_date = fake.date_between(start_date=checkin, end_date=checkout)
        card = fake.credit_card_number()
        exp = fake.date_between(start_date='today', end_date='+3y')
        cvv = str(random.randint(100, 999))
        seed_sql.append(f"""
        INSERT INTO Payment (BookingID, PaymentNumber, PaymentMethod, PaymentDate, PaymentStatus,
        CardNumber, ExpiryDate, CVV, Amount)
        VALUES ({booking_id}, 1, '{method}', '{pay_date}', 'completed', '{card}', '{exp}', '{cvv}', {total_price});
        """)

# ✅ Reviews
seed_sql.append("-- Insert Reviews")
for customer_id in range(1, NUM_CUSTOMERS + 1):
    for review_num in range(1, random.randint(1, MAX_REVIEWS_PER_CUSTOMER) + 1):
        hotel_id = random.randint(1, NUM_HOTELS)
        rating = random.randint(1, 5)
        comment = fake.sentence()
        review_date = fake.date_between(start_date='-6M', end_date='today')
        seed_sql.append(f"""
        INSERT INTO Review (CustomerID, HotelID, ReviewNumber, Rating, Comment, ReviewDate)
        VALUES ({customer_id}, {hotel_id}, {review_num}, {rating}, '{comment}', '{review_date}');
        """)

# ✅ Execute SQL statements
try:
    conn = mysql.connector.connect(
        host="mariadb",
        user="user",
        password="upass",
        database="hotelbooking"
    )
    cursor = conn.cursor()
    for statement in "\n".join(seed_sql).split(";\n"):
        if statement.strip():
            cursor.execute(statement + ";")
    conn.commit()
    cursor.close()
    conn.close()
    print("MariaDB seeded successfully.")
except Exception as e:
    print("Error while seeding MariaDB:", e)
