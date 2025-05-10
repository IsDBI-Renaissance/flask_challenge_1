import os
from typing import Dict, List, Any, Optional
from openai import OpenAI
import json
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image
from io import BytesIO
import base64


class AdvancedIslamicFinanceAI:
    """Advanced features for the Islamic Finance AI system"""
    
    @staticmethod
    def generate_transaction_flow_diagram(transaction_details: Dict) -> nx.DiGraph:
        """
        Generate a visual transaction flow diagram based on transaction details
        
        Args:
            transaction_details: Dict containing transaction details
            
        Returns:
            NetworkX DiGraph object representing the transaction flow
        """
        # Create directed graph
        G = nx.DiGraph()
        
        # Extract entities
        entity = transaction_details.get("entity", "Bank")
        counterparty = transaction_details.get("counterparty", "Customer")
        asset = transaction_details.get("asset_description", "Asset")
        
        # Add nodes
        G.add_node(entity, type="bank")
        G.add_node(counterparty, type="customer")
        G.add_node(asset, type="asset")
        G.add_node("Lease Agreement", type="document")
        
        # Add edges based on transaction type
        if "ijarah" in transaction_details.get("transaction_type", "").lower():
            # For Ijarah transactions
            G.add_edge(entity, asset, label="purchases")
            G.add_edge(entity, "Lease Agreement", label="creates")
            G.add_edge(counterparty, "Lease Agreement", label="signs")
            G.add_edge(entity, counterparty, label="leases asset to")
            G.add_edge(counterparty, entity, label="pays rental")
            
            # If Ijarah Muntahia Bittamleek, add ownership transfer
            if "muntahia" in transaction_details.get("transaction_type", "").lower():
                G.add_edge(entity, counterparty, label="transfers ownership at end")
        
        return G
    
    @staticmethod
    def visualize_transaction_flow(graph: nx.DiGraph) -> plt.Figure:
        """
        Create visualization of transaction flow
        
        Args:
            graph: NetworkX DiGraph object
            
        Returns:
            Matplotlib figure with visualization
        """
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Define node colors based on type
        node_colors = {
            "bank": "#3498db",      # Blue
            "customer": "#e74c3c",  # Red
            "asset": "#2ecc71",     # Green
            "document": "#f39c12"   # Orange
        }
        
        # Set node colors
        node_color_list = [node_colors[graph.nodes[node]["type"]] for node in graph.nodes()]
        
        # Set positions using spring layout
        pos = nx.spring_layout(graph, seed=42)
        
        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, ax=ax, node_color=node_color_list, 
                              node_size=3000, alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(graph, pos, ax=ax, edge_color="gray", 
                              width=2, alpha=0.7, arrows=True, arrowsize=20)
        
        # Draw labels
        nx.draw_networkx_labels(graph, pos, ax=ax, font_size=12, font_weight="bold")
        
        # Draw edge labels
        edge_labels = {(u, v): d["label"] for u, v, d in graph.edges(data=True)}
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, 
                                    font_size=10, alpha=0.7)
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                      markersize=15, label=node_type.capitalize())
            for node_type, color in node_colors.items()
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        # Remove axis
        ax.axis('off')
        
        # Add title
        ax.set_title("Transaction Flow Diagram", fontsize=16)
        
        return fig
    
    @staticmethod
    def generate_shariah_compliance_analysis(transaction_details: Dict, 
                                           standard_id: str) -> Dict:
        """
        Generate Shariah compliance analysis for the transaction
        
        Args:
            transaction_details: Dict containing transaction details
            standard_id: AAOIFI standard ID
            
        Returns:
            Dict containing Shariah compliance analysis
        """
        # Use OpenAI to generate Shariah compliance analysis
        system_prompt = """
        You are an expert in Islamic finance and Shariah compliance.
        Analyze the given transaction details and AAOIFI standard to assess Shariah compliance.
        Focus on key principles such as:
        1. Avoidance of Riba (interest)
        2. Avoidance of Gharar (excessive uncertainty)
        3. Avoidance of Maysir (gambling)
        4. Asset-backed nature of transaction
        5. Risk-sharing principles
        6. Adherence to specific contract requirements
        
        Provide a detailed analysis with compliance score and recommendations if any.
        Format your response as a JSON object with keys:
        - compliance_score (0-1)
        - compliance_status (Fully Compliant, Mostly Compliant, Partially Compliant, Non-Compliant)
        - key_findings (list)
        - areas_of_concern (list or null)
        - recommendations (list or null)
        """
        
        input_text = f"""
        Transaction Details: {json.dumps(transaction_details, ensure_ascii=False)}
        AAOIFI Standard: {standard_id}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            compliance_analysis = json.loads(response.choices[0].message.content)
            return compliance_analysis
        except json.JSONDecodeError:
            # Fallback if the response isn't valid JSON
            return {
                "compliance_score": 0.5,
                "compliance_status": "Analysis Failed",
                "key_findings": ["Unable to process compliance analysis"],
                "areas_of_concern": ["System error in compliance processing"],
                "recommendations": ["Please review transaction manually"]
            }
    
    @staticmethod
    def generate_alternative_structures(transaction_details: Dict) -> List[Dict]:
        """
        Generate alternative Shariah-compliant structures for the transaction
        
        Args:
            transaction_details: Dict containing transaction details
            
        Returns:
            List of Dict containing alternative structures
        """
        # Use OpenAI to generate alternative structures
        system_prompt = """
        You are an expert in Islamic finance product structuring.
        Given the transaction details, suggest 2-3 alternative Shariah-compliant structures
        that could achieve similar economic objectives.
        
        For each alternative, provide:
        1. Name of structure
        2. Brief description
        3. Key advantages
        4. Key disadvantages
        5. Applicable AAOIFI standard(s)
        
        Format your response as a JSON array of objects, each with these keys.
        """
        
        input_text = f"""
        Transaction Details: {json.dumps(transaction_details, ensure_ascii=False)}
        Current Structure: {transaction_details.get('transaction_type', 'Unknown')}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            alternatives = json.loads(response.choices[0].message.content)
            if isinstance(alternatives, dict) and "alternatives" in alternatives:
                return alternatives["alternatives"]
            elif isinstance(alternatives, list):
                return alternatives
            else:
                return []
        except json.JSONDecodeError:
            # Fallback if the response isn't valid JSON
            return []
    
    @staticmethod
    def generate_amortization_schedule(transaction_details: Dict) -> pd.DataFrame:
        """
        Generate amortization schedule for the transaction
        
        Args:
            transaction_details: Dict containing transaction details
            
        Returns:
            Pandas DataFrame with amortization schedule
        """
        # Extract relevant details
        asset_cost = transaction_details.get("asset_cost", 0)
        if isinstance(transaction_details.get("additional_costs"), dict):
            additional_costs = sum(transaction_details["additional_costs"].values())
        else:
            additional_costs = transaction_details.get("additional_costs", 0)
        
        lease_term_years = transaction_details.get("lease_term_years", 1)
        annual_rental = transaction_details.get("annual_rental", 0)
        residual_value = transaction_details.get("residual_value", 0)
        transfer_price = transaction_details.get("transfer_price", 0)
        
        # Calculate values
        prime_cost = asset_cost + additional_costs
        rou_asset_value = prime_cost - transfer_price
        total_rentals = annual_rental * lease_term_years
        deferred_cost = total_rentals - rou_asset_value
        terminal_value_difference = residual_value - transfer_price
        amortizable_amount = rou_asset_value - terminal_value_difference
        
        # Create amortization schedule
        periods = lease_term_years * 12  # Monthly periods
        monthly_rental = annual_rental / 12
        monthly_amortization = amortizable_amount / periods
        monthly_deferred_cost_amortization = deferred_cost / periods
        
        # Create DataFrame
        data = []
        remaining_rou = rou_asset_value
        remaining_deferred = deferred_cost
        
        for period in range(1, periods + 1):
            data.append({
                "Period": period,
                "Monthly Rental": monthly_rental,
                "ROU Amortization": monthly_amortization,
                "Remaining ROU": remaining_rou - monthly_amortization,
                "Deferred Cost Amortization": monthly_deferred_cost_amortization,
                "Remaining Deferred Cost": remaining_deferred - monthly_deferred_cost_amortization
            })
            remaining_rou -= monthly_amortization
            remaining_deferred -= monthly_deferred_cost_amortization
        
        return pd.DataFrame(data)
    
    @staticmethod
    def expert_commentary(transaction_details: Dict, standard_id: str) -> str:
        """
        Generate expert commentary on the transaction and accounting treatment
        
        Args:
            transaction_details: Dict containing transaction details
            standard_id: AAOIFI standard ID
            
        Returns:
            Expert commentary as string
        """
        # Use OpenAI to generate expert commentary
        system_prompt = """
        You are a senior Islamic finance expert with extensive experience in AAOIFI standards.
        Provide an expert commentary on the given transaction and its accounting treatment.
        
        Your commentary should include:
        1. Assessment of the transaction structure
        2. Key considerations in applying the relevant AAOIFI standard
        3. Potential areas requiring management judgment
        4. Disclosure implications
        5. Comparison with conventional accounting treatment (if applicable)
        
        Keep your commentary professional, concise but comprehensive, and focused on accounting implications.
        """
        
        input_text = f"""
        Transaction Details: {json.dumps(transaction_details, ensure_ascii=False)}
        AAOIFI Standard: {standard_id}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ]
        )
        
        return response.choices[0].message.content
    
    @staticmethod
    def generate_qna(transaction_details: Dict, standard_id: str) -> List[Dict]:
        """
        Generate Q&A about the transaction and standard application
        
        Args:
            transaction_details: Dict containing transaction details
            standard_id: AAOIFI standard ID
            
        Returns:
            List of Dict with Q&A pairs
        """
        # Use OpenAI to generate Q&A
        system_prompt = """
        You are an expert in Islamic finance accounting.
        Generate 5 question-answer pairs that address key aspects of applying 
        the specified AAOIFI standard to the given transaction.
        
        Questions should cover:
        1. Initial recognition
        2. Subsequent measurement
        3. Presentation
        4. Disclosure
        5. Challenging aspects or edge cases
        
        Format your response as a JSON array of objects, each with "question" and "answer" keys.
        """
        
        input_text = f"""
        Transaction Details: {json.dumps(transaction_details, ensure_ascii=False)}
        AAOIFI Standard: {standard_id}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            qna_data = json.loads(response.choices[0].message.content)
            if isinstance(qna_data, dict) and "qna" in qna_data:
                return qna_data["qna"]
            elif isinstance(qna_data, list):
                return qna_data
            else:
                return []
        except json.JSONDecodeError:
            # Fallback if the response isn't valid JSON
            return []

