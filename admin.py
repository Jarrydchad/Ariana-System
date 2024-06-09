# admin.py
import logging
import os
from datetime import datetime
from urllib.parse import urlparse

import mysql
from flask import Blueprint, render_template, jsonify

admin_bp = Blueprint('admin', __name__)

# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'jcp@S4123',
#     'database': 'ballet'
# }

# Retrieve ClearDB URL from environment variable
clear_db_url = os.getenv('CLEARDB_DATABASE_URL')

# Parse the ClearDB URL
url = urlparse(clear_db_url)

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
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'jcp@S4123',
        'database': 'ballet'
    }

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@admin_bp.route('/admin/dashboard')
def dashboard():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Fetch total students
        cursor.execute("SELECT COUNT(*) FROM students")
        studentTotal = cursor.fetchone()[0]

        # Fetch total monthly fees received
        cursor.execute("SELECT SUM(amount) FROM payments")
        totalMonthlyFees = cursor.fetchone()[0]
        if totalMonthlyFees is None:
            totalMonthlyFees = 0.0
        totalMonthlyFees = round(totalMonthlyFees, 2)

        # Fetch total fees for the current year
        current_year = datetime.now().year
        start_date = f'{current_year}-01-01'
        end_date = f'{current_year}-12-31'
        query = '''
            SELECT 
                SUM(amount) AS totalFees
            FROM 
                payments
            WHERE 
                date >= %s AND date <= %s
        '''
        cursor.execute(query, (start_date, end_date))
        total_fees = cursor.fetchone()[0]
        if total_fees is None:
            total_fees = 0.0
        total_fees = round(total_fees, 2)

        expected = studentTotal * 200

        latest_payments = get_latest_payments()
        logger.info(f'Latest payments: {latest_payments}')

        # Assuming get_total_fees_per_month() is defined somewhere in your script
        total_fees_per_month = get_total_fees_per_month()
        logger.info(f'Total fees per month: {total_fees_per_month}')

        # Total students paid per month
        total_paid_monthly = get_students_paid_per_month()
        logger.info(f'Total students paid per month: {total_paid_monthly}')

        cursor.close()
        connection.close()

        return render_template('dashboard.html',
                               active_page='dashboard',
                               studentTotal=studentTotal,
                               totalMonthlyFees=totalMonthlyFees,
                               totalFees=total_fees,
                               expected=expected,
                               latest_payments=latest_payments,
                               total_fees_per_month=total_fees_per_month,
                               total_paid_monthly=total_paid_monthly)

    except mysql.connector.Error as error:
        logger.error(f'Database error: {error}')
        return render_template('error.html', message=str(error))


@admin_bp.route('/admin/student_payments/<int:student_id>')
def student_payments(student_id):
    payments = get_payments_for_student(student_id)
    print(payments)


    return render_template('student_payments.html', payments=payments)


def get_latest_payments():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = '''
            SELECT 
                p.date,
                p.amount,
                s.name,
                s.surname
            FROM 
                payments p
            JOIN 
                students s ON p.studentId = s.studentId
            ORDER BY 
                p.date DESC
            LIMIT 5
        '''
        cursor.execute(query)
        latest_payments = cursor.fetchall()

        cursor.close()
        connection.close()

        return latest_payments

    except mysql.connector.Error as error:
        logger.error(f'Database error: {error}')
        return []

import mysql.connector
from datetime import datetime

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'jcp@S4123',
    'database': 'ballet'
}

def get_total_fees_per_month():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        current_year = datetime.now().year
        current_month = datetime.now().month
        start_date = f'{current_year}-01-01 00:00:00'
        end_date = datetime.now().strftime('%Y-%m-%d 23:59:59')

        print(f"Start Date: {start_date}, End Date: {end_date}")  # Debugging

        query = '''
            SELECT 
                MONTH(date) AS month,
                SUM(amount) AS totalFees
            FROM 
                payments
            WHERE 
                date >= %s AND date <= %s
            GROUP BY 
                MONTH(date)
            ORDER BY 
                MONTH(date)
        '''

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        print(f'Query result: {rows}')  # Debugging

        cursor.close()
        connection.close()

        # Ensure all months are included, even if they have zero fees
        all_months = []
        total_fees_per_month = []
        for month in range(1, current_month + 1):
            all_months.append(datetime.strptime(str(month), "%m").strftime("%b"))
            found = False
            for row in rows:
                if row[0] == month:
                    total_fees_per_month.append(row[1])
                    found = True
                    break
            if not found:
                total_fees_per_month.append(0)

        return all_months, total_fees_per_month

    except mysql.connector.Error as error:
        print(f'Database error: {error}')
        return [], []

# Testing the function
months, fees = get_total_fees_per_month()
print(f'Months: {months}')
print(f'Fees: {fees}')



def get_students_paid_per_month():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        current_year = datetime.now().year
        start_date = f'{current_year}-01-01 00:00:00'
        end_date = datetime.now().strftime('%Y-%m-%d 23:59:59')

        query = '''
            SELECT 
                MONTH(date) AS month, 
                COUNT(DISTINCT studentId) AS studentsPaid
            FROM 
                payments
            WHERE 
                date >= %s AND date <= %s
            GROUP BY 
                MONTH(date)
            ORDER BY 
                MONTH(date)
        '''

        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        print(f'Query result: {rows}')  # Debugging

        cursor.close()
        connection.close()

        all_months = []
        students_paid_per_month = []
        current_month = datetime.now().month
        for month in range(1, current_month + 1):
            all_months.append(datetime.strptime(str(month), "%m").strftime("%b"))
            found = False
            for row in rows:
                if row[0] == month:
                    students_paid_per_month.append(row[1])
                    found = True
                    break
            if not found:
                students_paid_per_month.append(0)

        return all_months, students_paid_per_month

    except mysql.connector.Error as error:
        print(f'Database error: {error}')
        return [], []

# Testing the function
months, students_paid = get_students_paid_per_month()
print(f'Months: {months}')
print(f'Students Paid: {students_paid}')



def get_payments_for_student(student_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = '''
            SELECT 
                s.studentId,
                s.name,
                s.surname,
                p.date,
                p.amount
            FROM 
                payments p
            RIGHT JOIN 
                students s ON p.studentId = s.studentId
            WHERE 
                s.studentId = %s
            ORDER BY 
                p.date
        '''

        cursor.execute(query, (student_id,))
        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        if not rows:
            return {'error': 'No payments found for this student.'}

        student_details = {
            'studentId': rows[0][0],
            'name': rows[0][1],
            'surname': rows[0][2],
            'payments': []
        }

        for row in rows:
            if row[3] is not None and row[4] is not None:  # Check if payment details are not None
                student_details['payments'].append({
                    'date': row[3],
                    'amount': row[4]
                })

        return student_details

    except mysql.connector.Error as error:
        return {'error': str(error)}

