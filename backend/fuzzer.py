import requests
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import time
import json
from collections import deque
import logging
import os
import asyncio

from http_tester import send_http_request

# Configure fuzzer logging
logging.basicConfig(level=logging.INFO)
scan_logger = logging.getLogger(__name__)

class Fuzzer:
    def __init__(self, json_filename='fuzz_results.json'):
        self.scan_target = ''
        self.payloads = []
        self.auth_cookies = {}
        self.exclude_status_codes = []
        self.include_status_codes = []
        self.request_method = 'GET'
        self.content_length_filter = None
        self.network_proxy = ''
        self.custom_params = {}
        self.display_results_live = False
        # Runtime data
        self.total_scan_time = 0.0
        self.rate_of_requests = 0.0
        self.scan_report = []
        self.json_filename = json_filename  # Changed to match crawler style
        self.number_of_payloads = 0
        # Control flags for pause and stop functionality
        self.stop_flag = False
        self.pause_flag = False

    def parse_auth_cookies(self, cookie_string):
        if not cookie_string:
            return {}

        cookies = {}
        for item in cookie_string.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookies[key] = value
        return cookies
    
    def send_request(self, url, payload, method):
        try:
            # Ensure URL has proper format
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url  # Changed to http as the external client uses port 80
                
            # Construct the URL with the payload
            if method == 'GET':
                if 'FUZZ' in url:
                    fuzz_url = url.replace('FUZZ', payload)
                else:
                    separator = '&' if '?' in url else '?'
                    fuzz_url = f"{url}{separator}fuzz={payload}"
            else:
                fuzz_url = url
                
            # Prepare headers
            headers = {'User-Agent': 'TRACE Fuzzer 1.0'}
            
            # Prepare cookies if needed
            if self.auth_cookies:
                headers['Cookie'] = "; ".join([f"{k}={v}" for k, v in self.auth_cookies.items()])
                
            # For POST/PUT, prepare the body
            body = None
            if method in ['POST', 'PUT']:
                if self.custom_params:
                    # Format as form data
                    body = "&".join([f"{param}={payload}" for param in self.custom_params])
                else:
                    body = f"fuzz={payload}"
                    
            # Call HTTP client
            response_data = send_http_request(
                url=fuzz_url, 
                method=method,
                headers=headers,
                body=body
            )
            
            # Parse the response based on its format
            if isinstance(response_data, dict):
                status_code = response_data.get("status_code", 0)
                content = response_data.get("body", "")
            else:
                status_code = 200  # Default
                content = response_data
                
                # Extract status code from raw HTTP response
                if isinstance(content, str) and "HTTP/" in content:
                    status_line = content.split('\n')[0]
                    try:
                        status_code = int(status_line.split()[1])
                    except (IndexError, ValueError) as e:
                        scan_logger.warning(f"Could not parse status code: {e}")
                
                # Extract body from raw HTTP response
                if isinstance(content, str) and "\r\n\r\n" in content:
                    content = content.split("\r\n\r\n", 1)[1]
                    
            # Process response content
            lines = content.count('\n')
            words = len(content.split())
            chars = len(content)
            
            return {
                'url_used': fuzz_url,
                'status_code': status_code,
                'lines': lines,
                'words': words,
                'chars': chars,
                'length': len(content.encode('utf-8', errors='ignore')),
                'error': False
            }
            
        except Exception as e:
            scan_logger.error(f"Request error: {e}")
            return {
                'url_used': url if 'fuzz_url' not in locals() else fuzz_url,
                'status_code': 0,
                'lines': 0,
                'words': 0,
                'chars': 0,
                'length': 0,
                'error': True
            }

    def display_fuzzer_results(self, result):
        if self.exclude_status_codes and result['status_code'] in self.exclude_status_codes:
            return False

        if self.include_status_codes and result['status_code'] not in self.include_status_codes:
            return False
        if self.content_length_filter is not None:
            if result['length'] != self.content_length_filter:
                return False
        return True

    # New method to replace save_report_to_json
    def save_json(self):
        try:
            file_path = os.path.join("outputs_fuzzer", self.json_filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as json_file:
                fuzz_data = []
                for index, entry in enumerate(self.scan_report, start=1):
                    # Format entries to match crawler structure for consistency in database
                    fuzz_data.append({
                        'id': index,
                        'url': entry['url'],
                        'title': f"Payload: {entry['payload']}",  # Use payload as title
                        'word_count': entry['words'],
                        'char_count': entry['chars'],
                        'link_count': 0,  # Not applicable for fuzzer
                        'error': entry['error'],
                        'severity': self.calculate_severity(entry['response'])
                    })
                json.dump(fuzz_data, json_file, indent=4)
            scan_logger.info(f"Results saved to {file_path}")
        except Exception as e:
            scan_logger.error(f"Error saving JSON: {e}")

    def calculate_severity(self, status):
        # Match crawler's severity calculation for consistency
        if status < 100 or status >= 600:
            return "Unknown"
        elif status >= 100 and status < 200:
            return "Info"
        elif status >= 200 and status < 300:
            return "Low"
        elif status >= 300 and status < 400:
            return "Medium"
        else:
            return "High"

    # Control methods
    def stop_scan(self):
        scan_logger.info("Stopping scan requested")
        self.stop_flag = True

    def pause_scan(self):
        scan_logger.info("Pausing scan requested")
        self.pause_flag = True

    def resume_scan(self):
        scan_logger.info("Resuming scan requested")
        self.pause_flag = False

    async def run_scan(self, scan_parameters):
        self.configure_scan_parameters(scan_parameters)
        if not self.payloads:
            self.payloads = ['test', 'admin', 'password', '123456']
        self.number_of_payloads = len(self.payloads)
        
        # Reset control flags at the start of a new scan
        self.stop_flag = False
        self.pause_flag = False

        start = time.time()
        processed_requests = 0
        filtered_requests = 0

        for i, payload in enumerate(self.payloads):
            # Check if stop was requested
            if self.stop_flag:
                scan_logger.info("Scan stopped by user request")
                break
            # Check if pause was requested and wait if needed
            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
            while self.pause_flag:
                await asyncio.sleep(0.5)  # Wait while paused
                if self.stop_flag:  # Check if stop was requested while paused
                    break

            result = self.send_request(self.scan_target, payload, self.request_method)
            processed_requests += 1

            result_entry = {
                'id': i + 1,
                'url': result['url_used'],
                'response': result['status_code'],
                'lines': result['lines'],
                'words': result['words'],
                'chars': result['chars'],
                'payload': payload,
                'length': result['length'],
                'error': result['error']
            }

            if self.display_fuzzer_results(result):
                self.scan_report.append(result_entry)
                filtered_requests += 1

            # Calculate progress and stats
            elapsed = time.time() - start
            requests_per_second = processed_requests / elapsed if elapsed > 0 else 0

            # Create the update object to yield
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
        self.rate_of_requests = round(processed_requests / self.total_scan_time, 2) if self.total_scan_time > 0 else 0
        # Use the new method to save results in crawler-compatible format
        self.save_json()

    def configure_scan_parameters(self, scan_params):
        self.scan_target = scan_params.get('target_url', '')

        # Handling word list possibilities - file path, list of strings, or comma-separated string
        if 'word_list' in scan_params and scan_params['word_list']:
            word_list_param = scan_params['word_list']
            scan_logger.info(f"Processing wordlist parameter: {word_list_param}")
            
            if isinstance(word_list_param, list):
                self.payloads = word_list_param
                scan_logger.info(f"Using list of {len(self.payloads)} payloads")
            elif isinstance(word_list_param, str):
                # Check if it's a file path, particularly from file upload
                if (word_list_param.startswith('./wordlist_uploads/') or 
                    word_list_param.startswith('wordlist_uploads/') or 
                    os.path.exists(word_list_param)):
                    try:
                        with open(word_list_param, 'r') as file:
                            self.payloads = [line.strip() for line in file if line.strip()]
                        scan_logger.info(f"Loaded {len(self.payloads)} payloads from file: {word_list_param}")
                    except Exception as e:
                        scan_logger.error(f"Error reading wordlist file: {e}")
                        self.payloads = [word_list_param]  # Use as single item if error occurs
                elif ',' in word_list_param:
                    # comma-separated list
                    self.payloads = [word.strip() for word in word_list_param.split(',')]
                    scan_logger.info(f"Using comma-separated list of {len(self.payloads)} payloads")
                elif '\n' in word_list_param:
                    # newline separated list
                    self.payloads = [word.strip() for word in word_list_param.split('\n') if word.strip()]
                    scan_logger.info(f"Using newline-separated list of {len(self.payloads)} payloads")
                else:
                    # Look for the file again with different path formats
                    possible_paths = [
                        word_list_param,
                        f"./wordlist_uploads/{word_list_param}",
                        f"wordlist_uploads/{word_list_param}",
                        f"./{word_list_param}"
                    ]
                    
                    file_found = False
                    for path in possible_paths:
                        if os.path.exists(path):
                            try:
                                with open(path, 'r') as file:
                                    self.payloads = [line.strip() for line in file if line.strip()]
                                scan_logger.info(f"Loaded {len(self.payloads)} payloads from alternate path: {path}")
                                file_found = True
                                break
                            except Exception as e:
                                scan_logger.error(f"Error reading wordlist at path {path}: {e}")
                    
                    if not file_found:
                        # Single item
                        self.payloads = [word_list_param]
                        scan_logger.info(f"Using single payload: {word_list_param}")

        # Parse cookies from string
        if 'cookies' in scan_params and scan_params['cookies']:
            self.auth_cookies = self.parse_auth_cookies(scan_params['cookies'])

        # Handle status code
        if 'hide_status' in scan_params and scan_params['hide_status']:
            try:
                self.exclude_status_codes = [int(code.strip()) for code in scan_params['hide_status'].split(',') if code.strip()]
            except ValueError:
                scan_logger.warning("Invalid hide_status format. Expected comma-separated integers.")

        if 'show_status' in scan_params and scan_params['show_status']:
            try:
                self.include_status_codes = [int(code.strip()) for code in scan_params['show_status'].split(',') if code.strip()]
            except ValueError:
                scan_logger.warning("Invalid show_status format. Expected comma-separated integers.")

        #HTTP method
        if 'http_method' in scan_params and scan_params['http_method'] in ['GET', 'POST', 'PUT']:
            self.request_method = scan_params['http_method']

        # Set content length filter
        if 'filter_by_content_length' in scan_params and scan_params['filter_by_content_length']:
            try:
                self.content_length_filter = int(scan_params['filter_by_content_length'])
            except ValueError:
                scan_logger.warning("Invalid filter_by_content_length format. Expected integer.")

        # Set the proxy
        if 'proxy' in scan_params and scan_params['proxy']:
            self.network_proxy = scan_params['proxy']

        # Set show results option
        if 'show_results' in scan_params:
            self.display_results_live = scan_params.get('show_results', True)

        # Setting additional parameters
        if 'additional_parameters' in scan_params and scan_params['additional_parameters']:
            if isinstance(scan_params['additional_parameters'], dict):
                self.custom_params = scan_params['additional_parameters']
            elif isinstance(scan_params['additional_parameters'], str):
                try:
                    self.custom_params = dict(item.split('=') for item in scan_params['additional_parameters'].split('&') if '=' in item)
                except:
                    scan_logger.warning("Invalid additional_parameters format. Expected param1=value1&param2=value2")