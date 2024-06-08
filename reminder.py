import datetime
import time
import pytz  # Import pytz module for timezone support

def print_message_at_specific_time(message, target_datetime):
    while True:
        current_datetime = datetime.datetime.now(pytz.timezone('Asia/Riyadh'))  # Get current time in SA timezone
        if current_datetime.hour == target_datetime.hour and current_datetime.minute == target_datetime.minute:
            print(message)
            break
        time.sleep(1)  # Sleep for 1 second before checking again

# Define the target time (10:57 PM SA time)
target_time = datetime.time(22, 57, 0)

# Get today's date
today_date = datetime.datetime.now(pytz.timezone('Asia/Riyadh')).date()

# Combine today's date with the target time to create the target datetime
target_datetime = datetime.datetime.combine(today_date, target_time)

# Define the message to be printed
message = "Hello! It's time to do something."

# Call the function to print the message at the specific time
print_message_at_specific_time(message, target_datetime)
