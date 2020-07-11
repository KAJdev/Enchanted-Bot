# Enchanted-Bot
older discord bot with a real-time PVP system


# A statement about why this is public
I have worked on this bot ever since the start of Febuary 2020. I have built literally this entire bot, with the exception of maybe around 50 lines by Niels.
Anyway, I have worked on this bot ever since it's inception, and on July 8th I woke up to being removed from the team. my code was kept by them, I was removed from my roles,
and they had deleted lots of data from my personal DataBase that Enchanted has used. They didn't bother to explain why they removed me, or tell me before hand. They had 
made an announcement in the public discord that I was removed. They explained that the big issue was communication, Which is weird since I would explain everything I was doing, 
had good commit messages, and overall communicated my ideas. I then spent the next 3 days trying to convince them that removing a team member that literally built the entire project
was a mistake, and even a bit cruel. They didn't listen at all, and stuck with their decision. So, I will be posting the source code of the bot, not to get them back, but so that I
can actually gain something from working on a project for over 6 months.

# How to run the bot
1. Clone the repo any way you want (you can use the green button to download a .zip of the files)
2. Start a Mongo Database (google a tutorial or something. It's not too hard)
3. Open Config.py and put the URI in the URI place in line 7-8 of the config. (`myclient = pymongo.MongoClient("URI")`)
4. go to https://discord.com/developers/applications and create a new application
5. On the left, click the 'Bot' tab and create a bot user. Copy the token for use in the next step.
6. On line 47 and 49 of Config.py replace each string with the a bot token. the Main bot token will be used for production, and the testing bot token will be used for testing. (can be the same)
7. make sure Python 3.6 is installed. if not, google "Install python 3.6"
8. Open a command promp (or terminal on MacOS) and navigate to the place yoiu downloaded the bot. (google if you get stuck)
9. to start the bot, 
Windows: 'py Main.py'
MacOS/Linux: 'python3 Main.py'

Boom. You have your very own enchanted. There can be some extra steps, like filling in IDs for discord servers for clan icons to be uploaded to but those aren't 100% critical.
