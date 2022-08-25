from datetime import date, timedelta
import requests
from discord.ext import commands, tasks
from subprocess import check_output
import logging
from scrambleconvert import scramble, solve
from concurrent.futures import ThreadPoolExecutor
import time
import json

logging.basicConfig(filename="/home/josh/clockbot/clockbot.log",level=logging.INFO,format="%(asctime)s:%(message)s")
logging.getLogger("discord").setLevel(logging.ERROR)

client = commands.Bot(command_prefix = "!")
client.remove_command('help')

countries=['all','afghanistan', 'albania', 'algeria', 'andorra', 'angola', 'antigua and barbuda', 'argentina', 'armenia', 'australia', 'austria', 'azerbaijan', 'bahamas', 'bahrain', 'bangladesh', 'barbados', 'belarus', 'belgium', 'belize', 'benin', 'bhutan', 'bolivia', 'bosnia and herzegovina', 'botswana', 'brazil', 'brunei', 'bulgaria', 'burkina faso', 'burundi', 'cabo verde', 'cambodia', 'cameroon', 'canada', 'central african republic', 'chad', 'chile', 'china', 'colombia', 'comoros', 'congo', 'costa rica', 'côte d&#39;ivoire', 'croatia', 'cuba', 'cyprus', 'czech republic', 'democratic people&#39;s republic of korea', 'democratic republic of the congo', 'denmark', 'djibouti', 'dominica', 'dominican republic', 'ecuador', 'egypt', 'el salvador', 'equatorial guinea', 'eritrea', 'estonia', 'eswatini', 'ethiopia', 'federated states of micronesia', 'fiji', 'finland', 'france', 'gabon', 'gambia', 'georgia', 'germany', 'ghana', 'greece', 'grenada', 'guatemala', 'guinea', 'guinea bissau', 'guyana', 'haiti', 'honduras', 'hong kong', 'hungary', 'iceland', 'india', 'indonesia', 'iran', 'iraq', 'ireland', 'israel', 'italy', 'jamaica', 'japan', 'jordan', 'kazakhstan', 'kenya', 'kiribati', 'kosovo', 'kuwait', 'kyrgyzstan', 'laos', 'latvia', 'lebanon', 'lesotho', 'liberia', 'libya', 'liechtenstein', 'lithuania', 'luxembourg', 'macau', 'madagascar', 'malawi', 'malaysia', 'maldives', 'mali', 'malta', 'marshall islands', 'mauritania', 'mauritius', 'mexico', 'moldova', 'monaco', 'mongolia', 'montenegro', 'morocco', 'mozambique', 'multiple countries (africa)', 'multiple countries (americas)', 'multiple countries (asia)', 'multiple countries (europe)', 'multiple countries (north america)', 'multiple countries (oceania)', 'multiple countries (south america)', 'multiple countries (world)', 'myanmar', 'namibia', 'nauru', 'nepal', 'netherlands', 'new zealand', 'nicaragua', 'niger', 'nigeria', 'north macedonia', 'norway', 'oman', 'pakistan', 'palau', 'palestine', 'panama', 'papua new guinea', 'paraguay', 'peru', 'philippines', 'poland', 'portugal', 'qatar', 'republic of korea', 'romania', 'russia', 'rwanda', 'saint kitts and nevis', 'saint lucia', 'saint vincent and the grenadines', 'samoa', 'san marino', 'são tomé and príncipe', 'saudi arabia', 'senegal', 'serbia', 'seychelles', 'sierra leone', 'singapore', 'slovakia', 'slovenia', 'solomon islands', 'somalia', 'south africa', 'south sudan', 'spain', 'sri lanka', 'sudan', 'suriname', 'sweden', 'switzerland', 'syria', 'taiwan', 'tajikistan', 'tanzania', 'thailand', 'timor-leste', 'togo', 'tonga', 'trinidad and tobago', 'tunisia', 'turkey', 'turkmenistan', 'tuvalu', 'uganda', 'ukraine', 'united arab emirates', 'united kingdom', 'united states', 'uruguay', 'uzbekistan', 'vanuatu', 'vatican city', 'venezuela', 'vietnam', 'yemen', 'zambia', 'zimbabwe']


@client.event
async def on_ready():
  print("Bot is online!")
  logging.info("bot online")
  task_loop.start()
  task_loop2.start()


