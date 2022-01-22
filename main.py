import asyncio
import re
import os
op = os.name == 'nt'
if op: import winsound
from concurrent.futures import ThreadPoolExecutor
from timeit import default_timer
import time

import requests

from dhooks import Webhook, Embed

from plyer import notification

sound = False
profit = 10000000 # change this to how much minimun money in profit you want, ONLY FOR WEBHOOK

c = requests.get("https://api.hypixel.net/skyblock/auctions?page=0")
resp = c.json()
now = resp['lastUpdated']
toppage = resp['totalPages']

results = []
prices = {}

# stuff to remove
REFORGES = []

# Constant for the lowest priced item you want to be shown to you; feel free to change this
LOWEST_PRICE = 5

# Constant to turn on/off desktop notifications
NOTIFY = False

# Constant for the lowest percent difference you want to be shown to you; feel free to change this
LOWEST_PERCENT_MARGIN = 1/2

START_TIME = default_timer()

def fetch(session, page):
    global toppage
    base_url = "https://api.hypixel.net/skyblock/auctions?page="
    with session.get(base_url + page) as response:
        # puts response in a dict
        data = response.json()
        toppage = data['totalPages']
        if data['success']:
            toppage = data['totalPages']
            for auction in data['auctions']:
                if not auction['claimed'] and 'bin' in auction and not "Furniture" in auction["item_lore"]: # if the auction isn't a) claimed and is b) BIN
                    # removes level if it's a pet, also 
                    index = re.sub("\[[^\]]*\]", "", auction['item_name']) + auction['tier']
                    # removes reforges and other yucky characters
                    for reforge in REFORGES: index = index.replace(reforge, "")
                    # if the current item already has a price in the prices map, the price is updated

                    if index in prices:
                        if prices[index][0] > auction['starting_bid']:
                            prices[index][1] = prices[index][0]
                            prices[index][0] = auction['starting_bid']
                        elif prices[index][1] > auction['starting_bid']:
                            prices[index][1] = auction['starting_bid']
                    # otherwise, it's added to the prices map
                    else:
                        prices[index] = [auction['starting_bid'], float("inf")]
                        
                    # if the auction fits in some parameters
                    if prices[index][1] > LOWEST_PRICE and prices[index][0]/prices[index][1] < LOWEST_PERCENT_MARGIN and auction['start']+60000 > now:
                        results.append([auction['uuid'], auction['item_name'], auction['starting_bid'], index])
        return data

async def get_data_asynchronous():
    # puts all the page strings
    pages = [str(x) for x in range(toppage)]
    with ThreadPoolExecutor(max_workers=10) as executor:
        with requests.Session() as session:
            loop = asyncio.get_event_loop()
            START_TIME = default_timer()
            tasks = [
                loop.run_in_executor(
                    executor,
                    fetch,
                    *(session, page) # Allows us to pass in multiple arguments to `fetch`
                )
                # runs for every page
                for page in pages if int(page) < toppage
            ]
            for response in await asyncio.gather(*tasks):
                pass

def main():
    # Resets variables
    global results, prices, START_TIME
    START_TIME = default_timer()
    results = []
    prices = {}
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    future = asyncio.ensure_future(get_data_asynchronous())
    loop.run_until_complete(future)
    
    # Makes sure all the results are still up to date
    if len(results): results = [[entry, prices[entry[3]][1]] for entry in results if (entry[2] > LOWEST_PRICE and prices[entry[3]][1] != float('inf') and prices[entry[3]][0] == entry[2] and prices[entry[3]][0]/prices[entry[3]][1] < LOWEST_PERCENT_MARGIN)]
    
    if len(results): # if there's results to print

        if NOTIFY: 
            notification.notify(
                title = max(results, key=lambda entry:entry[1])[0][1],
                message = "Lowest BIN: " + f'{max(results, key=lambda entry:entry[1])[0][2]:,}' + "\nSecond Lowest: " + f'{max(results, key=lambda entry:entry[1])[1]:,}',
                app_icon = None,
                timeout = 4,
            )
        
    
        done = default_timer() - START_TIME

        if sound == True:
            if op: winsound.Beep(500, 500) # emits a frequency 500hz, for 500ms
        for result in results:

            myself = 'https://discord.com/api/webhooks/925021265587241011/U8RP6aP9YvCGt9sA95SBSnq4idtFJUkPW5XfUPl5-b4nNl3t-6xRJvF0YRqE8JFc15-z'

            if result[1] - result[0][2] >= profit:
                for x in [myself]:
                    hook = Webhook(x)
                    profitz = result[1] - result[0][2] 
                    embed = Embed(
                        description="Item Name: " + str(result[0][1]) + "\nItem price: {:,}".format(result[0][2]) + "\nSecond lowest BIN: {:,}".format(result[1]) + "\nProfit: {:,}".format(profitz) + "\nAuction UUID: " + str(result[0][0]),
                        color=0x5CDBF0,
                        timestamp='now'  # sets the timestamp to current time
                    )
                    image1 = 'https://i.imgur.com/08elL7k.png'
                    embed.set_author(name="NEW FLIP")
                    embed.add_field(name='Copy Command', value='/viewauction ' + str(result[0][0]))
                    embed.set_footer(text='Made by Ntdi • https://discord.gg/Rgd4VtyXFV')
                    embed.set_thumbnail(image1)
                    hook.send(embed=embed)

            print("Auction UUID: " + str(result[0][0]) + " | Item Name: " + str(result[0][1]) + " | Item price: {:,}".format(result[0][2]), " | Second lowest BIN: {:,}".format(result[1]) + " | Time to refresh AH: " + str(round(done, 2)))
        print("\nLooking for auctions...")

print("Looking for auctions...")
main()

def dostuff():
    global now, toppage

    # if 60 seconds have passed since the last update
    if time.time()*1000 > now + 60000:
        prevnow = now
        now = float('inf')
        c = requests.get("https://api.hypixel.net/skyblock/auctions?page=0").json()
        if c['lastUpdated'] != prevnow:
            now = c['lastUpdated']
            toppage = c['totalPages']
            main()
        else:
            now = prevnow
    time.sleep(0.5)

while True:
    dostuff()
