from flask import Flask, render_template, request
from bakong_khqr import KHQR
import qrcode

app = Flask(__name__)


@app.get('/')
def home():  # put application's code here
    return render_template('index.html')

@app.get('/payment')
def payment():
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiYjc3Y2EyOWY5YzdlNDJhNiJ9LCJpYXQiOjE3NzUyMDQ5OTYsImV4cCI6MTc4Mjk4MDk5Nn0.BBFqs0iDpERORoZTqK91YEGeBOeYfvnibZiwlgpTHZs'
    khqr = KHQR(token)

    price = request.args.get('price')
    # Generate QR code data for a transaction:
    qr = khqr.create_qr(
        bank_account='choeurn_pinchai@aclb',
        merchant_name='choeurn_pinchai',
        merchant_city='Phnom Penh',
        amount=float(price),
        currency='KHR',  # USD or KHR
        store_label='Phsar Thmei',
        phone_number='099774967',
        bill_number='TRX012345',
        terminal_label='POS-01',
        static=False,  # Static or Dynamic QR code (default: False)
        expiration=2
        # Expiration time in 2 days for the QR code (default: 1 day). This is used to calculate the expiration time for the QR code.
    )

    img = qrcode.make(qr)
    img.save("./static/qrcode.png")
    return render_template('pay.html', price=price, qr=qr)


@app.get('/check_status')
def check_status():
    qr = request.args.get('qrcode')
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJkYXRhIjp7ImlkIjoiYjc3Y2EyOWY5YzdlNDJhNiJ9LCJpYXQiOjE3NzUyMDQ5OTYsImV4cCI6MTc4Mjk4MDk5Nn0.BBFqs0iDpERORoZTqK91YEGeBOeYfvnibZiwlgpTHZs'
    khqr = KHQR(token)
    # Get Hash MD5
    md5 = khqr.generate_md5(qr)

    # Check Transaction paid or unpaid:
    payment_status = khqr.check_payment(md5)
    print(payment_status)
    # String Result: "UNPAID"
    # Indicates that this transaction has not yet been paid.
    return payment_status


if __name__ == '__main__':
    app.run()
