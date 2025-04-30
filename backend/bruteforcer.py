import time
import json
import os
import logging
from urllib.parse import urljoin, urlparse, urlunparse, parse_qs, urlencode
from http_tester import send_http_request  # Importing from http_tester.py
from proxy_logic import handle_proxy_request  # Importing from proxy_logic.py
import asyncio


# Configure BruteForcer logging
logging.basicConfig(level=logging.INFO)
scan_logger = logging.getLogger(__name__)

class BruteForcer:
    def __init__(self, output_filename='outputs_bruteforcer/brute_force_results.json'):
        self.target_url = ''
        self.wordlist = []
        self.auth_cookies = {}
        self.exclude_status_codes = []
        self.include_status_codes = []
        self.content_length_filter = None
        self.network_proxy = ''
        self.custom_params = {}
        self.display_results_live = True

        # Runtime data
        self.total_scan_time = 0.0
        self.scan_report = []
        self.report_file = output_filename
        self.number_of_payloads = 0

        # Control flags for pause and stop functionality
        self.stop_flag = False
        self.pause_flag = False

    def send_request(self, url, payload):
        """Send the request to check directory existence and return response details."""
        try:
            headers = {'User-Agent': 'BruteForcer 1.0'}

            # 1) Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # 2) Build path + payload
            p = urlparse(url)
            # ensure no double-slash
            new_path = p.path.rstrip('/') + '/' + payload
            p = p._replace(path=new_path)

            # 3) Merge in any additional_parameters into the query string
            if self.custom_params:
                # parse existing query into dict of lists
                qs = parse_qs(p.query, keep_blank_values=True)
                # override/add your custom_params
                for k, v in self.custom_params.items():
                    qs[k] = [v]
                # re-encode back to a query-string
                p = p._replace(query=urlencode(qs, doseq=True))

            # 4) Get the final URL
            full_url = urlunparse(p)
            scan_logger.info(f"Attempting: {full_url}")

            # 5) Send via proxy or direct
            if self.network_proxy:
                result = handle_proxy_request(full_url, 'GET')
            else:
                result = send_http_request(full_url, 'GET')

            # 6) Parse the response
            content = result['body']
            status_code = result['status_code']
            lines = content.count('\n')
            words = len(content.split())
            chars = len(content)

            return {
                'url': full_url,
                'status_code': status_code,
                'lines': lines,
                'words': words,
                'chars': chars,
                'length': len(content),
                'error': False
            }

        except Exception as e:
            scan_logger.error(f"Request error for payload '{payload}': {e}")
            return {
                'url': full_url if 'full_url' in locals() else f"{url}/{payload}",
                'status_code': 0,
                'lines': 0,
                'words': 0,
                'chars': 0,
                'length': 0,
                'error': True
            }

    def display_bruteforce_results(self, result):
        """Return True if this result should be shown, False if filtered out."""
        code = result['status_code']
        length = result['length']

        # 1) hide_status
        if code in self.exclude_status_codes:
            return False

        # 2) show_status (if specified, only these codes pass)
        if self.include_status_codes and code not in self.include_status_codes:
            return False

        # 3) content-length range
        if self.content_length_filter is not None:
            mn, mx = self.content_length_filter
            if not (mn <= length <= mx):
                return False

        return True

    def save_report_to_json(self):
        """Save the results to a JSON file."""
        try:
            with open(self.report_file, 'w') as json_file:
                json.dump(self.scan_report, json_file, indent=4)
        except Exception as e:
            scan_logger.error(f"Error saving results as JSON file: {e}")

    async def run_scan(self, scan_parameters):
        """Run the brute force scan with user-provided parameters."""
        self.configure_scan_parameters(scan_parameters)
        
        # 🧪 Log parameters
        print("🧪 Target URL:", self.target_url)
        print("🧪 Wordlist loaded:", self.wordlist)

        if not self.wordlist:
            self.wordlist = ['admin', 'test', 'password', 'backup', 'config']

        # Reset control flags at the start of a new scan
        self.stop_flag = False
        self.pause_flag = False

        self.number_of_payloads = len(self.wordlist)
        start = time.time()
        processed_requests = 0
        filtered_requests = 0

        for i, payload in enumerate(self.wordlist):
            # Check if stop was requested
            if self.stop_flag:
                scan_logger.info("Scan stopped by user request")
                break
            # Check if pause was requested and wait if needed
            if i>0:
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                while self.pause_flag:
                    await asyncio.sleep(0.5)  # Wait while paused
                    if self.stop_flag:  # Check if stop was requested while paused
                        break

            result = self.send_request(self.target_url, payload)
            processed_requests += 1

            result_entry = {
                'id': i + 1,
                'url': result['url'], 
                'response': result['status_code'],
                'lines': result['lines'],
                'words': result['words'],
                'chars': result['chars'],
                'payload': payload,
                'length': result['length'],
                'error': result['error']
            }

            if self.display_bruteforce_results(result):
                self.scan_report.append(result_entry)
                filtered_requests += 1

            # Calculate progress and statistics
            elapsed = time.time() - start
            requests_per_second = processed_requests / elapsed if elapsed > 0 else 0

            update = {
                "progress": (i + 1) / self.number_of_payloads,
                "processed_requests": processed_requests,
                "filtered_requests": filtered_requests,
                "requests_per_second": round(requests_per_second, 2)
            }

            if self.display_results_live:
                # only show matching entries as they happen
                if self.display_bruteforce_results(result):
                    update.update(result_entry)
                    yield update
            else:
                # if not live, keep dumping the summary each iteration
                yield update

        if not self.display_results_live:
            for result in self.scan_report:
                yield result

        end = time.time()
        self.total_scan_time = end - start
        self.save_report_to_json()

    def configure_scan_parameters(self, scan_params):
        """Configure scan parameters from user input."""
        # 1) Target URL
        self.target_url = scan_params.get('target_url', '')

        # 2) Wordlist: either a file path, a list, or a single string
        word_list_param = scan_params.get('word_list', [])
        if isinstance(word_list_param, str) and os.path.exists(word_list_param):
            # load from file
            with open(word_list_param, 'r') as f:
                self.wordlist = [line.strip() for line in f if line.strip()]
        elif isinstance(word_list_param, list):
            self.wordlist = word_list_param
        elif isinstance(word_list_param, str) and word_list_param:
            self.wordlist = [word_list_param]
        else:
            self.wordlist = []

        # 3) hide_status ⇒ exclude_status_codes
        hide = scan_params.get('hide_status', [])
        if isinstance(hide, list):
            self.exclude_status_codes = hide
        elif isinstance(hide, str) and hide.strip():
            self.exclude_status_codes = [
                int(code) for code in hide.split(',') if code.strip().isdigit()
            ]
        else:
            self.exclude_status_codes = []

        # 4) show_status ⇒ include_status_codes
        show = scan_params.get('show_status', [])
        if isinstance(show, list):
            self.include_status_codes = show
        elif isinstance(show, str) and show.strip():
            self.include_status_codes = [
                int(code) for code in show.split(',') if code.strip().isdigit()
            ]
        else:
            self.include_status_codes = []

        # 5) Content-length filter
        fl = scan_params.get("filter_by_content_length")
        if isinstance(fl, int):
            # treat a lone integer as "minimum only"
            self.content_length_filter = (fl, float("inf"))
        elif isinstance(fl, str) and fl.strip():
            mn, mx = None, None
            for part in fl.split(","):
                part = part.strip()
                if part.startswith(">"):
                    try:
                        mn = int(part[1:]) + 1
                    except ValueError:
                        pass
                elif part.startswith("<"):
                    try:
                        mx = int(part[1:]) - 1
                    except ValueError:
                        pass
                elif part.isdigit():
                    mn = mx = int(part)
            # default bounds
            if mn is None: mn = 0
            if mx is None: mx = float("inf")
            self.content_length_filter = (mn, mx)
        else:
            self.content_length_filter = None

        # 6) Proxy and extra params
        self.network_proxy = scan_params.get('proxy', '') or self.network_proxy
        # Parse additional_parameters as URL query-string
        raw = scan_params.get('additional_param', '')
        parsed = parse_qs(raw, keep_blank_values=False)
        self.custom_params = {k: v[0] for k, v in parsed.items()}

        # 7) Live updates flag
        self.display_results_live = scan_params.get('show_results', True)

    # Add methods for stopping, pausing, and resuming scans
    def stop_scan(self):
        scan_logger.info("Stopping scan requested")
        self.stop_flag = True

    def pause_scan(self):
        scan_logger.info("Pausing scan requested")
        self.pause_flag = True

    def resume_scan(self):
        scan_logger.info("Resuming scan requested")
        self.pause_flag = False