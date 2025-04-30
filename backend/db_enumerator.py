import mysql.connector
from typing import List, Dict, Any
import json
 
class DBEnumerator:
    def __init__(self):
        self.tableNames: List[str] = []
        self.columnNames: List[str] = []
        self.table: Dict[str, Dict[str, Any]] = {}
        self.connection = None
        self.cursor = None
 
    def connect(self, host: str, port: int, user: str, password: str, database: str) -> bool:
        try:
            self.connection = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.connection.cursor()
            print("[+] Connected to MySQL.")
            return True
        except mysql.connector.Error as e:
            print(f"[!] Connection failed: {e}")
            return False
 
    def enumerate_database(self) -> None:
        if not self.connection or not self.cursor:
            print("[!] No active DB connection.")
            return
        self.enumerate_tables()
        self.enumerate_columns()
 
    def enumerate_tables(self) -> None:
        self.cursor.execute("SHOW TABLES")
        tables = self.cursor.fetchall()
        self.tableNames = [table[0] for table in tables]
        self.table = {table: {} for table in self.tableNames}
 
    def enumerate_columns(self) -> None:
        self.columnNames.clear()
        for table in self.tableNames:
            self.cursor.execute(f"SHOW COLUMNS FROM `{table}`")
            columns = self.cursor.fetchall()
            column_names = [col[0] for col in columns]
            self.columnNames.extend(column_names)
            self.table[table]['columns'] = column_names
 
    def process_response(self) -> Dict[str, Any]:
        return {
            'table_count': len(self.tableNames),
            'tables': self.table
        }
 
    def save_results(self, filename: str = "db_enum_results.json") -> None:
        with open(filename, 'w') as f:
            json.dump(self.process_response(), f, indent=4)
 
    def display_results(self) -> None:
        results = self.process_response()
        print(f"Total Tables: {results['table_count']}")
        for table, info in results["tables"].items():
            print(f"\nTable: {table}")
            print("Columns:", ", ".join(info["columns"]))
 
    def reset(self) -> None:
        self.tableNames.clear()
        self.columnNames.clear()
        self.table.clear()
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
 
    def __del__(self):
        self.reset()