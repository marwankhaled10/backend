import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import numpy as np

def analyze_medication_data():
    """
    Analyze the medication dataset and generate insights
    """
    try:
        # Load the dataset
        url = "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/finaldatasets-EwfO5Xa82dxayNxObPBoz3Pzyujsvg.csv"
        df = pd.read_csv(url)
        print(f"Successfully loaded dataset with {len(df)} medications")
        
        # Basic dataset information
        print("\n=== Dataset Overview ===")
        print(f"Total medications: {len(df)}")
        print(f"Number of columns: {len(df.columns)}")
        
        # Category analysis
        print("\n=== Category Analysis ===")
        category_counts = df['Category'].value_counts()
        print(f"Number of unique categories: {len(category_counts)}")
        print("\nTop 10 categories:")
        print(category_counts.head(10))
        
        # Price analysis
        print("\n=== Price Analysis ===")
        # Convert price to numeric, handling any non-numeric values
        df['Price_Numeric'] = pd.to_numeric(df['Price'], errors='coerce')
        print(f"Average price: {df['Price_Numeric'].mean():.2f}")
        print(f"Median price: {df['Price_Numeric'].median():.2f}")
        print(f"Min price: {df['Price_Numeric'].min():.2f}")
        print(f"Max price: {df['Price_Numeric'].max():.2f}")
        
        # Side effects analysis
        print("\n=== Side Effects Analysis ===")
        # Count medications with side effects
        side_effects_columns = [col for col in df.columns if col.startswith('Side_Effect_')]
        has_side_effects = df[side_effects_columns].notna().any(axis=1).sum()
        print(f"Medications with at least one side effect: {has_side_effects} ({has_side_effects/len(df)*100:.1f}%)")
        
        # Collect all side effects
        all_side_effects = []
        for col in side_effects_columns:
            all_side_effects.extend(df[col].dropna().tolist())
        
        # Count frequency of each side effect
        side_effect_counts = Counter(all_side_effects)
        print("\nTop 10 most common side effects:")
        for effect, count in side_effect_counts.most_common(10):
            print(f"- {effect}: {count} occurrences")
        
        # Local vs Import analysis
        print("\n=== Local vs Import Analysis ===")
        origin_counts = df['Local/Import'].value_counts()
        print(origin_counts)
        
        # Generate some visualizations (these would be saved to files in a real scenario)
        print("\n=== Generating Visualizations ===")
        print("(In a real scenario, these would be saved as image files)")
        
        # 1. Category distribution (top 10)
        plt.figure(figsize=(12, 6))
        category_counts.head(10).plot(kind='bar')
        plt.title('Top 10 Medication Categories')
        plt.xlabel('Category')
        plt.ylabel('Number of Medications')
        plt.tight_layout()
        # plt.savefig('category_distribution.png')
        
        # 2. Price distribution
        plt.figure(figsize=(10, 6))
        sns.histplot(df['Price_Numeric'].dropna(), bins=30, kde=True)
        plt.title('Medication Price Distribution')
        plt.xlabel('Price')
        plt.ylabel('Frequency')
        plt.tight_layout()
        # plt.savefig('price_distribution.png')
        
        # 3. Local vs Import pie chart
        plt.figure(figsize=(8, 8))
        origin_counts.plot(kind='pie', autopct='%1.1f%%')
        plt.title('Local vs Imported Medications')
        plt.ylabel('')
        plt.tight_layout()
        # plt.savefig('local_vs_import.png')
        
        print("\nAnalysis complete!")
        
    except Exception as e:
        print(f"Error during data analysis: {e}")

if __name__ == "__main__":
    analyze_medication_data()
