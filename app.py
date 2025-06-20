# app.py
import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# --- Configuration ---
# To run this app, you need to set your Gemini API key as an environment variable.
# For example, in your terminal:
# export GEMINI_API_KEY='YOUR_API_KEY'
# Or, for development, you can uncomment the line below and add your key directly.
# IMPORTANT: Do not hardcode your key in production code.
# os.environ['GEMINI_API_KEY'] = "YOUR_API_KEY" 

try:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
except AttributeError:
    print("="*80)
    print("ERROR: The Gemini API key is not configured.")
    print("Please set the GEMINI_API_KEY environment variable.")
    print("For example: export GEMINI_API_KEY='YOUR_API_KEY'")
    print("="*80)
    exit()

# --- Gemini Model ---
# We will use the gemini-1.5-flash model.
model = genai.GenerativeModel('gemini-2.0-flash')

def clean_json_response(text):
    """
    Cleans the model's response to get a valid JSON string.
    The model might wrap the JSON in markdown backticks.
    """
    if '```json' in text:
        text = text.split('```json')[1]
    if '```' in text:
        text = text.split('```')[0]
    return text.strip()


@app.route('/', methods=['GET'])
def index():
    """Renders the main page."""
    return render_template('index.html')


@app.route('/check_spelling', methods=['POST'])
def check_spelling():
    """
    Handles the spell-checking logic, now with suggestions.
    """
    try:
        text_to_check = request.form.get('text', '')
        if not text_to_check.strip():
            return jsonify({'error': 'Please enter some text to check.'}), 400

        # --- Prompt Engineering for Spelling and Suggestions ---
        # The prompt is updated to ask for a suggestion for each error.
        prompt = f"""
        Please analyze the following Thai text for spelling errors. 
        Your response must be in a clean JSON format without any markdown.
        The JSON object should have a single key "errors".
        The value of "errors" should be an array of objects, where each object represents a misspelled word and contains three keys: 
        1. "word" (the incorrect word)
        2. "index" (the starting position of that word in the original text)
        3. "suggestion" (the suggested correction)

            
        
        {{
            "errors": [
                {{"word": "ฉัรรัก", "word_index": 0, "suggestion": "ฉันรัก"}},
                {{"word": "ประเทษ", "word_index": 6, "suggestion": "ประเทศ"}},
                {{"word": "ไท", "word_index": 12, "suggestion": "ไทย"}}
            ]
        }}
        
        If there are no errors, return an empty array for "errors".

        Here is the text to check:
        "{text_to_check}"
        """
        # --- API Call ---
        response = model.generate_content(prompt)
        #print(f"Response from Gemini API: {response.text}")
        
        cleaned_response_text = clean_json_response(response.text)
        #print(f"Cleaned response text: {cleaned_response_text}")

        # Validate that the response is valid JSON
        try:
            json.loads(cleaned_response_text)
        except json.JSONDecodeError:
            # If parsing fails, ask the model to fix the JSON
            fix_prompt = f"The following text is not valid JSON. Please fix it and provide only the valid JSON object: {cleaned_response_text}"
            correction_response = model.generate_content(fix_prompt)
            cleaned_response_text = clean_json_response(correction_response.text)

        return jsonify({'original_text': text_to_check, 'result': cleaned_response_text})

    except Exception as e:
        print(f"An error occurred in /check_spelling: {e}")
        return jsonify({'error': 'An error occurred while communicating with the Gemini API.'}), 500


if __name__ == '__main__':
    app.run(debug=True)
