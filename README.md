# Trakt-or.py
Python script to track your PLEX media library progress with trakt.tv public API.


![Upcoming Shows](https://github.com/h1f0x/docker-trackt-plex-tracker/blob/master/images/1.png?raw=true)
![Detail Show](https://github.com/h1f0x/docker-trackt-plex-tracker/blob/master/images/2.png?raw=true)


## Install instructions
To install the the script run the following:

````
git clone <URL>

cd trakt-plex-tracker
pip install -r requirements.txt
````

### trakt.tv API keys
Visit https://trakt.tv/oauth/applications and create a new application.

You will get the following API keys:
- Client ID
- Client Secret

Note it down.

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

# language codes examples > de, fr, it, es and so on.. (https://trakt.docs.apiary.io/#reference/languages/get-languages)
# script default language is "en"
library_language = en
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
