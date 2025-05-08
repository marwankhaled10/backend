import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import pandas as pd
from medication_processor import MedicationProcessor

logger = logging.getLogger(__name__)

class QuestionAnsweringEngine:
    """
    Engine for answering questions about medications
    """
    
    def __init__(self, medication_processor: MedicationProcessor):
        """
        Initialize the QuestionAnsweringEngine
        
        Args:
            medication_processor: Instance of MedicationProcessor
        """
        self.medication_processor = medication_processor
        self.common_words = {
            'what', 'is', 'are', 'the', 'for', 'of', 'and', 'to', 'in', 'with', 
            'can', 'i', 'my', 'me', 'about', 'tell', 'how', 'much', 'does', 'cost',
            'a', 'an', 'this', 'that', 'these', 'those', 'it', 'they', 'them',
            'use', 'used', 'using', 'take', 'taking', 'have', 'has', 'had',
            'do', 'does', 'did', 'should', 'would', 'could', 'will', 'shall'
        }
        
        # Intent patterns for different types of questions
        self.intent_patterns = {
            'side_effects': [
                r'side effect', r'adverse', r'reaction', r'negative', r'bad effect',
                r'harmful', r'danger', r'risk', r'warning'
            ],
            'price': [
                r'price', r'cost', r'how much', r'expensive', r'cheap', r'afford'
            ],
            'usage': [
                r'use', r'treat', r'for', r'indication', r'what is', r'what\'s', 
                r'help with', r'cure', r'heal', r'remedy', r'therapy', r'treatment'
            ],
            'dosage': [
                r'dose', r'dosage', r'how much', r'how many', r'take', r'frequency',
                r'daily', r'times a day', r'administration', r'how to take'
            ],
            'category': [
                r'category', r'type', r'class', r'group', r'similar to', r'classification'
            ],
            'comparison': [
                r'compare', r'versus', r'vs', r'difference', r'better', r'worse',
                r'alternative', r'substitute', r'replacement'
            ],
            'availability': [
                r'available', r'find', r'get', r'buy', r'purchase', r'obtain',
                r'where can i', r'pharmacy', r'store', r'online'
            ],
            'storage': [
                r'store', r'keep', r'refrigerate', r'temperature', r'shelf life',
                r'expiration', r'expire', r'stability'
            ],
            'interaction': [
                r'interact', r'interaction', r'together with', r'combine', r'mix',
                r'along with', r'simultaneously', r'conflict'
            ],
            'pregnancy': [
                r'pregnancy', r'pregnant', r'breastfeeding', r'nursing', r'lactation',
                r'expecting', r'trimester'
            ]
        }
    
    def _preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess text
        
        Args:
            text: Text to preprocess
            
        Returns:
            Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from the text
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of keywords
        """
        # Preprocess the text
        processed_text = self._preprocess_text(text)
        
        # Split into words
        words = processed_text.split()
        
        # Remove common words
        keywords = [word for word in words if word not in self.common_words]
        
        return keywords
    
    def _identify_medication_names(self, text: str) -> List[Dict[str, Any]]:
        """
        Identify medication names mentioned in the text
        
        Args:
            text: Text to identify medication names in
            
        Returns:
            List of medication dictionaries
        """
        processed_text = self._preprocess_text(text)
        found_medications = []
        
        # Check for exact medication names
        for name, idx in self.medication_processor.trade_name_index.items():
            if name in processed_text:
                medication = self.medication_processor.medications_dict.get(str(idx))
                if medication:
                    found_medications.append(medication)
        
        # Check for generic names
        for name, idx in self.medication_processor.generic_name_index.items():
            if name in processed_text:
                medication = self.medication_processor.medications_dict.get(str(idx))
                if medication:
                    found_medications.append(medication)
        
        # Remove duplicates (by ID)
        unique_medications = {}
        for med in found_medications:
            unique_medications[med['id']] = med
        
        return list(unique_medications.values())
    
    def _identify_intent(self, text: str) -> str:
        """
        Identify the user's intent from the question
        
        Args:
            text: Question text
            
        Returns:
            Intent string
        """
        processed_text = self._preprocess_text(text)
        
        # Check for each intent
        matched_intents = {}
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(r'\b' + pattern + r'\b', processed_text):
                    if intent in matched_intents:
                        matched_intents[intent] += 1
                    else:
                        matched_intents[intent] = 1
        
        # Return the intent with the most matches, or 'general_info' if no matches
        if matched_intents:
            return max(matched_intents.items(), key=lambda x: x[1])[0]
        return 'general_info'
    
    def _identify_category_query(self, text: str) -> Optional[str]:
        """
        Identify if the user is asking about medications for a specific condition
        
        Args:
            text: Question text
            
        Returns:
            Condition string or None
        """
        processed_text = self._preprocess_text(text)
        
        # Check for patterns like "medications for X"
        patterns = [
            r'medications? for ([\w\s]+)',
            r'drugs? for ([\w\s]+)',
            r'medicine for ([\w\s]+)',
            r'treatment for ([\w\s]+)',
            r'cure for ([\w\s]+)',
            r'remedy for ([\w\s]+)',
            r'what (treats|cures|helps with) ([\w\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, processed_text)
            if match:
                if pattern.endswith('([\w\s]+)'):
                    condition = match.group(1).strip()
                else:
                    condition = match.group(2).strip()
                return condition
        
        return None
    
    def _analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyze a user question and extract structured information
        
        Args:
            question: User question
            
        Returns:
            Dictionary containing extracted information
        """
        result = {
            'medications': self._identify_medication_names(question),
            'intent': self._identify_intent(question),
            'condition': self._identify_category_query(question),
            'keywords': self._extract_keywords(question)
        }
        
        return result
    
    def _generate_side_effects_response(self, medication: Dict[str, Any]) -> str:
        """Generate a response about side effects"""
        side_effects = medication.get('Side_Effects', [])
        
        if not side_effects:
            return f"**Side Effects of {medication['Trade_Name']}:**\n\nNo specific side effects are listed in our database for {medication['Trade_Name']}. Please consult your doctor or pharmacist for more information."
        
        response = f"**Side Effects of {medication['Trade_Name']}:**\n\n"
        response += '\n'.join([f"• {effect}" for effect in side_effects])
        response += "\n\nIf you experience severe side effects, contact your healthcare provider immediately."
        
        return response
    
    def _generate_price_response(self, medication: Dict[str, Any]) -> str:
        """Generate a response about price"""
        return f"**{medication['Trade_Name']}** is priced at {medication['Price']}.\n\nPlease note that prices may vary by location and pharmacy."
    
    def _generate_usage_response(self, medication: Dict[str, Any]) -> str:
        """Generate a response about usage"""
        response = f"**{medication['Trade_Name']}** ({medication['Generic_Name']}) is used for:\n\n{medication['Indications_for_Use']}"
        
        if medication['Dosage_Form'] and medication['Strength']:
            response += f"\n\nIt comes as {medication['Dosage_Form']} with strength of {medication['Strength']}."
        
        return response
    
    def _generate_general_info_response(self, medication: Dict[str, Any]) -> str:
        """Generate a general information response"""
        response = f"**{medication['Trade_Name']}** ({medication['Generic_Name']})\n\n"
        response += f"**Category:** {medication['Category']}\n\n"
        response += f"**Used for:** {medication['Indications_for_Use']}\n\n"
        response += f"**Dosage Form:** {medication['Dosage_Form']}\n"
        response += f"**Strength:** {medication['Strength']}\n"
        response += f"**Quantity:** {medication['Quantity_of_Dosage_Form']}\n"
        response += f"**Price:** {medication['Price']}\n"
        response += f"**Origin:** {medication['Local_Import']}\n\n"
        
        side_effects = medication.get('Side_Effects', [])
        if side_effects:
            response += "**Common Side Effects:**\n"
            for i, effect in enumerate(side_effects[:5]):
                response += f"• {effect}\n"
            
            if len(side_effects) > 5:
                response += f"\nAnd {len(side_effects) - 5} more side effects."
        
        return response
    
    def _generate_category_response(self, condition: str) -> str:
        """Generate a response for medications in a category or for a condition"""
        # Search for medications by category or indication
        matching_meds = []
        
        for med in self.medication_processor.medications_dict.values():
            if (condition.lower() in med['Category'].lower() or 
                condition.lower() in med['Indications_for_Use'].lower()):
                matching_meds.append(med)
        
        if not matching_meds:
            return f"I couldn't find any medications specifically for '{condition}' in our database. Please try a different search term or consult with your healthcare provider."
        
        response = f"Here are medications that might be used for {condition}:\n\n"
        
        for i, med in enumerate(matching_meds[:5]):
            response += f"**{med['Trade_Name']}** ({med['Generic_Name']})\n"
            response += f"• {med['Indications_for_Use']}\n"
            response += f"• Price: {med['Price']}\n\n"
        
        if len(matching_meds) > 5:
            response += f"And {len(matching_meds) - 5} more. You can ask about any specific medication for more details."
        
        return response
    
    def _generate_storage_response(self) -> str:
        """Generate a response about medication storage"""
        return "Here are some general guidelines for storing medications properly:\n\n1. Keep in a cool, dry place (avoid bathroom medicine cabinets which can be humid)\n2. Store at room temperature (15-25°C or 59-77°F) unless specified otherwise\n3. Keep away from direct sunlight\n4. Store in original containers with labels intact\n5. Keep medications out of reach of children and pets\n6. Some medications require refrigeration - check the label\n7. Don't use medications past their expiration date\n8. Don't store different medications in the same container\n\nAlways check the specific storage instructions on your medication's packaging or ask your pharmacist for guidance."
    
    def _generate_generic_vs_brand_response(self) -> str:
        """Generate a response about generic vs brand medications"""
        return "Generic vs. Brand-Name Medications:\n\n**Brand-Name Medications:**\n• Developed and patented by pharmaceutical companies\n• Usually more expensive\n• Same active ingredients as their generic counterparts\n• Undergo extensive testing before FDA approval\n\n**Generic Medications:**\n• Contain the same active ingredients as brand-name versions\n• FDA-approved and meet the same quality standards\n• Usually 80-85% less expensive\n• May differ in inactive ingredients (colors, fillers, etc.)\n• Become available after the brand-name patent expires\n\nBoth types are equally effective for most people. The main difference is cost. However, some patients with specific sensitivities may respond differently to inactive ingredients in generic versions."
    
    def _generate_default_response(self) -> str:
        """Generate a default response when no specific information is found"""
        return 'Thank you for your question. Based on our medication database, I don\'t have specific information about that query.\n\nYou can ask about specific medications by name, their side effects, prices, or uses. You can also ask about medications for specific conditions.\n\nFor example, try asking:\n• "What is Panadol used for?"\n• "What are the side effects of Augmentin?"\n• "How much does Lipitor cost?"\n• "What medications are available for allergies?"\n\nFor more specific medical advice tailored to your situation, I recommend consulting with your healthcare provider or pharmacist.'
    
    def answer_question(self, question: str) -> str:
        """
        Answer a question about medications
        
        Args:
            question: User question
            
        Returns:
            Answer string
        """
        # Analyze the question
        analysis = self._analyze_question(question)
        logger.debug(f"Question analysis: {analysis}")
        
        # Check for medication information requests
        if analysis['medications']:
            medication = analysis['medications'][0]  # Use the first identified medication
            
            # Check what information is being requested
            if analysis['intent'] == 'side_effects':
                return self._generate_side_effects_response(medication)
            
            elif analysis['intent'] == 'price':
                return self._generate_price_response(medication)
            
            elif analysis['intent'] == 'usage':
                return self._generate_usage_response(medication)
            
            # Default to general information
            return self._generate_general_info_response(medication)
        
        # Check for category queries
        if analysis['condition']:
            return self._generate_category_response(analysis['condition'])
        
        # Handle general questions about medication storage, etc.
        if 'store' in question.lower() and ('medication' in question.lower() or 'medicine' in question.lower()):
            return self._generate_storage_response()
        
        if 'generic' in question.lower() and 'brand' in question.lower():
            return self._generate_generic_vs_brand_response()
        
        # Default response for other questions
        return self._generate_default_response()
