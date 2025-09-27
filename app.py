from flask import Flask, request, jsonify, render_template, send_file, url_for
import pandas as pd
import smtplib
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

# --- Base Directories ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "static", "compound_images")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "sialic acid analog")  # folder in root

# --- Load Excel dataset ---
data_file = os.path.join(BASE_DIR, "descriptions.xlsx")  # file in root
all_sheets = pd.read_excel(data_file, sheet_name=None)  # None = all sheets
df = pd.concat(all_sheets.values(), ignore_index=True)

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('qa_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            answered_at TIMESTAMP,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()
# --- Utility: Get image path (returns a URL for the frontend) ---
def get_image_path(compound_name):
    filename = f"{compound_name}.PNG"
    fs_path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(fs_path):
        return url_for('static', filename=f"compound_images/{filename}")
    return None

# --- Routes ---

@app.route("/")
def index():
    return render_template("test.html")

# Suggestions for autocomplete
@app.route("/suggestions", methods=["GET"])
def suggestions():
    query = request.args.get("query")
    if not query:
        return jsonify({"suggestions": []})

    query = query.strip().lower()
    suggestions = df[df["Sialic acid analogues"].str.contains(query, case=False, na=False, regex=False)]
    suggestions_list = suggestions["Sialic acid analogues"].tolist()
    return jsonify({"suggestions": suggestions_list})

# Search route
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    if not query:
        return jsonify({"results": [], "suggestions": []})

    query = query.strip().lower()

    try:
        results = df[df["Sialic acid analogues"].str.contains(query, case=False, na=False, regex=False)]
    except Exception as e:
        return jsonify({"error": f"Error processing the search: {str(e)}"})

    if results.empty:
        return jsonify({"results": [], "suggestions": []})

    results_dict = results.to_dict(orient="records")
    for result in results_dict:
        result["Image"] = get_image_path(result["Sialic acid analogues"])

    suggestions = [result["Sialic acid analogues"] for result in results_dict]
    return jsonify({"results": results_dict, "suggestions": suggestions})

# Download MOL file
@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(file_path, as_attachment=True)

# Browse All (HTML page)
@app.route("/browse_all", methods=["GET"])
def browse_all():
    try:
        renamed_df = df.rename(columns={"Sialic acid analogues": "Name"})
        all_records = renamed_df.to_dict(orient="records")
        return render_template("browse_all.html", records=all_records)
    except Exception as e:
        return f"Error fetching records: {e}"

# Browse All (JSON for DataTables)
@app.route("/browse_all_json", methods=["GET"])
def browse_all_json():
    try:
        import pandas as pd
        import os

        # Read all sheets into a dict
        all_sheets = pd.read_excel("descriptions.xlsx", sheet_name=None)  # None = all sheets
        # Concatenate all sheets into a single DataFrame
        combined_df = pd.concat(all_sheets.values(), ignore_index=True)

        # Keep only the Sialic acid analogues column
        data = combined_df[["Sialic acid analogues"]].dropna().to_dict(orient="records")

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# Email configuration (from environment variables)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL", "example@example.com")  # fallback if not set

@app.route("/submit_question", methods=["POST"])
def submit_question():
    question = request.form.get("user_question")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        # Store question in database
        conn = sqlite3.connect('qa_database.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO questions (question) VALUES (?)",
            (question,)
        )
        conn.commit()
        question_id = cursor.lastrowid
        conn.close()
        
        # Also send email notification
        try:
            send_email(question)
        except Exception as e:
            print(f"Email sending failed: {e}")
        
        return jsonify({
            "message": "Question submitted successfully! You can check back later for the answer.",
            "question_id": question_id
        })
    except Exception as e:
        return jsonify({"error": f"Failed to submit question: {str(e)}"}), 500

def send_email(question):
    from_email = SMTP_USERNAME
    to_email = TO_EMAIL
    subject = "New Question"
    body = f"You have received a new question:\n\n{question}"

    email_message = f"Subject: {subject}\n\n{body}"

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(from_email, to_email, email_message)

# API to get all names (for autocomplete)
@app.route("/all_names", methods=["GET"])
def all_names():
    try:
        names = df["Sialic acid analogues"].dropna().astype(str).unique().tolist()
        return jsonify({"names": names})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get all Q&A for display
@app.route("/get_qa", methods=["GET"])
def get_qa():
    try:
        conn = sqlite3.connect('qa_database.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, question, answer, submitted_at, answered_at, status 
            FROM questions 
            WHERE status = 'answered' 
            ORDER BY answered_at DESC
        """)
        questions = cursor.fetchall()
        conn.close()
        
        qa_list = []
        for q in questions:
            qa_list.append({
                'id': q[0],
                'question': q[1],
                'answer': q[2],
                'submitted_at': q[3],
                'answered_at': q[4],
                'status': q[5]
            })
        
        return jsonify({"qa_list": qa_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Admin route to answer questions
@app.route("/admin/questions", methods=["GET"])
def admin_questions():
    try:
        conn = sqlite3.connect('qa_database.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, question, answer, submitted_at, answered_at, status 
            FROM questions 
            ORDER BY submitted_at DESC
        """)
        questions = cursor.fetchall()
        conn.close()
        
        return render_template("admin_questions.html", questions=questions)
    except Exception as e:
        return f"Error fetching questions: {e}"

# Admin route to submit answers
@app.route("/admin/answer", methods=["POST"])
def submit_answer():
    question_id = request.form.get("question_id")
    answer = request.form.get("answer")
    
    if not question_id or not answer:
        return jsonify({"error": "Question ID and answer are required"}), 400
    
    try:
        conn = sqlite3.connect('qa_database.db')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE questions 
            SET answer = ?, answered_at = ?, status = 'answered'
            WHERE id = ?
        """, (answer, datetime.now(), question_id))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Answer submitted successfully!"})
    except Exception as e:
        return jsonify({"error": f"Failed to submit answer: {str(e)}"}), 500
# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
