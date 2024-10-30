# local_llm_server/server.py
import os
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import HF_API_KEY

# Initialize FastAPI
app = FastAPI()

# Set model cache path to avoid re-downloading
CACHE_DIR = "./models"
flan_t5_model_name = "google/flan-t5-large"
flan_t5_model_path = os.path.join(CACHE_DIR, flan_t5_model_name)

# Ensure the cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Load Flan-T5 Model and Tokenizer (from cache if exists)
flan_t5_tokenizer = AutoTokenizer.from_pretrained(flan_t5_model_path if os.path.exists(flan_t5_model_path) else flan_t5_model_name, use_auth_token=HF_API_KEY)
flan_t5_model = AutoModelForSeq2SeqLM.from_pretrained(flan_t5_model_path if os.path.exists(flan_t5_model_path) else flan_t5_model_name, use_auth_token=HF_API_KEY)

# Define a request model for prompt input
class Request(BaseModel):
    prompt: str

# Flan-T5 Endpoint
@app.post("/flan-t5")
async def flan_t5_generate(request: Request):
    inputs = flan_t5_tokenizer(request.prompt, return_tensors="pt")
    outputs = flan_t5_model.generate(inputs["input_ids"], max_new_tokens=50)
    response = flan_t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"response": response}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
