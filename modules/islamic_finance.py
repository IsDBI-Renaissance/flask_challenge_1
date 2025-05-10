import os
import json
import re
from typing import Dict, List, Any, Optional
#from openai import OpenAI

class IslamicFinanceAI:
    def __init__(self, api_key: str = None):
        """Initialize with enhanced error handling"""
        self.client = OpenAI(
            api_key=api_key or os.environ.get("TOGETHER_API_KEY"),
            base_url="https://api.together.xyz/v1"
        )
        if not self.client.api_key:
            raise ValueError("API key must be provided")
        self.standards = self._load_standards()

    def _load_standards(self) -> Dict:
        """Standards data with fallback templates"""
        return {
            "FAS_4": {
                "name": "Foreign Currency Transactions",
                "key_terms": ["foreign currency", "exchange rate"],
                "template": [
                    {"account": "Asset", "direction": "debit"},
                    {"account": "Liability", "direction": "credit"}
                ]
            },
            "FAS_32": {
                "name": "Ijarah",
                "key_terms": ["ijarah", "lease"],
                "template": [
                    {"account": "Right of Use Asset", "direction": "debit"},
                    {"account": "Ijarah Liability", "direction": "credit"}
                ]
            }
        }

    def process_input(self, input_text: str, language: str = "english") -> Dict:
        """Always returns data, even if minimal"""
        if not input_text:
            return {"amount": 0, "transaction_type": "Unknown"}
        
        try:
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-3-70b-chat-hf",
                messages=[{
                    "role": "system",
                    "content": "Extract financial details as JSON with 'amount' and 'transaction_type'"
                }, {
                    "role": "user", 
                    "content": input_text
                }],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            data["amount"] = float(data.get("amount", self._extract_amount(input_text) or 0))
            return data
        except Exception:
            return {
                "amount": self._extract_amount(input_text) or 0,
                "transaction_type": "Unknown"
            }

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract first number found in text"""
        match = re.search(r'(\d[\d,.]*\d*)', text.replace(',', ''))
        return float(match.group(1)) if match else None

    def generate_entries(self, details: Dict) -> Dict:
        """Generate journal entries with guaranteed output"""
        amount = details.get("amount", 0)
        standard_id = self.classify_standard(details)
        template = self.standards[standard_id]["template"]
        
        entries = []
        for entry in template:
            entries.append({
                "account": entry["account"],
                "debit": amount if entry["direction"] == "debit" else 0,
                "credit": amount if entry["direction"] == "credit" else 0
            })
        
        return {
            "standard_id": standard_id,
            "journal_entries": entries,
            "calculations": {"amount": amount}
        }

    def classify_standard(self, details: Dict) -> str:
        """Simple standard classification"""
        text = json.dumps(details).lower()
        if any(term in text for term in ["ijarah", "lease"]):
            return "FAS_32"
        return "FAS_4"  # Default fallback

    def get_standards_info(self) -> List[Dict]:
        """Get all supported standards"""
        return [{
            "id": k, 
            "name": v["name"], 
            "key_terms": v["key_terms"]
        } for k, v in self.standards.items()]