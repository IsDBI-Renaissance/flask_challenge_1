import os
import json
import re
from typing import Dict, List, Any, Tuple, Optional, Union
import numpy as np
from openai import OpenAI
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display
import base64
from io import BytesIO

class IslamicFinanceAI:
    def __init__(self, api_key: str = None):
        """
        Initialize the Islamic Finance AI with the knowledge base
        
        Args:
            api_key: OpenAI API key (will use environment variable if not provided)
        """
        # Use provided API key or get from environment
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
            
        if not api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
            
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        self.standards = self._load_standards()
        self.calculation_engines = {
            "FAS_4": self._calculate_fas4,
            "FAS_7": self._calculate_fas7_salam,
            "FAS_10": self._calculate_fas10_istisna,
            "FAS_28": self._calculate_fas28_murabaha,
            "FAS_32": self._calculate_fas32_ijarah
        }
        
    def _load_standards(self) -> Dict:
        """
        Load AAOIFI standards
        
        Returns:
            Dict containing structured representation of standards
        """
        # Enhanced representation of standards based on the handwritten notes
        standards = {
            "FAS_4": {
                "name": "Foreign Currency Transactions and Foreign Operations",
                "key_terms": ["foreign currency", "exchange rate", "translation", "monetary items"],
                "recognition_criteria": ["Exchange rate at transaction date for initial recognition", 
                                       "Closing rate for monetary items at reporting date"],
                "measurement_rules": ["Exchange differences recognized in income statement"],
                "journal_entry_templates": {
                    "foreign_currency_purchase": [
                        {"account": "Asset", "direction": "debit", "amount": "purchase_price_in_local_currency"},
                        {"account": "Cash/Bank", "direction": "credit", "amount": "purchase_price_in_local_currency"}
                    ]
                }
            },
            "FAS_7": {
                "name": "Salam and Parallel Salam",
                "key_terms": ["salam", "parallel salam", "advance payment", "future delivery"],
                "recognition_criteria": ["Salam capital (advance payment) must be paid in full at contract time",
                                        "Delivery of goods at specified future date"],
                "measurement_rules": ["Salam receivables measured at cash equivalent value",
                                    "Revenue recognized at the time of delivery of goods (not contract signing)"],
                "journal_entry_templates": {
                    "salam_payment": [
                        {"account": "Salam Financing", "direction": "debit", "amount": "salam_capital"},
                        {"account": "Cash/Bank", "direction": "credit", "amount": "salam_capital"}
                    ],
                    "parallel_salam": [
                        {"account": "Cash/Bank", "direction": "debit", "amount": "selling_price"},
                        {"account": "Salam Revenue", "direction": "credit", "amount": "selling_price"}
                    ],
                    "profit_recognition": [
                        {"account": "Salam Cost", "direction": "debit", "amount": "salam_capital"},
                        {"account": "Salam Financing", "direction": "credit", "amount": "salam_capital"},
                        {"account": "Salam Revenue", "direction": "debit", "amount": "selling_price"},
                        {"account": "Profit on Salam", "direction": "credit", "amount": "selling_price - salam_capital"}
                    ]
                }
            },
            "FAS_10": {
                "name": "Istisna'a and Parallel Istisna'a",
                "key_terms": ["istisna'a", "parallel istisna'a", "manufacturing contract", "customized goods"],
                "recognition_criteria": ["Contract for manufacturing goods to specifications",
                                        "Al-Mustasni' (buyer) and Sani' (manufacturer/seller)"],
                "measurement_rules": ["Progress recognition allowed", 
                                    "Profit calculated as difference between contract price and production cost"],
                "journal_entry_templates": {
                    "istisna_contract_signing": [
                        {"account": "Istisna'a Receivables", "direction": "debit", "amount": "contract_value"},
                        {"account": "Istisna'a Revenue", "direction": "credit", "amount": "contract_value"}
                    ],
                    "parallel_istisna_contract": [
                        {"account": "Work in Progress", "direction": "debit", "amount": "manufacturing_cost"},
                        {"account": "Istisna'a Payable", "direction": "credit", "amount": "manufacturing_cost"}
                    ],
                    "profit_recognition": [
                        {"account": "Cost of Istisna'a", "direction": "debit", "amount": "manufacturing_cost"},
                        {"account": "Work in Progress", "direction": "credit", "amount": "manufacturing_cost"},
                        {"account": "Istisna'a Revenue", "direction": "debit", "amount": "contract_value"},
                        {"account": "Profit on Istisna'a", "direction": "credit", "amount": "contract_value - manufacturing_cost"}
                    ]
                }
            },
            "FAS_28": {
                "name": "Murabaha and Other Deferred Payment Sales",
                "key_terms": ["murabaha", "cost-plus financing", "deferred payment", "profit margin"],
                "recognition_criteria": ["Bank purchases asset then sells to client at marked-up price",
                                        "Payment is deferred (installments)"],
                "measurement_rules": ["Profit is recognized over the period of financing",
                                    "No profit guarantee (risk sharing)"],
                "journal_entry_templates": {
                    "murabaha_acquisition": [
                        {"account": "Murabaha Asset", "direction": "debit", "amount": "acquisition_cost"},
                        {"account": "Cash/Bank", "direction": "credit", "amount": "acquisition_cost"}
                    ],
                    "murabaha_sale": [
                        {"account": "Murabaha Receivable", "direction": "debit", "amount": "selling_price"},
                        {"account": "Murabaha Asset", "direction": "credit", "amount": "acquisition_cost"},
                        {"account": "Deferred Profit", "direction": "credit", "amount": "selling_price - acquisition_cost"}
                    ],
                    "profit_recognition": [
                        {"account": "Deferred Profit", "direction": "debit", "amount": "monthly_profit"},
                        {"account": "Income on Murabaha Financing", "direction": "credit", "amount": "monthly_profit"}
                    ]
                }
            },
            "FAS_32": {
                "name": "Ijarah and Ijarah Muntahia Bittamleek",
                "key_terms": ["ijarah", "lease", "right of use", "muntahia bittamleek", "ownership transfer"],
                "recognition_criteria": ["Lease that ends with transfer of ownership to lessee",
                                        "5-year typical period based on notes"],
                "measurement_rules": ["Right of use asset and liability model similar to IFRS 16",
                                    "Transfer of ownership at end of lease term"],
                "journal_entry_templates": {
                    "initial_recognition": [
                        {"account": "Right of Use Asset (ROU)", "direction": "debit", "amount": "rou_asset_value"},
                        {"account": "Deferred Ijarah Cost", "direction": "debit", "amount": "deferred_cost"},
                        {"account": "Ijarah Liability", "direction": "credit", "amount": "total_rentals"}
                    ],
                    "periodic_payment": [
                        {"account": "Ijarah Liability", "direction": "debit", "amount": "periodic_rental"},
                        {"account": "Cash/Bank", "direction": "credit", "amount": "periodic_rental"}
                    ],
                    "amortization": [
                        {"account": "Ijarah Expense", "direction": "debit", "amount": "periodic_amortization"},
                        {"account": "Accumulated Amortization", "direction": "credit", "amount": "periodic_amortization"}
                    ],
                    "ownership_transfer": [
                        {"account": "Asset", "direction": "debit", "amount": "transfer_price"},
                        {"account": "Right of Use Asset", "direction": "credit", "amount": "remaining_book_value"},
                        {"account": "Cash/Bank", "direction": "credit", "amount": "transfer_price"}
                    ]
                }
            }
        }
        return standards
        
    def process_input(self, input_text: str, language: str = "english") -> Dict:
        """
        Process input text to extract transaction details
        
        Args:
            input_text: Text containing transaction details
            language: Language of the input text ("english", "french" or "arabic")
            
        Returns:
            Dict containing extracted transaction details
        """
        system_prompt = """
        You are an expert in Islamic finance accounting standards (AAOIFI). 
        Extract all transaction details from the input text that would be relevant for accounting purposes.
        Include all monetary values, dates, contract types, parties involved, and specific terms.
        Format your response as a JSON object with keys corresponding to the extracted parameters.
        
        Based on the transaction type, extract specific parameters:
        
        For Salam transaction:
        - transaction_type (should be "Salam" or "Parallel Salam")
        - salam_capital (the advance payment amount)
        - commodity_details (description of goods to be delivered)
        - delivery_date
        - selling_price (for parallel salam)
        - parties_involved (buyer and seller)
        
        For Istisna'a transaction:
        - transaction_type (should be "Istisna'a" or "Parallel Istisna'a")
        - contract_value (the agreed price)
        - manufacturing_cost (for parallel istisna'a)
        - project_duration (in months/years)
        - specifications (brief description of the goods to be manufactured)
        - parties_involved (al-mustasni and sani)
        
        For Murabaha transaction:
        - transaction_type (should be "Murabaha")
        - acquisition_cost (cost of asset to bank)
        - selling_price (marked-up price to client)
        - financing_period (in months/years)
        - profit_margin (or calculate from cost and selling price)
        - payment_schedule (if available)
        - parties_involved (bank and client)
        
        For Ijarah transaction:
        - transaction_type (should be "Ijarah" or "Ijarah Muntahia Bittamleek")
        - asset_cost (the cost of the asset being leased)
        - additional_costs (like import tax, freight, etc. - as a dict or number)
        - lease_term_years (duration of the lease in years)
        - annual_rental (yearly rental payment)
        - residual_value (expected value at end of lease)
        - transfer_price (price to transfer ownership)
        - parties_involved (lessor and lessee)
        """
        
        if language.lower() == "arabic":
            system_prompt += " The input will be in Arabic, but provide output JSON keys in English with values in Arabic where appropriate."
        elif language.lower() == "french":
            system_prompt += " The input will be in French, but provide output JSON keys in English with values in French where appropriate."
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ]
        )

        try:
            extracted_data = json.loads(response.choices[0].message.content)
            return extracted_data
        except json.JSONDecodeError:
            # Fallback if the response isn't valid JSON
            return {"error": "Failed to extract transaction details. Please check the input format."}
    
    def classify_standard(self, transaction_details: Dict) -> str:
        """
        Determine which AAOIFI standard applies to the transaction
        
        Args:
            transaction_details: Dict containing transaction details
            
        Returns:
            Standard ID (e.g., "FAS_32")
        """
        # Enhanced logic to classify based on transaction type
        transaction_type = transaction_details.get("transaction_type", "").lower()
        
        # Direct mapping of transaction types to standards
        if "salam" in transaction_type:
            return "FAS_7"
        elif "istisna" in transaction_type or "istisna'a" in transaction_type:
            return "FAS_10"
        elif "murabaha" in transaction_type:
            return "FAS_28"
        elif "ijarah" in transaction_type or "lease" in transaction_type:
            return "FAS_32"
        elif "foreign" in transaction_type or "currency" in transaction_type:
            return "FAS_4"
        
        # If no direct match, use LLM-based classification
        standard_descriptions = "\n".join([
            f"- {std_id}: {details['name']} (Key terms: {', '.join(details['key_terms'])})"
            for std_id, details in self.standards.items()
        ])
        
        system_prompt = f"""
        You are an expert in Islamic finance accounting standards (AAOIFI).
        Given a transaction description, determine which AAOIFI standard applies.
        Focus only on the following standards:
        {standard_descriptions}
        
        Return only the standard ID (e.g., FAS_32) without any explanation.
        """
        
        transaction_text = json.dumps(transaction_details, ensure_ascii=False)
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transaction details: {transaction_text}"}
            ],
            max_tokens=10  # Keep it short as we just want the standard ID
        )
        
        # Extract standard ID using regex to clean up any potential extra text
        standard_match = re.search(r"FAS_\d+", response.choices[0].message.content)
        if standard_match:
            return standard_match.group(0)
        else:
            # Default to the most likely standard based on available fields
            if "asset_cost" in transaction_details and "lease_term_years" in transaction_details:
                return "FAS_32"  # Ijarah
            elif "acquisition_cost" in transaction_details and "selling_price" in transaction_details:
                return "FAS_28"  # Murabaha
            elif "contract_value" in transaction_details and "manufacturing_cost" in transaction_details:
                return "FAS_10"  # Istisna'a
            elif "salam_capital" in transaction_details:
                return "FAS_7"   # Salam
            else:
                return "FAS_32"  # Default case
    
    def analyze_transaction(self, transaction_details: Dict, standard_id: str) -> Dict:
        """
        Analyze transaction details against the identified standard
        
        Args:
            transaction_details: Dict containing transaction details
            standard_id: Identified AAOIFI standard ID
            
        Returns:
            Dict containing analysis results
        """
        # Enhanced analysis based on the specific standards
        if standard_id == "FAS_7":  # Salam
            transaction_type_lower = transaction_details.get("transaction_type", "").lower()
            if "parallel" in transaction_type_lower:
                return {
                    "standard_id": standard_id,
                    "transaction_type": "Parallel_Salam",
                    "applicable_templates": ["salam_payment", "parallel_salam", "profit_recognition"],
                    "required_calculations": ["profit_amount"]
                }
            else:
                return {
                    "standard_id": standard_id,
                    "transaction_type": "Salam",
                    "applicable_templates": ["salam_payment"],
                    "required_calculations": []
                }
                
        elif standard_id == "FAS_10":  # Istisna'a
            transaction_type_lower = transaction_details.get("transaction_type", "").lower()
            if "parallel" in transaction_type_lower:
                return {
                    "standard_id": standard_id,
                    "transaction_type": "Parallel_Istisna",
                    "applicable_templates": ["istisna_contract_signing", "parallel_istisna_contract", "profit_recognition"],
                    "required_calculations": ["profit_amount"]
                }
            else:
                return {
                    "standard_id": standard_id,
                    "transaction_type": "Istisna",
                    "applicable_templates": ["istisna_contract_signing"],
                    "required_calculations": []
                }
                
        elif standard_id == "FAS_28":  # Murabaha
            return {
                "standard_id": standard_id,
                "transaction_type": "Murabaha",
                "applicable_templates": ["murabaha_acquisition", "murabaha_sale", "profit_recognition"],
                "required_calculations": ["profit_amount", "monthly_profit"]
            }
                
        elif standard_id == "FAS_32":  # Ijarah
            transaction_type_lower = transaction_details.get("transaction_type", "").lower()
            if "muntahia" in transaction_type_lower or "bittamleek" in transaction_type_lower:
                return {
                    "standard_id": standard_id,
                    "transaction_type": "Ijarah_MBT",
                    "applicable_templates": ["initial_recognition", "periodic_payment", "amortization", "ownership_transfer"],
                    "required_calculations": ["rou_asset_value", "deferred_cost", "total_rentals", "amortizable_amount"]
                }
            else:
                return {
                    "standard_id": standard_id,
                    "transaction_type": "Ijarah",
                    "applicable_templates": ["initial_recognition", "periodic_payment", "amortization"],
                    "required_calculations": ["rou_asset_value", "deferred_cost", "total_rentals"]
                }
        
        # Generic analysis for other cases
        return {
            "standard_id": standard_id,
            "transaction_type": transaction_details.get("transaction_type", "Unknown"),
            "applicable_templates": list(self.standards[standard_id]["journal_entry_templates"].keys()),
            "required_calculations": []
        }
    
    def calculate_entries(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """
        Calculate accounting entries based on transaction details and analysis
        
        Args:
            transaction_details: Dict containing transaction details
            analysis_results: Dict containing analysis results
            
        Returns:
            Dict containing calculation results
        """
        standard_id = analysis_results["standard_id"]
        
        if standard_id in self.calculation_engines:
            return self.calculation_engines[standard_id](transaction_details, analysis_results)
        else:
            return {"error": f"No calculation engine available for {standard_id}"}
    
    def _parse_numeric_value(self, value) -> float:
        """
        Parse numeric value from different formats (string, int, float)
        
        Args:
            value: Numeric value in various formats
            
        Returns:
            float: Parsed numeric value
        """
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            # Remove currency symbols, commas, spaces and other non-numeric chars except decimal point
            clean_value = re.sub(r'[^\d.]', '', value)
            try:
                return float(clean_value)
            except ValueError:
                return 0.0
        else:
            return 0.0
            
    def _calculate_fas7_salam(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """
        Calculate entries for FAS 7 (Salam)
        
        Args:
            transaction_details: Dict containing transaction details
            analysis_results: Dict containing analysis results
            
        Returns:
            Dict containing calculation results
        """
        # Extract required parameters from transaction details
        salam_capital = self._parse_numeric_value(transaction_details.get("salam_capital", 0))
        selling_price = self._parse_numeric_value(transaction_details.get("selling_price", 0))
        
        # Calculate profit
        profit_amount = selling_price - salam_capital if selling_price > 0 else 0
        
        return {
            "salam_capital": salam_capital,
            "selling_price": selling_price,
            "profit_amount": profit_amount,
            "calculations": {
                "profit": f"{selling_price} - {salam_capital} = {profit_amount}"
            }
        }
        
    def _calculate_fas10_istisna(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """
        Calculate entries for FAS 10 (Istisna'a)
        
        Args:
            transaction_details: Dict containing transaction details
            analysis_results: Dict containing analysis results
            
        Returns:
            Dict containing calculation results
        """
        # Extract required parameters from transaction details
        contract_value = self._parse_numeric_value(transaction_details.get("contract_value", 0))
        manufacturing_cost = self._parse_numeric_value(transaction_details.get("manufacturing_cost", 0))
        
        # Calculate profit
        profit_amount = contract_value - manufacturing_cost
        
        return {
            "contract_value": contract_value,
            "manufacturing_cost": manufacturing_cost,
            "profit_amount": profit_amount,
            "calculations": {
                "profit": f"{contract_value} - {manufacturing_cost} = {profit_amount}"
            }
        }
    
    def _calculate_fas28_murabaha(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """
        Calculate entries for FAS 28 (Murabaha)
        
        Args:
            transaction_details: Dict containing transaction details
            analysis_results: Dict containing analysis results
            
        Returns:
            Dict containing calculation results
        """
        # Extract required parameters from transaction details
        acquisition_cost = self._parse_numeric_value(transaction_details.get("acquisition_cost", 0))
        selling_price = self._parse_numeric_value(transaction_details.get("selling_price", 0))
        financing_period = self._parse_numeric_value(transaction_details.get("financing_period", 0))
        
        # If financing period is in years, convert to months
        if financing_period <= 10:  # Assume if period is small number, it's in years
            financing_period_months = financing_period * 12
        else:
            financing_period_months = financing_period
            
        # Calculate profit
        profit_amount = selling_price - acquisition_cost
        monthly_profit = profit_amount / financing_period_months if financing_period_months > 0 else 0
        
        return {
            "acquisition_cost": acquisition_cost,
            "selling_price": selling_price,
            "profit_amount": profit_amount,
            "financing_period_months": financing_period_months,
            "monthly_profit": monthly_profit,
            "calculations": {
                "profit": f"{selling_price} - {acquisition_cost} = {profit_amount}",
                "monthly_profit": f"{profit_amount} / {financing_period_months} = {monthly_profit}"
            }
        }
    
    def _calculate_fas32_ijarah(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """
        Calculate entries for FAS 32 (Ijarah) - Enhanced based on handwritten notes
        
        Args:
            transaction_details: Dict containing transaction details
            analysis_results: Dict containing analysis results
            
        Returns:
            Dict containing calculation results
        """
        # Extract required parameters from transaction details
        asset_cost = self._parse_numeric_value(transaction_details.get("asset_cost", 0))
        
        # Handle different structures of additional costs
        additional_costs = 0
        if "additional_costs" in transaction_details:
            if isinstance(transaction_details["additional_costs"], dict):
                for key, value in transaction_details["additional_costs"].items():
                    additional_costs += self._parse_numeric_value(value)
            else:
                additional_costs = self._parse_numeric_value(transaction_details["additional_costs"])
        
        # Check for specific additional costs
        if "import_tax" in transaction_details:
            additional_costs += self._parse_numeric_value(transaction_details["import_tax"])
            
        if "freight" in transaction_details:
            additional_costs += self._parse_numeric_value(transaction_details["freight"])
        
        lease_term_years = self._parse_numeric_value(transaction_details.get("lease_term_years", 5))  # Default to 5 years as per notes
        annual_rental = self._parse_numeric_value(transaction_details.get("annual_rental", 0))
        residual_value = self._parse_numeric_value(transaction_details.get("residual_value", 0))
        transfer_price = self._parse_numeric_value(transaction_details.get("transfer_price", 0))
        
        # Calculate total prime cost
        prime_cost = asset_cost + additional_costs
        
        # Calculate right of use asset value (based on handwritten notes formula)
        rou_asset_value = prime_cost - transfer_price
        
        # Calculate total rentals
        total_rentals = annual_rental * lease_term_years
        
        # Calculate deferred ijarah cost - difference between total rentals and ROU asset
        deferred_cost = total_rentals - rou_asset_value
        
        # Calculate terminal value difference
        terminal_value_difference = residual_value - transfer_price
        
        # Calculate amortizable amount
        amortizable_amount = rou_asset_value - terminal_value_difference
        
        # Calculate annual amortization
        annual_amortization = amortizable_amount / lease_term_years if lease_term_years > 0 else 0
        
        return {
            "prime_cost": prime_cost,
            "rou_asset_value": rou_asset_value,
            "total_rentals": total_rentals,
            "deferred_cost": deferred_cost,
            "terminal_value_difference": terminal_value_difference,
            "amortizable_amount": amortizable_amount,
            "annual_amortization": annual_amortization,
            "calculations": {
                "prime_cost": f"{asset_cost} + {additional_costs} = {prime_cost}",
                "rou_asset": f"{prime_cost} - {transfer_price} = {rou_asset_value}",
                "total_rentals": f"{annual_rental} × {lease_term_years} = {total_rentals}",
                "deferred_cost": f"{total_rentals} - {rou_asset_value} = {deferred_cost}",
                "terminal_value_difference": f"{residual_value} - {transfer_price} = {terminal_value_difference}",
                "amortizable_amount": f"{rou_asset_value} - {terminal_value_difference} = {amortizable_amount}",
                "annual_amortization": f"{amortizable_amount} / {lease_term_years} = {annual_amortization}"
            }
        }
    
    def _calculate_fas4(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """Calculate entries for FAS 4 (Foreign Currency Transactions)"""
        # Basic implementation based on standard principles
        local_amount = self._parse_numeric_value(transaction_details.get("local_amount", 0))
        foreign_amount = self._parse_numeric_value(transaction_details.get("foreign_amount", 0))
        exchange_rate = self._parse_numeric_value(transaction_details.get("exchange_rate", 0))
        
        # Calculate conversion if exchange rate is provided
        if exchange_rate > 0:
            if local_amount > 0:
                calculated_foreign = local_amount / exchange_rate
            else:
                calculated_foreign = 0
                
            if foreign_amount > 0:
                calculated_local = foreign_amount * exchange_rate
            else:
                calculated_local = 0
        else:
            calculated_foreign = 0
            calculated_local = 0
            
        return {
            "local_amount": local_amount,
            "foreign_amount": foreign_amount,
            "exchange_rate": exchange_rate,
            "calculated_foreign_amount": calculated_foreign,
            "calculated_local_amount": calculated_local,
            "calculations": {
                "foreign_to_local": f"{foreign_amount} × {exchange_rate} = {calculated_local}",
                "local_to_foreign": f"{local_amount} ÷ {exchange_rate} = {calculated_foreign}"
            }
        }
    
    def generate_journal_entries(self, transaction_details: Dict, analysis_results: Dict, calculation_results: Dict) -> Dict:
        """
        Generate journal entries based on calculation results
        
        Args:
            transaction_details: Dict containing transaction details
            analysis_results: Dict containing analysis results
            calculation_results: Dict containing calculation results
            
        Returns:
            Dict containing journal entries and explanations
        """
        standard_id = analysis_results["standard_id"]
        transaction_type = analysis_results["transaction_type"]
        
        # Journal entries for each standard type
        if standard_id == "FAS_7":  # Salam
            if transaction_type == "Parallel_Salam":
                salam_capital = calculation_results.get("salam_capital", 0)
                selling_price = calculation_results.get("selling_price", 0)
                profit_amount = calculation_results.get("profit_amount", 0)
                
                entries = [
                    {"account": "Salam Financing", "debit": salam_capital, "credit": 0},
                    {"account": "Cash/Bank", "debit": 0, "credit": salam_capital},
                    {"account": "Cash/Bank", "debit": selling_price, "credit": 0},
                    {"account": "Salam Revenue", "debit": 0, "credit": selling_price},
                    {"account": "Salam Cost", "debit": salam_capital, "credit": 0},
                    {"account": "Salam Financing", "debit": 0, "credit": salam_capital},
                    {"account": "Salam Revenue", "debit": selling_price, "credit": 0},
                    {"account": "Profit on Salam", "debit": 0, "credit": profit_amount}
                ]
                
                explanation = """
                According to FAS 7, for Parallel Salam transactions:
                
                1. Initial Salam contract:
                   - Debit Salam Financing (representing the advance payment)
                   - Credit Cash/Bank (for the payment made)
                
                2. Parallel Salam contract:
                   - Debit Cash/Bank (for the selling price received)
                   - Credit Salam Revenue (recognizing the revenue)
                
                3. Profit recognition upon delivery:
                   - Debit Salam Cost (recognizing cost of goods sold)
                   - Credit Salam Financing (closing the financing account)
                   - Debit Salam Revenue (closing the revenue account)
                   - Credit Profit on Salam (recognizing the profit)
                """
                
                return {
                    "standard_applied": "FAS 7",
                    "journal_entries": entries,
                    "explanation": explanation,
                    "calculations": calculation_results.get("calculations", {})
                }
            else:  # Regular Salam
                salam_capital = calculation_results.get("salam_capital", 0)
                
                entries = [
                    {"account": "Salam Financing", "debit": salam_capital, "credit": 0},
                    {"account": "Cash/Bank", "debit": 0, "credit": salam_capital}
                ]
                
                explanation = """
                According to FAS 7, for Salam transactions, the initial recognition requires:
                
                1. Debit Salam Financing (representing the advance payment)
                2. Credit Cash/Bank (for the payment made)
                
                Profit is recognized only upon delivery of goods.
                """
                
                return {
                    "standard_applied": "FAS 7",
                    "journal_entries": entries,
                    "explanation": explanation,
                    "calculations": calculation_results.get("calculations", {})
                }
                
        elif standard_id == "FAS_10":  # Istisna'a
            if transaction_type == "Parallel_Istisna":
                contract_value = calculation_results.get("contract_value", 0)
                manufacturing_cost = calculation_results.get("manufacturing_cost", 0)
                profit_amount = calculation_results.get("profit_amount", 0)
                
                entries = [
                    {"account": "Istisna'a Receivables", "debit": contract_value, "credit": 0},
                    {"account": "Istisna'a Revenue", "debit": 0, "credit": contract_value},
                    {"account": "Work in Progress", "debit": manufacturing_cost, "credit": 0},
                    {"account": "Istisna'a Payable", "debit": 0, "credit": manufacturing_cost},
                    {"account": "Cost of Istisna'a", "debit": manufacturing_cost, "credit": 0},
                    {"account": "Work in Progress", "debit": 0, "credit": manufacturing_cost},
                    {"account": "Istisna'a Revenue", "debit": contract_value, "credit": 0},
                    {"account": "Profit on Istisna'a", "debit": 0, "credit": profit_amount}
                ]
                
                explanation = """
                According to FAS 10, for Parallel Istisna'a transactions:
                
                1. Istisna'a contract with customer:
                   - Debit Istisna'a Receivables (representing amount due from customer)
                   - Credit Istisna'a Revenue (representing future revenue)
                
                2. Parallel Istisna'a contract with manufacturer:
                   - Debit Work in Progress (representing asset being manufactured)
                   - Credit Istisna'a Payable (representing amount due to manufacturer)
                
                3. Profit recognition upon completion:
                   - Debit Cost of Istisna'a (recognizing cost of project)
                   - Credit Work in Progress (closing WIP account)
                   - Debit Istisna'a Revenue (closing revenue account)
                   - Credit Profit on Istisna'a (recognizing the profit)
                """
                
                return {
                    "standard_applied": "FAS 10",
                    "journal_entries": entries,
                    "explanation": explanation,
                    "calculations": calculation_results.get("calculations", {})
                }
            else:  # Regular Istisna'a
                contract_value = calculation_results.get("contract_value", 0)
                
                entries = [
                    {"account": "Istisna'a Receivables", "debit": contract_value, "credit": 0},
                    {"account": "Istisna'a Revenue", "debit": 0, "credit": contract_value}
                ]
                
                explanation = """
                According to FAS 10, for Istisna'a transactions, the initial recognition requires:
                
                1. Debit Istisna'a Receivables (representing amount due from customer)
                2. Credit Istisna'a Revenue (representing future revenue)
                
                Additional entries would be needed for progress recognition and completion.
                """
                
                return {
                    "standard_applied": "FAS 10",
                    "journal_entries": entries,
                    "explanation": explanation,
                    "calculations": calculation_results.get("calculations", {})
                }
                
        elif standard_id == "FAS_28":  # Murabaha
            acquisition_cost = calculation_results.get("acquisition_cost", 0)
            selling_price = calculation_results.get("selling_price", 0)
            profit_amount = calculation_results.get("profit_amount", 0)
            monthly_profit = calculation_results.get("monthly_profit", 0)
            
            entries = [
                {"account": "Murabaha Asset", "debit": acquisition_cost, "credit": 0},
                {"account": "Cash/Bank", "debit": 0, "credit": acquisition_cost},
                {"account": "Murabaha Receivable", "debit": selling_price, "credit": 0},
                {"account": "Murabaha Asset", "debit": 0, "credit": acquisition_cost},
                {"account": "Deferred Profit", "debit": 0, "credit": profit_amount},
                {"account": "Deferred Profit", "debit": monthly_profit, "credit": 0},
                {"account": "Income on Murabaha Financing", "debit": 0, "credit": monthly_profit}
            ]
            
            explanation = """
            According to FAS 28, for Murabaha transactions:
            
            1. Asset acquisition:
               - Debit Murabaha Asset (representing the asset purchased)
               - Credit Cash/Bank (for the payment made)
            
            2. Sale to customer:
               - Debit Murabaha Receivable (representing amount due from customer)
               - Credit Murabaha Asset (closing the asset account)
               - Credit Deferred Profit (representing the profit to be recognized over time)
            
            3. Monthly profit recognition:
               - Debit Deferred Profit (reducing the deferred profit)
               - Credit Income on Murabaha Financing (recognizing portion of profit)
            
            The profit is recognized proportionally over the financing period.
            """
            
            return {
                "standard_applied": "FAS 28",
                "journal_entries": entries,
                "explanation": explanation,
                "calculations": calculation_results.get("calculations", {})
            }
            
        elif standard_id == "FAS_32":  # Ijarah
            if transaction_type == "Ijarah_MBT" or transaction_type == "Ijarah":
                rou_asset_value = calculation_results.get("rou_asset_value", 0)
                deferred_cost = calculation_results.get("deferred_cost", 0)
                total_rentals = calculation_results.get("total_rentals", 0)
                annual_rental = transaction_details.get("annual_rental", 0)
                annual_amortization = calculation_results.get("annual_amortization", 0)
                transfer_price = transaction_details.get("transfer_price", 0)
                
                # Initial recognition entries
                entries = [
                    {"account": "Right of Use Asset (ROU)", "debit": rou_asset_value, "credit": 0},
                    {"account": "Deferred Ijarah Cost", "debit": deferred_cost, "credit": 0},
                    {"account": "Ijarah Liability", "debit": 0, "credit": total_rentals}
                ]
                
                # Add periodic payment entry if applicable
                if annual_rental:
                    entries.extend([
                        {"account": "Ijarah Liability", "debit": annual_rental, "credit": 0},
                        {"account": "Cash/Bank", "debit": 0, "credit": annual_rental}
                    ])
                
                # Add amortization entry if applicable
                if annual_amortization:
                    entries.extend([
                        {"account": "Ijarah Expense", "debit": annual_amortization, "credit": 0},
                        {"account": "Accumulated Amortization", "debit": 0, "credit": annual_amortization}
                    ])
                
                # Add transfer entry for Ijarah MBT if applicable
                if transaction_type == "Ijarah_MBT" and transfer_price:
                    entries.extend([
                        {"account": "Asset", "debit": transfer_price, "credit": 0},
                        {"account": "Right of Use Asset", "debit": 0, "credit": rou_asset_value},
                        {"account": "Cash/Bank", "debit": 0, "credit": transfer_price}
                    ])
                
                explanation = """
                According to FAS 32, for Ijarah Muntahia Bittamleek, the initial recognition requires:
                
                1. Right of Use Asset (ROU): This represents the present value of the asset being leased. 
                   It's calculated as the prime cost of the asset minus the transfer price.
                
                2. Deferred Ijarah Cost: This represents the difference between total rentals and the ROU asset value.
                   It will be amortized over the lease term.
                
                3. Ijarah Liability: This represents the total rental obligation over the lease term.
                
                For periodic payments:
                - Debit Ijarah Liability (reducing the liability)
                - Credit Cash/Bank (for the payment made)
                
                For amortization:
                - Debit Ijarah Expense (recognizing periodic expense)
                - Credit Accumulated Amortization (accumulating the amortization)
                
                For Ijarah Muntahia Bittamleek, ownership transfer at the end:
                - Debit Asset (recognizing the asset at transfer price)
                - Credit Right of Use Asset (removing the ROU asset)
                - Credit Cash/Bank (for any payment made)
                """
                
                return {
                    "standard_applied": "FAS 32",
                    "journal_entries": entries,
                    "explanation": explanation,
                    "calculations": calculation_results.get("calculations", {})
                }
        
        elif standard_id == "FAS_4":  # Foreign Currency
            local_amount = calculation_results.get("local_amount", 0)
            foreign_amount = calculation_results.get("foreign_amount", 0)
            calculated_local = calculation_results.get("calculated_local_amount", 0)
            
            entries = [
                {"account": "Asset/Expense", "debit": calculated_local, "credit": 0},
                {"account": "Cash/Bank", "debit": 0, "credit": calculated_local}
            ]
            
            explanation = """
            According to FAS 4, for Foreign Currency Transactions:
            
            1. Initial recognition at transaction date:
               - Debit Asset/Expense (at local currency equivalent)
               - Credit Cash/Bank (at local currency equivalent)
            
            Foreign currency amounts are converted to local currency using the exchange rate at transaction date.
            Subsequent measurement would require adjustments at reporting date for monetary items.
            """
            
            return {
                "standard_applied": "FAS 4",
                "journal_entries": entries,
                "explanation": explanation,
                "calculations": calculation_results.get("calculations", {})
            }
            
        # Fallback for other standards/transaction types
        return {
            "standard_applied": standard_id,
            "journal_entries": [],
            "explanation": "Generic journal entries for this transaction type.",
            "calculations": {}
        }

    def format_output(self, transaction_details: Dict, standard_id: str, journal_entries: Dict, language: str = "english") -> Dict:
        """
        Format the output with visual representations and explanations
        
        Args:
            transaction_details: Dict containing transaction details
            standard_id: Identified AAOIFI standard ID
            journal_entries: Dict containing journal entries and explanations
            language: Output language ("english", "french" or "arabic")
            
        Returns:
            Dict containing formatted output
        """
        # Add standard information
        standard_info = {
            "standard_id": standard_id,
            "standard_name": self.standards[standard_id]["name"],
            "key_terms": self.standards[standard_id]["key_terms"],
            "recognition_criteria": self.standards[standard_id]["recognition_criteria"],
            "measurement_rules": self.standards[standard_id]["measurement_rules"]
        }
        
        # Generate chart data for visualization
        chart_data = self._generate_chart_data(journal_entries["journal_entries"])
        
        output = {
            "transaction_summary": transaction_details,
            "standard_info": standard_info,
            "journal_entries": journal_entries["journal_entries"],
            "explanation": journal_entries["explanation"],
            "calculations": journal_entries.get("calculations", {}),
            "chart_data": chart_data
        }
        
        # Translate output if needed
        if language.lower() in ["arabic", "french"]:
            output = self._translate_output(output, language)
        
        return output
    
    def _generate_chart_data(self, journal_entries: List[Dict]) -> Dict:
        """
        Generate data for chart visualization
        
        Args:
            journal_entries: List of journal entries
            
        Returns:
            Dict containing chart data
        """
        accounts = []
        debits = []
        credits = []
        
        for entry in journal_entries:
            accounts.append(entry["account"])
            debits.append(entry["debit"])
            credits.append(entry["credit"])
        
        return {
            "accounts": accounts,
            "debits": debits,
            "credits": credits
        }
    
    def _translate_output(self, output: Dict, language: str) -> Dict:
        """
        Translate output to Arabic or French
        
        Args:
            output: Dict containing output in English
            language: Target language ("arabic" or "french")
            
        Returns:
            Dict containing output translated to target language
        """
        system_prompt = f"""
        You are an expert translator for Islamic finance terminology.
        Translate the given JSON from English to {language.capitalize()}, preserving all keys in English
        but translating values that are strings. Do not translate numbers or keys.
        Ensure that all financial and accounting terminology is accurately translated
        using proper terminology used in Islamic finance.
        """
        
        output_text = json.dumps(output, ensure_ascii=False)
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate this JSON to {language}: {output_text}"}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            translated_output = json.loads(response.choices[0].message.content)
            return translated_output
        except json.JSONDecodeError:
            # Fallback if the response isn't valid JSON
            return output
    
    def visualize_journal_entries(self, journal_entries: Dict, language: str = "english") -> str:
        """
        Create visualization of journal entries and return as base64 encoded image
        
        Args:
            journal_entries: Dict containing journal entries
            language: Language for visualization ("english", "french" or "arabic")
            
        Returns:
            Base64 encoded image string
        """
        entries = journal_entries["journal_entries"]
        accounts = [entry["account"] for entry in entries]
        debits = [entry["debit"] for entry in entries]
        credits = [entry["credit"] for entry in entries]
        
        # Handle Arabic text if needed
        if language.lower() == "arabic":
            accounts = [arabic_reshaper.reshape(account) for account in accounts]
            accounts = [get_display(account) for account in accounts]
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Set up bar chart
        x = np.arange(len(accounts))
        width = 0.35
        
        # Create bars
        debit_bars = ax.bar(x - width/2, debits, width, label='Debit', color='#1f77b4')
        credit_bars = ax.bar(x + width/2, credits, width, label='Credit', color='#ff7f0e')
        
        # Add labels and title
        ax.set_ylabel('Amount', fontsize=12)
        ax.set_title('Journal Entries', fontsize=14, pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(accounts, rotation=45, ha='right', fontsize=10)
        ax.legend(fontsize=10)
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Add values on top of bars
        for bar in debit_bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{height:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=8)
        
        for bar in credit_bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{height:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=8)
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert plot to base64 encoded image
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=120, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return image_base64
    def get_standards_info(self) -> List[Dict]:
     """Return simplified standards information for API"""
     return [
        {
            "id": std_id,
            "name": details["name"],
            "key_terms": details["key_terms"],
            "recognition_criteria": details["recognition_criteria"]
        }
        for std_id, details in self.standards.items()
     ]
    def process(self, input_text: str, language: str = "english", visualize: bool = True) -> Dict:
        """
        Process input and generate complete output
        
        Args:
            input_text: Text containing transaction details
            language: Language of input/output ("english", "french" or "arabic")
            visualize: Whether to generate visualizations
            
        Returns:
            Dict containing complete output
        """
        # Extract transaction details
        transaction_details = self.process_input(input_text, language)
        
        if "error" in transaction_details:
            return transaction_details
        
        # Classify applicable standard
        standard_id = self.classify_standard(transaction_details)
        
        # Analyze transaction against standard
        analysis_results = self.analyze_transaction(transaction_details, standard_id)
        
        # Calculate accounting entries
        calculation_results = self.calculate_entries(transaction_details, analysis_results)
        
        if "error" in calculation_results:
            return calculation_results
        
        # Generate journal entries
        journal_entries = self.generate_journal_entries(transaction_details, analysis_results, calculation_results)
        
        # Format output
        output = self.format_output(transaction_details, standard_id, journal_entries, language)
        
        # Generate visualizations if requested
        if visualize:
            try:
                image_base64 = self.visualize_journal_entries(journal_entries, language)
                output["visualization"] = image_base64
            except Exception as e:
                output["visualization_error"] = str(e)
        
        return output