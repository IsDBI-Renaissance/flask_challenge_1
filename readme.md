# Islamic Finance API

An API for processing Islamic finance transactions according to AAOIFI standards.

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Then edit `.env` with your OpenAI API key

## Running the API

```
python app.py
```

The API will be available at http://localhost:5000

## API Endpoints

### POST /api/process

Process a transaction description to get accounting entries according to AAOIFI standards.

#### Request Parameters

- `input_text`: Text description of the transaction (required)
- `language`: Language of input and output - "english" or "arabic" (optional, default: "english")
- `visualize`: Whether to generate visualizations (optional, default: true)

#### Example Request

```json
{
  "input_text": "Alpha Islamic Bank is entering into an Ijarah Muntahia Bittamleek agreement with Super Generators for a generator with the following details: - Asset cost: $450,000 - Import tax: $12,000 - Freight: $30,000 - Lease term: 2 years - Annual rental: $300,000 - Expected residual value: $5,000 - Transfer of ownership price: $3,000. The bank needs to record the initial recognition entry.",
  "language": "english",
  "visualize": true
}
```

#### Example Response

See the API documentation for response format details.
