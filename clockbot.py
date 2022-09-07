from datetime import date, timedelta
import requests
from discord.ext import commands, tasks
from subprocess import check_output
import logging
from scrambleconvert import scramble, solve
from concurrent.futures import ThreadPoolExecutor
import json

logging.basicConfig(filename="/home/josh/clockbot/clockbot.log",level=logging.INFO,format="%(asctime)s:%(message)s")
logging.getLogger("discord").setLevel(logging.ERROR)


#note: this program currently uses discord.py version 1.7.3
client = commands.Bot(command_prefix = "!")
client.remove_command('help')



@client.event
async def on_ready():
  print("Bot is online!")
  logging.info("bot online")
  task_loop.start()


@client.command()
async def compupdates(ctx):
  await ctx.channel.send("this is no longer a command due to issues sending out messages to all channels when competitions are announced.")


#this task loop checks for new competitions every 15 minutes.
@tasks.loop(seconds=900)
async def task_loop():
  try:
    r=requests.get("https://www.worldcubeassociation.org/competitions?utf8=%E2%9C%93&event_ids%5B%5D=clock&region=all&search=&year=all+years&state=by_announcement&from_date=&to_date=&delegate=&display=list")
    comps=r.text.split('<a href="/competitions/')
    for i in range(len(comps)):
      comps[i]=comps[i].split('">')[1].split('</a>')[0]
    comps.pop(0)
    comps.pop(0)
    with open("/home/josh/clockbot/newcomps.txt","r") as x: known_comps = x.readlines()
    for i in comps:
      if i+"\n" not in known_comps:
        print(i)
        with open("/home/josh/clockbot/newcomps.txt","a") as x: x.write(i+"\n")
        logging.info("competition just found: "+i)
        location = r.text.split(i)[1].split('<div class="location">\n          <strong>')[1].split("</strong")[0]
        if location=="United States":
          location=r.text.split(i)[1].split("United States")[1].split(", ")[2].split("\n")[0]+", United States"
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
        try:
          channel = client.get_channel(1015043542822957106) #clock-comps channel of the clock solvers disord
          await channel.send(f"""{i.replace('&#39;',"'")} was just announced in {location} with {rounds} of clock!""")
        except:
          logging.info("announcement failed")
    logging.info("updated comp list")
  except:
    logging.info("comp list update failed") #this try except is here so that things don't get messed up if the requests fail because the wca site is down





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
