from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from typing import Optional
import shutil
import os
from mdp3 import CredentialGeneratorMDP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#creates endpoints
app = FastAPI(title="Routes")

@app.post("/upload-wordlist")
async def upload_wordlist(file: UploadFile = File(...)):
    # Save to local path so you can use it in mdp3
    filename = f"./wordlist_uploads/{file.filename}"
    os.makedirs("./wordlist_uploads", exist_ok=True)
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"path": filename}

class CredentialRequest(BaseModel):
    # path or name of the wordlist if needed
    wordlist_path: Optional[str] = "wordlist_uploads\wordlist.txt"

    # toggles for user
    user_include_char: bool = True
    user_include_num: bool = True
    user_include_sym: bool = True
    user_length: int = 12

    # toggles for password
    pass_include_char: bool = True
    pass_include_num: bool = True
    pass_include_sym: bool = True
    pass_length: int = 12

    # how many credentials to generate
    count: int = 10


@app.post("/generate-credentials")
async def generate_credentials_endpoint(req: CredentialRequest):
    logging.info(f"Received credential generation request: {req}")

    generator = CredentialGeneratorMDP(
        csv_path ="site_list.csv",      # or wherever your CSV is
        wordlist_path =req.wordlist_path or "wordlist_uploads\wordlist.txt",

        user_include_char = req.user_include_char or True,
        user_include_num = req.user_include_num or True,
        user_include_sym = req.user_include_sym or True,
        user_length = req.user_length or 12,

        pass_include_char = req.pass_include_char or True,
        pass_include_num = req.pass_include_num or True,
        pass_include_sym = req.pass_include_sym or True,
        pass_length = req.pass_length or 12
    )

    credentials = generator.generate_credentials(req.count)
    return {"credentials": credentials}

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)