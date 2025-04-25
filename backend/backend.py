from fastapi import FastAPI, File, UploadFile, Form,  HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, Field
from DB_projects.ProjectManager import ProjectManager
from crawler import Crawler
from typing import List, Optional
import logging
from fastapi.responses import StreamingResponse
import json
from fuzzer import Fuzzer
from bruteforcer import BruteForcer
import os
import shutil
import requests
import neo4j.time
import mdp3
from mdp3 import CredentialGeneratorMDP, WebScraper, CredentialMDP
from typing import Dict, Optional
import json
import csv
import sys
import json
csv.field_size_limit(2**31-1)# logs whenever an endpoint is hit using logger.info
CRAWL_RESULTS_PATH = 'outputs_crawler/crawl_results.json'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("asyncio")

# creates endpoints
app = FastAPI(title="Routes")

# params for crawler (optionals for optional params,
# both int | str in case they type into box and then delete input, prevents error and request goes through)
# note, with this set up, all inputs become strings, will handle in crawler process
class CrawlRequest(BaseModel):
    url: str
    depth: Optional[int | str] = ''
    max_pages: Optional[int | str] = ''
    user_agent: str = ''
    delay: Optional[str | int] = ''
    proxy: str = ''

crawler = None
'''
 for now basically just launches the crawl based on the form submitted by the user
'''
@app.post("/crawler")
async def launchCrawl(request: CrawlRequest):
    global crawler
    crawler = Crawler()
    params_dict = request.model_dump()
    logger.info(request)
    
    async def crawl_stream():
        try:
            async for update in crawler.start_crawl(params_dict):
                yield json.dumps(update) + "\n"
        except Exception  as e:
            logger.error(f"Error in crawl stream: {e}", exc_info=True)
    
    return StreamingResponse(crawl_stream(), media_type="application/json")

@app.post("/validate_url")
async def validate_url(request: CrawlRequest):
    url = request.url
    try:
        response = requests.get(url, timeout=5)
        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            return {"valid": True, "message": "URL is valid"}
        else:
            return {"valid": False, "message": f"URL is not reachable with a status code of {response.status_code}"}
    # These are to catch specific exceptions that can occur with requests such as invalid URL format, connection errors, and timeouts
    except requests.exceptions.MissingSchema:
        return {"valid": False, "message": "Invalid URL format"}
    except requests.exceptions.ConnectionError:
        return {"valid": False, "message": "URL is not reachable"}
    except requests.exceptions.Timeout:
        return {"valid": False, "message": "Request to URL timed out"}
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while validating the URL")
    

# function that stops the execution of crawler when button is clicked
@app.post("/stop_crawler")
async def stopCrawler():
    global crawler
    if crawler:
        crawler.stop_crawl()
        crawler = Crawler()
        return {"message" : "Crawl stopping requested"}
    return {"message" : "nothing to stop"}

@app.post("/pause_crawler")
async def pauseCrawler():
    global crawler
    if crawler:
        crawler.pause_crawl()
        return {"message" :" Crawler Paused"}
    return {"message": "nothing to pause"}

@app.post("/resume_crawler")
async def resumeCrawl():
    global crawler
    if crawler:
        crawler.resume_crawl()        
        return {"message" :" Crawler Resumed"}
    return {"message": "nothing to resume"}

# Add fuzzer request model --- FUZZER
class FuzzRequest(BaseModel):
    target_url: str
    word_list: Optional[str] = ''
    cookies: Optional[str] = ''
    hide_status: Optional[str] = ''
    show_status: Optional[str] = ''
    http_method: str = 'GET'
    filter_by_content_length: Optional[str | int] = ''
    proxy: str = ''
    additional_parameters: Optional[str] = ''
    show_results: bool = True  # New parameter for toggling result visibility

# Global fuzzer instance to control across endpoints
fuzzer = None

# Add fuzzer endpoint 
@app.post("/fuzzer")
async def launchFuzz(request: FuzzRequest):
    global fuzzer
    fuzzer = Fuzzer()
    params_dict = request.model_dump()
    logger.info(request)
    
    async def fuzz_stream():
        try:
            async for update in fuzzer.run_scan(params_dict):
                yield json.dumps(update) + "\n"
        except Exception as e:
            logger.error(f"Error in fuzz stream: {e}", exc_info=True)
    
    
    return StreamingResponse(fuzz_stream(), media_type="application/json")

# control endpoints for the fuzzer
@app.post("/stop_fuzzer")
async def stopFuzzer():
    global fuzzer
    if fuzzer:
        fuzzer.stop_scan()
        return {"message": "Fuzzer stopping requested"}
    return {"message": "No active fuzzer to stop"}

