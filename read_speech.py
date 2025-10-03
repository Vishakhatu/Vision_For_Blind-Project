import cv2
import google.generativeai as genai
from gtts import gTTS
import tempfile
import os
import sys

# Load Gemini API key
genai.configure(api_key="AIzaSyDLlBafCLwjjal1163TDwkNPnrZD802KGA")

# Create model
model = genai.GenerativeModel("gemini-1.5-flash")

# Ask user for preferred language
print("🌍 Select Language for Speech:")
print("1. English")
print("2. Hindi")
print("3. Marathi")

choice = input("Enter choice (1/2/3): ").strip()

if choice == "1":
    lang = "en"
elif choice == "2":
    lang = "hi"
elif choice == "3":
    lang = "mr"
else:
    print("⚠️ Invalid choice, defaulting to English.")
    lang = "en"

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Could not open webcam")
    sys.exit()

print("\n✅ Webcam started")
print("Press 's' to capture and read text, 'q' to quit.")

counter = 1
while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break

    cv2.imshow("Webcam - Press 's' to capture, 'q' to quit", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):
        # Save frame to temp folder
        filename = os.path.join(tempfile.gettempdir(), f"capture_{counter}.jpg")
        cv2.imwrite(filename, frame)

        # Send to Gemini API
        with open(filename, "rb") as f:
            response = model.generate_content(
                ["Extract any text from this image.", {"mime_type": "image/jpeg", "data": f.read()}]
            )

        extracted_text = response.text
        print("\n📜 Extracted Text from Gemini:")
        print(extracted_text)

        if extracted_text.strip():
            # Convert extracted text to chosen language speech
            speech_file = os.path.join(tempfile.gettempdir(), f"speech_{counter}.mp3")
            tts = gTTS(text=extracted_text, lang=lang)
            tts.save(speech_file)

            print(f"🔊 Playing: {speech_file}")
            os.system(f"start {speech_file}")  # Windows play

            counter += 1
        else:
            print("⚠️ No text detected by Gemini.")

    elif key == ord('q'):
        print("👋 Exiting...")
        break

cap.release()
cv2.destroyAllWindows()
