CREATE DATABASE IF NOT EXISTS hotelbooking;
USE hotelbooking;


-- Hotel Booking Platform Database Schema (Final Version: Review uses ReviewNumber as weak key)

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

CREATE TABLE Room (
    RoomNumber VARCHAR(10) PRIMARY KEY,
    RoomFloor INT,
    PricePerNight DECIMAL(10,2),
    MaxGuests INT,
    Status TEXT CHECK (Status IN ('available', 'occupied', 'maintenance')),
    HotelID INT
);


CREATE TABLE DeluxeRoom (
    RoomNumber VARCHAR(10) PRIMARY KEY,
    PrivateBalcony BOOLEAN,
    BonusServices TEXT,
    FOREIGN KEY (RoomNumber) REFERENCES Room(RoomNumber)
);

CREATE TABLE SuiteRoom (
    RoomNumber VARCHAR(10) PRIMARY KEY,
    SeparateLivingRoom BOOLEAN,
    Jacuzzi BOOLEAN,
    FOREIGN KEY (RoomNumber) REFERENCES Room(RoomNumber)
);

CREATE TABLE Booking (
    BookingID INT PRIMARY KEY,
    CheckInDate DATE,
    CheckOutDate DATE,
    TotalPrice DECIMAL(10,2),
    CustomerID INT,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
);

CREATE TABLE Contains (
    BookingID INT,
    RoomNumber VARCHAR(10),
    PRIMARY KEY (BookingID, RoomNumber),
    FOREIGN KEY (BookingID) REFERENCES Booking(BookingID),
    FOREIGN KEY (RoomNumber) REFERENCES Room(RoomNumber)
);

CREATE TABLE Review (
    ReviewNumber INT PRIMARY KEY,
    Rating INT CHECK (Rating BETWEEN 1 AND 5),
    Comment TEXT,
    ReviewDate DATE,
    CustomerID INT,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
);


CREATE TABLE Payment (
    PaymentNumber INT PRIMARY KEY,
    PaymentMethod TEXT,
    PaymentDate DATE,
    PaymentStatus TEXT CHECK (PaymentStatus IN ('pending', 'completed', 'failed')),
    CardNumber TEXT,
    ExpiryDate DATE,
    CVV TEXT,
    Amount DECIMAL(10,2),
    BookingID INT
);
