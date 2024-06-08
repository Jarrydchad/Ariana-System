import openpyxl
import pandas as pd
import mysql.connector
from mysql.connector import Error

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'jcp@S4123',
    'database': 'ballet'
}

# Function to read Excel file and insert data into MySQL
# def import_data_from_excel(file_path):
#     try:
#         # Read Excel file
#         df = pd.read_excel(file_path)
#
#         print('Data read successfully')
#
#         # Establish database connection
#         conn = mysql.connector.connect(**db_config)
#         cursor = conn.cursor()
#
#         # Insert data into students table
#         for index, row in df.iterrows():
#             # Using iloc for positional indexing
#             name = row.iloc[1]  # Assuming name is in the 2nd column (index 1)
#             surname = row.iloc[2]  # Assuming surname is in the 3rd column (index 2)
#             # Skip rows with NaN values in either name or surname
#             if pd.isna(name) or pd.isna(surname):
#                 continue
#             cursor.execute("INSERT INTO students (name, surname) VALUES (%s, %s)", (name, surname))
#             print(f'Inserted Name: {name}, Surname: {surname}')
#
#         # Commit the transaction
#         conn.commit()
#         print("Data inserted successfully")
#     except Error as e:
#         print(f"Error: {e}")
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()
#
# # Main execution
# file_path = 'Sleeping Beauty register - 18.05.2024.xlsx'
# import_data_from_excel(file_path)


# Function to parse name and surname
def parse_name_surname(full_name):
    parts = full_name.split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], ''
    else:
        return parts

# Function to insert data into MySQL
def insert_student(cursor, school_id, name, surname):
    try:
        cursor.execute("INSERT INTO students (name, surname, schoolId) VALUES (%s, %s, %s)", (name, surname, school_id))
    except Error as e:
        print(f"Error inserting student: {e}")

# Main execution
def main():
    file_path = 'DOC-20240510-WA0006..xlsx'
    # Use uppercase sheet names
    school_ids = {'ASTRA': 1, 'GELVANDALE': 2, 'FERNWOOD': 3, 'TRIOMF': 4}

    try:
        # Establish database connection
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Read data from each sheet
        workbook = openpyxl.load_workbook(file_path)
        for sheet_name, school_id in school_ids.items():
            sheet = workbook[sheet_name]
            for row in sheet.iter_rows(min_row=2, max_col=1, values_only=True):
                full_name = row[0]
                if full_name:
                    name, surname = parse_name_surname(full_name)
                    insert_student(cursor, school_id, name, surname)

        # Commit the transaction
        conn.commit()
        print("Data inserted successfully")
    except Error as e:
        print(f"Error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

main()
