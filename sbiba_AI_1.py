from flask import Flask, request, jsonify, send_file
import openai
import requests
import io
import base64
import time
from PIL import Image

# Initialize Flask app
app = Flask(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Set up your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Your Assistant IDs (Replace with yours)
ASSISTANT_ID_1 = os.getenv("ASSISTANT_ID_1")
ASSISTANT_ID_2 = os.getenv("ASSISTANT_ID_2")
ASSISTANT_ID_3 = os.getenv("ASSISTANT_ID_3")


# Endpoint 1: Ask Sbiba about monuments
@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        user_input = data.get("message", "Tell me about Sbiba")
        user_age = data.get("age", 25)  # Default age 25
        language = data.get("language", "English")  # Default language

        # Create a new thread for the conversation
        thread = openai.beta.threads.create()

        # Send a message to the assistant
        message = openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"I am {user_age} years old. Please answer in {language}. {user_input}"
        )

        # Run the assistant on the thread
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID_1
        )

        # Wait for the response
        import time
        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            time.sleep(1)  # Wait for completion

        # Retrieve messages from the thread
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content[0].text.value

        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Endpoint 2: Sbiba bot for specific questions about Sbiba monuments
@app.route('/sbiba_bot', methods=['POST'])
def sbiba_bot():
    try:
        data = request.json
        user_input = data.get("message", "Tell me about Sbiba")
        user_age = data.get("age", 25)  # Default age 25
        language = data.get("language", "English")  # Default language

        # Create a new thread for the conversation
        thread = openai.beta.threads.create()

        # Send a message to the assistant
        message = openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"I am {user_age} years old. Please answer in {language}. {user_input}"
        )

        # Run the assistant on the thread
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID_2
        )

        # Wait for the response
        import time
        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            time.sleep(1)  # Wait for completion

        # Retrieve messages from the thread
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content[0].text.value

        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Endpoint 3: Recommend reconstruction for rock samples
@app.route('/recommend_reconstruction', methods=['POST'])
def recommend_reconstruction():
    try:
        data = request.json
        if "rock_1_description" not in data or "rock_2_description" not in data:
            return jsonify({"error": "Please provide descriptions for both rocks"}), 400

        # Create a new thread for the conversation
        thread = openai.beta.threads.create()

        # Send a message to the assistant with the details of the rocks
        message = openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Rock 1 details:\n{data['rock_1_description']}\n\nRock 2 details:\n{data['rock_2_description']}\n\nAre they compatible? If yes, recommend the best technique for the reconstitution of the monument."
        )

        # Run the assistant on the thread
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID_3
        )

        # Wait for the response
        import time
        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            time.sleep(1)  # Wait for completion

        # Retrieve messages from the thread
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content[0].text.value

        return jsonify({"reconstruction_recommendation": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Endpoint 4: Analyze rock image
@app.route('/analyze_rock', methods=['POST'])
def analyze_rock():
    if 'image' not in request.files:
        return jsonify({"error": "Please upload an image with the key 'image'"}), 400

    # Convert image to Base64
    image_b64 = encode_image_to_base64(request.files['image'])

    # Prepare payload for Gemini API
    payload = {
        "model": "gemini-1.5-flash",
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Describe this rock sample for archaeological restoration. Provide a highly detailed description including:\n\n"
                            "- **Color**\n"
                            "- **Texture**\n"
                            "- **Material Composition**\n"
                            "- **Visible Erosion**\n"
                            "- **Fracture Patterns**\n\n"
                            "Ensure the description is detailed and precise."
                        )
                    },
                    {"inlineData": {"mimeType": "image/jpeg", "data": image_b64}}
                ]
            }
        ]
    }

    # Send request to Gemini API
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
        json=payload
    )

    # Handle response
    if response.status_code == 200:
        extracted_text = extract_rock_details(response.json())
        return jsonify({"rock_description": extracted_text})
    else:
        return jsonify({"error": "Failed to process request", "details": response.text}), response.status_code


