import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient

db = AsyncIOMotorClient("mongodb+srv://enchanted:sCqG3duvWNQpMxPO@enchanted-1-ertal.mongodb.net/")


async def main():
    coll = db["enchanted-main"]['users']

    async for d in coll.find({}):
        titles = [{'type': 'color', 'name': 'Basic color', 'value': "0xdb58dd"}, {'type': 'emote', 'value': "Wow!"}, {'type': 'emote', 'value': "Good Game!"}, {'type': 'emote', 'value': '<:smi:729075126532046868>'}]
        for title in d["titles"]:
            if "Aged" or "aged" not in title:
                titles.append({'type': 'title', 'value': title})
        try:
            await coll.replace_one(
                {"_id": d["_id"]},
                {
                    'user_id': d["user_id"], 
                    'rubies': d["rubies"], 
                    'crowns': 0, 
                    'claimed_contract': {}, 
                    'coins': d["coins"], 
                    'xp': d["xp"], 
                    'inventory': d["inventory"], 
                    'weapon': d["weapon"], 
                    'armor': d["armor"], 
                    'class': d["class"], 
                    'cosmetics': titles,
                    'selected_title': " The " + d["class"].capitalize(), 
                    'selected_embed_color': {'name': "Basic color", 'value': "0xdb58dd"}, 
                    'selected_embed_image': None, 
                    'keys': d["keys"], 
                    'grown': d["grown"], 
                    'crops': d["crops"], 
                    'stats': d['stats'], 
                    'seeds': d["seeds"],
                    'battles': d["battles"], 
                    'power': d["power"], 
                    'chests': d["chests"], 
                    'spells': d["spells"], 
                    'slots': d["slots"], 
                    'registered': d["registered"],
                },
            )
        except KeyError:
            print(d["user_id"])


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
