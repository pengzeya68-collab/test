"""
Migration: Change global_variables unique constraint from (name) to (name, user_id)

SQLite doesn't support ALTER TABLE DROP CONSTRAINT, so we need to recreate the table.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "instance", "testmaster.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if the old unique constraint exists
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='global_variables'")
    table_sql = cursor.fetchone()
    if not table_sql:
        print("Table global_variables does not exist, skipping")
        conn.close()
        return

    print(f"Current table SQL: {table_sql[0]}")

    # Check if we already have the composite index
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_global_variables_name_user'")
    if cursor.fetchone():
        print("Composite index already exists, migration already done")
        conn.close()
        return

    # Step 1: Create new table with correct constraints
    cursor.execute("""
        CREATE TABLE global_variables_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            is_encrypted BOOLEAN DEFAULT 0,
            user_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Step 2: Copy data
    cursor.execute("INSERT INTO global_variables_new SELECT * FROM global_variables")

    # Step 3: Drop old table
    cursor.execute("DROP TABLE global_variables")

    # Step 4: Rename new table
    cursor.execute("ALTER TABLE global_variables_new RENAME TO global_variables")

    # Step 5: Create indexes
    cursor.execute("CREATE INDEX idx_global_variables_user_id ON global_variables(user_id)")
    cursor.execute("CREATE UNIQUE INDEX idx_global_variables_name_user ON global_variables(name, user_id)")

    conn.commit()

    # Verify
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='global_variables'")
    indexes = cursor.fetchall()
    print(f"New indexes: {[idx[0] for idx in indexes]}")

    cursor.execute("SELECT COUNT(*) FROM global_variables")
    count = cursor.fetchone()[0]
    print(f"Total rows: {count}")

    conn.close()
    print("Migration completed successfully")


if __name__ == "__main__":
    migrate()