@app.post("/pause_fuzzer")
async def pauseFuzzer():
    global fuzzer
    if fuzzer:
        fuzzer.pause_scan()
        return {"message": "Fuzzer paused"}
    return {"message": "No active fuzzer to pause"}

@app.post("/resume_fuzzer")
async def resumeFuzzer():
    global fuzzer
    if fuzzer:
        fuzzer.resume_scan()
        return {"message": "Fuzzer resumed"}
    return {"message": "No active fuzzer to resume"}

# ==== TREE GRAPH ENDPOINTS START ====
@app.get("/api/tree-data")
async def get_tree_data():
    """Fetch list of URLs with severity for Tree List page."""
    try:
        with open(CRAWL_RESULTS_PATH, 'r') as file:
            data = json.load(file)
        if not data:
            return []

        # Example: Return list of dicts with id, url, severity
        return [{"id": item["id"], "url": item["url"], "severity": item.get("severity", "Info")} for item in data]

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Crawl results not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint to get Tree Graph structure for Vis.js
@app.get("/api/tree-graph")
async def get_tree_graph():
    try:
        with open(CRAWL_RESULTS_PATH, 'r') as file:
            data = json.load(file)
        if not data:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []

        for item in data:
            nodes.append({
                "id": item["id"],
                "label": item["url"],
                "color": severity_color(item.get("severity", "Info"))
            })

            # Simple logic: connect based on slashes in URL
            url_depth = item["url"].count('/')
            if url_depth > 2:  # Assuming base URL has http(s)://
                parent_id = find_parent(data, item)
                if parent_id:
                    edges.append({"from": parent_id, "to": item["id"]})

        return {"nodes": nodes, "edges": edges}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Helper to assign colors based on severity
def severity_color(severity):
    return {
        "Info": "#3498db",    # Blue
        "Low": "#f1c40f",     # Yellow
        "Medium": "#e67e22",  # Orange
        "High": "#e74c3c"     # Red
    }.get(severity, "#95a5a6")  # Default Grey


# Helper to find parent node (basic example)
def find_parent(data, current_item):
    current_url = current_item["url"]
    possible_parents = [item for item in data if item["id"] != current_item["id"]]
    parent = None
    max_match = 0

    for item in possible_parents:
        if current_url.startswith(item["url"]) and len(item["url"]) > max_match:
            parent = item["id"]
            max_match = len(item["url"])

    return parent
# ==== TREE GRAPH ENDPOINTS END ====


# Add BruteForcer request model --- BRUTEFORCER
class BruteForcerRequest(BaseModel):
    target_url: str
    word_list: Optional[str] = ''
    hide_status: Optional[str] = ''
    show_status: Optional[str] = ''
    filter_by_content_length: Optional[str | int] = ''
    additional_parameters: Optional[str] = ''
    show_results: bool = True  # New parameter for toggling result visibility

# Global bruteforcer instance
brute_forcer = None

# Add BruteForcer endpoint
@app.post("/bruteforcer")
async def launchBruteForcer(request: BruteForcerRequest):
    global brute_forcer
    brute_forcer = BruteForcer()
    params_dict = request.model_dump()
    logger.info(request)
    
    async def brute_force_stream():
        try:
            async for update in brute_forcer.run_scan(params_dict):
                yield json.dumps(update) + "\n"
        except Exception as e:
            logger.error(f"Error in brute force stream: {e}", exc_info=True)
    
    
    return StreamingResponse(brute_force_stream(), media_type="application/json")

# also need to Add wordlist upload endpoint
@app.post("/upload-wordlist")
async def upload_wordlist(file: UploadFile = File(...)):
    try:
        # Create directory if needed
        os.makedirs("./wordlist_uploads", exist_ok=True)
        
        # Save filename to local path
        filename = f"./wordlist_uploads/{file.filename}"
        
        with open(filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Wordlist file uploaded: {filename}")
        return {"path": filename}
    
    except Exception as e:
        logger.error(f"Error uploading wordlist file {str(e)}")
        return {"error !": str(e)}, 500
    
def extract_services_sites(json_paths: list[str],
                           csv_path: str = 'services_sites/services_sites.csv') -> bool:
    # Ensure the folder for the CSV exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    valid_data = []
    at_least_one_valid = False

    # Check each JSON path
    for idx, path in enumerate(json_paths):
        if os.path.isfile(path):
            at_least_one_valid = True
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data:
                        valid_data.append((entry.get('id'), entry.get('url')))
            except Exception as e:
                print(f"Error reading {path}: {e}")
                continue
        else:
            if idx == 0:
                # First JSON is required (crawler)
                print("Crawler JSON path is invalid or missing.")
                return False

    if not at_least_one_valid:
        print("No valid JSON files provided.")
        return False

    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'website'])
            writer.writerows(valid_data)
        return True  # Success
    except Exception as e:
        print(f"Unexpected error while writing CSV: {e}")
        return False
  

