/* 
INPUT FORMAT SPECIFICATION

The system accepts input in the following formats:
1. Plain text description (English or Arabic)
2. Structured JSON
3. File upload (PDF, DOCX, TXT)
4. API request

Examples:

1. Plain Text Input (English):
*/

Alpha Islamic Bank is entering into an Ijarah Muntahia Bittamleek agreement with Super Generators 
for a generator with the following details:
- Asset cost: $450,000
- Import tax: $12,000
- Freight: $30,000
- Lease term: 2 years
- Annual rental: $300,000
- Expected residual value: $5,000
- Transfer of ownership price: $3,000

The bank needs to record the initial recognition entry.

/*
2. Plain Text Input (Arabic):
*/

يدخل بنك ألفا الإسلامي في اتفاقية إجارة منتهية بالتمليك مع شركة سوبر للمولدات
لمولد كهربائي بالتفاصيل التالية:
- تكلفة الأصل: 450,000 دولار
- ضريبة الاستيراد: 12,000 دولار
- الشحن: 30,000 دولار
- مدة الإيجار: سنتان
- الإيجار السنوي: 300,000 دولار
- القيمة المتبقية المتوقعة: 5,000 دولار
- سعر نقل الملكية: 3,000 دولار

يحتاج البنك إلى تسجيل قيد الاعتراف الأولي.

/*
3. Structured JSON Input:
*/

{
  "transaction_type": "Ijarah_MBT",
  "entity": "Alpha Islamic Bank",
  "counterparty": "Super Generators",
  "asset_description": "Generator",
  "asset_cost": 450000,
  "additional_costs": {
    "import_tax": 12000,
    "freight": 30000
  },
  "lease_term_years": 2,
  "annual_rental": 300000,
  "residual_value": 5000,
  "transfer_price": 3000,
  "entry_requested": "initial_recognition"
}

/*
4. API Request Format:
*/

POST /api/islamic-finance/process
Content-Type: application/json

{
  "input_text": "Alpha Islamic Bank is entering into an Ijarah Muntahia Bittamleek agreement...",
  "language": "english",
  "visualize": true,
  "output_format": "json"
}

/* 
OUTPUT FORMAT SPECIFICATION

The system produces output in the following format:
*/

{
  "transaction_summary": {
    "transaction_type": "Ijarah_MBT",
    "entity": "Alpha Islamic Bank",
    "counterparty": "Super Generators",
    "asset_description": "Generator",
    "asset_cost": 450000,
    "additional_costs": {
      "import_tax": 12000,
      "freight": 30000
    },
    "lease_term_years": 2,
    "annual_rental": 300000,
    "residual_value": 5000,
    "transfer_price": 3000
  },
  "standard_info": {
    "standard_id": "FAS_32",
    "standard_name": "Ijarah and Ijarah Muntahia Bittamleek",
    "key_terms": ["ijarah", "lease", "right of use", "muntahia bittamleek", "rental"]
  },
  "journal_entries": [
    {"account": "Right of Use Asset (ROU)", "debit": 489000, "credit": 0},
    {"account": "Deferred Ijarah Cost", "debit": 111000, "credit": 0},
    {"account": "Ijarah Liability", "debit": 0, "credit": 600000}
  ],
  "explanation": "According to FAS 32, for Ijarah Muntahia Bittamleek, the initial recognition requires...",
  "calculations": {
    "prime_cost": "450000 + 12000 + 30000 = 492000",
    "rou_asset": "492000 - 3000 = 489000",
    "total_rentals": "300000 × 2 = 600000",
    "deferred_cost": "600000 - 489000 = 111000",
    "terminal_value_difference": "5000 - 3000 = 2000",
    "amortizable_amount": "489000 - 2000 = 487000"
  },
  "chart_data": {
    "accounts": ["Right of Use Asset (ROU)", "Deferred Ijarah Cost", "Ijarah Liability"],
    "debits": [489000, 111000, 0],
    "credits": [0, 0, 600000]
  },
  "visualization_created": true
}