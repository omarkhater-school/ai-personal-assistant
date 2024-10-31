import pytest
import httpx
import respx

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL) as client:
        yield client

@respx.mock
def test_server_status(client):
    """
    Test to check if the server status endpoint is working.
    """
    # Mock the response for the /status endpoint
    respx.get(f"{BASE_URL}/status").mock(
        return_value=httpx.Response(200, json={"status": "running"})
    )

    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "running"}

@respx.mock
def test_model_route(client):
    """
    Test to check if the model route is accessible.
    """
    # Mock the response for the /flan-t5/model endpoint
    respx.get(f"{BASE_URL}/flan-t5/model").mock(
        return_value=httpx.Response(200, json={"model": "google/flan-t5-large"})
    )

    response = client.get("/flan-t5/model")
    assert response.status_code == 200
    assert response.json() == {"model": "google/flan-t5-large"}

@respx.mock
def test_flan_t5_generate(client):
    """
    Test to check if the Flan-T5 generation endpoint is working.
    """
    # Mock the response for the /flan-t5 endpoint
    respx.post(f"{BASE_URL}/flan-t5").mock(
        return_value=httpx.Response(200, json={"response": "This is a generated response"})
    )

    payload = {"prompt": "Translate English to French: Hello, how are you?"}
    response = client.post("/flan-t5", json=payload)
    assert response.status_code == 200
    assert "response" in response.json()

@respx.mock
def test_query_pdf_with_private_instructions(client):
    """
    Test querying the PDF with private instructions using the local LLM.
    """
    # Mock the response for the /run_query endpoint
    respx.post(f"{BASE_URL}/run_query").mock(
        return_value=httpx.Response(200, json={"response": "This is a mocked response"})
    )

    payload = {
        "directory_path": "some/directory/path",
        "question": "What are the main topics?",
        "is_private": True
    }
    response = client.post("/run_query", json=payload)
    assert response.status_code == 200
    assert "response" in response.json()

@respx.mock
def test_decline_public_api_with_private_data(client):
    """
    Test that the app declines to use the public API when private data is flagged.
    """
    # Mock the response for the /run_query endpoint with a 400 error
    respx.post(f"{BASE_URL}/run_query").mock(
        return_value=httpx.Response(400, json={"error": "Cannot use public API with private data."})
    )

    payload = {
        "model": "gpt-4-turbo",
        "directory_path": "some/directory/path",
        "question": "What are the main topics?",
        "is_private": True
    }
    response = client.post("/run_query", json=payload)
    assert response.status_code == 400
    assert "error" in response.json()
    assert response.json()["error"] == "Cannot use public API with private data."