import requests
import time
import logging
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv('API_KEY')

# Headers for the API requests
HEADERS = {
    "Authorization": f"GenieKey {API_KEY}",
    "Content-Type": "application/json"
}

# Logging config
logging.basicConfig(filename='OutputFiles-Logs/execution.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# Function to fetch all teams
def get_all_teams():
    url = "https://api.opsgenie.com/v2/teams"
    logging.info("Fetching all teams from OpsGenie...")
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        teams_data = response.json()
        teams = teams_data.get('data', [])
        logging.info(f"Successfully fetched {len(teams)} teams.")
        print(f"Successfully fetched {len(teams)} teams.")
        return teams
    else:
        error_message = f"Error fetching teams: {response.status_code}, {response.text}"
        logging.error(error_message)
        print(error_message)
        return []


# Function to fetch team members and filter admins
def get_team_admins(team_id):
    url = f"https://api.opsgenie.com/v2/teams/{team_id}"
    logging.info(f"Fetching team members for team ID {team_id}...")
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        team_data = response.json()
        members = team_data.get('data', {}).get('members', [])

        # Filter members with the role 'admin'
        admin_members = []
        for member in members:
            role = member.get('role')
            if role == 'admin':
                username = member.get('user', {}).get('username', 'N/A')
                admin_members.append(username)

        logging.info(f"Found {len(admin_members)} admin(s) in team ID {team_id}.")
        print(f"Found {len(admin_members)} admin(s) in team ID {team_id}.")
        return admin_members
    else:
        error_message = f"Error fetching team members for team ID {team_id}: {response.status_code}, {response.text}"
        logging.error(error_message)
        print(error_message)
        return []


# Function to get all team admins
def get_all_team_admins():
    logging.info("Starting process to fetch all team admins.")
    teams = get_all_teams()  # Fetch all teams
    all_admins = []  # List to store all admin usernames

    # Iterate through each team and fetch admins
    for team in teams:
        team_id = team.get('id')
        team_name = team.get('name')
        logging.info(f"Processing team: {team_name} (ID: {team_id})")
        print(f"\nProcessing team: {team_name} (ID: {team_id})")

        # Fetch and collect admins for this team
        admins = get_team_admins(team_id)
        all_admins.extend(admins)  # Add the admins to the all_admins list

    logging.info(f"Completed fetching admins. Total admins found: {len(all_admins)}")
    print(f"Completed fetching admins. Total admins found: {len(all_admins)}")
    return all_admins  # Return the list of all admins


if __name__ == "__main__":
    get_all_team_admins()
