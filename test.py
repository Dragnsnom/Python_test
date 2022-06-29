from fastapi.testclient import TestClient
from main import app, get_request
from requests.auth import HTTPBasicAuth

client = TestClient(app)

def test_security_http_basic():
    auth = HTTPBasicAuth(username = "stanleyjobson", password = "swordfish")
    response = client.get("/users/me", auth = auth)
    assert response.status_code == 200, response.text
    assert response.json() == {'username': 'stanleyjobson'}
    
def test_not_authenticated_get():
    response = client.get("/frames/0")
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not authenticated'}
    
def test_not_authenticated_delete():
    response = client.delete("/frames/0")
    assert response.status_code == 401
    assert response.json() == {'detail': 'Not authenticated'}
    
def test_authenticated_get_zero_elements():
    auth = HTTPBasicAuth(username = "stanleyjobson", password = "swordfish")
    response = client.get("/frames/0", auth = auth)
    assert response.status_code == 200
    assert response.json() == {'0': []}
    
def test_authenticated_post_zero_elements():
    auth = HTTPBasicAuth(username = "stanleyjobson", password = "swordfish")
    response = client.get("/frames/", auth = auth)
    assert response.status_code == 405
    assert response.json() == {'detail': 'Method Not Allowed'}
    
def test_authenticated_post_with_elements():
    auth = HTTPBasicAuth(username = "stanleyjobson", password = "swordfish")
    response = client.post("/frames/", files={"files": ("2.jpg", open("2.jpg", "rb"), "image/jpeg")}, auth = auth)
    assert response.status_code == 200
    
def test_authenticated_get():
    req  = get_request()
    auth = HTTPBasicAuth(username = "stanleyjobson", password = "swordfish")
    response = client.get("/frames/" + str(req), auth = auth)
    assert response.status_code == 200
    
def test_authenticated_delete():
    req  = get_request()
    auth = HTTPBasicAuth(username = "stanleyjobson", password = "swordfish")
    response = client.delete("/frames/" + str(req), auth = auth)
    assert response.status_code == 200
    

    
    


    