# Helper function to encode image to Base64
def encode_image_to_base64(image_file):
    img = Image.open(image_file)
    img = img.convert("RGB")  # Ensure it is in RGB mode
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


# Function to extract and return raw text description from Gemini response
def extract_rock_details(response):
    try:
        # Extract text from the API response
        text = response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

        # Return raw text without structuring
        if text:
            return text
        else:
            return "No description provided by Gemini API."

    except Exception as e:
        return f"Error extracting text: {str(e)}"

# Define the function to convert text to speech
def text_to_speech(text, voice="fable"):  # Change 'narrator' to 'fable' or another valid voice
    response = openai.audio.speech.create(
        model="tts-1",
        voice=voice,  # Use a valid voice
        input=text
    )
    return response.content

# Function to handle the 'ask' endpoint and chain it with the 'text-to-speech' conversion
@app.route('/ask-and-convert', methods=['POST'])
def ask_and_convert():
    try:
        # Step 1: Get the input data
        data = request.get_json()
        user_input = data.get("message", "Tell me about Sbiba")
        user_age = data.get("age", 25)  # Default age 25
        language = data.get("language", "English")  # Default English

        # Step 2: Create a new thread for the conversation
        thread = openai.beta.threads.create()

        # Send a message to the assistant
        message = openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"I am {user_age} years old. Please answer in {language}. {user_input}"
        )

        # Run the assistant on the thread
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID_1
        )

        # Wait for the response
        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            time.sleep(1)  # Wait for completion

        # Retrieve messages from the thread
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        response_text = messages.data[0].content[0].text.value

        # Step 3: Convert the response text to speech
        audio_content = text_to_speech(response_text, voice="fable")  # Use the 'fable' voice for a historical tone

        # Create a byte stream of the audio content
        audio_stream = io.BytesIO(audio_content)

        # Return the MP3 file as a response
        return send_file(audio_stream, mimetype='audio/mp3', as_attachment=True, download_name="output.mp3")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API endpoint to analyze a monument image
@app.route('/analyze_monument', methods=['POST'])
def analyze_monument():
    if 'image' not in request.files:
        return jsonify({"error": "Please upload an image with the key 'image'"}), 400

    # Convert image to Base64
    image_b64 = encode_image_to_base64(request.files['image'])

    # Prepare payload for Gemini API
    payload = {
        "model": "gemini-1.5-flash",  # You can choose the version that fits your use case
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Describe this monument in the context of archaeology and history. "
                            "Provide a detailed description including:\n\n"
                            "- **Architectural Style**\n"
                            "- **Material Composition**\n"
                            "- **Historical Significance**\n"
                            "- **Visible Erosion and Deterioration**\n"
                            "- **Surrounding Environment and Cultural Context**\n\n"
                            "Ensure the description is precise and relevant to the monument's historical importance."
                        )
                    },
                    {"inlineData": {"mimeType": "image/jpeg", "data": image_b64}}
                ]
            }
        ]
    }

    # Send request to Gemini API
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
        json=payload
    )

    # Debugging - Print raw response from Gemini API
    raw_response = response.json()
    print("🔍 Raw Response from Gemini API:", raw_response)

    # Handle response
    if response.status_code == 200:
        extracted_text = extract_monument_details(raw_response)
        return jsonify({"monument_description": extracted_text})
    else:
        return jsonify({"error": "Failed to process request", "details": response.text}), response.status_code


# Helper function to encode image to Base64
def encode_image_to_base64(image_file):
    img = Image.open(image_file)
    img = img.convert("RGB")  # Ensure it is in RGB mode
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


# Function to extract and return raw text description from Gemini response
def extract_monument_details(response):
    try:
        # Extract text from the API response
        text = response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

        # Return raw text without structuring
        if text:
            return text
        else:
            return "No description provided by Gemini API."

    except Exception as e:
        return f"Error extracting text: {str(e)}"



# Run Flask App
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
