# Trakt-or.py
Python script to track your PLEX media library progress with trakt.tv public API.

## Install instructions
To install the the script run the following:

````
git clone <URL>

cd trakt-plex-tracker
pip install -r requirements.txt
````

## Configure Trakt-or.py

The configuration file is located at the "/" of the script

> config.ini

Modify the following lines in the configuration file:

```
[trakt.tv]
client_id = <CLIENT_ID>
client_secret = <CLIENT_SECRET>

[Plex]
database_location = <PATH-TO>/com.plexapp.plugins.library.db
```

Now you are ready to run the script.

## Run Trakt-or.py

To run the script enter the following command:
```
python trakt-or.py
```

After the script run successfully start a simple webserver at the following location:

```
cd ./frontend/
python3 -m http.server
```

Open the browser and go to:

> http://localhost:8000
