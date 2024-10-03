import requests
from getNotSchedluedUsers_V2 import process_users_and_schedules
import logging
from dotenv import load_dotenv
import os

load_dotenv()

# logging config
logging.basicConfig(filename='OutputFiles-Logs/execution.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = os.getenv('API_KEY')
HEADERS = {
    'Authorization': f'GenieKey {API_KEY}',
    'Content-Type': 'application/json'
}


def get_user_id(username):
    # API endpoint to get user details by username
    url = f"https://api.opsgenie.com/v2/users/{username}"
    logging.info(f"Fetching user ID for {username}.")
    print(f"Fetching user ID for {username}.")
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            data = response.json()
            user_id = data.get('data', {}).get('id', None)
            if user_id:
                logging.info(f"User ID for {username} is {user_id}.")
                print(f"User ID for {username} is {user_id}.")
                return user_id
            else:
                logging.warning(f"User ID for {username} not found.")
                print(f"User ID for {username} not found.")
                return None
        except ValueError:
            logging.error("Error parsing JSON response for user ID.")
            print("Error parsing JSON response for user ID.")
            return None
    else:
        logging.error(f"Error fetching user ID for {username}: {response.status_code}, {response.text}")
        print(f"Error fetching user ID for {username}: {response.status_code}, {response.text}")
        return None


def get_user_teams(user):
    url = f"https://api.opsgenie.com/v2/users/{user}/teams"
    logging.info(f"Fetching teams for user {user}.")
    print(f"Fetching teams for user {user}.")
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            data = response.json()
            teams = data.get('data', [])
            if teams:
                team_info = [{'name': team['name'], 'id': team['id']} for team in teams]
                logging.info(
                    f"User {user} belongs to the following teams: {', '.join([team['name'] for team in team_info])}")
                print(f"User {user} belongs to the following teams: {', '.join([team['name'] for team in team_info])}")
                return team_info
            else:
                logging.info(f"User {user} does not belong to any teams.")
                print(f"User {user} does not belong to any teams.")
                return []
        except ValueError:
            logging.error("Error parsing JSON response for teams.")
            print("Error parsing JSON response for teams.")
            return None
    else:
        logging.error(f"Error fetching teams for {user}: {response.status_code}, {response.text}")
        print(f"Error fetching teams for {user}: {response.status_code}, {response.text}")
        return None


def delete_user_from_team(user_id, team_id):
    url = f"https://api.opsgenie.com/v2/teams/{team_id}/members/{user_id}"
    logging.info(f"Removing user ID {user_id} from team ID {team_id}.")
    print(f"Removing user ID {user_id} from team ID {team_id}.")
    response = requests.delete(url, headers=HEADERS)

    if response.status_code == 200:
        logging.info(f"Successfully removed user ID {user_id} from team ID {team_id}.")
        print(f"Successfully removed user ID {user_id} from team ID {team_id}.")
    else:
        logging.error(
            f"Error removing user ID {user_id} from team ID {team_id}: {response.status_code}, {response.text}")
        print(f"Error removing user ID {user_id} from team ID {team_id}: {response.status_code}, {response.text}")


def get_user_schedules(user):
    url = f"https://api.opsgenie.com/v2/users/{user}/schedules"
    logging.info(f"Fetching schedules for user {user}.")
    print(f"Fetching schedules for user {user}.")
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        try:
            data = response.json()
            schedules = data.get('data', [])
            if schedules:
                schedule_info = [{'name': schedule['name'], 'id': schedule['id']} for schedule in schedules]
                logging.info(
                    f"User {user} belongs to the following schedules: {', '.join([schedule['name'] for schedule in schedule_info])}")
                print(f"User {user} belongs to the following schedules: {', '.join([schedule['name'] for schedule in schedule_info])}")
                return schedule_info
            else:
                logging.info(f"User {user} does not belong to any schedules.")
                print(f"User {user} does not belong to any schedules.")
                return []
        except ValueError:
            logging.error("Error parsing JSON response for schedules.")
            print("Error parsing JSON response for schedules.")
            return None
    else:
        logging.error(f"Error fetching schedules for {user}: {response.status_code}, {response.text}")
        print(f"Error fetching schedules for {user}: {response.status_code}, {response.text}")
        return None


def get_rotations_with_user(schedule_id, user):
    """Fetches rotations that include the specified user from a schedule."""
    url = f"https://api.opsgenie.com/v2/schedules/{schedule_id}/rotations"
    print(f"Fetching rotations for schedule {schedule_id}.")
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        rotations = response.json().get('data', [])
        # Filter to get only the rotations that include the user
        rotations_with_user = [rotation for rotation in rotations if any(p.get('username') == user for p in rotation.get('participants', []))]

        if rotations_with_user:
            print(f"Found {len(rotations_with_user)} rotations with user {user} in schedule {schedule_id}.")
            return rotations_with_user
        else:
            print(f"No rotations found with user {user} in schedule {schedule_id}.")
            return []
    else:
        print(f"Error fetching rotations for schedule {schedule_id}: {response.status_code}, {response.text}")
        return []


def update_schedule_rotation_without_user(schedule_id, rotation_id, user):
    """Updates the rotation to remove the specified user."""
    url = f"https://api.opsgenie.com/v2/schedules/{schedule_id}/rotations/{rotation_id}?scheduleIdentifierType=id"
    print(f"Updating rotation {rotation_id} in schedule {schedule_id} to remove user {user}.")
    logging.info(f"Updating rotation {rotation_id} in schedule {schedule_id} to remove user {user}.")

    # Fetch the current rotation details
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        rotation = response.json().get('data', {})
        participants = rotation.get('participants', [])
        print(f"PARTICIPANTS:{participants}")
        logging.info(f"Rotation PARTICIPANTS before change:{participants}")

        # Filter out the user from the participants
        updated_participants = [p for p in participants if p.get('username') != user]
        print(f"UPDATED PARTICIPANTS: {updated_participants}")
        logging.info(f"Rotation PARTICIPANTS after removing user:{participants}")

        # Patch the rotation with updated participants
        payload = {"participants": updated_participants}
        # patch_response = requests.patch(url, headers=HEADERS, json=payload)

        # if patch_response.status_code == 200:
        #     print(f"Successfully removed user {user} from rotation {rotation_id} in schedule {schedule_id}.")
        # else:
        #     print(
        #         f"Error updating rotation {rotation_id} in schedule {schedule_id}: {patch_response.status_code}, {patch_response.text}")
    else:
        print(f"Error fetching rotation {rotation_id}: {response.status_code}, {response.text}")


def change_user_role(user_list, new_role):
    for user in user_list:
        logging.info(f"Processing user {user}.")
        print(f"Processing user {user}.")
        user_id = get_user_id(user)  # check user ID
        if user_id is None:
            logging.warning(f"Skipping user {user} due to ID fetch error.")
            print(f"Skipping user {user} due to ID fetch error.")
            continue  # Skip to the next user if ID is not found

        user_teams = get_user_teams(user)  # check user Teams
        if user_teams is None:
            logging.warning(f"Skipping user {user} due to team fetch error.")
            print(f"Skipping user {user} due to team fetch error.")
        elif not user_teams:
            logging.info(f"No teams found for user {user}. Skipping deletion from teams.")
            print(f"No teams found for user {user}. Skipping deletion from teams.")
        else:
            for team in user_teams:
                delete_user_from_team(user_id, team['id'])  # Use team ID to remove the user from the team

        user_schedules = get_user_schedules(user)  # check user schedules
        if user_schedules is None:
            logging.warning(f"Skipping user {user} due to schedule fetch error.")
            print(f"Skipping user {user} due to schedule fetch error.")
        elif not user_schedules:
            logging.info(f"No schedules found for user {user}. Skipping deletion from schedules.")
            print(f"No schedules found for user {user}. Skipping deletion from schedules.")
        else:
            for schedule in user_schedules:
                rotations_with_user = get_rotations_with_user(schedule['id'], user)
                for rotation in rotations_with_user:
                    # Patch the rotation to remove the user
                    print(schedule['id'], rotation['id'], user)
                    update_schedule_rotation_without_user(schedule['id'], rotation['id'], user)

        # URL for updating user role
        url = f"https://api.opsgenie.com/v2/users/{user_id}"
        payload = {
            "role": {
                "id": new_role,
                "name": new_role
            }
        }
        logging.info(f"Changing role for user ID {user_id} to {new_role}.")
        print(f"Changing role for user ID {user_id} to {new_role}.")
        response = requests.patch(url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            logging.info(f"Successfully changed role for user ID {user_id} to {new_role}.")
            print(f"Successfully changed role for user ID {user_id} to {new_role}.")
        else:
            logging.error(f"Error changing role for user ID {user_id}: {response.status_code}, {response.text}")
            print(f"Error changing role for user ID {user_id}: {response.status_code}, {response.text}")


if __name__ == "__main__":
    change_user_role(['santhosh.r@nutanix.com'], 'Stakeholder')
    # change_user_role(process_users_and_schedules(), 'Stakeholder')
