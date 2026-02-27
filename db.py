# /telegram-stock-bot/db.py

import logging
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from config import DB_CONFIG

logger = logging.getLogger(__name__)

try:
    # Buat connection pool alih-alih koneksi tunggal
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="bot_pool",
        pool_size=5,  # Sesuaikan ukuran pool sesuai kebutuhan
        **DB_CONFIG
    )
    logger.info("Database connection pool created successfully.")
except Error as e:
    logger.error(f"Error creating database connection pool: {e}")
    db_pool = None

@contextmanager
def managed_cursor(commit=False):
    """Context manager untuk mengelola koneksi dan cursor dari pool."""
    if not db_pool:
        raise ConnectionError("Database pool is not available.")
    conn = db_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
    finally:
        if commit: conn.commit()
        cursor.close()
        conn.close() # Mengembalikan koneksi ke pool

def search_products(keyword: str):
    """Searches for products by name or code using a keyword."""
    try:
        with managed_cursor() as cursor:
            # Split the keyword into individual words
            keywords = keyword.lower().split()
            if not keywords:
                return []

            # Build a dynamic query to match all keywords
            # Example: WHERE (LOWER(name) LIKE %word1% AND LOWER(name) LIKE %word2%)
            conditions = " AND ".join(["LOWER(name) LIKE %s"] * len(keywords))
            query = f"SELECT * FROM products WHERE ({conditions})"
            
            # Prepare search terms (e.g., ['%word1%', '%word2%'])
            search_terms = [f"%{kw}%" for kw in keywords]
            
            cursor.execute(query, search_terms)
            return cursor.fetchall()
    except (Error, ConnectionError) as e:
        logger.error(f"Error during search: {e}")
        return []

def get_all_products():
    """Retrieves all products from the database."""
    try:
        with managed_cursor() as cursor:
            cursor.execute("SELECT * FROM products ORDER BY name ASC")
            return cursor.fetchall()
    except (Error, ConnectionError) as e:
        logger.error(f"Error fetching all products: {e}")
        return []

def get_product_by_code(code: str):
    """Retrieves a single product by its unique code."""
    try:
        with managed_cursor() as cursor:
            query = "SELECT * FROM products WHERE code = %s"
            cursor.execute(query, (code,))
            return cursor.fetchone()
    except (Error, ConnectionError) as e:
        logger.error(f"Error fetching product by code: {e}")
        return None

def update_stock(code: str, quantity_to_deduct: int):
    """Updates the stock for a given product code using a transaction."""
    if not db_pool:
        return False, "Database connection failed."

    conn = None
    try:
        # Dapatkan koneksi secara manual untuk kontrol transaksi
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        # Start a transaction
        conn.start_transaction()

        # Lock the row for update to prevent race conditions
        query_select = "SELECT * FROM products WHERE code = %s FOR UPDATE"
        cursor.execute(query_select, (code,))
        product = cursor.fetchone()

        if not product:
            conn.rollback()
            return False, "Product code not found."

        if product['stock'] < quantity_to_deduct:
            conn.rollback()
            return False, f"Insufficient stock. Available: {product['stock']}"

        # Deduct stock
        new_stock = product['stock'] - quantity_to_deduct
        query_update = "UPDATE products SET stock = %s WHERE code = %s"
        cursor.execute(query_update, (new_stock, code))

        # Commit the transaction
        conn.commit()

        # Return the updated product info
        product['stock'] = new_stock
        return True, product

    except Error as e:
        if conn: conn.rollback()
        logger.error(f"Error updating stock: {e}")
        return False, "An error occurred during the transaction."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close() # Mengembalikan koneksi ke pool

def add_stock(code: str, quantity_to_add: int):
    """Adds stock for a given product code using a transaction."""
    if not db_pool:
        return False, "Database connection failed."

    conn = None
    try:
        # Dapatkan koneksi secara manual untuk kontrol transaksi
        conn = db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        # Start a transaction
        conn.start_transaction()

        # Lock the row for update
        query_select = "SELECT * FROM products WHERE code = %s FOR UPDATE"
        cursor.execute(query_select, (code,))
        product = cursor.fetchone()

        if not product:
            conn.rollback()
            return False, "Product code not found."

        # Add stock
        new_stock = product['stock'] + quantity_to_add
        query_update = "UPDATE products SET stock = %s WHERE code = %s"
        cursor.execute(query_update, (new_stock, code))

        # Commit the transaction
        conn.commit()

        product['stock'] = new_stock
        return True, product

    except Error as e:
        if conn: conn.rollback()
        logger.error(f"Error adding stock: {e}")
        return False, "An error occurred during the transaction."
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close() # Mengembalikan koneksi ke pool
