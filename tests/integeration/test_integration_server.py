import subprocess
import os
import time
import pytest
import httpx

# Base URL for the local server
BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="module", autouse=True)
def start_server():
    # Start the server as a subprocess
    server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../local_llm_server/server.py'))
    process = subprocess.Popen(
        ["uvicorn", f"local_llm_server.server:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    time.sleep(5)  # Wait for the server to start

    yield  # This is where the testing happens

    # Terminate the server after tests
    process.terminate()
    process.wait()

@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client

def test_server_status(client):
    """
    Test to check if the server status endpoint is working.
    """
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "running"}

def test_model_route(client):
    """
    Test to check if the model route is accessible.
    """
    response = client.get("/flan-t5/model")
    assert response.status_code == 200
    assert response.json() == {"model": "google/flan-t5-large"}

def test_flan_t5_generate(client):
    """
    Test to check if the Flan-T5 generation endpoint is working.
    """
    payload = {"prompt": "Translate English to French: Hello, how are you?"}
    response = client.post("/flan-t5", json=payload)
    assert response.status_code == 200
    assert "response" in response.json()

def test_query_pdf_with_private_instructions(client):
    """
    Test querying the PDF with private instructions using the local LLM.
    """
    payload = {
        "directory_path": "some/directory/path",
        "question": "What are the main topics?",
        "is_private": True
    }
    response = client.post("/run_query", json=payload)
    assert response.status_code == 200
    assert "response" in response.json()