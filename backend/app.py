from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, Field
from typing import List
import requests
import os

load_dotenv()

TOGETHER_AI_API_KEY = os.getenv('TOGETHER_AI_API_KEY')

# Initialize Flask App
app = Flask(__name__)

# Enable CORS for your React app running on localhost:3000
CORS(app, origins=["http://localhost:3000"])  # Allow only React frontend

# Load environment variables for MongoDB connection
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
try:
    client.admin.command('ping')  # Test MongoDB connection
    print("MongoDB connected successfully")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise
db = client.notepad
notes_collection = db.notes

# Define a schema for the note//testt
class NoteItem(BaseModel):
    note_number: int
    content: str

class NoteSchema(BaseModel):
    title: str = Field(..., min_length=1)
    note_list: List[NoteItem]

# API endpoint to fetch all notes
@app.route('/api/notes', methods=['GET'])
def get_notes():
    notes = list(notes_collection.find({}, {'_id': 0}))  # Exclude MongoDB's _id field
    return jsonify(notes)

# API endpoint to add a new note (only saves the title)
@app.route('/api/notes', methods=['POST'])
def add_note():
    data = request.get_json()
    try:
        title = data.get('title')
        if not title:
            return jsonify({'message': 'Title is required!'}), 400
        
        # Save only the title (no content or note_list)
        note_data = {
            "title": title,
            "note_list": [],  # No content stored yet
            "summary": ""  # Empty summary for now
        }
        
        notes_collection.insert_one(note_data)  # Save note data with just the title
        return jsonify({'message': 'Note added successfully!'})
    except Exception as e:
        return jsonify({'message': 'Error saving note!', 'error': str(e)}), 500

# API endpoint to delete a note by title
@app.route('/api/notes', methods=['DELETE'])
def delete_note():
    title = request.json.get('title')
    if not title:
        return jsonify({'message': 'Title is required!'}), 400
    notes_collection.delete_one({'title': title})
    return jsonify({'message': 'Note deleted successfully!'})

# API endpoint to summarize note content
@app.route('/api/summarize', methods=['POST'])
def summarize_note():
    data = request.get_json()
    note_content = data.get('noteContent', '')
    
    if not note_content:
        return jsonify({'message': 'No content provided for summarization'}), 400
    
    # Call the external summarization API (Together.AI)
    url = "https://api.together.ai/v1/summarize"  # Ensure this is the correct URL
    headers = {
        "Authorization": f"Bearer {TOGETHER_AI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "text": note_content,
        "language": "en",  # Assuming English content
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Response Status Code: {response.status_code}")  # Log status code
        print(f"Response Headers: {response.headers}")  # Log response headers
        print(f"Response Body: {response.text}")  # Log response body (full content)
        
        # Check if response is successful (status code 200)
        response.raise_for_status()  # Will raise an error for bad status codes
        summary = response.json().get('summary', '')
        
        # If no summary is returned, send an error message
        if not summary:
            return jsonify({'message': 'No summary found in response'}), 500
        
        return jsonify({'summary': summary})
    except requests.exceptions.RequestException as e:
        print(f"Error while summarizing: {e}")  # Log error
        return jsonify({'message': 'Error while summarizing the note'}), 500



if __name__ == '__main__':
    app.run(debug=True)
