import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Union
import re

logger = logging.getLogger(__name__)

class MedicationProcessor:
    """
    Class for processing and managing medication data
    """
    
    def __init__(self):
        """Initialize the MedicationProcessor"""
        self.df = None
        self.medications_dict = {}
        self.categories = []
        self.trade_name_index = {}
        self.generic_name_index = {}
        self.category_index = {}
        
    def load_data(self, source: str) -> bool:
        """
        Load medication data from a CSV file or URL
        
        Args:
            source: Path or URL to the CSV file
            
        Returns:
            bool: True if data was loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading medication data from {source}")
            self.df = pd.read_csv(source)
            
            # Clean the data
            self._clean_data()
            
            # Create indexes for faster lookups
            self._create_indexes()
            
            # Create a dictionary of medications for faster access
            self._create_medications_dict()
            
            logger.info(f"Successfully loaded {len(self.df)} medications")
            return True
        except Exception as e:
            logger.error(f"Error loading medication data: {str(e)}")
            return False
    
    def _clean_data(self) -> None:
        """Clean and preprocess the data"""
        # Fill NaN values
        self.df = self.df.fillna('')
        
        # Clean column names (remove whitespace)
        self.df.columns = [col.strip() for col in self.df.columns]
        
        # Ensure required columns exist
        required_columns = ['SN.', 'Trade_Name', 'Generic_Name', 'Category', 'Price']
        for col in required_columns:
            if col not in self.df.columns:
                logger.warning(f"Required column '{col}' not found in dataset")
        
        # Convert price to numeric where possible
        if 'Price' in self.df.columns:
            self.df['Price_Numeric'] = pd.to_numeric(self.df['Price'], errors='coerce')
    
    def _create_indexes(self) -> None:
        """Create indexes for faster lookups"""
        # Extract categories
        if 'Category' in self.df.columns:
            self.categories = sorted(self.df['Category'].dropna().unique().tolist())
            
            # Create category index
            for category in self.categories:
                self.category_index[category.lower()] = category
        
        # Create trade name index
        if 'Trade_Name' in self.df.columns:
            for idx, name in enumerate(self.df['Trade_Name']):
                if pd.notna(name) and name:
                    self.trade_name_index[name.lower()] = idx
        
        # Create generic name index
        if 'Generic_Name' in self.df.columns:
            for idx, name in enumerate(self.df['Generic_Name']):
                if pd.notna(name) and name:
                    self.generic_name_index[name.lower()] = idx
    
    def _create_medications_dict(self) -> None:
        """Create a dictionary of medications for faster access"""
        for idx, row in self.df.iterrows():
            # Extract side effects
            side_effects = []
            for i in range(1, 10):
                effect_col = f'Side_Effect_{i}'
                if effect_col in row and row[effect_col] and pd.notna(row[effect_col]):
                    side_effects.append(row[effect_col])
            
            # Create medication object
            medication = {
                'id': str(idx),
                'SN': row.get('SN.', ''),
                'Trade_Name': row.get('Trade_Name', ''),
                'Strength': row.get('Strenght/\nConc.', ''),
                'Dosage_Form': row.get('Dosage_Form', ''),
                'Quantity_of_Dosage_Form': row.get('Quantity_of_Dosage_Form', ''),
                'Price': row.get('Price', ''),
                'Generic_Name': row.get('Generic_Name', ''),
                'Local_Import': row.get('Local/Import', ''),
                'Category': row.get('Category', ''),
                'Indications_for_Use': row.get('Indications_for_Use', ''),
                'Side_Effects': side_effects,
                'Image_URL': row.get('Image_URL', '')
            }
            
            self.medications_dict[str(idx)] = medication
    
    def is_data_loaded(self) -> bool:
        """Check if data is loaded"""
        return self.df is not None and not self.df.empty
    
    def get_medication_count(self) -> int:
        """Get the number of medications"""
        return len(self.df) if self.df is not None else 0
    
    def get_categories(self) -> List[str]:
        """Get all medication categories"""
        return self.categories
    
    def get_medications(self, search: str = '', category: str = '', limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get medications, optionally filtered by search term or category
        
        Args:
            search: Search term to filter medications
            category: Category to filter medications
            limit: Maximum number of medications to return
            
        Returns:
            List of medication dictionaries
        """
        results = []
        
        # If no filters, return all medications (up to limit)
        if not search and not category:
            results = list(self.medications_dict.values())
            if limit:
                results = results[:limit]
            return results
        
        # Filter by category
        if category:
            if self.df is not None:
                category_filter = self.df['Category'] == category
                filtered_df = self.df[category_filter]
                
                for idx in filtered_df.index:
                    if str(idx) in self.medications_dict:
                        results.append(self.medications_dict[str(idx)])
        else:
            # Start with all medications
            results = list(self.medications_dict.values())
        
        # Filter by search term
        if search:
            search = search.lower()
            filtered_results = []
            
            for med in results:
                if (search in med['Trade_Name'].lower() or
                    search in med['Generic_Name'].lower() or
                    search in med['Category'].lower() or
                    search in med['Indications_for_Use'].lower()):
                    filtered_results.append(med)
            
            results = filtered_results
        
        # Apply limit
        if limit and len(results) > limit:
            results = results[:limit]
        
        return results
    
    def get_medication_by_id(self, medication_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a medication by its ID
        
        Args:
            medication_id: ID of the medication
            
        Returns:
            Medication dictionary or None if not found
        """
        return self.medications_dict.get(medication_id)
    
    def get_medication_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a medication by its trade name or generic name
        
        Args:
            name: Trade name or generic name of the medication
            
        Returns:
            Medication dictionary or None if not found
        """
        name_lower = name.lower()
        
        # Check trade name index
        if name_lower in self.trade_name_index:
            idx = self.trade_name_index[name_lower]
            return self.medications_dict.get(str(idx))
        
        # Check generic name index
        if name_lower in self.generic_name_index:
            idx = self.generic_name_index[name_lower]
            return self.medications_dict.get(str(idx))
        
        return None
    
    def advanced_search(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Perform an advanced search on medications
        
        Args:
            criteria: Dictionary of search criteria
            
        Returns:
            List of medication dictionaries matching the criteria
        """
        if self.df is None:
            return []
        
        query_df = self.df.copy()
        
        # Apply filters based on criteria
        if 'trade_name' in criteria and criteria['trade_name']:
            query_df = query_df[query_df['Trade_Name'].str.contains(criteria['trade_name'], case=False, na=False)]
        
        if 'generic_name' in criteria and criteria['generic_name']:
            query_df = query_df[query_df['Generic_Name'].str.contains(criteria['generic_name'], case=False, na=False)]
        
        if 'category' in criteria and criteria['category']:
            query_df = query_df[query_df['Category'] == criteria['category']]
        
        if 'min_price' in criteria and criteria['min_price'] is not None:
            query_df = query_df[query_df['Price_Numeric'] >= criteria['min_price']]
        
        if 'max_price' in criteria and criteria['max_price'] is not None:
            query_df = query_df[query_df['Price_Numeric'] <= criteria['max_price']]
        
        if 'indication' in criteria and criteria['indication']:
            query_df = query_df[query_df['Indications_for_Use'].str.contains(criteria['indication'], case=False, na=False)]
        
        # Convert results to list of dictionaries
        results = []
        for idx in query_df.index:
            if str(idx) in self.medications_dict:
                results.append(self.medications_dict[str(idx)])
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the medication dataset
        
        Returns:
            Dictionary of statistics
        """
        if self.df is None:
            return {}
        
        stats = {
            'total_medications': len(self.df),
            'total_categories': len(self.categories),
            'price_statistics': {},
            'categories_distribution': {},
            'dosage_forms_distribution': {},
            'local_import_distribution': {}
        }
        
        # Price statistics
        if 'Price_Numeric' in self.df.columns:
            price_stats = self.df['Price_Numeric'].describe().to_dict()
            stats['price_statistics'] = {
                'min': price_stats.get('min', 0),
                'max': price_stats.get('max', 0),
                'mean': price_stats.get('mean', 0),
                'median': self.df['Price_Numeric'].median()
            }
        
        # Categories distribution
        if 'Category' in self.df.columns:
            category_counts = self.df['Category'].value_counts().to_dict()
            stats['categories_distribution'] = category_counts
        
        # Dosage forms distribution
        if 'Dosage_Form' in self.df.columns:
            dosage_counts = self.df['Dosage_Form'].value_counts().to_dict()
            stats['dosage_forms_distribution'] = dosage_counts
        
        # Local/Import distribution
        if 'Local/Import' in self.df.columns:
            origin_counts = self.df['Local/Import'].value_counts().to_dict()
            stats['local_import_distribution'] = origin_counts
        
        return stats
