import re
import string
from collections import Counter

class MedicationNLP:
    """
    Enhanced NLP capabilities for the Virtual Pharmacist
    """
    
    def __init__(self, medications_df):
        self.medications_df = medications_df
        self.medication_names = set()
        self.generic_names = set()
        self.categories = set()
        self.common_words = set(['what', 'is', 'are', 'the', 'for', 'of', 'and', 'to', 'in', 'with', 'can', 'i', 'my', 'me', 'about', 'tell'])
        self._initialize_data()
    
    def _initialize_data(self):
        """Initialize data structures for faster lookups"""
        if self.medications_df is not None and not self.medications_df.empty:
            # Extract all medication names (lowercase for case-insensitive matching)
            self.medication_names = {name.lower() for name in self.medications_df['Trade_Name'].dropna()}
            
            # Extract all generic names
            self.generic_names = {name.lower() for name in self.medications_df['Generic_Name'].dropna()}
            
            # Extract all categories
            self.categories = {cat.lower() for cat in self.medications_df['Category'].dropna()}
    
    def preprocess_text(self, text):
        """Clean and preprocess text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        return text
    
    def extract_keywords(self, text):
        """Extract important keywords from the text"""
        # Preprocess the text
        processed_text = self.preprocess_text(text)
        
        # Split into words
        words = processed_text.split()
        
        # Remove common words
        keywords = [word for word in words if word not in self.common_words]
        
        return keywords
    
    def identify_medication_names(self, text):
        """Identify medication names mentioned in the text"""
        processed_text = self.preprocess_text(text)
        
        found_medications = []
        
        # Check for exact medication names
        for med_name in self.medication_names:
            if med_name in processed_text:
                # Find the original medication name with proper capitalization
                original_name = next((name for name in self.medications_df['Trade_Name'] 
                                     if name.lower() == med_name), med_name)
                found_medications.append(original_name)
        
        # Check for generic names
        for gen_name in self.generic_names:
            if gen_name in processed_text:
                # Find medications with this generic name
                matching_meds = self.medications_df[
                    self.medications_df['Generic_Name'].str.lower() == gen_name
                ]['Trade_Name'].tolist()
                found_medications.extend(matching_meds)
        
        return list(set(found_medications))  # Remove duplicates
    
    def identify_intent(self, text):
        """Identify the user's intent from the question"""
        processed_text = self.preprocess_text(text)
        
        # Define intent patterns
        intent_patterns = {
            'side_effects': ['side effect', 'adverse', 'reaction', 'negative', 'bad'],
            'price': ['price', 'cost', 'how much', 'expensive', 'cheap'],
            'usage': ['use', 'treat', 'for', 'indication', 'what is', 'what\'s', 'help with'],
            'dosage': ['dose', 'dosage', 'how much', 'how many', 'take', 'frequency'],
            'category': ['category', 'type', 'class', 'group', 'similar to'],
            'comparison': ['compare', 'versus', 'vs', 'difference', 'better', 'worse'],
            'availability': ['available', 'find', 'get', 'buy', 'purchase'],
            'storage': ['store', 'keep', 'refrigerate', 'temperature']
        }
        
        # Check for each intent
        matched_intents = {}
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in processed_text:
                    if intent in matched_intents:
                        matched_intents[intent] += 1
                    else:
                        matched_intents[intent] = 1
        
        # Return the intent with the most matches, or None if no matches
        if matched_intents:
            return max(matched_intents.items(), key=lambda x: x[1])[0]
        return 'general_info'  # Default intent
    
    def identify_category_query(self, text):
        """Identify if the user is asking about medications for a specific condition"""
        processed_text = self.preprocess_text(text)
        
        # Check for patterns like "medications for X"
        patterns = [
            r'medications? for ([\w\s]+)',
            r'drugs? for ([\w\s]+)',
            r'medicine for ([\w\s]+)',
            r'treatment for ([\w\s]+)',
            r'cure for ([\w\s]+)',
            r'remedy for ([\w\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, processed_text)
            if match:
                condition = match.group(1).strip()
                return condition
        
        return None
    
    def analyze_question(self, question):
        """
        Analyze a user question and extract structured information
        
        Returns:
            dict: Contains extracted information including:
                - medications: List of medication names mentioned
                - intent: The primary intent of the question
                - condition: Condition being asked about (if applicable)
                - keywords: Important keywords from the question
        """
        result = {
            'medications': self.identify_medication_names(question),
            'intent': self.identify_intent(question),
            'condition': self.identify_category_query(question),
            'keywords': self.extract_keywords(question)
        }
        
        return result

# Example usage (if run directly)
if __name__ == "__main__":
    import pandas as pd
    
    # Load the dataset
    try:
        url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/finaldatasets-EwfO5Xa82dxayNxObPBoz3Pzyujsvg.csv"
        df = pd.read_csv(url)
        
        # Initialize the NLP processor
        nlp = MedicationNLP(df)
        
        # Test with some example questions
        test_questions = [
            "What are the side effects of Panadol?",
            "How much does Lipitor cost?",
            "What is Zyrtec used for?",
            "Can you tell me about medications for allergies?",
            "What's the difference between generic and brand medications?",
            "How should I store my antibiotics?"
        ]
        
        print("Testing NLP analysis with example questions:")
        for question in test_questions:
            analysis = nlp.analyze_question(question)
            print(f"\nQuestion: {question}")
            print(f"Medications mentioned: {analysis['medications']}")
            print(f"Intent: {analysis['intent']}")
            print(f"Condition: {analysis['condition']}")
            print(f"Keywords: {analysis['keywords']}")
    
    except Exception as e:
        print(f"Error: {e}")
