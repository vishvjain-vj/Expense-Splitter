import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()

db_config = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "expense_splitter"),
}

connection_pool = pooling.MySQLConnectionPool(
    pool_name="splitter_pool",
    pool_size=5,
    **db_config
)

def get_connection():
    return connection_pool.get_connection()

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups_tbl (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            name        VARCHAR(100) NOT NULL,
            description VARCHAR(255),
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            group_id   INT NOT NULL,
            name       VARCHAR(100) NOT NULL,
            email      VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups_tbl(id) ON DELETE CASCADE,
            UNIQUE KEY unique_member (group_id, email)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            group_id    INT NOT NULL,
            paid_by     INT NOT NULL,
            description VARCHAR(255) NOT NULL,
            amount      DECIMAL(10,2) NOT NULL,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups_tbl(id) ON DELETE CASCADE,
            FOREIGN KEY (paid_by) REFERENCES members(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_splits (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            expense_id INT NOT NULL,
            member_id  INT NOT NULL,
            share      DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
            FOREIGN KEY (member_id)  REFERENCES members(id)  ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
