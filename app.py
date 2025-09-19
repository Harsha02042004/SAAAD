from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import smtplib
import os

app = Flask(__name__)

# --- Base Directories ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "static", "compound_images")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "sialic acid analog")  # folder in root

# --- Load Excel dataset ---
data_file = os.path.join(BASE_DIR, "descriptions.xlsx")
df = pd.read_excel(data_file)

# Ensure the search column exists and is string type
if "Sialic acid analogues" not in df.columns:
    raise ValueError("Column 'Sialic acid analogues' not found in Excel file.")
df["Sialic acid analogues"] = df["Sialic acid analogues"].fillna("").astype(str)

# --- Utility: Get image path ---
def get_image_path(compound_name):
    image_path = os.path.join(IMAGE_DIR, f"{compound_name}.PNG")
    return image_path if os.path.exists(image_path) else None

# --- Routes ---
@app.route("/")
def index():
    return render_template("test.html")

@app.route("/suggestions", methods=["GET"])
def suggestions():
    query = request.args.get("query", "")
    query = str(query).strip().lower()
    if not query:
        return jsonify({"suggestions": []})

    # Case-insensitive substring search
    matches = df[df["Sialic acid analogues"].str.lower().str.contains(query, na=False)]
    return jsonify({"suggestions": matches["Sialic acid analogues"].tolist()})

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "")
    query = str(query).strip().lower()
    if not query:
        return jsonify({"results": [], "suggestions": []})

    try:
        results = df[df["Sialic acid analogues"].str.lower().str.contains(query, na=False)]
    except Exception as e:
        return jsonify({"error": f"Error processing the search: {str(e)}"})

    if results.empty:
        return jsonify({"results": [], "suggestions": []})

    results_dict = results.to_dict(orient="records")
    for result in results_dict:
        result["Image"] = get_image_path(result["Sialic acid analogues"])

    suggestions = [r["Sialic acid analogues"] for r in results_dict]
    return jsonify({"results": results_dict, "suggestions": suggestions})

# --- Download MOL file route ---
@app.route("/download/<filename>")
def download_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(file_path, as_attachment=True)

# --- Email Config ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL", "example@example.com")

@app.route("/submit_question", methods=["POST"])
def ask_question():
    question = request.form.get("user_question")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    send_email(question)
    return jsonify({"message": "Question sent successfully!"})

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

if __name__ == "__main__":
    app.run(debug=True)
