import mysql.connector
from datetime import datetime

conn = mysql.connector.connect(
    host="reminders1.c1c8m6ekuail.us-east-1.rds.amazonaws.com",
    user="admin",
    password="88888888",
    database="reminders",
)
cursor = conn.cursor()

def init_database():
    cursor.execute("CREATE TABLE IF NOT EXISTS reminders (id INT AUTO_INCREMENT PRIMARY KEY, user_id text, event_name text, event_time text, reminded int)")
    conn.commit()

def mark_reminded(user_id, event_name):
    cursor.execute("UPDATE reminders SET reminded = 1 WHERE user_id = %s AND event_name = %s", (user_id, event_name))
    conn.commit()

def delete_expired_reminders(user_id, event_name):
    mark_reminded(user_id, event_name)
    current_time = datetime.utcnow()
    cursor.execute("DELETE FROM reminders WHERE event_time <= %s OR reminded = 1", (current_time,))
    conn.commit()

def find_task(user_id):
    cursor.execute("SELECT event_name, event_time FROM reminders WHERE user_id = %s", (user_id,))
    tasks = cursor.fetchall()
    return tasks

def not_reminded():
    cursor.execute("SELECT user_id, event_name, event_time FROM reminders WHERE reminded = 0")
    events = cursor.fetchall()
    return events 

def add_reminder_in_db(user_id, event_name, event_time):
    cursor.execute("INSERT INTO reminders (user_id, event_name, event_time, reminded) VALUES (%s, %s, %s, %s)", (user_id, event_name, event_time, 0))
    conn.commit()