class AIParams(BaseModel):
    params: Dict[str, str | bool | int] = Field(default_factory=dict)


@app.post("/generate-credentials")
async def generate_credentials_endpoint(file: UploadFile = File(None), data: str = Form(...)):
    #logging.info(f"Received credential generation request: {req}")
    file_word = ""
    try:
        if file:
            # Save the uploaded file
            file_location = f"./wordlist_uploads/{file.filename}"
            with open(file_location, "wb") as buffer:
                buffer.write(await file.read())
            file_word= file_location  # Store file path in dictionary
 
 
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    craw_state = extract_services_sites([
    'outputs_crawler/crawl_results.json',      # required
    'outputs_bruteforcer/brute_force_results.json',         # optional
    'outputs_fuzzer/fuzz_results.json'                 # optional
    ])

    if (craw_state == False):
        return {"crawler": craw_state}
       
    urls = mdp3.load_urls_from_csv("services_sites/services_sites.csv")
    csv_path = "./csv_uploads/web_text.csv"
    scrapper = WebScraper(urls)
    scrapper.generate_csv(csv_path)
    mdp3.nlp_subroutine(csv_path)

    data = json.loads(data)
    global generator
    generator = CredentialGeneratorMDP(
        csv_path= csv_path,
        wordlist_path= file_word,
        user_include_char = data["userChar"],
        user_include_num = data["userNum"],
        user_include_sym = data["userSymb"],
        user_length = data["userLen"],

        pass_include_char = data["passChar"],
        pass_include_num = data["passNum"],
        pass_include_sym = data["passSymb"], 
        pass_length = data["passLen"] 
    )
    credentials = generator.generate_credentials(10)
    print("\nGenerated Credentials:")
    for username, password in credentials:
        print(f"Username: {username}, Password: {password}")
    return {"credentials": credentials}

# control endpoints for the fuzzer
@app.post("/stop_AI")
async def stopAI():
    global generator
    if generator:
        generator.stop_generating()
        generator = CredentialGeneratorMDP()
        return {"message": "AI stopping requested"}
    return {"message": "No active AI to stop"}

@app.post("/save_userpassword")
async def save_userpassword(file: UploadFile = File(None)):
    file_word = ""
    try:
        if file:
            # Save the uploaded file
            file_location = f"./user_passwords_uploads/{file.filename}"
            with open(file_location, "wb") as buffer:
                buffer.write(await file.read())
            file_word= file_location  # Store file path in dictionary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"saved_state": file.filename}

@app.post("/display_userList")
async def display_userList():
    usserpassword_list = []
    for root, dirs, files in os.walk("./user_passwords_uploads"):
        for file in files:
            usserpassword_list.append(file)
    return usserpassword_list

@app.post("/display_userpassword")
async def display_userpassword(file_path):
    credentials = []
    with open(file_path, 'r') as file:
        next(file)  # Skip header line
        for line in file:
            parts = line.strip().split(',')
            if len(parts) == 2:
                credentials.append((parts[0], parts[1]))
    return credentials

class FilenameInput(BaseModel):
    filename: str

@app.post("/delete_userpassword")
async def delete_userpassword(data: FilenameInput):
    
    filename = data.filename
    print(f"Got filename: {filename}")

    for root, dirs, files in os.walk("/user_passwords_uploads"):
        if filename in files:
            file_path = os.path.join(root, filename)
            os.remove(file_path)
            print(f"Deleted: {file_path}")
            return True
    print(f"File '{filename}' not found in 'user_passwords_uploads'.")
    return False



##
## TEAM 10 PART
##

pm = ProjectManager(uri="neo4j://941e739f.databases.neo4j.io", user="neo4j", password="Team_Blue")

def serialize_datetime(obj):
    if isinstance(obj, neo4j.time.DateTime):
        return obj.iso_format()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

