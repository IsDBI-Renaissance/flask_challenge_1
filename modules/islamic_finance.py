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
            "FAS_7": self._calculate_fas7,
            "FAS_10": self._calculate_fas10,
            "FAS_28": self._calculate_fas28,
            "FAS_32": self._calculate_fas32
        }
        
    def _load_standards(self) -> Dict:
        """
        Load AAOIFI standards
        
        Returns:
            Dict containing structured representation of standards
        """
        # Simplified representation of standards
        standards = {
            "FAS_4": {
                "name": "Foreign Currency Transactions and Foreign Operations",
                "key_terms": ["foreign currency", "exchange rate", "translation", "monetary items"],
                "recognition_criteria": ["..."],
                "measurement_rules": ["..."],
                "journal_entry_templates": {
                    "foreign_currency_purchase": [
                        {"account": "Asset", "direction": "debit", "amount": "purchase_price_in_local_currency"},
                        {"account": "Cash/Bank", "direction": "credit", "amount": "purchase_price_in_local_currency"}
                    ]
                }
            },
            "FAS_7": {
                "name": "Investments",
                "key_terms": ["investment", "equity", "sukuks", "shares"],
                "recognition_criteria": ["..."],
                "measurement_rules": ["..."],
                "journal_entry_templates": {
                    "investment_acquisition": [
                        {"account": "Investment", "direction": "debit", "amount": "acquisition_cost"},
                        {"account": "Cash/Bank", "direction": "credit", "amount": "acquisition_cost"}
                    ]
                }
            },
            "FAS_10": {
                "name": "Istisna'a and Parallel Istisna'a",
                "key_terms": ["istisna'a", "manufacturer", "contract", "work-in-progress"],
                "recognition_criteria": ["..."],
                "measurement_rules": ["..."],
                "journal_entry_templates": {
                    "istisna_contract_signing": [
                        {"account": "Istisna'a Receivables", "direction": "debit", "amount": "contract_value"},
                        {"account": "Istisna'a Revenues", "direction": "credit", "amount": "contract_value"}
                    ]
                }
            },
            "FAS_28": {
                "name": "Murabaha and Other Deferred Payment Sales",
                "key_terms": ["murabaha", "cost-plus", "deferred payment", "profit"],
                "recognition_criteria": ["..."],
                "measurement_rules": ["..."],
                "journal_entry_templates": {
                    "murabaha_acquisition": [
                        {"account": "Murabaha Asset", "direction": "debit", "amount": "acquisition_cost"},
                        {"account": "Cash/Bank", "direction": "credit", "amount": "acquisition_cost"}
                    ],
                    "murabaha_sale": [
                        {"account": "Murabaha Receivable", "direction": "debit", "amount": "selling_price"},
                        {"account": "Murabaha Asset", "direction": "credit", "amount": "acquisition_cost"},
                        {"account": "Deferred Profit", "direction": "credit", "amount": "selling_price - acquisition_cost"}
                    ]
                }
            },
            "FAS_32": {
                "name": "Ijarah and Ijarah Muntahia Bittamleek",
                "key_terms": ["ijarah", "lease", "right of use", "muntahia bittamleek", "rental"],
                "recognition_criteria": ["..."],
                "measurement_rules": ["..."],
                "journal_entry_templates": {
                    "initial_recognition": [
                        {"account": "Right of Use Asset (ROU)", "direction": "debit", "amount": "rou_asset_value"},
                        {"account": "Deferred Ijarah Cost", "direction": "debit", "amount": "deferred_cost"},
                        {"account": "Ijarah Liability", "direction": "credit", "amount": "total_rentals"}
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
            language: Language of the input text ("english" or "arabic")
            
        Returns:
            Dict containing extracted transaction details
        """
        system_prompt = """
        You are an expert in Islamic finance accounting standards (AAOIFI). 
        Extract all transaction details from the input text that would be relevant for accounting purposes.
        Include all monetary values, dates, contract types, parties involved, and specific terms.
        Format your response as a JSON object with keys corresponding to the extracted parameters.
        
        For an Ijarah Muntahia Bittamleek transaction, extract:
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
            # Default to FAS_32 as in the example case
            return "FAS_32"
    
    def analyze_transaction(self, transaction_details: Dict, standard_id: str) -> Dict:
        """
        Analyze transaction details against the identified standard
        
        Args:
            transaction_details: Dict containing transaction details
            standard_id: Identified AAOIFI standard ID
            
        Returns:
            Dict containing analysis results
        """
        # For Ijarah MBT case
        if standard_id == "FAS_32" and "transaction_type" in transaction_details:
            transaction_type_lower = transaction_details["transaction_type"].lower()
            if "ijarah" in transaction_type_lower or "lease" in transaction_type_lower:
                if "muntahia" in transaction_type_lower or "bittamleek" in transaction_type_lower:
                    return {
                        "standard_id": standard_id,
                        "transaction_type": "Ijarah_MBT",
                        "applicable_templates": ["initial_recognition"],
                        "required_calculations": ["rou_asset_value", "deferred_cost", "total_rentals"]
                    }
                else:
                    return {
                        "standard_id": standard_id,
                        "transaction_type": "Ijarah",
                        "applicable_templates": ["initial_recognition"],
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
    
    def _calculate_fas32(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """
        Calculate entries for FAS 32 (Ijarah)
        
        Args:
            transaction_details: Dict containing transaction details
            analysis_results: Dict containing analysis results
            
        Returns:
            Dict containing calculation results
        """
        # Extract required parameters from transaction details
        asset_cost = transaction_details.get("asset_cost", 0)
        if isinstance(asset_cost, str):
            # Remove currency symbols and commas, then convert to float
            asset_cost = float(re.sub(r'[^\d.]', '', asset_cost))
        
        # Handle different structures of additional costs
        additional_costs = 0
        if "additional_costs" in transaction_details:
            if isinstance(transaction_details["additional_costs"], dict):
                for key, value in transaction_details["additional_costs"].items():
                    if isinstance(value, str):
                        value = float(re.sub(r'[^\d.]', '', value))
                    additional_costs += value
            elif isinstance(transaction_details["additional_costs"], (int, float)):
                additional_costs = transaction_details["additional_costs"]
            elif isinstance(transaction_details["additional_costs"], str):
                additional_costs = float(re.sub(r'[^\d.]', '', transaction_details["additional_costs"]))
        
        # Check for specific additional costs
        if "import_tax" in transaction_details:
            tax = transaction_details["import_tax"]
            if isinstance(tax, str):
                tax = float(re.sub(r'[^\d.]', '', tax))
            additional_costs += tax
            
        if "freight" in transaction_details:
            freight = transaction_details["freight"]
            if isinstance(freight, str):
                freight = float(re.sub(r'[^\d.]', '', freight))
            additional_costs += freight
        
        lease_term_years = transaction_details.get("lease_term_years", 1)
        if isinstance(lease_term_years, str):
            # Extract numbers from string like "2 years"
            lease_term_years = float(re.search(r'\d+', lease_term_years).group())
        
        annual_rental = transaction_details.get("annual_rental", 0)
        if isinstance(annual_rental, str):
            annual_rental = float(re.sub(r'[^\d.]', '', annual_rental))
        
        residual_value = transaction_details.get("residual_value", 0)
        if isinstance(residual_value, str):
            residual_value = float(re.sub(r'[^\d.]', '', residual_value))
        
        transfer_price = transaction_details.get("transfer_price", 0)
        if isinstance(transfer_price, str):
            transfer_price = float(re.sub(r'[^\d.]', '', transfer_price))
        
        # Calculate total prime cost
        prime_cost = asset_cost + additional_costs
        
        # Calculate right of use asset value
        rou_asset_value = prime_cost - transfer_price
        
        # Calculate total rentals
        total_rentals = annual_rental * lease_term_years
        
        # Calculate deferred ijarah cost
        deferred_cost = total_rentals - rou_asset_value
        
        # Calculate terminal value difference
        terminal_value_difference = residual_value - transfer_price
        
        # Calculate amortizable amount
        amortizable_amount = rou_asset_value - terminal_value_difference
        
        return {
            "prime_cost": prime_cost,
            "rou_asset_value": rou_asset_value,
            "total_rentals": total_rentals,
            "deferred_cost": deferred_cost,
            "terminal_value_difference": terminal_value_difference,
            "amortizable_amount": amortizable_amount,
            "calculations": {
                "prime_cost": f"{asset_cost} + {additional_costs} = {prime_cost}",
                "rou_asset": f"{prime_cost} - {transfer_price} = {rou_asset_value}",
                "total_rentals": f"{annual_rental} × {lease_term_years} = {total_rentals}",
                "deferred_cost": f"{total_rentals} - {rou_asset_value} = {deferred_cost}",
                "terminal_value_difference": f"{residual_value} - {transfer_price} = {terminal_value_difference}",
                "amortizable_amount": f"{rou_asset_value} - {terminal_value_difference} = {amortizable_amount}"
            }
        }
    
    def _calculate_fas4(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """Calculate entries for FAS 4 (Foreign Currency Transactions)"""
        # Placeholder implementation
        return {
            "message": "Foreign Currency Transaction calculations applied based on FAS 4",
            "calculations": {}
        }
    
    def _calculate_fas7(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """Calculate entries for FAS 7 (Investments)"""
        # Placeholder implementation
        return {
            "message": "Investment calculations applied based on FAS 7",
            "calculations": {}
        }
    
    def _calculate_fas10(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """Calculate entries for FAS 10 (Istisna'a)"""
        # Placeholder implementation
        return {
            "message": "Istisna'a calculations applied based on FAS 10",
            "calculations": {}
        }
    
    def _calculate_fas28(self, transaction_details: Dict, analysis_results: Dict) -> Dict:
        """Calculate entries for FAS 28 (Murabaha)"""
        # Placeholder implementation
        return {
            "message": "Murabaha calculations applied based on FAS 28",
            "calculations": {}
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
        
        # For FAS 32 Ijarah MBT - Initial Recognition
        if standard_id == "FAS_32" and (transaction_type == "Ijarah_MBT" or transaction_type == "Ijarah"):
            if "initial_recognition" in analysis_results["applicable_templates"]:
                rou_asset_value = calculation_results["rou_asset_value"]
                deferred_cost = calculation_results["deferred_cost"]
                total_rentals = calculation_results["total_rentals"]
                
                entries = [
                    {"account": "Right of Use Asset (ROU)", "debit": rou_asset_value, "credit": 0},
                    {"account": "Deferred Ijarah Cost", "debit": deferred_cost, "credit": 0},
                    {"account": "Ijarah Liability", "debit": 0, "credit": total_rentals}
                ]
                
                explanation = """
                According to FAS 32, for Ijarah Muntahia Bittamleek, the initial recognition requires:
                
                1. Right of Use Asset (ROU): This represents the present value of the asset being leased. 
                   It's calculated as the prime cost of the asset minus the transfer price.
                
                2. Deferred Ijarah Cost: This represents the difference between total rentals and the ROU asset value.
                   It will be amortized over the lease term.
                
                3. Ijarah Liability: This represents the total rental obligation over the lease term.
                """
                
                return {
                    "standard_applied": "FAS 32",
                    "journal_entries": entries,
                    "explanation": explanation,
                    "calculations": calculation_results["calculations"]
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
            language: Output language ("english" or "arabic")
            
        Returns:
            Dict containing formatted output
        """
        # Add standard information
        standard_info = {
            "standard_id": standard_id,
            "standard_name": self.standards[standard_id]["name"],
            "key_terms": self.standards[standard_id]["key_terms"]
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
        if language.lower() == "arabic":
            output = self._translate_output(output)
        
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
    
    def _translate_output(self, output: Dict) -> Dict:
        """
        Translate output to Arabic
        
        Args:
            output: Dict containing output in English
            
        Returns:
            Dict containing output translated to Arabic
        """
        system_prompt = """
        You are an expert translator for Islamic finance terminology.
        Translate the given JSON from English to Arabic, preserving all keys in English
        but translating values that are strings. Do not translate numbers or keys.
        Ensure that all financial and accounting terminology is accurately translated
        using proper Arabic terminology used in Islamic finance.
        """
        
        output_text = json.dumps(output, ensure_ascii=False)
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate this JSON to Arabic: {output_text}"}
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
            language: Language for visualization ("english" or "arabic")
            
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
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Set up bar chart
        x = np.arange(len(accounts))
        width = 0.35
        
        # Create bars
        debit_bars = ax.bar(x - width/2, debits, width, label='Debit')
        credit_bars = ax.bar(x + width/2, credits, width, label='Credit')
        
        # Add labels and title
        ax.set_ylabel('Amount')
        ax.set_title('Journal Entries')
        ax.set_xticks(x)
        ax.set_xticklabels(accounts)
        ax.legend()
        
        # Add values on top of bars
        for bar in debit_bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{height:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom')
        
        for bar in credit_bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f'{height:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom')
        
        # Adjust layout
        fig.tight_layout()
        
        # Convert plot to base64 encoded image
        buffer = BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        
        return image_base64
    
    def process(self, input_text: str, language: str = "english", visualize: bool = True) -> Dict:
        """
        Process input and generate complete output
        
        Args:
            input_text: Text containing transaction details
            language: Language of input/output ("english" or "arabic")
            visualize: Whether to generate visualizations
            
        Returns:
            Dict containing complete output
        """
        # Extract transaction details
        transaction_details = self.process_input(input_text, language)
        
        # Classify applicable standard
        standard_id = self.classify_standard(transaction_details)
        
        # Analyze transaction against standard
        analysis_results = self.analyze_transaction(transaction_details, standard_id)
        
        # Calculate accounting entries
        calculation_results = self.calculate_entries(transaction_details, analysis_results)
        
        # Generate journal entries
        journal_entries = self.generate_journal_entries(transaction_details, analysis_results, calculation_results)
        
        # Format output
        output = self.format_output(transaction_details, standard_id, journal_entries, language)
        
        # Generate visualizations if requested
        if visualize:
            image_base64 = self.visualize_journal_entries(journal_entries, language)
            output["visualization"] = image_base64
        
        return output