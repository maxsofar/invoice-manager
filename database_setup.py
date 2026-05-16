import sqlite3
import os

# Define the path to the database file
db_path = os.path.join(os.path.dirname(__file__), 'database.db')

# Connect to the database
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Drop existing tables if they exist
cursor.execute('''DROP TABLE IF EXISTS clients''')
cursor.execute('''DROP TABLE IF EXISTS orders''')
cursor.execute('''DROP TABLE IF EXISTS order_items''')

# Create tables for clients, orders, and order_items
cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone_number TEXT
                 )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER,
                    date TEXT,
                    FOREIGN KEY (client_id) REFERENCES clients (id)
                 )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    description TEXT,
                    quantity INTEGER,
                    price_per_unit REAL,
                    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
                 )''')

# Save and close
connection.commit()
connection.close()

print("Database and tables created with updated schema!")
