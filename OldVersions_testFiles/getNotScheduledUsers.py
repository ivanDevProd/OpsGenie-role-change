import requests
import time

# Set your Opsgenie API key
API_KEY = "623a40f4-7c85-4259-a463-ce1553567154"  # Replace with your actual API key
HEADERS = {
    "Authorization": f"GenieKey {API_KEY}",
    "Content-Type": "application/json"
}

# Constants
LIMIT = 100  # Maximum number of results per request

# Fetch all active users with pagination
def get_all_users():
    url = "https://api.opsgenie.com/v2/users"
    all_users = []
    offset = 0

    while True:
        params = {
            "limit": LIMIT,
            "offset": offset
        }
        response = requests.get(url, headers=HEADERS, params=params)

        print(f"Response for all users: {response.json()}")  # Debugging line

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


# Fetch users scheduled for a specific schedule between start_date and end_date
def get_scheduled_users(schedule_id, start_date, end_date):
    url = f"https://api.opsgenie.com/v2/schedules/{schedule_id}/on-calls"
    params = {
        'flat': 'true',
        'interval': 'custom',
        'dateRangeStart': start_date,
        'dateRangeEnd': end_date
    }

    retries = 5  # Increase the retry count here
    for attempt in range(retries):
        response = requests.get(url, headers=HEADERS, params=params)

        print(f"Response for schedule ID {schedule_id}: {response.json()}")  # Debugging line

        if response.status_code == 200:
            data = response.json().get('data', {})
            return data.get('onCallRecipients', [])
        elif response.status_code == 429:  # Rate limit
            wait_time = 16 * (attempt + 1)  # Exponential backoff
            print(f"Rate limited, retrying in {wait_time} seconds (Retry {attempt + 1}/{retries})...")
            time.sleep(wait_time)
        else:
            print(f"Error fetching scheduled users: {response.status_code}, {response.text}")
            break

    print(f"Failed to fetch schedule ID {schedule_id} after {retries} retries.")
    return []


# Main function to get all active users and those scheduled for the specified quarter
def get_users_info(schedule_ids, start_date, end_date):
    all_users = set(get_all_users())
    scheduled_users = set()

    for schedule_id in schedule_ids:
        scheduled_users.update(get_scheduled_users(schedule_id, start_date, end_date))
        time.sleep(0.1)  # Sleep for 1 second between requests to reduce frequency

    return all_users, scheduled_users


# Get the list of all schedule IDs
def get_all_schedule_ids():
    url = "https://api.opsgenie.com/v2/schedules"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return [schedule['id'] for schedule in response.json()['data']]
    else:
        print(f"Error fetching schedules: {response.status_code}, {response.text}")
        return []


# Example usage
if __name__ == "__main__":
    schedule_ids = get_all_schedule_ids()

    # Define the start and end dates for the fourth quarter
    quarter_start = "2024-10-01T00:00:00Z"  # October 1
    quarter_end = "2024-12-31T23:59:59Z"  # December 31

    all_users, scheduled_users = get_users_info(schedule_ids, quarter_start, quarter_end)

    not_scheduled_users = all_users - scheduled_users

    # Print all required information
    print(f"Total number of users with role 'Users' detected in Opsgenie: {len(all_users)}")
    print("List of all users with role 'Users':", list(all_users))
    print(f"Total number of schedules: {len(schedule_ids)}")
    print(f"Total number of users detected in schedules for Q4: {len(scheduled_users)}")
    print("List of users in schedule for Q4:", list(scheduled_users))
    print(f"Total number of active users not in schedule for Q4: {len(not_scheduled_users)}")
    print("List of active users not scheduled for Q4:", list(not_scheduled_users))