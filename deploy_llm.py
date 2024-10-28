from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM

# Initialize FastAPI
app = FastAPI()

# Load Flan-T5 Model and Tokenizer
flan_t5_model_name = "google/flan-t5-large"  # You can change to "google/flan-t5-xl" for a larger model
flan_t5_tokenizer = AutoTokenizer.from_pretrained(flan_t5_model_name)
flan_t5_model = AutoModelForSeq2SeqLM.from_pretrained(flan_t5_model_name)

# # Load LLaMA 2 Model and Tokenizer
# llama_model_name = "meta-llama/Llama-2-7b-chat-hf"  # or "meta-llama/Llama-2-13b-chat-hf"
# llama_tokenizer = AutoTokenizer.from_pretrained(llama_model_name)
# llama_model = AutoModelForCausalLM.from_pretrained(llama_model_name)

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

# # LLaMA 2 Endpoint
# @app.post("/llama2")
# async def llama2_generate(request: Request):
#     inputs = llama_tokenizer(request.prompt, return_tensors="pt")
#     outputs = llama_model.generate(inputs["input_ids"], max_new_tokens=50)
#     response = llama_tokenizer.decode(outputs[0], skip_special_tokens=True)
#     return {"response": response}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
