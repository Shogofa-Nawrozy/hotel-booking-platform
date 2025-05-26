USE hotelbooking;

-- Add sample hotels
INSERT INTO Hotel (HotelID, Name, Location, Rating) VALUES
(1, 'Hotel Vienna Center', 'Vienna, Austria', 4.5),
(2, 'Berlin Grand Stay', 'Berlin, Germany', 4.3);

-- Add hotel partnerships
INSERT INTO HotelPartnership VALUES (1, 2);

-- Add sample customers
INSERT INTO Customer (CustomerID, Username, Password, FirstName, LastName, Email, PhoneNumber) VALUES
(1, 'shogofa.n', 'pass123', 'Shogofa', 'Nawrozy', 'shogofa@example.com', '1234567890'),
(2, 'nelin.d', 'pass456', 'Nelin', 'Dogu', 'nelin@example.com', '0987654321');

-- Add rooms (Room is weak entity → must include HotelID + RoomNumber)
INSERT INTO Room (HotelID, RoomNumber, RoomFloor, MaxGuests, Status, PricePerNight) VALUES
(1, '101A', 1, 2, 'available', 100.00),
(1, '102B', 1, 3, 'available', 120.00),
(2, '201A', 2, 2, 'maintenance', 90.00);

-- Add specialized rooms
INSERT INTO SuiteRoom (HotelID, RoomNumber, HasJacuzzi, HasSeparateLivingRoom) VALUES
(1, '101A', TRUE, TRUE);

INSERT INTO DeluxeRoom (HotelID, RoomNumber, PrivateBalcony, BonusServices) VALUES
(1, '102B', TRUE, 'Spa access');

-- Add bookings
INSERT INTO Booking (BookingID, CustomerID, BookingDate, CheckInDate, CheckOutDate, TotalPrice) VALUES
(1001, 1, '2025-04-01', '2025-04-10', '2025-04-15', 400.00);

-- Booking includes rooms
INSERT INTO Contains (BookingID, HotelID, RoomNumber) VALUES
(1001, 1, '101A'),
(1001, 1, '102B');

-- Payments (weak entity)
INSERT INTO Payment (BookingID, PaymentNumber, PaymentMethod, CardNumber, CVV, ExpiryDate, Amount, PaymentDate, PaymentStatus) VALUES
(1001, 1, 'Credit Card', '1111222233334444', '123', '2026-01-01', 400.00, '2025-04-01', 'completed');

-- Review
INSERT INTO Review (CustomerID, HotelID, ReviewNumber, ReviewDate, Rating, Comment) VALUES
(1, 1, 1, '2025-04-16', 5, 'Great stay!');