# Example usage
def demonstrate_advanced_features():
    """Demo function to showcase advanced features"""
    
    # Sample transaction details
    transaction_details = {
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
    }
    
    # Standard ID
    standard_id = "FAS_32"
    
    # Generate transaction flow diagram
    flow_graph = AdvancedIslamicFinanceAI.generate_transaction_flow_diagram(transaction_details)
    flow_fig = AdvancedIslamicFinanceAI.visualize_transaction_flow(flow_graph)
    
    # Generate Shariah compliance analysis
    compliance_analysis = AdvancedIslamicFinanceAI.generate_shariah_compliance_analysis(
        transaction_details, standard_id)
    
    # Generate alternative structures
    alternatives = AdvancedIslamicFinanceAI.generate_alternative_structures(transaction_details)
    
    # Generate amortization schedule
    amortization_schedule = AdvancedIslamicFinanceAI.generate_amortization_schedule(transaction_details)
    
    # Generate expert commentary
    commentary = AdvancedIslamicFinanceAI.expert_commentary(transaction_details, standard_id)
    
    # Generate Q&A
    qna = AdvancedIslamicFinanceAI.generate_qna(transaction_details, standard_id)
    
    # Print results
    print("===== Transaction Flow Diagram Created =====")
    print("\n===== Shariah Compliance Analysis =====")
    print(json.dumps(compliance_analysis, indent=2, ensure_ascii=False))
    print("\n===== Alternative Structures =====")
    print(json.dumps(alternatives, indent=2, ensure_ascii=False))
    print("\n===== Amortization Schedule (First 5 Periods) =====")
    print(amortization_schedule.head())
    print("\n===== Expert Commentary =====")
    print(commentary)
    print("\n===== Q&A =====")
    print(json.dumps(qna, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    demonstrate_advanced_features()