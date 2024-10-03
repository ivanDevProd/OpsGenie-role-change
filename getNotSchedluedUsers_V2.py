import requests
import pandas as pd
import time
from fetchTeamAdmins import get_all_team_admins
import datetime
import logging
from dotenv import load_dotenv
import os

load_dotenv()

pd.set_option('display.max_columns', None)  # None means unlimited
pd.set_option('display.expand_frame_repr', False)  # Prevents line wrapping

logging.basicConfig(filename='OutputFiles-Logs/execution.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = os.getenv('API_KEY')
HEADERS = {
    'Authorization': f'GenieKey {API_KEY}',
    'Content-Type': 'application/json'
}


def get_all_users():
    LIMIT = 100  # Maximum number of results per request

    url = "https://api.opsgenie.com/v2/users"
    all_users = []
    offset = 0

    logging.info("Starting to fetch all users from OpsGenie.")
    print("Fetching all users...")

    while True:
        params = {
            "limit": LIMIT,
            "offset": offset
        }
        response = requests.get(url, headers=HEADERS, params=params)

        # print(f"Response for all users: {response.json()}")  # Debugging line

        if response.status_code == 200:
            data = response.json().get('data', [])
            # Filter for active users (not blocked)
            active_users = [user['username'] for user in data if user.get('role', {}).get('name') == 'User']
            all_users.extend(active_users)

            if len(data) < LIMIT:
                break  # Exit if fewer users were returned
            offset += LIMIT
        else:
            print(f"Error fetching users: {response.status_code}, {response.text}")
            break

    logging.info(f"Total number of users fetched: {len(all_users)}")
    print(f"Total number of users fetched: {len(all_users)}")
    return all_users


# Function to fetch all schedules
def fetch_all_schedules():
    logging.info("Fetching all schedules from OpsGenie...")
    print("Fetching all schedules...")
    url = "https://api.opsgenie.com/v2/schedules"

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        logging.info("Successfully fetched schedules.")
        print("Schedules fetched.")
        return response.json()
    else:
        error_message = f"Error fetching schedules: {response.status_code}, {response.text}"
        logging.error(error_message)
        print(error_message)
        return {}


# Function to fetch schedule data
def fetch_schedule_data(schedule_id):
    today = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today = today.replace("+00:00", "Z")  # Adjust the offset for UTC

    interval = 24
    interval_unit = "months"

    logging.info(f"Fetching data for schedule ID: {schedule_id}...")
    print(f"Fetching data for schedule ID: {schedule_id}...")
    url = f"https://api.opsgenie.com/v2/schedules/{schedule_id}/timeline?interval={interval}&intervalUnit={interval_unit}&date={today}"

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        logging.info(f"Data fetched for schedule ID: {schedule_id}.")
        print(f"Data fetched for schedule ID: {schedule_id}.")
        return response.json()
    else:
        error_message = f"Error fetching schedule data for ID {schedule_id}: {response.status_code}, {response.text}"
        logging.error(error_message)
        print(error_message)
        return {}


# Function to process users and schedules
def process_users_and_schedules():
    logging.info("\n")  # add empty row
    logging.info("Starting process to fetch all schedules and process users.")

    # Step 1: Fetch all schedules
    schedules_data = fetch_all_schedules()
    schedule_ids = [schedule['id'] for schedule in schedules_data.get('data', [])]

    all_data = []

    # Process each schedule ID
    for schedule_id in schedule_ids:
        schedule_data = fetch_schedule_data(schedule_id)

        if 'data' in schedule_data and 'finalTimeline' in schedule_data['data']:
            rotations = schedule_data['data']['finalTimeline']['rotations']

            for rotation in rotations:
                rotation_name = rotation['name']

                if 'periods' in rotation:
                    for period in rotation['periods']:
                        if 'recipient' in period and 'name' in period['recipient']:
                            recipient_name = period['recipient']['name']
                            start_date = period['startDate']
                            end_date = period['endDate']

                            # Append the data to the list
                            all_data.append({
                                'schedule_name': schedule_data['data']['_parent']['name'],
                                'rotation_name': rotation_name,
                                'recipient_name': recipient_name,
                                'startDate': start_date,
                                'endDate': end_date
                            })
                else:
                    warning_message = f"No 'periods' found for rotation: {rotation_name} in Schedule: {schedule_data['data']['_parent']['name']}"
                    logging.warning(warning_message)
                    print(warning_message)

        time.sleep(0.25)  # To avoid hitting the API rate limit

    # Create a DataFrame from the collected data
    df = pd.DataFrame(all_data)
    logging.info(f"Created DataFrame with {len(df)} entries.")
    print(df)

    # Export the filtered DataFrame to a CSV file
    csv_file_path = 'OutputFiles-Logs/raw_schedule_data.csv'
    df.to_csv(csv_file_path, index=False)
    logging.info(f"Data exported to {csv_file_path}.")
    print(f"Data exported to {csv_file_path}.")

    # Create a list of unique recipient names
    unique_users_in_schedule = df['recipient_name'].unique().tolist()

    # Fetch all OpsGenie users
    all_users_in_opsgenie = get_all_users()
    logging.info(f"Total number of users in OpsGenie with 'Users' role: {len(all_users_in_opsgenie)}.")
    print(f"Total number of users with role 'Users' detected in OpsGenie: {list(all_users_in_opsgenie)}")

    # Print the unique recipient names
    logging.info(f"Unique recipient names in schedule: {len(unique_users_in_schedule)}.")
    print(f"List of users in schedule ({len(unique_users_in_schedule)}):", unique_users_in_schedule)

    # Find users who are not scheduled
    not_scheduled_users = [item for item in all_users_in_opsgenie if item not in unique_users_in_schedule]
    logging.info(f"Total number of non-scheduled users: {len(set(not_scheduled_users))}.")
    print(f"Total number of non-scheduled users: {len(set(not_scheduled_users))}: {list(set(not_scheduled_users))}")

    team_admins = get_all_team_admins()
    print(f"Team admins: ({len(set(team_admins))}):", team_admins)

    # Remove users that exist in team_admins
    users_to_downgrade = [user for user in not_scheduled_users if user not in team_admins]
    logging.info(f"Users whose roles can be downgraded (without Team-admins, Stakeholders, OpsGenie-Admins): "
                 f"{len(users_to_downgrade)}: {list(users_to_downgrade)}")
    print(f"Users whose roles can be downgraded (without Team-admins, Stakeholders, OpsGenie-Admins): "
          f"{len(users_to_downgrade)}: {list(users_to_downgrade)}")

    return users_to_downgrade


if __name__ == "__main__":
    process_users_and_schedules()
