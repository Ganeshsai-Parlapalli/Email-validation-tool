import os
import sys
import pandas as pd
import dns.resolver
import smtplib
import socket
from concurrent.futures import ThreadPoolExecutor
from flask import (
    Flask, render_template, request,
    send_file, redirect, url_for, abort
)
from email_validator import validate_email
from werkzeug.utils import secure_filename

# =========================
# PyInstaller helper
# =========================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static")
)

UPLOAD_FOLDER = resource_path("uploads")
OUTPUT_FOLDER = resource_path("outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =========================
# PERFORMANCE CONFIG
# =========================
MAX_THREADS = 25
SMTP_TIMEOUT = 4

domain_cache = {}
mx_cache = {}

major_providers = {
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com",
    "live.com", "yahoo.com",
    "icloud.com"
}

role_prefixes = {
    "info", "admin", "support", "sales",
    "contact", "hello", "team", "office",
    "billing", "postmaster", "abuse"
}

# =========================
# LOAD DISPOSABLE LIST
# =========================
def load_disposable_domains():
    try:
        path = resource_path("disposable_domains.txt")
        with open(path, "r") as f:
            return set(line.strip().lower() for line in f if line.strip())
    except:
        return set()

disposable_domains = load_disposable_domains()

# =========================
# VALIDATION FUNCTIONS
# =========================

def check_syntax(email):
    try:
        validate_email(email, check_deliverability=False)
        return True
    except:
        return False

def check_domain(domain):
    if domain in domain_cache:
        return domain_cache[domain]
    try:
        socket.gethostbyname(domain)
        domain_cache[domain] = True
        return True
    except:
        domain_cache[domain] = False
        return False

def check_mx(domain):
    if domain in mx_cache:
        return mx_cache[domain]
    try:
        records = dns.resolver.resolve(domain, "MX")
        mx_cache[domain] = len(records) > 0
        return mx_cache[domain]
    except:
        mx_cache[domain] = False
        return False

def check_disposable(domain):
    for d in disposable_domains:
        if domain.endswith(d):
            return True
    return False

def is_role_based(email):
    local = email.split("@")[0]
    return local.lower() in role_prefixes

def smtp_check(email, domain):
    try:
        records = dns.resolver.resolve(domain, "MX")
        mx_record = str(records[0].exchange)

        server = smtplib.SMTP(timeout=SMTP_TIMEOUT)
        server.connect(mx_record)
        server.helo("validator.local")
        server.mail("noreply@validator.local")
        code, _ = server.rcpt(email)
        server.quit()
        return code
    except:
        return None

# =========================
# MAIN VALIDATION
# =========================

def validate_email_pro(email):

    score = 0

    # Syntax
    if not check_syntax(email):
        return {"email": email, "status": "invalid", "score": score}
    score += 15

    domain = email.split("@")[1]

    # Role-based (slightly risky)
    if is_role_based(email):
        score += 5

    # Domain
    if not check_domain(domain):
        return {"email": email, "status": "invalid", "score": score}
    score += 15

    # MX
    if not check_mx(domain):
        return {"email": email, "status": "invalid", "score": score}
    score += 20

    # Disposable
    if check_disposable(domain):
        return {"email": email, "status": "invalid", "score": score}
    score += 15

    # SMTP (single check only)
    if domain in major_providers:
        score += 15
    else:
        code = smtp_check(email, domain)
        if code in (250, 251):
            score += 20
        elif code in (421, 450, 451, 452):
            score += 5
        elif code is None:
            score += 0
        else:
            score -= 10

    # =========================
    # FINAL CLASSIFICATION
    # =========================
    if score >= 65:
        status = "valid"
    elif score >= 30:
        status = "risky"
    else:
        status = "invalid"

    return {"email": email, "status": status, "score": score}

# =========================
# ROUTES
# =========================

@app.route("/")
def dashboard():
    return render_template(
        "dashboard.html",
        valid_count=0,
        risky_count=0,
        invalid_count=0,
        show_results=False
    )

@app.route("/validate", methods=["POST"])
def validate_file():

    file = request.files.get("file")
    if not file:
        return redirect(url_for("dashboard"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    df = pd.read_csv(filepath) if filename.lower().endswith(".csv") else pd.read_excel(filepath)
    df.columns = [c.strip().lower() for c in df.columns]

    email_column = next((c for c in df.columns if "email" in c), None)
    if not email_column:
        return redirect(url_for("dashboard"))

    emails = [str(e).strip().lower() for e in df[email_column] if not pd.isna(e)]

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        results = list(executor.map(validate_email_pro, emails))

    valid = [r["email"] for r in results if r["status"] == "valid"]
    risky = [r["email"] for r in results if r["status"] == "risky"]
    invalid = [r["email"] for r in results if r["status"] == "invalid"]

    pd.DataFrame(valid).to_csv(os.path.join(OUTPUT_FOLDER, "valid_emails.csv"), index=False)
    pd.DataFrame(risky).to_csv(os.path.join(OUTPUT_FOLDER, "risky_emails.csv"), index=False)
    pd.DataFrame(invalid).to_csv(os.path.join(OUTPUT_FOLDER, "invalid_emails.csv"), index=False)

    return render_template(
        "dashboard.html",
        valid_count=len(valid),
        risky_count=len(risky),
        invalid_count=len(invalid),
        show_results=True
    )

@app.route("/download/<filetype>")
def download_file(filetype):
    path = os.path.join(OUTPUT_FOLDER, f"{filetype}_emails.csv")
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run()
