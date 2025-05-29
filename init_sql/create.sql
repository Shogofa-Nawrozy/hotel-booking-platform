CREATE DATABASE IF NOT EXISTS hotelbooking;
USE hotelbooking;

CREATE TABLE Hotel (
    HotelID INT PRIMARY KEY,
    Name VARCHAR(100),
    Location VARCHAR(100),
    Rating DECIMAL(2,1)
);

CREATE TABLE HotelPartnership (
    HotelID1 INT,
    HotelID2 INT,
    PRIMARY KEY (HotelID1, HotelID2),
    FOREIGN KEY (HotelID1) REFERENCES Hotel(HotelID),
    FOREIGN KEY (HotelID2) REFERENCES Hotel(HotelID)
);

CREATE TABLE Customer (
    CustomerID INT PRIMARY KEY,
    Username VARCHAR(50) UNIQUE,
    Password VARCHAR(100),
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    Email VARCHAR(100),
    PhoneNumber VARCHAR(20)
);

-- Room is now a weak entity with composite key (HotelID, RoomNumber)
CREATE TABLE Room (
    HotelID INT,
    RoomNumber VARCHAR(10),
    RoomFloor INT,
    PricePerNight DECIMAL(10,2),
    MaxGuests INT,
    Status ENUM('available', 'occupied', 'maintenance'),
    PRIMARY KEY (HotelID, RoomNumber),
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID)
);

-- IS-A hierarchy for SuiteRoom and DeluxeRoom inherits composite PK
CREATE TABLE DeluxeRoom (
    HotelID INT,
    RoomNumber VARCHAR(10),
    PrivateBalcony BOOLEAN,
    BonusServices TEXT,
    PRIMARY KEY (HotelID, RoomNumber),
    FOREIGN KEY (HotelID, RoomNumber) REFERENCES Room(HotelID, RoomNumber)
);

CREATE TABLE SuiteRoom (
    HotelID INT,
    RoomNumber VARCHAR(10),
    SeparateLivingRoom BOOLEAN,
    Jacuzzi BOOLEAN,
    PRIMARY KEY (HotelID, RoomNumber),
    FOREIGN KEY (HotelID, RoomNumber) REFERENCES Room(HotelID, RoomNumber)
);

CREATE TABLE Booking (
    BookingID INT PRIMARY KEY,
    CheckInDate DATE,
    CheckOutDate DATE,
    TotalPrice DECIMAL(10,2),
    CustomerID INT,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
);

-- Many-to-many relationship Booking <-> Room via Contains associative table
CREATE TABLE Contains (
    BookingID INT,
    HotelID INT,
    RoomNumber VARCHAR(10),
    PRIMARY KEY (BookingID, HotelID, RoomNumber),
    FOREIGN KEY (BookingID) REFERENCES Booking(BookingID),
    FOREIGN KEY (HotelID, RoomNumber) REFERENCES Room(HotelID, RoomNumber)
);

-- Payment is weak entity dependent on Booking with composite PK (BookingID, PaymentNumber)
CREATE TABLE Payment (
    BookingID INT,
    PaymentNumber INT,
    PaymentMethod VARCHAR(50),
    PaymentDate DATE,
    PaymentStatus ENUM('pending', 'completed', 'failed'),
    CardNumber VARCHAR(20),
    ExpiryDate DATE,
    CVV VARCHAR(5),
    Amount DECIMAL(10,2),
    PRIMARY KEY (BookingID, PaymentNumber),
    FOREIGN KEY (BookingID) REFERENCES Booking(BookingID)
);

-- Review is weak entity dependent on (CustomerID, HotelID) with composite PK
CREATE TABLE Review (
    CustomerID INT,
    HotelID INT,
    ReviewNumber INT,
    Rating INT CHECK (Rating BETWEEN 1 AND 5),
    Comment TEXT,
    ReviewDate DATE,
    PRIMARY KEY (CustomerID, HotelID, ReviewNumber),
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID),
    FOREIGN KEY (HotelID) REFERENCES Hotel(HotelID)
);
