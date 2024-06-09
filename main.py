import base64
import datetime
import logging
import threading
import time

import pytz
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app
import requests
import hashlib
import os
from urllib.parse import urlencode, urlparse
from flask_mysqldb import MySQL
import mysql.connector
from mysql.connector import Error
import pdfkit
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr
from admin import admin_bp  # Import the admin blueprint


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Replace with your actual test secret key
COMPANY_LOGO_URL = 'static/img/logo.jpg'  # Replace with your actual logo URL
COMPANY_NAME = 'ToynBee Dance Academy'
COMPANY_EMAIL = 'admin@descendantinv.co.za'

# Configuring Flask-Mail
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 587  # Use port 587 for TLS or 465 for SSL
SMTP_USERNAME = "admin@descendantinv.co.za"
SMTP_PASSWORD = "@Cj2022!"


app = Flask(__name__)
app.secret_key = 'super secret key'
# Register the admin blueprint
app.register_blueprint(admin_bp)

# Replace with your actual test secret key
# YOCO_SECRET_KEY = 'sk_test_d84e2b4fK1op2aR54bd4230b03e2' ### TESTING SECRET KEY ###
YOCO_SECRET_KEY = 'sk_live_2c8a989aK1op2aR989746c895c77' ### LIVE SECRET KEY ###

# Retrieve ClearDB URL from environment variable
clear_db_url = os.getenv('CLEARDB_DATABASE_URL')

# Parse the ClearDB URL
url = urlparse(clear_db_url)

# config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
if 'DYNO' in os.environ:  # Check if running on Heroku
    path_wkhtmltopdf = '/app/bin/wkhtmltopdf'
    db_config = {
        'host': url.hostname,
        'user': url.username,
        'password': url.password,
        'database': url.path[1:],  # Removing the leading '/' from the path
        'port': url.port or 3306  # Use default MySQL port if not specified
    }
else:
    path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # Local path for development
    # db_config = {
    #     'host': 'localhost',
    #     'user': 'root',
    #     'password': 'jcp@S4123',
    #     'database': 'ballet'
    # }

db_config = {
    'host': url.hostname,
    'user': url.username,
    'password': url.password,
    'database': url.path[1:],  # Removing the leading '/' from the path
    'port': url.port or 3306  # Use default MySQL port if not specified
}

config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

# mysql = MySQL(app)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'jcp@S4123',
    'database': 'ballet'
}
# connection = mysql.connector.connect(**db_config)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        print(f'Chosen student is: {name}')
        return redirect(url_for('payment', name=name))
    return render_template('index.html')


@app.route('/payment')
def payment():
    studentId = request.args.get('name')
    print('in here')
    # Connect to the database
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    # Fetch students for the selected school from the database
    cursor.execute("SELECT name, surname FROM students WHERE studentId = %s", (studentId,))
    student = cursor.fetchone()
    students = {'name': student[0], 'surname': student[1]} if student else None

    print(f'student: {students}')
    # return jsonify(students)

    return render_template('pay.html', name=students, studentId=studentId)

@app.route('/make_payment', methods=['GET', 'POST'])
def make_payment():
    if request.method == 'POST':
        amount = int(request.form['amount'])
        studentId = request.form['studentId']
        date = datetime.datetime.now()

        print(f'studentId: {studentId}, amount: {amount}, date: {date}')
        connection = get_db_connection()
        if connection:
            cursor= connection.cursor()
            cursor.execute("SELECT name, surname FROM students WHERE studentId = %s", (studentId,))
            student = cursor.fetchone()
            students = {'name': student[0], 'surname': student[1]} if student else None
            sendReceivedPaymentEmail(students.get('name'), students.get('surname'), amount)

            cursor = connection.cursor()
            cursor.execute("INSERT INTO payments (amount, date, studentId) VALUES (%s, %s, %s)",
                           (amount, date, studentId))
            connection.commit()
            cursor.close()
            connection.close()

        flash("Cash payment made successfully!", "success")
        return redirect(url_for('make_payment'))



    return render_template('make_payment.html', active_page='payment')


