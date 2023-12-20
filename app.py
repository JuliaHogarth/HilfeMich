from flask import Flask, render_template, Response
import cv2
import time
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from deepface import DeepFace
import json
import spotipy
import spotipy.util as util
from openai import AzureOpenAI
import os

app = Flask(__name__)

client = AzureOpenAI(
	api_key = os.getenv("AZURE_OPENAI_KEY"),
	azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
	api_version = "2023-10-01-preview"
)

credentials = "spotify_keys.json"
with open(credentials, "r") as keys:
    api_tokens = json.load(keys)

client_id = api_tokens["client_id"]
client_secret = api_tokens["client_secret"]
redirectURI = api_tokens["redirect"]
username = api_tokens["username"]

scope = 'user-read-private user-read-playback-state user-modify-playback-state playlist-modify-public user-read-recently-played'
token = util.prompt_for_user_token(username, scope, client_id=client_id,
                           client_secret=client_secret,
                           redirect_uri=redirectURI)

sp = spotipy.Spotify(auth=token)

executor = ThreadPoolExecutor(max_workers=2)

def ask_question(emotion):
    messages = [
        {"role": "user", "content": f"Hello, could you please find me a song that best represents this emotion: {emotion}. Please respond only with the artist name and song name"}
    ]

    response = client.chat.completions.create(
        model="GPT-4",
        messages=messages
    )

    return response.choices[0].message.content

def find_song(emotion):
    song_name = ask_question(emotion)
    track_results = sp.search(q=song_name, type='track', limit=1)
    track_uri = [track_results["tracks"]["items"][0]["uri"]]
    devices = sp.devices()
    deviceID = devices['devices'][0]['id']
    sp.start_playback(deviceID, None, track_uri)
    print(track_uri)

def process_emotion(emotion):
    executor.submit(ask_question, emotion)
    executor.submit(find_song, emotion)

# Load the pre-trained emotion detection model
model = DeepFace.build_model("Emotion")

# Define emotion labels
emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

# Load face cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Define a class for implementing multi-threaded processing
class WebcamStream:
    def __init__(self, stream_id=0):
        self.stream_id = stream_id
        self.vcap = cv2.VideoCapture(self.stream_id)

        if not self.vcap.isOpened():
            print("[Exiting]: Error accessing webcam stream.")
            exit(0)

        self.set_resolution(640, 480)

        self.grabbed, self.frame = self.vcap.read()
        if not self.grabbed:
            print('[Exiting] No more frames to read')
            exit(0)

        self.stopped = True
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True

    def set_resolution(self, width, height):
        self.vcap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        fps_input_stream = int(self.vcap.get(5))
        print("FPS of webcam hardware/input stream: {}".format(fps_input_stream))

        self.grabbed, self.frame = self.vcap.read()
        if not self.grabbed:
            print('[Exiting] No more frames to read')
            exit(0)

        self.stopped = True
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True

    def start(self):
        self.stopped = False
        self.t.start()

    def update(self):
        while True:
            if self.stopped:
                break
            self.grabbed, self.frame = self.vcap.read()
            if not self.grabbed:
                print('[Exiting] No more frames to read')
                self.stopped = True
                break
        self.vcap.release()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True


webcam_stream = WebcamStream(stream_id=0)
webcam_stream.start()

def generate_frames():
    while True:
        frame = webcam_stream.read()
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            emotion_idx = predict_emotion(gray_frame[y:y + h, x:x + w])
            emotion = emotion_labels[emotion_idx]
            print(emotion)
            executor.submit(process_emotion, emotion)

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(frame, emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
        time.sleep(0.03)


def predict_emotion(face):
    resized_face = cv2.resize(face, (48, 48), interpolation=cv2.INTER_AREA)
    normalized_face = resized_face / 255.0
    reshaped_face = normalized_face.reshape(1, 48, 48, 1)

    preds = model.predict(reshaped_face)[0]
    return preds.argmax()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run()
