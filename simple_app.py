from flask import Flask, request, jsonify
import json
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables to store medications and categories
medications = []
categories = []

def load_sample_data():
    """Load some sample medication data"""
    global medications, categories
    
    # Sample medications data
    medications = [
        {
            "id": "1",
            "Trade_Name": "Panadol",
            "Generic_Name": "Paracetamol",
            "Category": "Pain Relief",
            "Indications_for_Use": "For the relief of mild to moderate pain and fever",
            "Price": "$5.99",
            "Side_Effects": ["Nausea", "Stomach pain", "Rash", "Headache"]
        },
        {
            "id": "2",
            "Trade_Name": "Zyrtec",
            "Generic_Name": "Cetirizine",
            "Category": "Allergy",
            "Indications_for_Use": "For the relief of symptoms associated with seasonal allergies",
            "Price": "$12.99",
            "Side_Effects": ["Drowsiness", "Dry mouth", "Fatigue"]
        },
        {
            "id": "3",
            "Trade_Name": "Lipitor",
            "Generic_Name": "Atorvastatin",
            "Category": "Cholesterol",
            "Indications_for_Use": "For lowering blood cholesterol and reducing risk of heart disease",
            "Price": "$45.99",
            "Side_Effects": ["Muscle pain", "Digestive problems", "Liver enzyme abnormalities"]
        },
        {
            "id": "4",
            "Trade_Name": "Augmentin",
            "Generic_Name": "Amoxicillin/Clavulanate",
            "Category": "Antibiotic",
            "Indications_for_Use": "For treating bacterial infections",
            "Price": "$25.50",
            "Side_Effects": ["Diarrhea", "Nausea", "Vomiting", "Rash", "Headache"]
        },
        {
            "id": "5",
            "Trade_Name": "Ventolin",
            "Generic_Name": "Albuterol",
            "Category": "Respiratory",
            "Indications_for_Use": "For relief of bronchospasm in asthma and COPD",
            "Price": "$30.75",
            "Side_Effects": ["Nervousness", "Shaking", "Headache", "Throat irritation"]
        }
    ]
    
    # Extract categories
    categories = sorted(list(set(med["Category"] for med in medications)))
    
    print(f"Loaded {len(medications)} sample medications")
    print(f"Categories: {categories}")

@app.route('/', methods=['GET'])
def home():
    return '''
    <h1>Welcome to MedAI Flask API </h1>
    <p>Try the following endpoints:</p>
    <ul>
        <li>/api/health</li>
        <li>/api/medications</li>
        <li>/api/categories</li>
        <li>/api/answer (POST)</li>
    </ul>
    '''




@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the API is running"""
    return jsonify({
        "status": "healthy", 
        "medications_count": len(medications),
        "categories_count": len(categories)
    })

@app.route('/api/medications', methods=['GET'])
def get_medications():
    """Return a list of medications, optionally filtered by search term or category"""
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    
    # Filter medications
    filtered_meds = medications
    
    if category:
        filtered_meds = [med for med in filtered_meds if med.get('Category') == category]
    
    if search:
        filtered_meds = [
            med for med in filtered_meds if 
            search in str(med.get('Trade_Name', '')).lower() or
            search in str(med.get('Generic_Name', '')).lower() or
            search in str(med.get('Category', '')).lower() or
            search in str(med.get('Indications_for_Use', '')).lower()
        ]
    
    return jsonify(filtered_meds)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Return a list of all medication categories"""
    return jsonify(categories)

@app.route('/api/answer', methods=['POST'])
def answer_question():
    """Answer a question about medications"""
    data = request.json
    if not data or 'question' not in data:
        return jsonify({"error": "No question provided"}), 400
    
    question = data.get('question', '').lower()
    
    # Simple question answering logic
    for med in medications:
        trade_name = med.get('Trade_Name', '').lower()
        generic_name = med.get('Generic_Name', '').lower()
        
        if trade_name in question or generic_name in question:
            # Generate a response based on the medication
            if 'side effect' in question or 'adverse' in question:
                side_effects = med.get('Side_Effects', [])
                
                if side_effects:
                    response = f"**Side Effects of {med['Trade_Name']}:**\n\n"
                    response += '\n'.join([f"• {effect}" for effect in side_effects])
                    response += "\n\nIf you experience severe side effects, contact your healthcare provider immediately."
                else:
                    response = f"No specific side effects are listed for {med['Trade_Name']}."
                
                return jsonify({"answer": response})
            
            if 'price' in question or 'cost' in question or 'how much' in question:
                return jsonify({"answer": f"**{med['Trade_Name']}** is priced at {med.get('Price', 'N/A')}.\n\nPlease note that prices may vary by location and pharmacy."})
            
            if 'use' in question or 'for' in question or 'treat' in question or 'indication' in question:
                return jsonify({"answer": f"**{med['Trade_Name']}** ({med['Generic_Name']}) is used for:\n\n{med.get('Indications_for_Use', 'N/A')}"})
            
            # General information
            response = f"**{med['Trade_Name']}** ({med['Generic_Name']})\n\n"
            response += f"**Category:** {med.get('Category', 'N/A')}\n\n"
            response += f"**Used for:** {med.get('Indications_for_Use', 'N/A')}\n\n"
            response += f"**Price:** {med.get('Price', 'N/A')}\n\n"
            
            if med.get('Side_Effects'):
                response += "**Common Side Effects:**\n"
                for effect in med.get('Side_Effects', [])[:5]:
                    response += f"• {effect}\n"
            
            return jsonify({"answer": response})
    
    # Check for category queries
    if 'medications for' in question or 'drugs for' in question or 'medicine for' in question:
        for category in categories:
            if category.lower() in question:
                category_meds = [med for med in medications if med.get('Category') == category]
                
                if category_meds:
                    response = f"Here are medications for {category}:\n\n"
                    
                    for med in category_meds:
                        response += f"**{med['Trade_Name']}** ({med['Generic_Name']})\n"
                        response += f"• {med['Indications_for_Use']}\n"
                        response += f"• Price: {med['Price']}\n\n"
                    
                    return jsonify({"answer": response})
    
    # Default response
    return jsonify({
        "answer": "Thank you for your question. Based on our medication database, I don't have specific information about that query.\n\nYou can ask about specific medications by name, their side effects, prices, or uses. You can also ask about medications for specific conditions.\n\nFor example, try asking:\n• \"What is Panadol used for?\"\n• \"What are the side effects of Augmentin?\"\n• \"How much does Lipitor cost?\"\n• \"What medications are available for allergies?\""
    })

if __name__ == '__main__':
    # Load sample data
    load_sample_data()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)