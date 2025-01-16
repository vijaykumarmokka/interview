from flask import Flask, render_template, jsonify
import sounddevice as sd
import numpy as np
import aiohttp
import asyncio
import speech_recognition as sr
import io

app = Flask(__name__)

# Async function to recognize speech continuously using sounddevice
async def continuous_speech_recognition():
    recognizer = sr.Recognizer()
    recognized_texts = []  # List to store recognized text

    # Parameters for audio recording
    sample_rate = 16000  # Sampling rate for audio recording
    duration = 5  # Duration in seconds for each audio recording chunk
    channels = 1  # Mono channel
    dtype = np.int16  # Data type for audio samples

    # Record audio continuously
    with sd.InputStream(samplerate=sample_rate, channels=channels, dtype=dtype) as stream:
        print("\n🎤 Listening... Speak now.")
        while True:
            audio_data, overflowed = stream.read(sample_rate * duration)
            if overflowed:
                print("Warning: Audio overflowed.")
            audio = np.array(audio_data, dtype=np.int16)

            # Convert numpy array to audio file-like object for recognition
            audio_file = io.BytesIO()
            audio.tofile(audio_file)

            # Use speech recognition to process the audio data
            try:
                audio_file.seek(0)
                audio_recognition = recognizer.recognize_google(sr.AudioFile(audio_file))
                print(f"Recognized: {audio_recognition}")
                recognized_texts.append(audio_recognition.strip())
            except sr.UnknownValueError:
                print("Sorry, I couldn't understand what you said.")
            except sr.RequestError as e:
                print(f"Error connecting to the speech recognition service: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

            await asyncio.sleep(0.5)  # Short delay to avoid CPU overuse

    return recognized_texts  # Return the list of recognized texts

# Async function to get an interview-style answer from Gemini API
async def get_interview_answer_from_gemini(text):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyAJ9dtI4fdUmNKODYBNGzWEh-sMi1Sy9Cw"
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
