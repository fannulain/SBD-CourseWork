import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from dotenv import load_dotenv
from typing import List, Optional
from .models import Subscriber
from .models import DebtorReport

load_dotenv()

class PostgresManager:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname=os.getenv("PG_DB"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT")
        )
        self.connection.autocommit = True
        self._create_table()

    def _create_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS subscribers(
                ric VARCHAR(50) PRIMARY KEY,
                pin_code VARCHAR(10) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                phone_model VARCHAR(100) NOT NULL,
                phone_type VARCHAR(50) NOT NULL,
                service_type VARCHAR(50) NOT NULL,
                contract_start_date DATE NOT NULL,
                contract_duration_months INT NOT NULL,
                monthly_fee DECIMAL(10, 2) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                last_payment_date DATE
            );
        """
        with self.connection.cursor() as cursor:
            cursor.execute(query)

    def add_subscriber(self, subscriber: Subscriber):
        query = """
            INSERT INTO subscribers(
                ric, pin_code, full_name, phone_model, phone_type,
                service_type, contract_start_date, contract_duration_months,
                monthly_fee, is_active, last_payment_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ric) DO NOTHING;
        """
        values = (
            subscriber.ric, subscriber.pin_code, subscriber.full_name, subscriber.phone_model,
            subscriber.phone_type, subscriber.service_type, subscriber.contract_start_date,
            subscriber.contract_duration_months, subscriber.monthly_fee, 
            subscriber.is_active, subscriber.last_payment_date
        )

        with self.connection.cursor() as cursor:
            cursor.execute(query, values)

    def get_subscriber(self, ric: str) -> Optional[Subscriber]:
        query = "SELECT * FROM subscribers WHERE ric = %s"

        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (ric,))
            row = cursor.fetchone()
            if row:
                return Subscriber(**row)
            return None
        
    def get_all_subscribers(self) -> List[Subscriber]:
        query = "SELECT * FROM subscribers"

        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [Subscriber(**row) for row in rows]
        
    def delete_subscriber(self, ric: str):
        query = "DELETE FROM subscribers WHERE ric = %s"

        with self.connection.cursor() as cursor:
            cursor.execute(query, (ric,))

    def deactivate_subscriber(self, ric: str):
        query = "UPDATE subscribers SET is_active = FALSE WHERE ric = %s"
        with self.connection.cursor() as cursor:
            cursor.execute(query, (ric,))

    def get_debtors_raw(self):
        query = """
            SELECT ric, full_name, last_payment_date, monthly_fee
            FROM subscribers
            WHERE last_payment_date < CURRENT_DATE - INTERVAL '1 month'
            AND is_active = TRUE
        """

        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [DebtorReport(**row) for row in rows]
        
    def get_custom_columns(self, columns: List[str]):
        if not columns:
            return []
        
        allowed_columns = {
            "ric", "pin_code", "full_name", "phone_model", "phone_type",
            "service_type", "contract_start_date", "contract_duration_months",
            "monthly_fee", "is_active", "last_payment_date"
        }

        safe_columns = [col for col in columns if col in allowed_columns]
        if not safe_columns:
            return []
        
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = sql.SQL("SELECT {} FROM subscribers").format(
                sql.SQL(', ').join(map(sql.Identifier, safe_columns))
            )
            cursor.execute(query)
            return cursor.fetchall()
        
    def get_tariff_analytics(self):
        query = """
            SELECT 
                service_type, 
                COUNT(*) as user_count, 
                SUM(monthly_fee) as total_revenue,
                AVG(monthly_fee) as avg_check
            FROM subscribers
            WHERE is_active = TRUE
            GROUP BY service_type
            ORDER BY total_revenue DESC;
        """
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            return cursor.fetchall()
        
    def close(self):
        self.connection.close()