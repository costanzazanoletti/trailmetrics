import os
from flask import Flask, jsonify, request
from app.segmentation import segment_activity
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

@app.route("/segment/<int:activity_id>", methods=["POST"])
def segment_and_store(activity_id):
    """
    API endpoint to segment an activity and store the results.
    """
    segments_df = segment_activity(activity_id)
    return jsonify({"message": f"Processed {len(segments_df)} segments"}), 200

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5001))  # Read from environment, default to 5001
    app.run(debug=True, host="0.0.0.0", port=port)
