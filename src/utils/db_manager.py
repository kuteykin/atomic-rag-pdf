# src/utils/db_manager.py

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Products table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    sku TEXT UNIQUE NOT NULL,
                    primary_product_number TEXT,
                    watt INTEGER,
                    voltage TEXT,
                    current TEXT,
                    color_temperature TEXT,
                    color_rendering_index INTEGER,
                    luminous_flux INTEGER,
                    beam_angle TEXT,
                    lebensdauer_stunden INTEGER,
                    operating_temperature TEXT,
                    dimensions TEXT,
                    weight TEXT,
                    application_area TEXT,
                    suitable_for TEXT,  -- JSON array
                    certifications TEXT,  -- JSON array
                    ip_rating TEXT,
                    full_description TEXT NOT NULL,
                    source_pdf TEXT NOT NULL,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sku ON products(sku)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_name ON products(product_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_watt ON products(watt)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_lebensdauer ON products(lebensdauer_stunden)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_application ON products(application_area)"
            )

            conn.commit()
            logger.info(f"Database schema initialized at {self.db_path}")

    def insert_product(self, product_data: Dict[str, Any]) -> int:
        """Insert a product and return the ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Convert lists to JSON strings
            suitable_for = str(product_data.get("suitable_for", []))
            certifications = str(product_data.get("certifications", []))

            cursor.execute(
                """
                INSERT INTO products (
                    product_name, sku, primary_product_number, watt, voltage, current,
                    color_temperature, color_rendering_index, luminous_flux, beam_angle,
                    lebensdauer_stunden, operating_temperature, dimensions, weight,
                    application_area, suitable_for, certifications, ip_rating,
                    full_description, source_pdf
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    product_data.get("product_name"),
                    product_data.get("sku"),
                    product_data.get("primary_product_number"),
                    product_data.get("watt"),
                    product_data.get("voltage"),
                    product_data.get("current"),
                    product_data.get("color_temperature"),
                    product_data.get("color_rendering_index"),
                    product_data.get("luminous_flux"),
                    product_data.get("beam_angle"),
                    product_data.get("lebensdauer_stunden"),
                    product_data.get("operating_temperature"),
                    product_data.get("dimensions"),
                    product_data.get("weight"),
                    product_data.get("application_area"),
                    suitable_for,
                    certifications,
                    product_data.get("ip_rating"),
                    product_data.get("full_description"),
                    product_data.get("source_pdf"),
                ),
            )

            product_id = cursor.lastrowid
            conn.commit()
            return product_id

    def search_exact(self, query: str) -> List[Dict[str, Any]]:
        """Search for exact matches"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Search in SKU, product name, and primary product number
            cursor.execute(
                """
                SELECT * FROM products 
                WHERE sku LIKE ? OR product_name LIKE ? OR primary_product_number LIKE ?
                ORDER BY 
                    CASE 
                        WHEN sku = ? THEN 1
                        WHEN primary_product_number = ? THEN 2
                        ELSE 3
                    END
            """,
                (f"%{query}%", f"%{query}%", f"%{query}%", query, query),
            )

            return [dict(row) for row in cursor.fetchall()]

    def search_by_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search by attribute filters"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            conditions = []
            params = []

            if filters.get("watt_min"):
                conditions.append("watt >= ?")
                params.append(filters["watt_min"])

            if filters.get("watt_max"):
                conditions.append("watt <= ?")
                params.append(filters["watt_max"])

            if filters.get("lebensdauer_min"):
                conditions.append("lebensdauer_stunden >= ?")
                params.append(filters["lebensdauer_min"])

            if filters.get("lebensdauer_max"):
                conditions.append("lebensdauer_stunden <= ?")
                params.append(filters["lebensdauer_max"])

            if filters.get("color_temperature"):
                conditions.append("color_temperature LIKE ?")
                params.append(f"%{filters['color_temperature']}%")

            if filters.get("application_area"):
                conditions.append("application_area LIKE ?")
                params.append(f"%{filters['application_area']}%")

            if filters.get("ip_rating"):
                conditions.append("ip_rating LIKE ?")
                params.append(f"%{filters['ip_rating']}%")

            if not conditions:
                return []

            sql = f"SELECT * FROM products WHERE {' AND '.join(conditions)}"
            cursor.execute(sql, params)

            return [dict(row) for row in cursor.fetchall()]

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT source_pdf) FROM products")
            total_pdfs = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM products WHERE watt IS NOT NULL")
            products_with_watt = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM products WHERE lebensdauer_stunden IS NOT NULL")
            products_with_lifetime = cursor.fetchone()[0]

            return {
                "total_products": total_products,
                "total_pdfs": total_pdfs,
                "products_with_watt": products_with_watt,
                "products_with_lifetime": products_with_lifetime,
            }
