from flask import Flask, request, jsonify, render_template, send_file, url_for
import pandas as pd
import smtplib
import os

app = Flask(__name__)

# --- Base Directories ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "static", "compound_images")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "sialic acid analog")  # folder in root

# --- Load Excel dataset ---
data_file = os.path.join(BASE_DIR, "descriptions.xlsx")  # file in root
df = pd.read_excel(data_file)

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

# API to get all names (for autocomplete)
@app.route("/all_names", methods=["GET"])
def all_names():
    try:
        names = df["Sialic acid analogues"].dropna().astype(str).unique().tolist()
        return jsonify({"names": names})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
