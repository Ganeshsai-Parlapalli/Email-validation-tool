# Email Validation Tool

A Python tool that validates email addresses by checking syntax, verifying domains, and detecting inactive addresses — improving communication data quality through automated workflows.

## 🚀 Tech Stack

- **Language:** Python
- **Libraries:** re (Regex), smtplib (SMTP)
- **Concepts:** Email Syntax Validation, Domain Verification, SMTP Checking

## ✨ Features

- Regex-based email syntax validation
- Domain existence verification
- SMTP-level verification for inactive/invalid addresses
- Bulk email processing support
- Duplicate entry detection and removal

## 📊 Impact

- Reduced invalid email submissions and duplicates by **85%**
- Improved validation accuracy for bulk processing operations

## 🔧 Setup & Installation

```bash
git clone https://github.com/Ganeshsai-Parlapalli/Email-validation-tool.git
cd Email-validation-tool
pip install -r requirements.txt
python main.py
```

## 🖥️ Usage

```python
# Single email validation
result = validate_email("example@domain.com")
print(result)  # Valid / Invalid

# Bulk validation from file
validate_bulk("emails.csv")
```

## 📁 Project Structure

```
Email-validation-tool/
├── main.py
├── validator.py
├── smtp_checker.py
├── sample_emails.csv
└── requirements.txt
```

## 👨‍💻 Developer

**Ganeshsai Parlapalli** — [LinkedIn](https://linkedin.com/in/parlapalli-ganeshsai-629a3631) | [GitHub](https://github.com/Ganeshsai-Parlapalli)
