from flask import Flask, request, jsonify, render_template
from flask_caching import Cache
from modules.islamic_finance import IslamicFinanceAI
from modules.visualizations import create_journal_entries_chart
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
class Config:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    MAX_INPUT_LENGTH = 2000  # Prevent overly long inputs
    CACHE_TIMEOUT = 3600  # 1 hour cache for standards

app.config.from_object(Config)

# Initialize caching
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

# Initialize the Islamic Finance AI
if not app.config['OPENAI_API_KEY']:
    raise ValueError("OPENAI_API_KEY environment variable not set")

ai_system = IslamicFinanceAI(api_key=app.config['OPENAI_API_KEY'])

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_transaction():
    """
    Process a transaction description and return analysis results
    ---
    tags:
      - Transactions
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            input_text:
              type: string
              description: Transaction description
            language:
              type: string
              enum: [english, arabic, french]
              default: english
            visualize:
              type: boolean
              default: true
    responses:
      200:
        description: Successful processing
      400:
        description: Invalid input
      500:
        description: Processing error
    """
    # Validate input
    if not request.json or 'input_text' not in request.json:
        return jsonify({"error": "Missing required parameter: input_text"}), 400
        
    input_text = request.json['input_text'].strip()
    if not input_text:
        return jsonify({"error": "Input text cannot be empty"}), 400
    if len(input_text) > app.config['MAX_INPUT_LENGTH']:
        return jsonify({"error": f"Input text exceeds maximum length of {app.config['MAX_INPUT_LENGTH']} characters"}), 400
    
    # Get optional parameters
    language = request.json.get('language', 'english')
    visualize = request.json.get('visualize', True)
    
    try:
        # Process through all stages
        transaction_details = ai_system.process_input(input_text, language)
        standard_id = ai_system.classify_standard(transaction_details)
        analysis_results = ai_system.analyze_transaction(transaction_details, standard_id)
        calculation_results = ai_system.calculate_entries(transaction_details, analysis_results)
        journal_entries = ai_system.generate_journal_entries(transaction_details, analysis_results, calculation_results)
        output = ai_system.format_output(transaction_details, standard_id, journal_entries, language)
        
        # Add visualization if requested
        if visualize:
            try:
                output["visualization"] = create_journal_entries_chart(journal_entries, language)
            except Exception as e:
                app.logger.warning(f"Visualization generation failed: {str(e)}")
                output["visualization_error"] = "Could not generate visualization"
        
        return jsonify(output)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
        return jsonify({"error": "Internal processing error"}), 500

@app.route('/api/supported_standards', methods=['GET'])
@cache.cached(timeout=app.config['CACHE_TIMEOUT'])
def get_supported_standards():
    """
    Get list of supported AAOIFI standards
    ---
    tags:
      - Reference Data
    responses:
      200:
        description: List of supported standards
    """
    return jsonify({
        "standards": ai_system.get_standards_info(),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/health')
def health_check():
    """
    Service health check
    ---
    tags:
      - Service Status
    responses:
      200:
        description: Service status
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api')
def api_docs():
    """Basic API documentation"""
    base_url = request.url_root.rstrip('/')
    return jsonify({
        "endpoints": {
            f"{base_url}/api/process": {
                "method": "POST",
                "description": "Process Islamic finance transactions",
                "parameters": {
                    "input_text": {"type": "string", "required": True},
                    "language": {"type": "string", "enum": ["english", "arabic", "french"], "default": "english"},
                    "visualize": {"type": "boolean", "default": True}
                }
            },
            f"{base_url}/api/supported_standards": {
                "method": "GET",
                "description": "List supported AAOIFI standards"
            },
            f"{base_url}/api/health": {
                "method": "GET",
                "description": "Service health check"
            }
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get("DEBUG", False))