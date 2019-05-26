# RMX Foos Elo Bot
This is a combination of three services (a Django backend, a discord bot, and a Postgres DB) that allows us to maintain a Elo scoreboard for the team.

## Running the service: 
Create a file called `.env` in the root of this project, and provide the following values for the discord server you will be using.
```
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_TOKEN=
```

This will build all the images and start them up:

`docker-compose up --build`

Once the containers are started, any code changes you make will need to be reloaded in the service changed. This can be done by running:

`docker-compose build <service_name> && docker-compose restart <service_name>`

where `<service_name>` is either `elo-service` or `discord-bot`.

The Postgres data is stored within `./data`.
