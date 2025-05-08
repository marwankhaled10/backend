import pandas as pd

# Load your dataset
df = pd.read_csv("finaldatasets.csv")
df['Indications_for_Use'] = df['Indications_for_Use'].astype(str).str.lower()

# Define symptoms
simple_symptoms = [
    'headache', 'fever', 'cough', 'cold', 'sore throat', 'diarrhea',
    'spasm', 'nausea', 'indigestion', 'constipation', 'bloating', 'allergies', 'acne'
]

emergency_symptoms = [
    'chest pain', 'vision loss', 'severe bleeding', 'unconscious',
    'seizure', 'difficulty breathing', 'blood in stool', 
    'high blood pressure', 'persistent vomiting'
]

def chatbot_response(user_input):
    user_input = user_input.lower()

    for symptom in emergency_symptoms:
        if symptom in user_input:
            return "⚠️ This seems serious. Please consult a doctor immediately."

    for symptom in simple_symptoms:
        if symptom in user_input:
            matches = df[df['Indications_for_Use'].str.contains(symptom, na=False)]
            if not matches.empty:
                suggestions = matches[['Trade_Name', 'Indications_for_Use']].head(3).to_dict(orient='records')
                reply = "💊 Here are some medicines that may help:\n"
                for item in suggestions:
                    reply += f"- {item['Trade_Name']}: {item['Indications_for_Use']}\n"
                return reply
            else:
                return "✅ I understand your symptom, but I couldn't find a matching medicine in my database."

    return "❓ I'm not sure about that symptom. Please consult a doctor to be safe."

# Loop to chat with user
print("👨‍⚕️ Welcome to the Medical Chatbot! (type 'exit' to quit)\n")
while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Bot: Stay safe! 👋")
        break
    response = chatbot_response(user_input)
    print("Bot:", response)
