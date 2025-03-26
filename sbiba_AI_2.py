import openai
from flask import Flask, request, jsonify
from pyngrok import ngrok
from threading import Thread

# Initialize Flask app
app = Flask(__name__)

# OpenAI API Key (Use environment variables for security)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Assistant ID for monument recognition
ASSISTANT_ID_MONUMENT = os.getenv("ASSISTANT_ID_MONUMENT")  # Replace with your actual Assistant ID for recognition

# Assistant ID for quiz generation
ASSISTANT_ID_QUIZ = os.getenv("ASSISTANT_ID_QUIZ")  # Replace with your actual Assistant ID for quiz generation

# Define system instructions for monument recognition
system_instruction_recognition = """
You are an expert in the monuments of Sbiba, Tunisia. Your task is to recognize the monument based on an object description from an image.
The input will be a description of an object or monument from an image. Your response should only contain the **name of the monument** from Sbiba. Do not provide any additional explanations, context, or text.
for example the amphitheatre or nymphé or aqiduc or every other monument you will find in the PDF files 

Ensure that only the name of the monument is provided, with **no extra text**.
"""

# Define system instructions for quiz generation
system_instruction_quiz = """
You are an expert in the monuments of Sbiba. Based on the user's request, generate a quiz with only **one** multiple-choice question about the specified monument.
The question must be directly related to the monument mentioned in the user's input (e.g., "Amphitheatre of Sbiba").

Do **not** infer any additional information not explicitly mentioned in the user's prompt or pre-existing knowledge. Your answer must be based only on the content or description of the monument that is provided or implied by the user's input.

For each question:
1. Ask a clear, well-formulated question about the monument.
2. Provide 4 distinct answer choices.
3. Mark **one** of the answers as correct and clearly indicate it.
4. Provide an explanation or reasoning behind the correct answer based on the details the user mentioned.

Format of the response:
Question: [Your Question]
A) [Answer A]
B) [Answer B]
C) [Answer C]
D) [Answer D]

Correct Answer: [A/B/C/D]

Explanation: [Explanation for the correct answer]
"""

# Define route to recognize the monument
@app.route('/recognize_monument', methods=['POST'])
def recognize_monument():
    try:
        # Get the input from the POST request
        data = request.json
        object_description = data.get("description", "Unknown description")  # Default to "Unknown description" if no description is provided

        # Construct the prompt dynamically based on the description provided by the user
        user_prompt = f"Recognize the monument based on this description: {object_description}"

        # Make the request to OpenAI's chat API for monument recognition
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Replace with the desired model
            messages=[
                {"role": "system", "content": system_instruction_recognition},  # Use the system instructions for recognition
                {"role": "user", "content": user_prompt}
            ]
        )

        # Extract response text and ensure it's only the monument name
        monument_name = response['choices'][0]['message']['content'].strip()

        # If the assistant gives any extra text, ensure it's excluded
        if monument_name.lower() == "unknown":
            return jsonify({"monument_name": "Unknown"})
        
        return jsonify({"monument_name": monument_name})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Define route to generate quiz
@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    try:
        data = request.json
        monument_name = data.get("monument_name", "Amphitheatre of Sbiba")  # Default monument name

        user_prompt = f"Give me one question about {monument_name}"

        # Make the request to OpenAI's chat API for quiz generation
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_instruction_quiz},  # Use the system instructions for quiz
                {"role": "user", "content": user_prompt}
            ]
        )

        quiz = response['choices'][0]['message']['content']

        return jsonify({"quiz": quiz})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Start Flask in a separate thread
    server = Thread(target=app.run, kwargs={"debug": True, "use_reloader": False})
    server.start()