@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    try:
        search_term = request.args.get('term')

        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Fetch schools and students matching the search term
        cursor.execute("SELECT id, name, 'school' AS type FROM schools WHERE name LIKE %s", (f'%{search_term}%',))
        schools = [{'id': id, 'name': name, 'type': type} for (id, name, type) in cursor.fetchall()]

        cursor.execute("SELECT id, name, 'student' AS type FROM students WHERE name LIKE %s", (f'%{search_term}%',))
        students = [{'id': id, 'name': name, 'type': type} for (id, name, type) in cursor.fetchall()]

        return jsonify(schools + students)
    except Exception as e:
        return str(e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/schools')
def get_schools():
    try:
        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Fetch schools from the database
        cursor.execute("SELECT id, name FROM schools")
        schools = [{'id': id, 'name': name} for (id, name) in cursor.fetchall()]

        return jsonify(schools)
    except Exception as e:
        return str(e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/students/<school_id>')
def get_students(school_id):
    try:
        # Connect to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Fetch students for the selected school from the database
        cursor.execute("SELECT id, name FROM students WHERE school_id = %s", (school_id,))
        students = [{'id': id, 'name': name} for (id, name) in cursor.fetchall()]

        return jsonify(students)
    except Exception as e:
        return str(e)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()





@app.route('/schools')
def schools():

    return render_template('schools.html')

@app.route('/test')
def test():

    return render_template('test.html')

@app.route('/search', methods=['POST'])
def search():
    print('searching...')

    # school_id = session['school_id']
    term = request.form.get('term')

    # Query the learners table based on the search term
    # cursor = db.cursor()
    # connection = mysql.connector.connect(**db_config)
    connection = get_db_connection()
    cursor = connection.cursor()
    query = f"SELECT studentId, name, surname FROM students WHERE name LIKE %s OR surname LIKE %s"
    cursor.execute(query, ('%' + term + '%', '%' + term + '%'))
    results = cursor.fetchall()
    print(results)

    # Build HTML for search results
    html = ""
    for studentId, name, surname in results:
        html += f'<option value="{studentId}">{name} {surname}</option>'

    return html


@app.route('/students')
def students():

    # cursor = mysql.connection.cursor()
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM students")
    students = cursor.fetchall()

    return render_template('students.html', students=students, active_page='students')


def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None


@app.route('/add_learners', methods=['POST', 'GET'])
def add_learners():
    schools = []
    try:
        connection = get_db_connection()
        if connection is None or not connection.is_connected():
            flash("Failed to connect to the database.", "danger")
            return render_template('add_learners.html', active_page='add_learners', schools=schools)

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM school")
            schools = cursor.fetchall()
            print(f'schools: {schools}')

    except Error as e:
        print(f"Error: {e}")
        flash("An error occurred while retrieving schools.", "danger")
    finally:
        if connection and connection.is_connected():
            connection.close()

    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        schoolId = request.form['schoolId']

        try:
            connection = get_db_connection()
            if connection is None or not connection.is_connected():
                flash("Failed to connect to the database.", "danger")
                return render_template('add_learners.html', active_page='add_learners', schools=schools)

            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO students (name, surname, schoolId) VALUES (%s, %s, %s)",
                               (name, surname, schoolId))
                connection.commit()
                flash("Student added successfully!", "success")

        except Error as e:
            print(f"Error: {e}")
            flash("An error occurred while adding the learner.", "danger")
        finally:
            if connection and connection.is_connected():
                connection.close()

    return render_template('add_learners.html', active_page='add_learners', schools=schools)


@app.route('/delete_student/<int:student_id>', methods=['DELETE', 'GET'])
def delete_student(student_id):
    try:
        connection = get_db_connection()
        if connection is None or not connection.is_connected():
            flash("Failed to connect to the database. Please try again later", "danger")
            return redirect(url_for('students'))

        with connection.cursor() as cursor:
            cursor.execute('DELETE FROM students WHERE studentId = %s', (student_id,))
            connection.commit()
            flash("Student deleted successfully!", "success")
            return redirect(url_for('students'))

    except Error as e:
        print(f"Error: {e}")
        flash("An error occurred while deleting the student.", "danger")
        return redirect(url_for('students'))

    finally:
        if connection and connection.is_connected():
            connection.close()


@app.route('/pay', methods=['POST'])
def pay():
    try:
        token = request.form['token']
        amount = int(float(request.form['amount']) * 100)  # Amount in cents

        headers = {
            'X-Auth-Secret-Key': YOCO_SECRET_KEY,
        }

        payload = {
            'token': token,
            'amountInCents': amount,
            'currency': 'ZAR'
        }

        response = requests.post('https://online.yoco.com/v1/charges/', json=payload, headers=headers)
        response_data = response.json()

        # Log the response for debugging
        print(response_data)
        print(response.status_code)

        if response.status_code in [200, 201] and response_data.get('status') == 'successful':
            name = request.form['name']
            surname = request.form['surname']
            email = request.form['email']
            studentId = request.form['studentId']
            print(f'Student Id: {studentId}, name: {name} + {surname}')
            date = datetime.datetime.now()
            formatted_datetime = date.strftime('%Y-%m-%d %H:%M:%S')
            invoice_pdf = generate_invoice(response_data, name, surname, email, formatted_datetime)

            connection = get_db_connection()
            if connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO payments (amount, date, studentId) VALUES (%s, %s, %s)", (amount/100, formatted_datetime, studentId))
                connection.commit()
                cursor.close()
                connection.close()

            sendReceivedPaymentEmail(name, surname, amount/100)
            send_invoice(response_data['source']['id'], invoice_pdf, email)
            return render_template('success.html', data=response_data)
        else:
            error_message = response_data.get('message', 'Unknown error')
            return render_template('error.html', error_message=error_message, data=response_data)

    except Exception as e:
        print(f"Exception occurred: {e}")
        return render_template('error.html', error_message=str(e))



def generate_invoice(data, name, surname, email, date):
    with open('static/img/logo.jpg', 'rb') as f:
        img_data = f.read()
        img_base64 = base64.b64encode(img_data).decode()

    static_folder = current_app.static_folder
    static_files = os.listdir(os.path.join(static_folder, 'img'))
    print('Static files:', static_files)
    print(f'found the name: {name} {surname}')
    print(f'logo: {COMPANY_LOGO_URL}')

    rendered = render_template('invoice.html', data=data, company_logo=img_base64, company_name=COMPANY_NAME, name=name, surname=surname, email=email, date=date)
    pdf = pdfkit.from_string(rendered, False, configuration=config, options={"enable-local-file-access": ""})

    # pdf_filename = 'invoice.pdf'
    # with open(pdf_filename, 'wb') as f:
    #     f.write(pdf)

    return pdf

def send_invoice(card_id, invoice_pdf, email):
    # recipient_email = 'jarrydchad@gmail.com'  # Replace with the actual recipient's email address
    recipient_email = email
    msg = MIMEMultipart()
    msg['From'] = formataddr((COMPANY_NAME, COMPANY_EMAIL))
    msg['To'] = recipient_email
    msg['Subject'] = 'Invoice for Your Payment'

    body = 'Dear Customer,\n\nThank you for your payment. Please find attached the invoice for your recent transaction.\n\nBest regards,\nToynBee Dance Academy'
    msg.attach(MIMEText(body, 'plain'))

    part = MIMEApplication(invoice_pdf, Name='invoice.pdf')
    part['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
    msg.attach(part)

    with smtplib.SMTP('smtp.zoho.com', 587) as server:  # Replace with your SMTP server details
        server.starttls()
        server.login(COMPANY_EMAIL, '@Cj2022!')  # Replace with your email login details
        server.sendmail(COMPANY_EMAIL, recipient_email, msg.as_string())


def sendReceivedPaymentEmail(name, surname, amount):
    # Send notification email to yourself
    try:
        self_email = 'jarrydchad@gmail.com' # use ariana email
        notification_msg = MIMEMultipart()
        notification_msg['From'] = formataddr((COMPANY_NAME, COMPANY_EMAIL))
        notification_msg['To'] = self_email
        notification_msg['Subject'] = 'Client Payment Received'

        notification_body = (f'Client Payment Details:\n\n'
                             f'Name: {name} {surname}\n'
                             f'Amount: R{amount:.2f}\n')
        notification_msg.attach(MIMEText(notification_body, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(COMPANY_EMAIL, '@Cj2022!')
            server.sendmail(COMPANY_EMAIL, 'jarrydchad@gmail.com', notification_msg.as_string())
    except Error as e:
        logging.error(f'Unable to send email: {e}')


def send_email(subject, message, recipients):
    sender_email = COMPANY_EMAIL
    password = '@Cj2022!'

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    with smtplib.SMTP('smtp.zoho.com', 587) as server:  # Replace with your SMTP server details
        server.starttls()
        server.login(COMPANY_EMAIL, '@Cj2022!')  # Replace with your email login details
        server.sendmail(COMPANY_EMAIL, recipients, msg.as_string())

def print_message_and_send_email(message, target_day, recipients):
    while True:
        current_datetime = datetime.datetime.now(pytz.timezone('Africa/Johannesburg'))
        if current_datetime.day == target_day:
            print(message)
            # Sending email
            subject = "Payment reminder"
            send_email(subject, message, recipients)
            break
        time.sleep(1)


def stop_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def run_script():
    target_day = 6
    message = "Hello! This is a payment reminder. You can do so using this link ..."
    recipients = ["jarrydchad@gmail.com", "celinebrown002@gmail.com"]  # Add your recipient email addresses
    print(message)
    # print_message_and_send_email(message, target_day, recipients)

if __name__ == '__main__':
    script_thread = threading.Thread(target=run_script)
    script_thread.start()
    app.run(debug=True, use_reloader=False)  # use_reloader=False to avoid duplicate running
    script_thread.join()  # Wait for the script thread to finish before stopping the server
    stop_server()
