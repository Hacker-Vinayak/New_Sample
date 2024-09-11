from flask import Flask, render_template, Response, request, jsonify
import cv2
import os
import time

app = Flask(__name__)

# Global variables to control the camera stream and recording
camera = None
camera_index = 0
recording = False
video_writer = None

# Base output path
base_output_path = os.path.join(os.path.expanduser("~"), "Desktop", "Tonbo_S_R")

# Ensure the base output directory exists
if not os.path.exists(base_output_path):
    os.makedirs(base_output_path)


def set_camera(index):
    global camera
    if camera is not None:
        camera.release()
    camera = cv2.VideoCapture(index)


@app.route('/')
def index():
    return render_template('index.html')


def generate_frames():
    global camera, recording, video_writer
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            if recording:
                video_writer.write(frame)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/connect_camera', methods=['POST'])
def connect_camera():
    global camera_index
    camera_index = int(request.args.get('camera_index'))
    set_camera(camera_index)
    return jsonify({"message": f"Camera {camera_index} connected."})


@app.route('/take_snapshot', methods=['POST'])
def take_snapshot():
    global camera, base_output_path
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")

    # Create snapshot directory with timestamp
    snapshot_dir = os.path.join(base_output_path, "Snapshots")
    if not os.path.exists(snapshot_dir):
        os.makedirs(snapshot_dir)
    
    # Save the snapshot with timestamp
    ret, frame = camera.read()
    if ret:
        image_path = os.path.join(snapshot_dir, f"snapshot_{timestamp}.jpg")
        cv2.imwrite(image_path, frame)
        return jsonify({"message": f"Snapshot saved as {image_path}"})
    else:
        return jsonify({"message": "Failed to take snapshot."})


@app.route('/start_recording', methods=['POST'])
def start_recording():
    global recording, video_writer, base_output_path, camera_index
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")

    # Create recording directory with timestamp
    recording_dir = os.path.join(base_output_path, "Recordings")
    if not os.path.exists(recording_dir):
        os.makedirs(recording_dir)

    # Start recording
    video_path = os.path.join(recording_dir, f"recording_{timestamp}.avi")
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))
    recording = True
    return jsonify({"message": f"Recording started, saving to {video_path}"})


@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    global recording, video_writer
    if recording:
        recording = False
        video_writer.release()
        return jsonify({"message": "Recording stopped."})
    else:
        return jsonify({"message": "No active recording to stop."})


if __name__ == "__main__":
    # Initialize the default camera
    set_camera(camera_index)
    app.run(host='0.0.0.0', port=5000, debug=True)

