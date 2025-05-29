# First, let's regenerate a matching seeder script based on the given ER diagram and schema.
# The key adjustments are:
# - Use composite keys (HotelID, RoomNumber) for Room-related tables
# - Reflect many-to-many relationships appropriately (e.g., Contains, HotelPartnership)
# - Ensure multi-payment per booking, multiple rooms per booking, and reviews

from faker import Faker
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

# Generate SQL statements for seeding the database
seed_sql = []

# Hotels
hotels = [(i+1, f"Hotel {chr(65+i)}", fake.city(), round(random.uniform(3.0, 5.0), 1)) for i in range(NUM_HOTELS)]
seed_sql.append("-- Insert Hotels")
for h in hotels:
    seed_sql.append(f"INSERT INTO Hotel (HotelID, Name, Location, Rating) VALUES ({h[0]}, '{h[1]}', '{h[2]}', {h[3]});")

# Hotel Partnerships (symmetric, without self-pairing)
seed_sql.append("-- Insert Hotel Partnerships")
for i in range(NUM_HOTELS):
    for j in range(i+1, NUM_HOTELS):
        seed_sql.append(f"INSERT INTO HotelPartnership (HotelID1, HotelID2) VALUES ({hotels[i][0]}, {hotels[j][0]});")

# Customers
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

# Rooms (per hotel)
seed_sql.append("-- Insert Rooms and Room Subtypes")
room_numbers = {}
for hotel_id in range(1, NUM_HOTELS + 1):
    for room_index in range(1, NUM_ROOMS_PER_HOTEL + 1):
        room_num = f"R{hotel_id:01d}{room_index:03d}"
        room_numbers.setdefault(hotel_id, []).append(room_num)
        floor = random.randint(1, 10)
        price = round(random.uniform(80, 500), 2)
        guests = random.randint(1, 4)
        status = random.choice(['available', 'occupied', 'maintenance'])
        seed_sql.append(f"""
        INSERT INTO Room (HotelID, RoomNumber, RoomFloor, PricePerNight, MaxGuests, Status)
        VALUES ({hotel_id}, '{room_num}', {floor}, {price}, {guests}, '{status}');
        """)
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

# Bookings, Contains, and Payments
seed_sql.append("-- Insert Bookings, Contains, Payments")
for booking_id in range(1, NUM_BOOKINGS + 1):
    customer_id = random.randint(1, NUM_CUSTOMERS)
    checkin = fake.date_between(start_date='-6M', end_date='-1d')
    checkout = checkin + timedelta(days=random.randint(1, 10))
    total_price = round(random.uniform(300, 3000), 2)
    seed_sql.append(f"""
    INSERT INTO Booking (BookingID, CheckInDate, CheckOutDate, TotalPrice, CustomerID)
    VALUES ({booking_id}, '{checkin}', '{checkout}', {total_price}, {customer_id});
    """)
    
    # Add rooms to Contains
    for _ in range(random.randint(1, MAX_ROOMS_PER_BOOKING)):
        hid = random.randint(1, NUM_HOTELS)
        rnum = random.choice(room_numbers[hid])
        seed_sql.append(f"""
        INSERT INTO Contains (BookingID, HotelID, RoomNumber)
        VALUES ({booking_id}, {hid}, '{rnum}');
        """)

    # Add multiple payments per booking
    for payment_num in range(1, random.randint(2, MAX_PAYMENTS_PER_BOOKING+1)):
        method = random.choice(['Credit Card', 'Debit Card'])
        pay_date = fake.date_between(start_date='-6M', end_date='today')
        status = random.choice(['pending', 'completed', 'failed'])
        card = fake.credit_card_number()
        exp = fake.date_between(start_date='today', end_date='+3y')
        cvv = str(random.randint(100, 999))
        amount = round(random.uniform(150, 1500), 2)
        seed_sql.append(f"""
        INSERT INTO Payment (BookingID, PaymentNumber, PaymentMethod, PaymentDate, PaymentStatus,
        CardNumber, ExpiryDate, CVV, Amount)
        VALUES ({booking_id}, {payment_num}, '{method}', '{pay_date}', '{status}', '{card}', '{exp}', '{cvv}', {amount});
        """)

# Reviews
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

# Join all SQL lines into one seeder script
seeder_script = "\n".join(seed_sql)
seeder_script[:1000]  # Show a preview of the beginning
