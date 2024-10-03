import requests
import pandas as pd
import time
from fetchTeamAdmins import get_all_team_admins

pd.set_option('display.max_columns', None)  # None means unlimited
pd.set_option('display.expand_frame_repr', False)  # Prevents line wrapping

def get_all_users():
    API_KEY = "623a40f4-7c85-4259-a463-ce1553567154"
    HEADERS = {
        "Authorization": f"GenieKey {API_KEY}",
        "Content-Type": "application/json"
    }
    # Constants
    LIMIT = 100  # Maximum number of results per request

    url = "https://api.opsgenie.com/v2/users"
    all_users = []
    offset = 0

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

    return all_users


# Function to fetch all schedules
def fetch_all_schedules():
    print("Fetching all schedules...")
    url = "https://api.opsgenie.com/v2/schedules"
    headers = {
        "Authorization": "GenieKey 623a40f4-7c85-4259-a463-ce1553567154",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    print("Schedules fetched.")
    return response.json()


# Function to fetch schedule data
def fetch_schedule_data(schedule_id):
    print(f"Fetching data for schedule ID: {schedule_id}...")
    url = f"https://api.opsgenie.com/v2/schedules/{schedule_id}/timeline?interval=4&intervalUnit=months"
    headers = {
        "Authorization": "GenieKey 623a40f4-7c85-4259-a463-ce1553567154",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f"Data fetched for schedule ID: {schedule_id}.")
    else:
        print(f"Error fetching info: {response.status_code}, {response.text}")
    return response.json()


# Step 1: Fetch all schedules
schedules_data = fetch_all_schedules()
schedule_ids = [schedule['id'] for schedule in schedules_data['data']]

# DataFrame to hold all data
all_data = []

# Step 2: Iterate through each schedule and collect data
for schedule_id in schedule_ids:
    schedule_data = fetch_schedule_data(schedule_id)

    if 'data' in schedule_data and 'finalTimeline' in schedule_data['data']:
        rotations = schedule_data['data']['finalTimeline']['rotations']

        for rotation in rotations:
            rotation_name = rotation['name']

            # Check if 'periods' exists in the rotation
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
                print(f"No 'periods' found for rotation: {rotation_name} in Schedule: {schedule_data['data']['_parent']['name']}")
    time.sleep(0.25)

# Create a DataFrame from the collected data
df = pd.DataFrame(all_data)
print(df)

# Convert startDate to datetime with mixed format
try:
    df['startDate'] = pd.to_datetime(df['startDate'], format='mixed', utc=True)
except Exception as e:
    print(f"Error converting startDate: {e}")
    print(df['startDate'])  # Print the raw data for debugging

# Convert endDate to datetime with mixed format
try:
    df['endDate'] = pd.to_datetime(df['endDate'], format='mixed', utc=True)
except Exception as e:
    print(f"Error converting endDate: {e}")
    print(df['endDate'])  # Print the raw data for debugging

start_range = pd.to_datetime('2024-10-01T00:00:00Z', utc=True)
end_range = pd.to_datetime('2024-12-31T23:59:59Z', utc=True)

# filtered_df = df[(df['startDate'] >= start_range) & (df['endDate'] <= end_range)]
filtered_df = df[(df['startDate'] <= end_range) & (df['endDate'] >= start_range)]

# Export the DataFrame to a CSV file
csv_file_path = '../OutputFiles-Logs/schedule_data.csv'
filtered_df.to_csv(csv_file_path, index=False)
print(f"Data exported to {csv_file_path}.")

# Create a list of unique recipient names
unique_users_in_schedule = filtered_df['recipient_name'].unique().tolist()

# **********

all_users_in_opsgenie = get_all_users()
print(f"Total number of users with role 'Users' detected in Opsgenie ({len(all_users_in_opsgenie)}): {list(all_users_in_opsgenie)}")

# Print the unique recipient names
print(f"List of users in schedule for Q4 ({len(unique_users_in_schedule)}):", unique_users_in_schedule)

team_admins = get_all_team_admins()
print(f"Team admins: ({len(team_admins)}):", team_admins)

not_scheduled_users = [item for item in all_users_in_opsgenie if item not in unique_users_in_schedule]
print(f"Total number of non-scheduled users for Q4: {len(not_scheduled_users)}: {list(not_scheduled_users)}")

# Remove users that exist in team_admins
remove_users = [user for user in not_scheduled_users if user not in team_admins]
print(f"Total number of non-scheduled users for Q4 (without team admins): {len(remove_users)}: {list(remove_users)}")