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
        """Initialize database schema dynamically from ProductSpecification"""
        from src.schemas.product_schema import ProductSpecification
        from src.utils.schema_utils import SchemaIntrospector

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get SQL schema from ProductSpecification
            sql_schema = SchemaIntrospector.generate_sql_schema(ProductSpecification)

            # Build CREATE TABLE statement dynamically
            columns = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]

            for field_name, sql_type in sql_schema.items():
                # Add UNIQUE constraint for SKU
                if field_name == "sku":
                    columns.append(f"{field_name} {sql_type} UNIQUE")
                # Add default timestamp for extracted_at
                elif field_name == "extracted_at":
                    columns.append(f"{field_name} TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                else:
                    columns.append(f"{field_name} {sql_type}")

            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS products (
                    {', '.join(columns)}
                )
            """

            cursor.execute(create_table_sql)

            # Create indexes for commonly searched fields
            index_fields = ["sku", "product_name", "wattage", "lifetime_hours", "application_area"]
            for field in index_fields:
                if field in sql_schema:
                    try:
                        cursor.execute(
                            f"CREATE INDEX IF NOT EXISTS idx_{field} ON products({field})"
                        )
                    except Exception as e:
                        logger.warning(f"Could not create index for {field}: {e}")

            conn.commit()
            logger.info(f"Database schema initialized dynamically at {self.db_path}")

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
                    product_name, sku, primary_product_number, wattage, voltage, current,
                    color_temperature, color_rendering_index, luminous_flux, beam_angle,
                    lifetime_hours, operating_temperature, dimensions, weight,
                    application_area, suitable_for, certifications, ip_rating,
                    full_description, source_pdf
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    product_data.get("product_name"),
                    product_data.get("sku"),
                    product_data.get("primary_product_number"),
                    product_data.get("wattage"),
                    product_data.get("voltage"),
                    product_data.get("current"),
                    product_data.get("color_temperature"),
                    product_data.get("color_rendering_index"),
                    product_data.get("luminous_flux"),
                    product_data.get("beam_angle"),
                    product_data.get("lifetime_hours"),
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

    def upsert_product(self, product_data: Dict[str, Any]) -> int:
        """Insert or update a product based on SKU and return the ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Convert lists to JSON strings
            suitable_for = str(product_data.get("suitable_for", []))
            certifications = str(product_data.get("certifications", []))

            # First try to get existing product by SKU
            cursor.execute("SELECT id FROM products WHERE sku = ?", (product_data.get("sku"),))
            existing = cursor.fetchone()

            if existing:
                # Update existing product
                product_id = existing[0]
                cursor.execute(
                    """
                    UPDATE products SET
                        product_name = ?, primary_product_number = ?, wattage = ?, voltage = ?, current = ?,
                        color_temperature = ?, color_rendering_index = ?, luminous_flux = ?, beam_angle = ?,
                        lifetime_hours = ?, operating_temperature = ?, dimensions = ?, weight = ?,
                        application_area = ?, suitable_for = ?, certifications = ?, ip_rating = ?,
                        full_description = ?, source_pdf = ?
                    WHERE sku = ?
                """,
                    (
                        product_data.get("product_name"),
                        product_data.get("primary_product_number"),
                        product_data.get("wattage"),
                        product_data.get("voltage"),
                        product_data.get("current"),
                        product_data.get("color_temperature"),
                        product_data.get("color_rendering_index"),
                        product_data.get("luminous_flux"),
                        product_data.get("beam_angle"),
                        product_data.get("lifetime_hours"),
                        product_data.get("operating_temperature"),
                        product_data.get("dimensions"),
                        product_data.get("weight"),
                        product_data.get("application_area"),
                        suitable_for,
                        certifications,
                        product_data.get("ip_rating"),
                        product_data.get("full_description"),
                        product_data.get("source_pdf"),
                        product_data.get("sku"),
                    ),
                )
                logger.info(f"Updated existing product with SKU: {product_data.get('sku')}")
            else:
                # Insert new product
                cursor.execute(
                    """
                    INSERT INTO products (
                        product_name, sku, primary_product_number, wattage, voltage, current,
                        color_temperature, color_rendering_index, luminous_flux, beam_angle,
                        lifetime_hours, operating_temperature, dimensions, weight,
                        application_area, suitable_for, certifications, ip_rating,
                        full_description, source_pdf
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        product_data.get("product_name"),
                        product_data.get("sku"),
                        product_data.get("primary_product_number"),
                        product_data.get("wattage"),
                        product_data.get("voltage"),
                        product_data.get("current"),
                        product_data.get("color_temperature"),
                        product_data.get("color_rendering_index"),
                        product_data.get("luminous_flux"),
                        product_data.get("beam_angle"),
                        product_data.get("lifetime_hours"),
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
                logger.info(f"Inserted new product with SKU: {product_data.get('sku')}")

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

            if filters.get("wattage_min"):
                conditions.append("wattage >= ?")
                params.append(filters["wattage_min"])

            if filters.get("wattage_max"):
                conditions.append("wattage <= ?")
                params.append(filters["wattage_max"])

            if filters.get("lifetime_hours_min"):
                conditions.append("lifetime_hours >= ?")
                params.append(filters["lifetime_hours_min"])

            if filters.get("lifetime_hours_max"):
                conditions.append("lifetime_hours <= ?")
                params.append(filters["lifetime_hours_max"])

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
            cursor.execute("SELECT * FROM products ORDER BY extracted_at DESC")
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

            cursor.execute("SELECT COUNT(*) FROM products WHERE wattage IS NOT NULL")
            products_with_wattage = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM products WHERE lifetime_hours IS NOT NULL")
            products_with_lifetime = cursor.fetchone()[0]

            # Calculate database size
            db_size_bytes = self.db_path.stat().st_size if self.db_path.exists() else 0
            db_size_mb = db_size_bytes / (1024 * 1024)

            return {
                "total_products": total_products,
                "total_pdfs": total_pdfs,
                "products_with_wattage": products_with_wattage,
                "products_with_lifetime": products_with_lifetime,
                "db_size_mb": db_size_mb,
            }