@app.get("/dashboard/{initials}")
async def dashboard(initials):
    lead_analyst_initials = "MR"
    my_projects = pm.get_my_projects(initials)
    shared_projects = pm.get_shared_projects(lead_analyst_initials)
    for project in my_projects:
        if "last_edit_date" in project and isinstance(project["last_edit_date"], neo4j.time.DateTime):
            project["last_edit_date"] = project["last_edit_date"].iso_format()
        if "Stamp_Date" in project and isinstance(project["Stamp_Date"], neo4j.time.DateTime):
            project["Stamp_Date"] = project["Stamp_Date"].iso_format()
        if "deleted_date" in project and isinstance(project["deleted_date"], neo4j.time.DateTime):
            project["deleted_date"]=project["deleted_date"].iso_format()
    for project in shared_projects:
        if "last_edit_date" in project and isinstance(project["last_edit_date"], neo4j.time.DateTime):
            project["last_edit_date"] = project["last_edit_date"].iso_format()
        if "Stamp_Date" in project and isinstance(project["Stamp_Date"], neo4j.time.DateTime):
            project["Stamp_Date"] = project["Stamp_Date"].iso_format()
    return {"my_projects": my_projects, "shared_projects": shared_projects}

@app.get("/create_folder/")
async def get_folders():
    result=pm.get_folders()
    for folders in result:
        if "creation_date" in folders and isinstance(folders["creation_date"], neo4j.time.DateTime):
            folders["creation_date"]=folders["creation_date"].iso_format()
    return {"my_folders": result}

@app.post("/delete/{projectName}")
async def delete_project(projectName:str):
    result=pm.delete_project(projectName)
    return result

@app.post("/restore/{projectName}")
async def restore_project(projectName: str):
    return pm.restore_project(projectName)

@app.post("/lock/{projectName}/{analyst_initials}")
async def lock_project(projectName: str, analyst_initials: str):
    analyst_initials = "MR"
    result = pm.lock_project(projectName, analyst_initials)
    return {"status": "success", "project": projectName}

@app.post("/unlock/{projectName}/{analyst_initials}")
async def unlock_project(projectName: str, analyst_initials:str):
    analyst_intials="MR"
    result = pm.unlock_project(projectName, analyst_initials)
    return {"status": "success", "project": projectName}

@app.post("/create/")
async def create_project(project_name: str = Form(...),
    description: str = Form(...),
    machine_IP: str = Form(...),
    status: str = Form(...),
    lead_analyst_initials: str = Form(...),
    locked: str = Form(...),
    files: list[UploadFile] = File(default=[])):
    result=pm.create_project(project_name, locked, description, machine_IP, status, lead_analyst_initials, files)
    return {"status": "success"}

@app.post("/analyst/{initials}/")
async def check_login(initials:str):
    result= pm.check_login(initials)
    return result

@app.get("/export/{projectName}")
async def export_project(projectName: str):
    try:
        result = pm.export_project(projectName)
        if result["status"] == "success":
            # Serialize any datetime objects in the result
            for project in [result["data"]["project"]]:
                if "stamp_date" in project and isinstance(project["stamp_date"], neo4j.time.DateTime):
                    project["stamp_date"] = project["stamp_date"].iso_format()
                if "last_edit_date" in project and isinstance(project["last_edit_date"], neo4j.time.DateTime):
                    project["last_edit_date"] = project["last_edit_date"].iso_format()
                if "deleted_date" in project and project["deleted_date"] and isinstance(project["deleted_date"], neo4j.time.DateTime):
                    project["deleted_date"] = project["deleted_date"].iso_format()
            return result
        else:
            return {"status": "failure", "error": result.get("error", "Failed to export project")}
    except Exception as e:
        return {"status": "failure", "error": f"Export failed: {str(e)}"}
    
@app.post("/submit_results/{result_type}")
async def submit_results(request: Request, result_type):
    try:
        test_data = await request.json()
        pm.submit_results(test_data, result_type)
    except Exception as e:
        return {"status": "failure", "error": f"Export failed: {str(e)}"}

@app.post("/project_folder/{folder_name}")
async def get_projects_in_folder(folder_name: str):
    result = pm.get_projects_in_folder(folder_name)
    for project in result:
        if "creation_date" in project and isinstance(project["creation_date"], neo4j.time.DateTime):
            project["creation_date"] = project["creation_date"].iso_format()
        if "last_edit_date" in project and isinstance(project["last_edit_date"], neo4j.time.DateTime):
            project["last_edit_date"] = project["last_edit_date"].iso_format()
        if "stamp_date" in project and isinstance(project["stamp_date"], neo4j.time.DateTime):
                    project["stamp_date"] = project["stamp_date"].iso_format()
    return {"projects": result}

# helps frontend and backend communicate (different ports for fastAPI and sveltekit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
