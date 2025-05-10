Islamic Finance API Documentation
================================

Project Structure
-----------------
islamic_finance_api/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── README.md               # Project overview
├── API_DOCUMENTATION.md    # This documentation file
├── tests/                  # Test files
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── locustfile.py       # Load testing
└── modules/                # Core modules
    ├── __init__.py         # Package initialization
    ├── islamic_finance.py  # Islamic finance logic
    └── visualizations.py   # Chart generation

API Endpoints
-------------

1. Health Check
---------------
Endpoint: GET /api/health
Description: Verify service availability

Response:
{
  "status": "healthy",
  "timestamp": "2023-07-20T12:00:00Z",
  "version": "1.0.0"
}

2. List Supported Standards
---------------------------
Endpoint: GET /api/supported_standards
Description: Returns all supported AAOIFI standards

Response:
{
  "standards": [
    {
      "id": "FAS_4",
      "name": "Foreign Currency Transactions",
      "key_terms": ["foreign currency", "exchange rate"],
      "recognition_criteria": ["..."],
      "measurement_rules": ["..."]
    }
  ],
  "timestamp": "2023-07-20T12:00:00Z"
}

3. Process Transaction
----------------------
Endpoint: POST /api/process
Description: Processes Islamic finance transaction descriptions

Request Body:
{
  "input_text": "string (required)",
  "language": "enum['english','arabic','french']",
  "visualize": "boolean (default: true)"
}

Example Request:
{
  "input_text": "Ijarah contract for $100,000 with 5 year term",
  "language": "english"
}

Success Response (200):
{
  "transaction_summary": {
    "transaction_type": "Ijarah",
    "asset_cost": 100000,
    "lease_term_years": 5
  },
  "standard_info": {
    "standard_id": "FAS_32",
    "standard_name": "Ijarah"
  },
  "journal_entries": [
    {"account": "ROU Asset", "debit": 100000, "credit": 0}
  ],
  "visualization": "base64_encoded_image"
}

Error Responses:
- 400 Bad Request: Invalid input
- 500 Internal Server Error: Processing error

4. API Documentation
--------------------
Endpoint: GET /api
Description: Returns API documentation

Response:
{
  "endpoints": {
    "/api/process": {
      "method": "POST",
      "description": "Process transactions"
    }
  }
}

Input/Output Examples
---------------------

Example Inputs:
{
  "input_text": "Murabaha contract for $50,000",
  "language": "english"
}

Example Output Structure:
{
  "transaction_summary": {},
  "standard_info": {},
  "journal_entries": [],
  "visualization": ""
}

Error Handling
-------------
All error responses follow this format:
{
  "error": "Error message",
  "details": "Additional details"
}

Common error codes:
- 400: Invalid request
- 404: Not found
- 500: Server error
- 503: Service unavailable

Authentication
--------------
Currently uses API key via environment variable:
OPENAI_API_KEY=l api key is here


Version: 1.0.0