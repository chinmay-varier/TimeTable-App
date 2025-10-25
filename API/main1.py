from __future__ import print_function
import os.path
import os
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pytz
from timeslots import timeslots
import json

with open('C:/Users/chinm/Desktop/TimeTable/details.json', 'r') as f:
    dataa = json.load(f)

with open('details2.json', 'w') as f:
    new_d = []
    for i in dataa:
        new_d.append({"key": i["key"], "value": [j for j in i["value"].split(",")]})
    
    for i in new_d:
        for value in i["value"]:
            if (value == "A"):
                i["value"].remove(value)
                i["value"].extend(["A1", "A2", "A3"])
            elif (value == "B"):
                i["value"].remove(value)
                i["value"].extend(["B1", "B2", "B3"])
            elif (value == "C"):
                i["value"].remove(value)
                i["value"].extend(["C1", "C2", "C3"])
            elif (value == "D"):
                i["value"].remove(value)
                i["value"].extend(["D1", "D2", "D3"])
            elif (value == "E"):
                i["value"].remove(value)
                i["value"].extend(["E1", "E2"])
            elif (value == "F"):
                i["value"].remove(value)
                i["value"].extend(["F1", "F2"])
            elif (value == "G"):
                i["value"].remove(value)
                i["value"].extend(["G1", "G2"])
            elif (value == "H"):
                i["value"].remove(value)
                i["value"].extend(["H1", "H2", "H3"])
            elif (value == "I"):
                i["value"].remove(value)
                i["value"].extend(["I1", "I2", "I3"])
            elif (value == "J"):
                i["value"].remove(value)
                i["value"].extend(["J1", "J2", "J3"])
            elif (value == "K"):
                i["value"].remove(value)
                i["value"].extend(["K1", "K2", "K3"])
            elif (value == "L"):
                i["value"].remove(value)
                i["value"].extend(["L1", "L2"])
            elif (value == "M"):
                i["value"].remove(value)
                i["value"].extend(["M1", "M2"])
            elif (value == "SP"):
                i["value"].remove(value)
                i["value"].extend(["SP1", "SP2"])
            else:
                pass
            
    json.dump(new_d,f)

# Permission to manage the calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():

    with open("details2.json", "r") as f:
        data = json.load(f)

    slots = [] 
    for course in data:
        for slot in course["value"]:
            slots.append(slot)

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file(os.getcwd().replace("\\", "/") + '/API/token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(os.getcwd().replace("\\", "/") +'/API/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    calendar_id = "darkequinox565@gmail.com"

    for slot in slots:
        summary = ""
        for course in data:
            if (slot in course["value"]):
                summary = course["key"]
        description = ""
        location = ""

        event_date = timeslots[slot][2] + " "

        start_time = timeslots[slot][0]
        end_time = timeslots[slot][1]
        
        start_local_str = event_date + start_time
        end_local_str = event_date + end_time

        # Convert to datetime objects
        local_tz = pytz.timezone("Asia/Kolkata")  # change to your local timezone if needed
        start_local = local_tz.localize(datetime.strptime(start_local_str, "%Y-%m-%d %H:%M"))
        end_local = local_tz.localize(datetime.strptime(end_local_str, "%Y-%m-%d %H:%M"))

        # Convert to UTC
        start_utc = start_local.astimezone(pytz.utc).isoformat()
        end_utc = end_local.astimezone(pytz.utc).isoformat()

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_utc,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_utc,
                'timeZone': 'UTC',
            },
        }

        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()

    print("Your classes have been scheduled!")

if __name__ == '__main__':
    main()