import requests
import base64
from io import BytesIO
from PIL import Image

BASE_URL = "http://localhost:5000"

def test_full_workflow():
    # Test English processing
    response = requests.post(
        f"{BASE_URL}/api/process",
        json={
            "input_text": "Ijarah contract for $100,000 with 5 year term",
            "language": "english"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data['standard_info']['standard_id'] == "FAS_32"
    
    # Verify visualization
    if 'visualization' in data:
        img_data = base64.b64decode(data['visualization'])
        img = Image.open(BytesIO(img_data))
        assert img.size[0] > 0  # Verify image is valid

def test_arabic_support():
    response = requests.post(
        f"{BASE_URL}/api/process",
        json={
            "input_text": "عقد إجارة بقيمة 100,000 دولار لمدة 5 سنوات",
            "language": "arabic"
        }
    )
    assert response.status_code == 200