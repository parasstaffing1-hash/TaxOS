import asyncio
import httpx
from fastapi.testclient import TestClient

from taxos.main import app

def test_crud():
    client = TestClient(app)
    
    # List
    r = client.get("/api/v1/dynamic-calculators/")
    assert r.status_code == 200
    print("Initial calculators count:", len(r.json()))
    
    # Create
    new_calc = {
      "name": "Customs Duty Calculator",
      "slug": "customs-duty-calculator",
      "category": "import",
      "title": "Customs Duty",
      "description": "Calc duties",
      "meta_title": "Customs",
      "meta_description": "Calc",
      "inputs": [],
      "formulas": [],
      "output": {"summary_cards": [], "charts": []},
      "version": "1.0",
      "supported_countries": ["US"],
      "supported_years": [2024]
    }
    r = client.post("/api/v1/dynamic-calculators/", json=new_calc)
    assert r.status_code == 200
    print("Created successfully!")
    
    # List again
    r = client.get("/api/v1/dynamic-calculators/")
    assert any(c["slug"] == "customs-duty-calculator" for c in r.json())
    print("Found newly created calculator in list.")
    
    # Update
    new_calc["title"] = "Updated Title"
    r = client.put("/api/v1/dynamic-calculators/customs-duty-calculator", json=new_calc)
    assert r.status_code == 200
    print("Updated successfully!")
    
    # Delete
    r = client.delete("/api/v1/dynamic-calculators/customs-duty-calculator")
    assert r.status_code == 204
    print("Deleted successfully!")
    
    # Verify deleted
    r = client.get("/api/v1/dynamic-calculators/")
    assert not any(c["slug"] == "customs-duty-calculator" for c in r.json())
    print("Verified deletion!")

if __name__ == "__main__":
    test_crud()
