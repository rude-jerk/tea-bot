## Bot Functionality

## Commands
### General:
* `tjoin`: Slash command. Accepts Guild Wars 2 account name as a parameter. Links the discord user to the guild wars account name. Checks the in-game guild roster, grants the Freshman discord role to guild members. Grants the Transfer Student role to non-guild members.
* `tregister`: Slash command. Accepts Guild Wars 2 API key as a parameter. Checks the in-game guild roster, grants Freshman, Senior, or Prefect discord roles depending on in-game guild role. Grants the Transfer Student role to non-guild members.
* `twelcome`: Resends the user the join message DM.
* `dailies`: Posts a full list of all current daily achievements.
### Admin Only:
##### Cannot be used in direct messages to the bot, limited to members with the Manage Users permission
* `tlink`: Slash command. Accepts a discord Member and a Guild Wars 2 account name as parameters. Admin version of `tjoin` for other users.
* `tunlink`: Slash command. Accepts a discord Member as a parameter. Removes the discord user's link to a Guild Wars 2 account. Removes all roles from the user.
* `twelcome_push`: Slash command. Accepts a discord Member as a parameter. Resends the user the join message DM.
* `troster`: Slash command. Creates a roster of in-game guild members and discord members, the file it creates is sent so only the invoker can see it.
* `gw2roster`: Slash command. Creates a roster of in-game guild members, the file it creates it sent so only the invoker can see it.


## Auto Functionality
* When a member joins, they receive a message with instructions on how to run `/tjoin` or `/trgister`. The message also contains a button with the label "I'm just visiting", that allows people who join to receive the visitor role. The button is disabled after being clicked, or after 5 minutes have passed. If it has not been interacted with, the user will be required to `/twelcome` to get a new button.
* When a member is given the visitor role, either through the bot or other means, the bot records the time they were granted the visitor role.
* Every hour the bot checks all users with the visitor role against the recorded visitor role time. If it has been longer than 24 hours, the visitor role is removed.
* Every 4 hours the bot checks all users who are linked with a gw2 account against the in-guild roster. Users who are linked with `tjoin` are granted Freshman if they do not already have it. Users linked with `tregister` are granted roles up to Prefect if they do not have them and are of that rank in-game.


### Other
* React roles (RAIDS, FRACTALS, STRIKES) in the notifications channel.
* Logs most usages to the bot-logs channel.

