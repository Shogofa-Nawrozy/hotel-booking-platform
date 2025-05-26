CREATE DATABASE IF NOT EXISTS hotelbooking;
USE hotelbooking;

-- Hotel (strong entity)
CREATE TABLE Hotel (
    HotelID INT PRIMARY KEY,
    Name VARCHAR(100),
    Location VARCHAR(100),
    Rating DECIMAL(2,1)
);

-- Customer (strong entity)
CREATE TABLE Customer (
    CustomerID INT PRIMARY KEY,
    Username VARCHAR(50) UNIQUE,
    Password VARCHAR(100),
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    Email VARCHAR(100),
    PhoneNumber VARCHAR(20)
);

-- Room (weak entity: uniquely identified by HotelID + RoomNumber)
CREATE TABLE Room (
    HotelID INT,
    RoomNumber VARCHAR(10),
    RoomFloor INT,
    MaxGuests INT,
    Status ENUM('available', 'occupied', 'maintenance'),
    PricePerNight DECIMAL(10,2),
    PRIMARY KEY (HotelID, RoomNumber),
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID)
);

-- SuiteRoom (IS-A of Room)
CREATE TABLE SuiteRoom (
    HotelID INT,
    RoomNumber VARCHAR(10),
    HasJacuzzi BOOLEAN,
    HasSeparateLivingRoom BOOLEAN,
    PRIMARY KEY (HotelID, RoomNumber),
    FOREIGN KEY (HotelID, RoomNumber) REFERENCES Room(HotelID, RoomNumber)
);

-- DeluxeRoom (IS-A of Room)
CREATE TABLE DeluxeRoom (
    HotelID INT,
    RoomNumber VARCHAR(10),
    PrivateBalcony BOOLEAN,
    BonusServices TEXT,
    PRIMARY KEY (HotelID, RoomNumber),
    FOREIGN KEY (HotelID, RoomNumber) REFERENCES Room(HotelID, RoomNumber)
);

-- Booking (HotelID removed)
CREATE TABLE Booking (
    BookingID INT PRIMARY KEY,
    CustomerID INT,
    BookingDate DATE,
    CheckInDate DATE,
    CheckOutDate DATE,
    TotalPrice DECIMAL(10,2),
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
);

-- Contains (M:N relationship between Booking and Room)
CREATE TABLE Contains (
    BookingID INT,
    HotelID INT,
    RoomNumber VARCHAR(10),
    PRIMARY KEY (BookingID, HotelID, RoomNumber),
    FOREIGN KEY (BookingID) REFERENCES Booking(BookingID),
    FOREIGN KEY (HotelID, RoomNumber) REFERENCES Room(HotelID, RoomNumber)
);

-- Payment (weak entity of Booking)
CREATE TABLE Payment (
    BookingID INT,
    PaymentNumber INT,
    PaymentMethod VARCHAR(50),
    CardNumber VARCHAR(20),
    CVV VARCHAR(4),
    ExpiryDate DATE,
    Amount DECIMAL(10,2),
    PaymentDate DATE,
    PaymentStatus ENUM('pending', 'completed', 'failed'),
    PRIMARY KEY (BookingID, PaymentNumber),
    FOREIGN KEY (BookingID) REFERENCES Booking(BookingID)
);

-- Review (as weak entity, using composite PK)
CREATE TABLE Review (
    CustomerID INT,
    HotelID INT,
    ReviewNumber INT,
    ReviewDate DATE,
    Rating INT CHECK (Rating BETWEEN 1 AND 5),
    Comment TEXT,
    PRIMARY KEY (CustomerID, HotelID, ReviewNumber),
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID),
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID)
);

-- HotelPartnership (recursive M:N on Hotel)
CREATE TABLE HotelPartnership (
    HotelID1 INT,
    HotelID2 INT,
    PRIMARY KEY (HotelID1, HotelID2),
    FOREIGN KEY (HotelID1) REFERENCES Hotel(HotelID),
    FOREIGN KEY (HotelID2) REFERENCES Hotel(HotelID)
);
