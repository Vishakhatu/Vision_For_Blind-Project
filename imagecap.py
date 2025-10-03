import cv2
import pyttsx3
import google.generativeai as genai
from inputs import get_gamepad, UnpluggedError
import time
from PIL import Image

IMAGE_FILE_PATH = "captured_image.jpg"

# Prompts
GEMINI_PROMPT = "Describe what you see in this image in one clear and descriptive sentence."
EMOTION_PROMPT = """You will be provided an image of a person, your job is to assess what kind of emotion are they feeling by looking at their faces.
EXAMPLE OUTPUT RESPONSE:
    1. person looks depressed
    2. person looks tired.
    3. person is crying.
    4. person is happy.

    Try to answer in 3 words, this is important!
    """
TEXT_READING_PROMPT = "Read aloud the text shown in this image. Just output the exact text clearly."
OBJECT_PROMPT = "Identify the main object in this image. Answer briefly in 3 words or less."

OPTIMIZED_IMAGE_SIZE = (800, 600)


def configure_gemini():
    api_key = ''  # replace with your key
    if not api_key:
        print("FATAL: GOOGLE_API_KEY not found.")
        return False
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"FATAL: Failed to configure Gemini: {e}")
        return False


def wait_for_trigger():
    print("\nSystem Ready. Press a button")
    while True:
        try:
            events = get_gamepad()
            for event in events:
                if event.ev_type == "Key" and event.state == 1 and event.code in ("BTN_SOUTH", "BTN_NORTH", "BTN_EAST", "BTN_WEST"):
                    print(f"Controller: {event.code} pressed. Triggering action...")
                    return [True, event.code]
        except UnpluggedError:
            print("Controller not found. Please connect a controller.")
            time.sleep(5)
        except Exception as e:
            print(f"Controller error: {e}. Retrying in 5 seconds.")
            time.sleep(5)


def capture_and_save_image():
    print("Vision: Initializing camera...")
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Vision Error: Cannot open camera.")
        return None

    time.sleep(0.5)
    ret, frame = cam.read()
    cam.release()

    if not ret:
        print("Vision Error: Failed to grab frame.")
        return None

    try:
        print(f"Vision: Resizing image to {OPTIMIZED_IMAGE_SIZE}...")
        resized_frame = cv2.resize(frame, OPTIMIZED_IMAGE_SIZE, interpolation=cv2.INTER_AREA)
        print(f"Vision: Saving resized image to '{IMAGE_FILE_PATH}'...")
        cv2.imwrite(IMAGE_FILE_PATH, resized_frame)
        return IMAGE_FILE_PATH
    except Exception as e:
        print(f"Vision Error: Failed to process or save image: {e}")
        return None


def get_image_caption(image_path: str, isEmotion: bool = False, isText: bool = False, isObject: bool = False):
    if not image_path:
        return "Error: No image path provided."

    print("Requesting caption from Gemini...")
    try:
        img = Image.open(image_path)
        model = genai.GenerativeModel('gemini-1.5-flash')

        if isEmotion:
            response = model.generate_content([EMOTION_PROMPT, img])
        elif isText:
            response = model.generate_content([TEXT_READING_PROMPT, img])
        elif isObject:
            response = model.generate_content([OBJECT_PROMPT, img])
        else:
            response = model.generate_content([GEMINI_PROMPT, img])

        if not hasattr(response, "text") or not response.text:
            return "Error: Model returned an empty response."

        print("Caption received.")
        return response.text.strip()
    except FileNotFoundError:
        return f"Error: Image file not found at {image_path}"
    except Exception as e:
        return f"Error from Gemini API: {e}"


def speak_caption(text: str):
    """Reinitialize TTS engine every time so it always works"""
    if not text:
        return
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)   # Clear, natural speed
        engine.setProperty('volume', 1.0)

        # Try to set female voice
        voices = engine.getProperty('voices')
        for voice in voices:
            if "female" in voice.name.lower() or "zira" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break

        print(f"TTS: Speaking -> \"{text}\"")
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"TTS Error: {e}")


def main():
    print("--- Visual Assistant Initializing ---")

    if not configure_gemini():
        return

    while True:
        trigger, button = wait_for_trigger()
        if trigger:
            image_path = capture_and_save_image()
            if not image_path:
                speak_caption("I couldn't capture an image from the camera.")
                continue

            if button == "BTN_SOUTH":
                caption = get_image_caption(image_path, isEmotion=False, isText=False, isObject=False)
            elif button == "BTN_NORTH":
                caption = get_image_caption(image_path, isEmotion=True, isText=False, isObject=False)
            elif button == "BTN_EAST":
                caption = get_image_caption(image_path, isEmotion=False, isText=True, isObject=False)
            elif button == "BTN_WEST":
                caption = get_image_caption(image_path, isEmotion=False, isText=False, isObject=True)
            else:
                continue

            if caption.lower().startswith("error:"):
                print(f"Captioning Failed: {caption}")
                speak_caption("Sorry, I had a problem analyzing the image.")
                continue

            speak_caption(caption)


if __name__ == "__main__":
    main()
