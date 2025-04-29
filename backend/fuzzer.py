import requests
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import time
import json
from collections import deque
import logging
import os
import asyncio
import uuid# need for db

# Configure  fuzzer logging
logging.basicConfig(level=logging.INFO)
scan_logger = logging.getLogger(__name__)

class Fuzzer:
    def __init__(self, output_filename='outputs_fuzzer/fuzz_results.json'):#place json file inside outputs folder
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
        self.project_name = None
        
        # Runtime data
        self.total_scan_time = 0.0
        self.rate_of_requests = 0.0
        self.scan_report = []
        self.report_file = output_filename
        self.number_of_payloads = 0
        self.is_running = True
        self.is_paused = False
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    def parse_auth_cookies(self, cookie_string):#parsing  cookie string in dictionary
        if not cookie_string:
            return {}

        cookies = {}
        for item in cookie_string.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookies[key] = value
        return cookies
#using request to test fuzzer functionality
    def send_request(self, url, payload, method):#Send request with payload and return response details
        try:
            headers = {'User-Agent': 'TRACE Fuzzer 1.0'}
            if not url.startswith(('http://', 'https://')):#check URL 
                url = 'https://' + url
            if method == 'GET':
            
                if 'FUZZ' in url:
                    fuzz_url = url.replace('FUZZ', payload)
                else:
                    separator = '&' if '?' in url else '?'
                    fuzz_url = f"{url}{separator}fuzz={payload}"
                response = requests.get(
                    fuzz_url,
                    cookies=self.auth_cookies,
                    proxies={'http': self.network_proxy, 'https': self.network_proxy} if self.network_proxy else None,
                    timeout=5,
                    headers=headers
                )

            elif method == 'POST':
                data = {param: payload for param in self.custom_params} if self.custom_params else {'fuzz': payload}
                response = requests.post(
                    url,
                    data=data,
                    cookies=self.auth_cookies,
                    proxies={'http': self.network_proxy, 'https': self.network_proxy} if self.network_proxy else None,
                    timeout=5,
                    headers=headers
                )

            elif method == 'PUT':
                data = {param: payload for param in self.custom_params} if self.custom_params else {'fuzz': payload}
                response = requests.put(
                    url,
                    data=data,
                    cookies=self.auth_cookies,
                    proxies={'http': self.network_proxy, 'https': self.network_proxy} if self.network_proxy else None,
                    timeout=5,
                    headers=headers
                )

            content = response.text
            lines = content.count('\n')
            words = len(content.split())
            chars = len(content)

            return {
                'status_code': response.status_code,
                'lines': lines,
                'words': words,
                'chars': chars,
                'length': len(response.content),
                'error': False
            }

        except requests.RequestException as e:
            scan_logger.error(f"Req error: {e}")
            return {
                'status_code': 0,
                'lines': 0,
                'words': 0,
                'chars': 0,
                'length': 0,
                'error': True
            }

    def display_fuzzer_results(self, result):#check status then display 
        if self.exclude_status_codes and result['status_code'] in self.exclude_status_codes:
            return False

        if self.include_status_codes and result['status_code'] not in self.include_status_codes:
            return False
        if self.content_length_filter is not None:
            if result['length'] != self.content_length_filter:
                
                return False
        return True

    def save_report_to_json(self):#Save results to JSON file for now . might have to be CSV
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.report_file), exist_ok=True)
            
            with open(self.report_file, 'w') as json_file:
                json.dump(self.scan_report, json_file, indent=4)
                
            scan_logger.info(f"Successfully saved results to {self.report_file}")
            return True
        except Exception as e:
            scan_logger.error(f"Error saving as JSON file: {e}")
            return False
            
    def stop_scan(self):
        self.is_running = False
        scan_logger.info("Scan stopping requested")

    def pause_scan(self):
        self.is_paused = True
        scan_logger.info("Scan paused")

    def resume_scan(self):
        self.is_paused = False
        scan_logger.info("Scan resumed")
        
    async def submit_to_database(self):#send to db
        if not self.project_name:
            scan_logger.warning("No project name ")
            return False
            
        try:
            # Preparget the data type for submission to the project database
            for entry in self.scan_report:
                if 'type' not in entry:
                    entry['type'] = 'fuzzer'
                    
            # Submit data to database endpoint
            api_url = f"/submit_results/fuzzer/{self.project_name}"
            
            headers = {'Content-Type': 'application/json'}
            
            try:
                response = requests.post(
                    api_url,
                    json=self.scan_report,
                    headers=headers
                )
                
                if response.status_code == 200:
                    scan_logger.info(f"Success: {self.project_name}")
                    return True
                else:
                    scan_logger.error(f"Failed: {response.status_code}")
                    scan_logger.error(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                scan_logger.error(f"Error: {e}")
                return False
                
        except Exception as e:
            scan_logger.error(f"Error {e}")
            return False

    async def run_scan(self, scan_parameters):#start fuzzer with user inputs params
        self.configure_scan_parameters(scan_parameters)
        if not self.payloads:# if empty this will be default 
            self.payloads = ['test', 'admin', 'password', '123456']
        self.number_of_payloads = len(self.payloads)
        self.is_running = True
        self.is_paused = False
        
        # Get project name from parameters if available
        self.project_name = scan_parameters.get('project_name')

        start = time.time()
        processed_requests = 0
        filtered_requests = 0

        for i, payload in enumerate(self.payloads):
            # Check if scan should stop
            if not self.is_running:
                scan_logger.info("Scan stopped by user")
                break
                
            # Check if scan is paused
            while self.is_paused:
                await asyncio.sleep(0.5)  # Sleep while paused
                if not self.is_running:  # Allow stopping while paused
                    break
                    
            result = self.send_request(self.scan_target, payload, self.request_method)
            processed_requests += 1

            result_entry = {# Add payload and result info
                'id': i + 1,
                'response': result['status_code'],
                'lines': result['lines'],
                'words': result['words'],
                'chars': result['chars'],
                'payload': payload,
                'length': result['length'],
                'error': result['error'],
                'url': self.scan_target  # Add URL for database context
            }

            if self.display_fuzzer_results(result):
                self.scan_report.append(result_entry)
                filtered_requests += 1

            # calc progress and also the stats
            elapsed = time.time() - start
            requests_per_second = processed_requests / elapsed if elapsed > 0 else 0

            # Create the update object to yield this.
            update = {
                "progress": (i + 1) / self.number_of_payloads,
                "processed_requests": processed_requests,
                "filtered_requests": filtered_requests,
                "requests_per_second": round(requests_per_second, 2)
            }
            if self.display_results_live:#reuslts display must be true then display
                update.update(result_entry)

            yield update

        if not self.display_results_live:
            for result in self.scan_report:
                yield result#sent resutls 

        end = time.time()
        self.total_scan_time = end - start
        self.rate_of_requests = round(processed_requests / self.total_scan_time, 2) if self.total_scan_time > 0 else 0
        
        # Save results to JSON file
        saved = self.save_report_to_json()
        if saved:
            scan_logger.info(f"Scan completed in {self.total_scan_time:.2f} seconds. Results saved to {self.report_file}")
            
            # If project name is provided, submit to database
            if self.project_name:
                try:
                    db_success = await self.submit_to_database()
                    if db_success:
                        yield {"status": "success", "message": f"Results submitted to project: {self.project_name}"}
                    else:
                        yield {"status": "warning", "message": "Failed to submit results to database"}
                except Exception as e:
                    scan_logger.error(f"Error submitting to database: {e}")
                    yield {"status": "error", "message": f"Database error: {str(e)}"}
        else:
            scan_logger.error("Failed to save scan results")
            yield {"status": "error", "message": "Failed to save scan results"}

    def configure_scan_parameters(self, scan_params):
        self.scan_target = scan_params.get('target_url', '')
        
        # Get project name if available
        self.project_name = scan_params.get('project_name')

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