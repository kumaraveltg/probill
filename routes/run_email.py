import requests

BASE_URL = "http://127.0.0.1:8000"
APPPASSWORD = "ijqitpzaddfpfzev"

try:
    # 1️⃣ Test your SMTP settings first
    tst_url = f"{BASE_URL}/test-smtp"
    print("Testing SMTP configuration...")
    r1 = requests.post(tst_url, json={
        "smtp_host": "smtp.gmail.com",
        "smtp_port": "587",
        "email_from": "kumaraveltg@gmail.com",  # Added
        "email_username": "kumaraveltg@gmail.com",  # Fixed field name
        "email_password": APPPASSWORD,
        "use_tls": True
    })
    print("SMTP Test Result:", r1.json())

    # Only proceed if test passes
    if r1.json().get("ok"):
        # 2️⃣ Then send pending emails
        send_url = f"{BASE_URL}/sendpending"
        print("\nSending pending emails...")
        r2 = requests.post(send_url)
        print("Send Email Result:", r2.json())
    else:
        print("\n SMTP test failed. Fix configuration before sending emails.")

except Exception as e:
    print("Error:", e)