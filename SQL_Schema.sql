SQL Schema
CREATE TABLE Users (
    User_ID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100),
    Email VARCHAR(100),
    Password VARCHAR(100)
);

CREATE TABLE Admin (
    Admin_ID INT PRIMARY KEY AUTO_INCREMENT,
    Username VARCHAR(100),
    Password VARCHAR(100)
);

CREATE TABLE Disease_Info (
    Disease_ID INT PRIMARY KEY AUTO_INCREMENT,
    Disease_Name VARCHAR(100),
    Description TEXT,
    Prevention TEXT
);

CREATE TABLE Symptoms (
    Symptom_ID INT PRIMARY KEY AUTO_INCREMENT,
    Disease_ID INT,
    Symptom_Name VARCHAR(100),
    FOREIGN KEY (Disease_ID) REFERENCES Disease_Info(Disease_ID)
);

CREATE TABLE Vaccination (
    Vaccine_ID INT PRIMARY KEY AUTO_INCREMENT,
    Disease_ID INT,
    Vaccine_Name VARCHAR(100),
    Schedule_Info VARCHAR(200),
    FOREIGN KEY (Disease_ID) REFERENCES Disease_Info(Disease_ID)
);

CREATE TABLE Health_Alerts (
    Alert_ID INT PRIMARY KEY AUTO_INCREMENT,
    Title VARCHAR(200),
    Description TEXT,
    Alert_Date DATE
);

CREATE TABLE Chat_History (
    Chat_ID INT PRIMARY KEY AUTO_INCREMENT,
    User_ID INT,
    Question TEXT,
    Response TEXT,
    Chat_Date DATE,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID)
);

CREATE TABLE Reports (
    Report_ID INT PRIMARY KEY AUTO_INCREMENT,
    Report_Name VARCHAR(100),
    Generated_Date DATE
);
