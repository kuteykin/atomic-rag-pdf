"""
Simple test script for querying and inspecting the product.db SQLite database
"""
import sqlite3
import os

DB_PATH = "storage/products.db"

def connect_db():
    """Connect to the SQLite database"""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return None

    print(f"✓ Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    return conn

def inspect_schema(conn):
    """Inspect database schema - tables and their structure"""
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("\n" + "="*60)
    print("DATABASE SCHEMA")
    print("="*60)

    for table in tables:
        table_name = table[0]
        print(f"\n📋 Table: {table_name}")
        print("-" * 60)

        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        print(f"{'Column':<20} {'Type':<15} {'NotNull':<8} {'Default':<10} {'PK'}")
        print("-" * 60)
        for col in columns:
            col_id, name, col_type, not_null, default_val, pk = col
            print(f"{name:<20} {col_type:<15} {not_null:<8} {str(default_val):<10} {pk}")

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"\nTotal rows: {count}")

        # Show first 3 rows as sample
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()
            print(f"\nSample data (first 3 rows):")
            for i, row in enumerate(rows, 1):
                print(f"  Row {i}: {row}")

def test_exact_search(conn):
    """Test exact search queries"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("TESTING EXACT SEARCH")
    print("="*60)

    # First, get table names to determine which table to search
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        print("❌ No tables found in database")
        return

    # Assume the main table is the first one or look for common names
    table_name = tables[0][0]
    print(f"\n🔍 Testing searches on table: {table_name}")

    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    # Get a sample value to test exact search
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
    sample_row = cursor.fetchone()

    if not sample_row:
        print("❌ No data in table to test")
        return

    print(f"\nColumns: {column_names}")
    print(f"Sample row: {sample_row}")

    # Test exact match on first text column
    for i, (col_name, value) in enumerate(zip(column_names, sample_row)):
        if value and isinstance(value, str):
            print(f"\n--- Test {i+1}: Exact match on column '{col_name}' ---")
            print(f"Searching for exact value: '{value}'")

            # Test exact match with =
            query = f"SELECT * FROM {table_name} WHERE {col_name} = ?"
            cursor.execute(query, (value,))
            results = cursor.fetchall()
            print(f"Query: {query}")
            print(f"Results found: {len(results)}")
            if results:
                print(f"First result: {results[0]}")

            # Test with LIKE
            query_like = f"SELECT * FROM {table_name} WHERE {col_name} LIKE ?"
            cursor.execute(query_like, (value,))
            results_like = cursor.fetchall()
            print(f"\nQuery with LIKE: {query_like}")
            print(f"Results found: {len(results_like)}")

            # Test case sensitivity
            if value != value.lower():
                query_case = f"SELECT * FROM {table_name} WHERE {col_name} = ?"
                cursor.execute(query_case, (value.lower(),))
                results_case = cursor.fetchall()
                print(f"\nTesting case sensitivity (lowercase): {len(results_case)} results")

            break  # Only test first text column

def custom_query(conn):
    """Allow custom SQL queries"""
    print("\n" + "="*60)
    print("CUSTOM QUERY MODE")
    print("="*60)
    print("Enter SQL queries (or 'exit' to quit):")

    cursor = conn.cursor()

    while True:
        query = input("\nSQL> ").strip()

        if query.lower() in ['exit', 'quit', 'q']:
            break

        if not query:
            continue

        try:
            cursor.execute(query)

            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                print(f"\nResults: {len(results)} rows")
                for i, row in enumerate(results[:10], 1):  # Show first 10
                    print(f"  {i}: {row}")
                if len(results) > 10:
                    print(f"  ... and {len(results) - 10} more rows")
            else:
                conn.commit()
                print(f"✓ Query executed successfully")

        except sqlite3.Error as e:
            print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("="*60)
    print("SQLite Database Inspector & Query Tester")
    print("="*60)

    conn = connect_db()
    if not conn:
        return

    try:
        # Inspect schema
        inspect_schema(conn)

        # Test exact search
        test_exact_search(conn)

        # Custom query mode (optional)
        print("\n" + "="*60)
        response = input("Would you like to run custom queries? (y/n): ").strip().lower()
        if response == 'y':
            custom_query(conn)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()
