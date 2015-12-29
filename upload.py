import requests
from pymongo import MongoClient
import json
import sys

def print_formatted(data):
    print(json.dumps(data, indent=4, sort_keys=True))

class UploadManager(object):
    def __init__(self):
        self._base_url = 'http://localhost:8009'
        self._username = 'anders'
        self._password = 'yoloyolo'
        self._token_key = 'x-tidepool-session-token'

    def prepare_for_uploads(self):
        self._clear_database()
        self._create_user()
        self._login()

    def upload_data(self):
        url = self._build_url('/upload/data')
        headers = {self._token_key: self._token}

        with open('upload_data.json', 'r') as f:
            upload_data = json.load(f)

        print(len(upload_data))

        index = 0
        for upload in upload_data:
            response = requests.post(url, headers=headers, json=upload)
            if response.status_code == 200:
                response_data = response.json()
            else:
                print(index)
                print_formatted(upload)
                print(response)
                print_formatted(response.text)
                sys.exit(1)
            index += 1

 
    def _clear_database(self):
        client = MongoClient('localhost', 27017)
        client.drop_database('user')
        client.close()

    def _create_user(self):
        url = self._build_url('/auth/user')
        payload = {'username': self._username, 'password': self._password}

        response = requests.post(url, json=payload)
        data = response.json()
        self._user_id = data['userid']
        self._token = response.headers['x-tidepool-session-token']

        self._verify_user()

    def _verify_user(self):
        client = MongoClient('localhost', 27017)
        db = client.user
        db.users.update_one(
            {"username": self._username},
            {"$set": {"authenticated": True}})
        client.close()

    def _login(self):
        url = self._build_url('/auth/login')
        response = requests.post(url, auth=(self._username, self._password))
        self._token = response.headers['x-tidepool-session-token']

    def _build_url(self, endpoint):
        return self._base_url + endpoint


def main():
    upload_manager = UploadManager()
    upload_manager.prepare_for_uploads()
    upload_manager.upload_data()

if __name__ == '__main__':
    main()