#this task loop checks for new clock cr or wrs.
counter=6 #counter is here so that the frequency of requests will change depending on the day of the week, so that less requests will be sent on a wednesday compared to a saturday. it starts at 6 so that immediately upon the script starting it will check for a record regardless of the day of the week.
@tasks.loop(seconds=300)
async def task_loop2():
  global counter
  counter+=1
  logging.info(f"counter: {counter}")
  if counter>5 or date.today().weekday()==5 or date.today().weekday()==6 or (counter>3 and (date.today().weekday()==3 or date.today().weekday()==4 or date.today().weekday()==0)):
    counter=0
    json_data = {
        'operationName': 'Competitions',
        'variables': {
            'from': '2022-07-19'
        },
        'query': 'query Competitions($from: Date!) {\n  competitions(from: $from) {\n    id\n    name\n    startDate\n    endDate\n    startTime\n    endTime\n    venues {\n      id\n      country {\n        iso2\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  recentRecords {\n    id\n    tag\n    type\n    attemptResult\n    result {\n      id\n      person {\n        id\n        name\n        country {\n          iso2\n          name\n          __typename\n        }\n        __typename\n      }\n      round {\n        id\n        competitionEvent {\n          id\n          event {\n            id\n            name\n            __typename\n          }\n          competition {\n            id\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}',
    }
    r = requests.post('https://live.worldcubeassociation.org/api', json=json_data)
    data=json.loads(r.text)
    x=data["data"]["recentRecords"]
    for i in x:
      if (i["tag"]=="CR" or i["tag"]=="WR") and i["result"]["round"]["competitionEvent"]["event"]["name"]=="Clock":
        with open("/home/josh/clockbot/records.txt","r") as x: known_records = x.readlines()
        if i["result"]["person"]["name"]+" "+str(int(i["attemptResult"])/100)+" "+i["tag"]+" "+i["type"]+'!\n' not in known_records:
          logging.info(i["result"]["person"]["name"]+" "+str(int(i["attemptResult"])/100)+" "+i["tag"]+" "+i["type"]+'!')
          with open("/home/josh/clockbot/records.txt","a") as x: x.write(i["result"]["person"]["name"]+" "+str(int(i["attemptResult"])/100)+" "+i["tag"]+" "+i["type"]+'!\n')
          channel=client.get_channel(868896519074480138)#news channel in clock solvers discord. dm me if you want me to add a channel to this, but I don't have a command for you to add it yourself because of problems that have been happening with the competition notifications
          await channel.send(i["result"]["person"]["name"]+" "+str(int(i["attemptResult"])/100)+" "+i["tag"]+" "+i["type"]+'!')



#command used for setting up competition updates
@client.command()
async def compupdates(ctx, *, message: str):
  logging.info(f"!compupdates {message}")
  if message.lower()=="help":
    await ctx.channel.send('do "!compupdates {country}" to start recieving competition updates in the channel of your choice (you can also use the command in a dm with the bot so you get pinged). if you want to be notified of all clock competitions do "!compupdates all". to stop being notified of new clock competitions in a channel, do "!compupdates stop". note that this will stop notifications for every previously added country.')
  else:
    with open("/home/josh/clockbot/channels.txt", "r") as x: l=x.readlines()
    if not any(str(ctx.channel.id) in s for s in l) and message.lower() in countries:
      with open("/home/josh/clockbot/channels.txt", "a") as x: x.write(f"{str(ctx.channel.id)},{message.lower()}\n")
      await ctx.channel.send(f'you will now get messages in this channel when new clock competitions are announced in {message}. to stop stop getting these messages, do "!compupdates stop". to get notified when competitions are announced in other countries, just use this command again but with the other country you would like to add.')
      logging.info(f"started !compupdates {message} in {ctx.channel.id}")
    else:
      if message.lower()=="stop":
        with open("/home/josh/clockbot/channels.txt", "w") as file:
          for line in l:
            if str(ctx.channel.id) not in line:
              file.write(line)
        await ctx.channel.send('messages will no longer be sent in this channel when competitions are announced. use "!compupdates {country}" to start them again. note that this command stops notifications for all countries that you have previously added.')
        logging.info(f"!compupdates stop in {ctx.channel.id}")
      else:
        if message.lower() in countries:
          with open("/home/josh/clockbot/channels.txt", "w") as file:
            for line in l:
              if str(ctx.channel.id) not in line:
                file.write(line)
              else:
                file.write(line.strip('\n')+","+message.lower()+"\n")
          await ctx.channel.send(f'you will now get messages in this channel when new clock competitions are announced in {message}. to stop stop getting these messages, do "!compupdates stop". to get notified when competitions are announced in other countries, just use this command again but with the other country you would like to add.')
          logging.info(f"{message} was added")
        else:
          await ctx.channel.send('that is not a country. check your spelling or do "!compupdates help" to learn how to use.')


