import psycopg2
import uuid
from datetime import datetime

from data.entities.product import Product

class ProductRepository:
    def __init__(self):
        db_params = {
            'host': 'localhost',
            'database': 'gurgencler-takip',
            'user': 'trendyol',
            'password': 'trendyol-bot-1234321'
        }

        self.conn = psycopg2.connect(**db_params)
        self.cursor = self.conn.cursor()
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Products (
                                Id TEXT PRIMARY KEY,
                                Title TEXT,
                                Link TEXT,
                                Price DECIMAL,
                                CreatedAt TIMESTAMP,
                                UpdatedAt TIMESTAMP,
                                IsDeleted BOOLEAN
                            )''')
        self.conn.commit()

    def add_product(self, product):
        self.cursor.execute('''INSERT INTO Products (Id, Title, Link, Price, CreatedAt, UpdatedAt, IsDeleted)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                            (product.id, product.title, product.link, product.price,
                             product.created_at, product.updated_at, product.is_deleted))

        print("new item added")
        self.conn.commit()

    def get_all_product_links(self):
        try:
            self.cursor.execute("SELECT Link FROM Products")
            rows = self.cursor.fetchall()
            links = [row[0] for row in rows]
            return links
        except Exception as e:
            print("Error occurred during SQL query:", e)

    def get_product_by_id(self, product_id):
        self.cursor.execute("SELECT * FROM Products WHERE Id=%s", (product_id,))
        row = self.cursor.fetchone()
        if row:
            return self._row_to_product(row)
        else:
            return None


    def get_product_by_link(self, link):
        try:
            link = link.strip().lower()

            self.cursor.execute("SELECT * FROM Products WHERE lower(trim(link)) = %s", (link,))
            row = self.cursor.fetchone()

            if row:
                return self._row_to_product(row)
            else:
                return False
        except Exception as e:
            print("Error occurred during SQL query:", e)

    def update_product(self, product):
        try:
            self.cursor.execute('''UPDATE Products SET Title=%s, Link=%s, Price=%s, UpdatedAt=%s, IsDeleted=%s
                                    WHERE Id=%s''',
                                (product.title, product.link, product.price, datetime.now(),
                                product.is_deleted, product.id))
            self.conn.commit()
            print("product updated successfully. id: ", product.id, "product new price: ", product.price)
        except Exception as err:
            print("error while updating the product: ", err)
            self.conn.rollback()  # Rollback changes if an error occurs

    def delete_product(self, product_id):
        self.cursor.execute("DELETE FROM Products WHERE Id=%s", (product_id,))
        self.conn.commit()

    def _row_to_product(self, row):
        return Product(
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6])

    def close(self):
        self.conn.close()