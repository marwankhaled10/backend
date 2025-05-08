from flask import Flask, request, jsonify
import pandas as pd
import logging
import os
from flask_cors import CORS
from medication_processor import MedicationProcessor
from question_answering import QuestionAnsweringEngine
from utils import setup_logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize global variables
medication_processor = None
qa_engine = None

@app.before_first_request
def initialize_data():
    """Initialize data before the first request"""
    global medication_processor, qa_engine
    
    try:
        # Initialize the medication processor
        logger.info("Initializing medication processor...")
        medication_processor = MedicationProcessor()
        
        # Load the dataset
        url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/finaldatasets-EwfO5Xa82dxayNxObPBoz3Pzyujsvg.csv"
        medication_processor.load_data(url)
        
        # Initialize the question answering engine
        logger.info("Initializing question answering engine...")
        qa_engine = QuestionAnsweringEngine(medication_processor)
        
        logger.info("Initialization complete!")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the API is running"""
    if medication_processor is None or not medication_processor.is_data_loaded():
        return jsonify({"status": "unhealthy", "message": "Data not loaded"}), 503
    
    return jsonify({
        "status": "healthy", 
        "medications_count": medication_processor.get_medication_count(),
        "categories_count": len(medication_processor.get_categories()),
        "version": "2.0.0"
    })

@app.route('/api/medications', methods=['GET'])
def get_medications():
    """Return a list of medications, optionally filtered by search term or category"""
    if medication_processor is None or not medication_processor.is_data_loaded():
        return jsonify({"error": "Medication data not available"}), 503
    
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    limit = request.args.get('limit', None)
    
    try:
        if limit and limit.isdigit():
            limit = int(limit)
        else:
            limit = None
            
        medications = medication_processor.get_medications(search=search, category=category, limit=limit)
        return jsonify(medications)
    except Exception as e:
        logger.error(f"Error retrieving medications: {str(e)}")
        return jsonify({"error": "Failed to retrieve medications"}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Return a list of all medication categories"""
    if medication_processor is None or not medication_processor.is_data_loaded():
        return jsonify({"error": "Medication data not available"}), 503
    
    try:
        categories = medication_processor.get_categories()
        return jsonify(categories)
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        return jsonify({"error": "Failed to retrieve categories"}), 500

@app.route('/api/medications/<medication_id>', methods=['GET'])
def get_medication_details(medication_id):
    """Return detailed information about a specific medication"""
    if medication_processor is None or not medication_processor.is_data_loaded():
        return jsonify({"error": "Medication data not available"}), 503
    
    try:
        medication = medication_processor.get_medication_by_id(medication_id)
        if medication:
            return jsonify(medication)
        else:
            return jsonify({"error": "Medication not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving medication details: {str(e)}")
        return jsonify({"error": "Failed to retrieve medication details"}), 500

@app.route('/api/answer', methods=['POST'])
def answer_question():
    """Answer a question about medications"""
    if qa_engine is None or not medication_processor.is_data_loaded():
        return jsonify({"error": "Question answering service not available"}), 503
    
    data = request.json
    if not data or 'question' not in data:
        return jsonify({"error": "No question provided"}), 400
    
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "Empty question provided"}), 400
    
    try:
        # Log the incoming question
        logger.info(f"Received question: {question}")
        
        # Process the question and generate a response
        response = qa_engine.answer_question(question)
        
        # Log the response (truncated for brevity in logs)
        truncated_response = response[:100] + "..." if len(response) > 100 else response
        logger.info(f"Generated response: {truncated_response}")
        
        return jsonify({"answer": response})
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        return jsonify({"error": "Failed to process your question"}), 500

@app.route('/api/search/advanced', methods=['POST'])
def advanced_search():
    """Perform an advanced search on medications"""
    if medication_processor is None or not medication_processor.is_data_loaded():
        return jsonify({"error": "Medication data not available"}), 503
    
    data = request.json
    if not data:
        return jsonify({"error": "No search criteria provided"}), 400
    
    try:
        results = medication_processor.advanced_search(data)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error performing advanced search: {str(e)}")
        return jsonify({"error": "Failed to perform advanced search"}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Return statistics about the medication dataset"""
    if medication_processor is None or not medication_processor.is_data_loaded():
        return jsonify({"error": "Medication data not available"}), 503
    
    try:
        stats = medication_processor.get_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error retrieving statistics: {str(e)}")
        return jsonify({"error": "Failed to retrieve statistics"}), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(debug=os.environ.get('FLASK_ENV') == 'development', 
            host='0.0.0.0', 
            port=port)