#this task loop checks for new competitions every 15 minutes.
@tasks.loop(seconds=900)
async def task_loop():
  r=requests.get("https://www.worldcubeassociation.org/competitions?utf8=%E2%9C%93&event_ids%5B%5D=clock&region=all&search=&year=all+years&state=by_announcement&from_date=&to_date=&delegate=&display=list")
  comps=r.text.split('<a href="/competitions/')
  for i in range(len(comps)):
    comps[i]=comps[i].split('">')[1].split('</a>')[0]
  comps.pop(0)
  comps.pop(0)
  with open("/home/josh/clockbot/newcomps.txt","r") as x: known_comps = x.readlines()
  for i in comps:
    if i+"\n" not in known_comps:
      with open("/home/josh/clockbot/newcomps.txt","a") as x: x.write(i+"\n")
      logging.info("competition just found: "+i)
      location = r.text.split(i)[1].split('<div class="location">\n          <strong>')[1].split("</strong")[0]
      r2=requests.get(f"""https://www.worldcubeassociation.org/competitions/{r.text.split(i)[0].split("/competitions/")[-1].split('">')[0]}#competition-events""")
      rounds="? rounds"
      if "clock-r4" in r2.text:
        rounds="4 rounds"
      elif "clock-r3" in r2.text:
        rounds="3 rounds"
      elif "clock-r2" in r2.text:
        rounds="2 rounds"
      elif "clock-r1" in r2.text:
        rounds="1 round"
      with open("/home/josh/clockbot/channels.txt","r") as x: clines=x.readlines()
      for channel_info in clines:
        if ('all' in channel_info.strip("\n").split(",")) or (location.lower() in channel_info.strip("\n").split(",")):
          try:
            channel=client.get_channel(int(channel_info.split(",")[0]))
            await channel.send(f"""{i.replace('&#39;',"'")} was just announced in {location} with {rounds} of clock!""")
          except:
            logging.info(f"failed in {channel_info.split(',')[0]}")#new competition updates have been frequently failing to send in several dms, which is annoying. luckily they have always sent correctly in the clock solvers announcements channel
  logging.info("updated comp list")






#shows list of upcoming competitions
@client.command(aliases=["competitions"])
async def comps(ctx):
  logging.info("!comps")
  with open("/home/josh/clockbot/comps.txt","r") as x: lastupdate=str(x.readline())
  if lastupdate != (str(date.today())+"\n"):
    await ctx.channel.send("updating...")
    logging.info("updating competitions")
    date1 = date.today()
    if date.today().weekday()==0:
      date2 = date1 + timedelta(6)#shows comps 6 days in advance if it is a monday so that sunday comps are shown
    else:
      date2 = date1 + timedelta(5)
    final= str(date.today())+f"\nclock comps from {date1} to {date2}:\n"
    r = requests.get(f"https://www.worldcubeassociation.org/competitions?utf8=%E2%9C%93&event_ids%5B%5D=clock&region=all&search=&year=all+years&state=custom&from_date={date1}&to_date={date2}&delegate=&display=list")

    temp = r.text.split('<a href="/competitions/')

    l=[]
    for i in temp:
      l.append(i.split('">')[0])

    l.pop(0)
    l.pop(0)


    def get_url(url):
      return requests.get(url)

    list_of_urls = [f"https://www.worldcubeassociation.org/competitions/{i}/registrations/psych-sheet/clock" for i in l]

    with ThreadPoolExecutor(max_workers=10) as pool:
        responses = list(pool.map(get_url,list_of_urls))


    for i in responses:
      timetemp=i.text.split('<td class="average">')
      nametemp=i.text.split('<td class="name">')
      times=[]
      names=[]
      temp=i.text.split('''<div id="competition-data">
      <h3>''')[1]
      temp=temp.split("</h3>")[0]
      try:
        temp=temp.split("</span>")[1]
      except:
        pass
      final+=temp.replace("&#39;", "'").replace("\n","").replace("  ","")+"\n"


      for z in range(len(timetemp)):
        times.append(timetemp[z].split('</td')[0])
        names.append(nametemp[z].split('</td')[0].replace("&#39;","'"))
      times.pop(0)
      names.pop(0)
      for n in range(len(times)):
        try:
          if float(times[n])<4:
            final+="        ***"+names[n]+" - "+times[n]+"***\n"
          elif float(times[n])<5:
            final+="        **"+names[n]+" - "+times[n]+"**\n"
          elif float(times[n])<6:
            final+="        *"+names[n]+" - "+times[n]+"*\n"
          elif float(times[n])<7:
            final+="        "+names[n]+" - "+times[n]+"\n"
          else:
            break
        except:
          break
    with open("/home/josh/clockbot/comps.txt", 'w') as x: x.write(final)
  with open("/home/josh/clockbot/comps.txt", 'r') as x: await ctx.channel.send(x.read().split("\n",1)[1])



