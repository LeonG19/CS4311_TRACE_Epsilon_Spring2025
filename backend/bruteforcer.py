import time
import json
import os
import logging
from urllib.parse import urljoin, urlparse, urlunparse
from http_tester import send_http_request  # Importing from http_tester.py
from proxy_logic import handle_proxy_request  # Importing from proxy_logic.py

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
        self.display_results_live = False

        # Runtime data
        self.total_scan_time = 0.0
        self.scan_report = []
        self.report_file = output_filename
        self.number_of_payloads = 0

    def send_request(self, url, payload):
        """Send the request to check directory existence and return response details."""
        try:
            headers = {'User-Agent': 'BruteForcer 1.0'}
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            parsed_url = urlparse(url)
            brute_force_url = parsed_url._replace(path=parsed_url.path + '/' + payload)
            full_url = urlunparse(brute_force_url)

            scan_logger.info(f"Attempting: {full_url}")

            # Use proxy if specified, otherwise use direct request
            if self.network_proxy:
                result = handle_proxy_request(full_url, 'GET')  # Proxy request logic
            else:
                result = send_http_request(full_url, 'GET')  # Direct HTTP request using http_tester.py

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
        """Check if results should be displayed based on the status code filters."""
        if self.exclude_status_codes and result['status_code'] in self.exclude_status_codes:
            return False

        if self.include_status_codes and result['status_code'] not in self.include_status_codes:
            return False

        if self.content_length_filter is not None and result['length'] != self.content_length_filter:
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
        if not self.wordlist:
            self.wordlist = ['admin', 'test', 'password', 'backup', 'config']

        self.number_of_payloads = len(self.wordlist)
        start = time.time()
        processed_requests = 0
        filtered_requests = 0

        for i, payload in enumerate(self.wordlist):
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
                update.update(result_entry)

            yield update

        if not self.display_results_live:
            for result in self.scan_report:
                yield result

        end = time.time()
        self.total_scan_time = end - start
        self.save_report_to_json()

    def configure_scan_parameters(self, scan_params):
        """Configure scan parameters from user input."""
        self.target_url = scan_params.get('target_url', '')

        # Handle word list (file or list of strings)
        word_list_param = scan_params.get('word_list', [])
        if isinstance(word_list_param, list):
            self.wordlist = word_list_param
        elif isinstance(word_list_param, str):
            if os.path.exists(word_list_param):
                try:
                    with open(word_list_param, 'r') as file:
                        self.wordlist = [line.strip() for line in file if line.strip()]
                except Exception as e:
                    scan_logger.error(f"Error reading wordlist file: {e}")
            else:
                self.wordlist = [word_list_param]

        # Parse status codes for filtering, with defaults
        self.exclude_status_codes = []
        self.include_status_codes = []

        # If 'hide_status' is provided, parse it, otherwise leave it empty
        if 'hide_status' in scan_params and scan_params['hide_status']:
            self.exclude_status_codes = [int(code.strip()) for code in scan_params['hide_status'].split(',') if code.strip()]

        # If 'show_status' is provided, parse it, otherwise leave it empty
        if 'show_status' in scan_params and scan_params['show_status']:
            self.include_status_codes = [int(code.strip()) for code in scan_params['show_status'].split(',') if code.strip()]

        # Content length filter
        if 'filter_by_content_length' in scan_params and scan_params['filter_by_content_length']:
            try:
                self.content_length_filter = int(scan_params['filter_by_content_length'])
            except ValueError:
                scan_logger.warning("Invalid content length filter format. Expected integer.")

        # Proxy settings
        if 'proxy' in scan_params and scan_params['proxy']:
            self.network_proxy = scan_params['proxy']

        # Display results live
        self.display_results_live = scan_params.get('show_results', True)