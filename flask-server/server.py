from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import re
import os
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_API_KEY_HERE')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.0-pro')

all_gift_ideas = []

@app.route('/generate_gift_idea', methods=['POST'])
def generate_gift_idea():
    try:
        data = request.json
        logging.debug(f"Received data for generating gift idea: {data}")

        age = data.get('age', '')
        gender = data.get('gender', '')
        occasion = data.get('occasion', '')
        recipient_type = data.get('recipient_type', '')
        categories = data.get('categories', [])
        price_range = data.get('price_range', '')
        prompt = data.get('prompt', '')
        
        prompt_text = create_search_prompt(prompt) if prompt else create_prompt(age, gender, occasion, recipient_type, categories, price_range)
        logging.debug(f"Generated prompt: {prompt_text}")

        response = model.generate_content(prompt_text)
        logging.debug(f"Model response: {response}")

        cleaned_text = clean_text(response.text)
        logging.debug(f"Cleaned response text: {cleaned_text}")

        gift_ideas = process_and_structure_gift_ideas(cleaned_text)
        logging.debug(f"Processed gift ideas: {gift_ideas}")

        unique_gift_ideas = filter_unique_gift_ideas(gift_ideas)
        logging.debug(f"Unique gift ideas: {unique_gift_ideas}")

        all_gift_ideas.extend(unique_gift_ideas)
        logging.debug(f"Updated global gift ideas list: {all_gift_ideas}")

        return jsonify({"gift_ideas": unique_gift_ideas})
    except Exception as e:
        logging.error(f"Error generating gift ideas: {e}", exc_info=True)
        return jsonify({"error": "Error generating gift ideas"}), 500

@app.route('/generate_more_gift_ideas', methods=['POST'])
def generate_more_ideas():
    try:
        data = request.json
        logging.debug(f"Received data for generating more gift ideas: {data}")
        
        response = generate_gift_idea()
        return response
    except Exception as e:
        logging.error(f"Error generating more gift ideas: {e}", exc_info=True)
        return jsonify({"error": "Error generating more gift ideas"}), 500

def create_prompt(age, gender, occasion, recipient_type, categories, price_range):
    prompt_parts = ["You are an expert in finding gifts for Indian people. Provide a list of 9 popular and trending products that can be searched using the product name. Each product should include the detailed product name, company, model, and price."]

    if age:
        prompt_parts.append(f"for a {age}-year-old")
    if recipient_type:
        prompt_parts.append(recipient_type)
    if gender:
        prompt_parts.append(f"who is {gender}")
    if categories:
        categories_str = ', '.join(categories)
        prompt_parts.append(f"and loves {categories_str} items")
    if occasion:
        prompt_parts.append(f"suitable for {occasion}")
    if price_range:
        prompt_parts.append(f"within the price range {price_range} INR")

    prompt_parts.append("These gifts should be popular among Indian people and available on e-commerce websites like Amazon India. Ensure that each product is followed by its detailed product name, company, model, price, and a convincing reason for its selection. Here is an example:")
    prompt_parts.append("Product_name: RVA Cute Flower Shaped Floor Cushion for Kids Room Living Room, Bedroom Furnishing Velvet Throw Pillow Cushion for Home Decoration Kids Girls Women Gift (Size 35 Cm) (Pink)")
    prompt_parts.append("Reason: Chosen for its cute design, suitable for kids and home decoration, and its popularity on Indian e-commerce sites. Always give output in this format:")
    prompt_parts.append("Product_name:\nReason:\n" + "Product_name:\nReason:\n" * 8)

    return ' '.join(prompt_parts)

def create_search_prompt(textdata):
    return (
        f"You are an expert in finding gifts for Indian people. Based on the following input: '{textdata}', provide a list of 9 popular and trending products in India that would make excellent gifts. "
        f"These products should be available on major Indian e-commerce websites like Amazon India. Ensure each product includes the detailed product name, company, model, price, followed by a convincing reason for selecting it. "
        f"Provide the output in the following format:\n\n"
        f"Product_name:\nReason:\n" * 9 +
        f"Here is an example:\n"
        f"Product_name: RVA Cute Flower Shaped Floor Cushion for Kids Room Living Room, Bedroom Furnishing Velvet Throw Pillow Cushion for Home Decoration Kids Girls Women Gift (Size 35 Cm) (Pink)\n"
        f"Reason: Chosen for its cute design, suitable for kids and home decoration, and its popularity on Indian e-commerce sites."
    )

def filter_unique_gift_ideas(new_gift_ideas):
    unique_gift_ideas = [idea for idea in new_gift_ideas if idea not in all_gift_ideas]
    return unique_gift_ideas

def clean_text(text):
    text = re.sub(r'[*-]', '', text)
    text = re.sub(r'\d+\.\s*', '', text)  # Remove numbering (e.g., "1. ", "2. ", etc.)
    return text

def process_and_structure_gift_ideas(text):
    gift_ideas = []
    current_gift = {}

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        if "Product_name:" in line:
            if current_gift:
                gift_ideas.append(current_gift)
                current_gift = {}
            current_gift["Product_name"] = line.replace("Product_name:", "").strip()
        elif "Reason:" in line:
            current_gift["Reason"] = line.replace("Reason:", "").strip()
        elif "Price:" in line:
            current_gift["Price"] = line.replace("Price:", "").strip()

    if current_gift:
        gift_ideas.append(current_gift)

    return gift_ideas

if __name__ == '__main__':
    app.run(debug=True)