#!optclock gives the optimal solution in standard wca notation
@client.command()
async def optclock(ctx, *, message: str):
  logging.info("!optclock "+message)
  if message=="help":
    await ctx.channel.send("""do '!optclock' followed by the scramble to use. in the solution, a lowercase pin such as 'dr' means to put up every pin except for that pin. this program uses optclock which was made by Michael Gottlieb""")
  else:
    try:
      await ctx.channel.send("searching for optimal solution...")
      if all(str(ele).isdigit() for ele in message.split(" ")):
        if len(message.split(" "))==14:
          out=check_output(["./clockbot/main"], input=f"{message}\nq\n", encoding="utf-8")
          await ctx.channel.send(out.split("solutions.\n")[1].split('\n')[0]+"\n"+solve(out.split("is optimal:\n")[1].split("\nOptimal solution")[0],"y2"))
        else:
          await ctx.channel.send('error. please check to make sure you entered the scramble correctly. use "!optclock help" to learn how to use.')
      else:
        out=check_output(["./clockbot/main"], input=f"{scramble(message)}\nq\n", encoding="utf-8")
        await ctx.channel.send(out.split("solutions.\n")[1].split('\n')[0]+"\n"+solve(out.split("is optimal:\n")[1].split("\nOptimal solution")[0],message))
    except:
       await ctx.channel.send('error. please check to make sure you entered the scramble correctly. use "!optclock help" to learn how to use.')
       logging.info("bad input")


#!noflip uses the normal notation that optclock typically uses.
@client.command()
async def noflip(ctx, *, message: str):
  logging.info("!noflip "+message)
  if message=="help":
    await ctx.channel.send("""do '!noflip' followed by the scramble to use. For the solution notation, the uppercase part (UUDU) is the state of the 4 pins, in order top-left, top-right, bottom-left, bottom-right. If the lowercase letter is a u, it means to turn a corner that is next to a pin that is up; if the lowercase letter is a d, it means to turn a corner next to a pin that is down. The number tells you the amount to turn. this program uses optclock which was made by Michael Gottlieb""")
  else:
    try:
      await ctx.channel.send("searching for optimal solution...")
      if all(str(ele).isdigit() for ele in message.split(" ")):
        if len(message.split(" "))==14:
          out=check_output(["./clockbot/main"], input=f"{message}\nq\n", encoding="utf-8")
          await ctx.channel.send(out.split("solutions.\n")[1].split('\n')[0]+"\n"+out.split("is optimal:\n")[1].split("\nOptimal solution")[0])
        else:
          await ctx.channel.send('error. please check to make sure you entered the scramble correctly. use "!noflip help" to learn how to use.')
      else:
        out=check_output(["./clockbot/main"], input=f"{scramble(message)}\nq\n", encoding="utf-8")
        await ctx.channel.send(out.split("solutions.\n")[1].split('\n')[0]+"\n"+out.split("is optimal:\n")[1].split("\nOptimal solution")[0])
    except:
       await ctx.channel.send('error. please check to make sure you entered the scramble correctly. use "!noflip help" to learn how to use.')
       logging.info("bad input")

client.run("put discord token here")