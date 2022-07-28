# numbers_tt
Google Sheet link - https://docs.google.com/spreadsheets/d/1J5AySFr8EH4V9FInoA-vglkN_5T4ae97fbsagNy3naw/edit#gid=0.

Due to the fact this project requires secret information it will be provided only once via pastebin link.

# instructions

How to setup an environment to use this backend-server using command-line:

1. Make sure you have python3.\* installed:
   `python --version`
2. Install virtual environment (this is **pipenv**, but you can choose your own):
    - go to directory you cloned this repository
    - `pip install pipenv`
3. Go to **pipenv** shell and install all packages:
    - `pipenv shell`
    - `pipenv install -r /path/to/requirements.txt`

Secrets preparation:

1. Create local DB in PostgreSQL and then run script *dump.sql* in it.
2. Fill in the *config.json* file with dbname, user, password, host and port information about DB you just created.
3. Open pastebin link https://pastebin.com/XQiKGh9L (password - name of the company, lowercase) and copy its content to *credential.json* file (*CAREFULL - BURN AFTER READ MODE*).


Run app:

In your local virtual python environment run the app: `python main.py`.

Changes for tests
