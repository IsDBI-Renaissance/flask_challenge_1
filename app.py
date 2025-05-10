from flask import Flask, request, jsonify
from flask_caching import Cache
from modules.islamic_finance import IslamicFinanceAI
from modules.visualizations import create_journal_entries_chart
import os
from datetime import datetime
from dotenv import load_dotenv
import logging

# Setup
load_dotenv()
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Configuration
app.config.update({
    'TOGETHER_API_KEY': os.environ.get("TOGETHER_API_KEY"),
    'MAX_INPUT_LENGTH': 2000
})

# Initialize AI
ai_system = IslamicFinanceAI(api_key=app.config['TOGETHER_API_KEY'])

@app.route('/api/process', methods=['POST'])
def process():
    """Main endpoint with robust error handling"""
    try:
        # Validate input
        data = request.get_json()
        if not data or 'input_text' not in data:
            return jsonify({"error": "Missing input_text"}), 400
        
        input_text = data['input_text'][:app.config['MAX_INPUT_LENGTH']]
        language = data.get('language', 'english')
        visualize = data.get('visualize', True)

        # Process transaction
        details = ai_system.process_input(input_text, language)
        result = ai_system.generate_entries(details)
        
        # Add visualization
        if visualize and result.get('journal_entries'):
            try:
                # Prepare the data in the correct format for visualization
                chart_data = {
                    "accounts": [entry["account"] for entry in result["journal_entries"]],
                    "debits": [entry["debit"] for entry in result["journal_entries"]],
                    "credits": [entry["credit"] for entry in result["journal_entries"]]
                }
                visualization_data = {"chart_data": chart_data}
                result['visualization'] = create_journal_entries_chart(visualization_data, language)
            except Exception as e:
                result['visualization_error'] = str(e)

        # Format response
        response = {
            "transaction": details,
            "accounting_entries": result,
            "standard": ai_system.standards[result['standard_id']],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(response)

    except Exception as e:
        return jsonify({
            "error": "Processing error",
            "details": str(e)
        }), 500

@app.route('/api/standards', methods=['GET'])
@cache.cached(timeout=3600)
def get_standards():
    return jsonify(ai_system.get_standards_info())

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('DEBUG', False))