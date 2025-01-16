from flask import Flask, render_template, jsonify
import speech_recognition as sr
import aiohttp
import asyncio

app = Flask(__name__)

# Async function to recognize speech continuously
async def continuous_speech_recognition():
    recognizer = sr.Recognizer()
    recognized_texts = []  # List to store recognized text

    with sr.Microphone() as source:
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("\n🎤 Listening... Speak now.")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
            print("🔄 Processing speech...")
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            recognized_texts.append(text.strip())
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand what you said.")
        except sr.RequestError as e:
            print(f"Error connecting to the speech recognition service: {e}")
        except sr.WaitTimeoutError:
            print("No input detected. Waiting for more input...")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    return recognized_texts  # Return the list of recognized texts

# Async function to get an interview-style answer from Gemini API
async def get_interview_answer_from_gemini(text):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_API_KEY"
    headers = {"Content-Type": "application/json"}
    prompt = f"This is an interview. Based on the input '{text}', formulate a relevant interview question and provide a detailed and human-like answer."

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    candidates = response_data.get("candidates", [])
                    if candidates:
                        return candidates[0].get("content", "No relevant answer found.")
                    return "No relevant information found."
                else:
                    return f"API Error: {response.status} - {await response.text()}"
        except aiohttp.ClientError as e:
            return f"Network error: {e}"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
async def process_speech():
    try:
        recognized_texts = await continuous_speech_recognition()  # Get continuous speech data
        if recognized_texts:
            combined_text = " ".join(recognized_texts)  # Combine recognized texts for context
            answer = await get_interview_answer_from_gemini(combined_text)
            return jsonify({"success": True, "text": combined_text, "answer": answer})
        else:
            return jsonify({"success": False, "error": "No input detected or recognition failed."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
