from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, Field
from typing import List
import os

load_dotenv()
# Initialize Flask App
app = Flask(__name__)

# Enable CORS for your React app running on localhost:3000
CORS(app, origins=["http://localhost:3000"])  # Allow only React frontend

# Load environment variables for MongoDB connection
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

# Define a schema for the note
class NoteItem(BaseModel):
    note_number: int
    content: str

class NoteSchema(BaseModel):
    title: str = Field(..., min_length=1)
    content: str
    note_list: List[NoteItem] = []

# API endpoint to fetch all notes
@app.route('/api/notes', methods=['GET'])
def get_notes():
    notes = list(notes_collection.find({}, {'_id': 0}))  # Exclude MongoDB's _id field
    return jsonify(notes)

# API endpoint to add a new note
@app.route('/api/notes', methods=['POST'])
def add_note():
    data = request.get_json()
    try:
        title = data.get('title')
        content = data.get('content')

        if not title:
            return jsonify({'message': 'Title is required!'}), 400
        
        # Save note with both title and content
        note_data = {
            "title": title,
            "content": content,  # Save the content as well
            "note_list": []  # No extra note details stored for now
        }
        
        notes_collection.insert_one(note_data)  # Save note data with title and content
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

if __name__ == '__main__':
    app.run(debug=True)
