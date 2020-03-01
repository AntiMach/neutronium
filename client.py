import discord
import json
import colorsys
import os
import asyncio
import math
import sys
import shutil
import copy
import traceback
import gc
from datetime import datetime
from random import randint as random
from random import choice as choice
from nums import shorten
from nums import getval
from functools import wraps

class Task:
	def __init__(self, func):
		self.name = func.__name__
		self.func = func
		self.task = None
	def __repr__(self):
		return "Task:{} -> {}".format(self.name, self.task)
	def start(self, loop):
		if self.task is None:
			self.task = asyncio.ensure_future(self.func(), loop=loop)
	def stop(self):
		if self.task is not None:
			self.task.cancel()

class Client(discord.Client):
	def __init__(self, owners=[], host="", main_server="", *, loop=None, **options):
		super().__init__(loop=loop, **options)
		self.tasks = []
		self.main_server = main_server
		self.owners = owners
		self.host = host
		
	async def close(self):
		for t in self.tasks:
			t.stop()
		await super().close()
		
	async def on_ready(self):
		self.main_server = self.get_server(self.main_server)
		self.owners = [(await self.get_user_info(o)) if type(o) is not discord.User else o for o in self.owners]
		self.owners.append((await self.application_info()).owner)
		self.owners = {o.id:o for o in self.owners if o is not None}
		print("\nLogged In!")
		await client.change_presence(game=discord.Game(name="@Neutronium Prefix?", type=0))
	async def on_error(self, event, *args, **kwargs):
		print("\nIgnoring execption on {}:".format(event))
		traceback.print_exc()
		if type(args[0]) is discord.Message:
			try:
				await client.send_message(args[0].channel, embed=initembed("Exception", "An exception has occured, please report the bug to <@300070444621627402>, explaining what you did to cause this.\nDetails: `{0.__name__}: {1}`".format(sys.exc_info()[0], sys.exc_info()[1])))
			except:
				pass
	
	def add_loop(self, delay=1):
		def decorator(func):
			@wraps(func)
			async def wrapper():
				print("Loop:{} | Waiting for bot to start".format(func.__name__))
				await self.wait_until_ready()
				print("Loop:{} | Loop ready!".format(func.__name__))
				while True:
					await asyncio.sleep(delay)
					try:
						await func()
					except Exception:
						await self.on_error("Loop:{}".format(func.__name__))
			t = Task(wrapper)
			self.tasks.append(t)
			t.start(loop=self.loop)
		return decorator

client = Client(owners=["236979113586458625"], host="398388189116497930")

def token():
	file = open("userclient.tkn", "r")
	tkn = file.read()
	file.close()
	return tkn

def setup():
	global cmds, data, rank, itemrank, idb, events, const

	async def startgrab(channel):
		try:
			if data["event"]["ongoing"] == "grab":
				await client.send_message(channel, embed=initembed("Quick!", "Type `{0}grab` to have a chance of getting a great prize!".format(data["servers"][channel.server.id]["prefix"])))
			elif data["event"]["ongoing"] == "supergrab":
				await client.send_message(channel, embed=initembed("Quicker!", "Type `{0}grab {1}` to have a chance of getting a great prize!".format(data["servers"][channel.server.id]["prefix"], data["event"]["data"]["code"])))
		except:
			pass
	def setcode():
		s = ""
		for n in range(5):
			s += str(random(0,9))
		data["event"]["data"]["code"] = s
		data["event"]["data"]["joined"] = []

	async def endgrab(channel, final):
		embed = None
		if data["event"]["ongoing"] == "grab":
			embed = initembed("Grab winners", "Here are the winners of the event!")
			for wininfo in final:
				try:
					user = getanyuser(wininfo[0]).name
				except:
					user = "Unknown"
				embed.add_field(name="{0}!".format(user), value="With a prize of **{1}{0[disc]}**!".format(const, shorten(wininfo[1], signs=["Qd"], base=15)), inline=False)
		elif data["event"]["ongoing"] == "supergrab":
			embed = initembed("Super grab winner", "Here are the winners of the event!")
			for wininfo in final:
				try:
					user = getanyuser(wininfo[0]).name
				except:
					user = "Unknown"
				embed.add_field(name="{0}!".format(user), value="With a great prize of **{1}{0[disc]}**!".format(const, shorten(wininfo[1], signs=["Qd"], base=15)), inline=False)

		if final == []:
			embed.add_field(name="No one?", value="No one tried to grab the Discs...")

		try:
			await client.send_message(channel, embed=embed)
		except:
			pass
	def giftwinner():
		ret = []

		data["event"]["data"]["joined"] = remdupes(data["event"]["data"]["joined"])

		if (data["event"]["ongoing"] == "grab"):
			winners = 5
			if len(data["event"]["data"]["joined"]) < 5:
				winners = len(data["event"]["data"]["joined"])
			for userid in [data["event"]["data"]["joined"][n] for n in range(winners)]:
				data["global"][userid]["discs"] += int(nextrank(userid) / 10)
				ret.append([userid, nextrank(userid) / 10])
		elif (data["event"]["ongoing"] == "supergrab"):
			winners = 5
			if len(data["event"]["data"]["joined"]) < 5:
				winners = len(data["event"]["data"]["joined"])
			for userid in [data["event"]["data"]["joined"][n] for n in range(winners)]:
				data["global"][userid]["discs"] += int(nextrank(userid) / 4)
				ret.append([userid, nextrank(userid) / 4])

		return ret

	##Bot Admin and Bot Owner commands | definitions
	async def init(_msg, _args):
		user = await getuser(_msg, parsearg(_args, 0), indata=False)

		try:
			data["global"][user.id] = copy.deepcopy(data["default"])
			await client.send_message(_msg.channel, embed=initembed("Initialize", "Initialized **{0}**'s data".format(user.name)))
		except:
			pass
	async def sgiveaway(_msg, _args):
		item = parsearg(_args, 0)

		if data["giveaway"]["item"] is None:
			if item not in idb:
				return
			data["giveaway"]["item"] = item
			data["giveaway"]["time"] = int(datetime.now().replace(day=datetime.now().day + 1, minute=0, second=0, microsecond=0).timestamp())
			data["giveaway"]["joined"] = []

			for server in data["servers"]:
				for channel in data["servers"][server]["eventchannels"]:
					if notifytype(server, channel, ["giveaway"]):
						try:
							await client.send_message(client.get_channel(channel), embed=initembed("Giveaway started! :tada:", "Type `{0}giveaway` to get more information about it!".format(data["servers"][server]["prefix"])))
						except:
							pass
		else:
			data["giveaway"]["time"] = 0
	async def forceevent(_msg, _args):
		data["event"]["timer"] = 0
	async def additem(_msg, _args):
		item = parsearg(_args, 0)
		try:
			amount = int(parsearg(_args, 1))
		except:
			return

		if item in idb:
			data["shop"][item] = amount
			idb[item]["repeat"] = False
			await client.send_message(_msg.channel, embed=initembed("Add Item", "Added {0} to the {1} Shop".format(item, "Nuclear" if idb[item]["nuclear"] else "Normal")))
	async def itemdb(_msg, _args):
		action = parsearg(_args, 0)

		if action == "add":
			item = parsearg(_args, 1)
			try:
				price = getval(parsearg(_args, 2), signs=["Qd"], base=15)
			except:
				return
			boost = int(parsearg(_args, 3))
			nuclear = True if parsearg(_args, 4).lower() == "true" else False
			exclusive = parsearg(_args, 5)
			description = parseargs(_args, 6)
			rank = int(math.ceil(boost / 5))
			if rank < 1:
				rank = 1
			if rank > 4:
				rank = 4

			idb[item] = {
				"price": price,
				"boost": boost,
				"rank": itemrank[rank - 1],
				"description": description if description != "" else None,
				"exclusive": _msg.server.id if exclusive.lower() == "true" else None,
				"nuclear": nuclear,
				"repeat": True
			}
			await client.send_message(_msg.channel, embed=initembed("Item added", "Added {0} to the Item Database".format(item)))
		if action == "giveaway":
			item = parsearg(_args, 1)
			description = parseargs(_args, 2)

			idb[item] = {
				"price": 0,
				"boost": random(16, 20),
				"rank": itemrank[-1],
				"description": description if description != "" else None,
				"exclusive": None,
				"nuclear": False,
				"repeat": False
			}
			await client.send_message(_msg.channel, embed=initembed("Item added", "Added {0} to the Item Database".format(item)))
		if action == "simple":
			item = parsearg(_args, 1)
			try:
				price = getval(parsearg(_args, 2), signs=["Qd"], base=15)
			except:
				return
			nuclear = True if parsearg(_args, 3).lower() == "true" else False
			exclusive = _msg.server.id if parsearg(_args, 4).lower() == "true" else None
			description = parseargs(_args, 5)

			if nuclear:
				boost = random(6,10) if price <= 10 else random(11,15)
			else:
				boost = 1
				if price >= 1000000:
					boost = 2
				if price >= 1000000000:
					boost = 3
				if price >= 1000000000000:
					boost = random(4,5)

			rank = int(math.ceil(boost / 5))
			if rank < 1:
				rank = 1
			if rank > 4:
				rank = 4

			idb[item] = {
				"price": price,
				"boost": boost,
				"rank": itemrank[rank - 1],
				"description": description if description != "" else None,
				"exclusive": exclusive,
				"nuclear": nuclear,
				"repeat": True
			}
			await client.send_message(_msg.channel, embed=initembed("Item added", "Added {0} to the Item Database".format(item)))
		elif action == "remove":
			item = parsearg(_args, 1)
			del idb[item]
			await client.send_message(_msg.channel, embed=initembed("Item removed", "Removed {0} from the Item Database".format(item)))
	async def remitem(_msg, _args):
		item = parsearg(_args, 0)

		if item in data["shop"]:
			del data["shop"][item]
			await client.send_message(_msg.channel, embed=initembed("Remove Item", "Removed {0} from the {1} Shop".format(item, "Nuclear" if idb[item]["nuclear"] else "Normal")))
	async def shuffleshop(_msg, _args):
		data["shop"] = {}
		for values in [[1, 1, False, 5, 500, True], [2, 2, False, 5, 250, True], [3, 3, False, 4, 100, True], [4, 5, False, 1, 50, False], [6, 10, True, 4, 25, False], [11, 15, True, 1, 10, False]]:
			items = [item for item in idb if ((idb[item]["boost"] >= values[0]) and (idb[item]["boost"] <= values[1]) and (idb[item]["nuclear"] == values[2]) and (values[5] or idb[item]["repeat"]))]
			num = values[3]
			if num > len(items):
				num = len(items)
			for n in range(num):
				toadd = choice(items)
				items.remove(toadd)
				idb[toadd]["repeat"] = False
				data["shop"][toadd] = values[4]

		for server in data["servers"]:
			for channel in data["servers"][server]["eventchannels"]:
				if notifytype(server, channel, ["shop"]):
					try:
						await client.send_message(client.get_channel(channel), embed=initembed("Shop update", "All items in the shop have been shuffled!\n\nDo `{0}shop` to check the new items.".format(data["servers"][server]["prefix"])))
					except:
						pass
	async def setperm(_msg, _args):
		user = await getuser(_msg, parsearg(_args, 1))
		try:
			level = int(parsearg(_args, 0))
		except:
			return

		if (level < getpermlevel(_msg.author.id)) and (level <= 2):
			data["global"][user.id]["permlevel"] = level
		else:
			await client.send_message(_msg.channel, embed=userembed("", "You don't have enough power to increase permission levels for that user", _msg.author))
			return

		await client.send_message(_msg.channel, embed=userembed("", "You're now a{0} {1}".format("n" if (const["permlevels"][level][0].lower() in "aeiou") else "", const["permlevels"][level]), user))
	async def senddm(_msg, _args):
		user = await getuser(_msg, parsearg(_args, 0))

		msg = parseargs(_args, 1)

		try:
			await client.send_message(user, embed=initembed(None, msg))
			await client.send_message(_msg.channel, embed=initembed("Send DM", "DM sent to **{0}**".format(user.name)))
		except:
			await client.send_message(_msg.channel, embed=initembed("Send DM", "Could not DM **{0}**".format(user.name)))
	async def messageall(_msg, _args):
		message = parseargs(_args, 0)
		for server in data["servers"]:
			for channel in data["servers"][server]["eventchannels"]:
				if notifytype(server, channel, ["message"]):
					if client.get_channel(channel) is not None:
						try:
							await client.send_message(client.get_channel(channel), embed=initembed("Message", message))
						except:
							pass
	async def permitcommand(_msg, _args):
		command = parsearg(_args, 0).lower()
		user = await getuser(_msg, parsearg(_args, 1))

		allcmds = []
		cmdtype = None
		for type in cmds:
			if command in [cmd for cmd in cmds[type]["cmd"]]:
				cmdtype = type

		if command in data["global"][user.id]["permitedcmds"]:
			await client.send_message(_msg.channel, embed=initembed("Command access permited", "**{0}** is already able to use the **{1}{2}** command".format(user.name, data["servers"][_msg.server.id]["prefix"], command)))
			return

		if cmdtype is not None:
			await client.send_message(_msg.channel, embed=initembed("Command access permited", "**{0}** can now use the **{1}{2}** command".format(user.name, data["servers"][_msg.server.id]["prefix"], command)))
			data["global"][user.id]["permitedcmds"][command] = cmdtype
		else:
			await client.send_message(_msg.channel, embed=initembed("Invalid command", "That command doesn't exist"))
	async def unpermitcommand(_msg, _args):
		command = parsearg(_args, 0).lower()
		user = await getuser(_msg, parsearg(_args, 1))

		if command in data["global"][user.id]["permitedcmds"]:
			await client.send_message(_msg.channel, embed=initembed("Command access unpermited", "**{0}** is no longer able to use the **{1}{2}** command".format(user.name, data["servers"][_msg.server.id]["prefix"], command)))
			del data["global"][user.id]["permitedcmds"][command]
			return
		else:
			await client.send_message(_msg.channel, embed=initembed("Invalid command", "That command has not been permited or doesn't exist"))
	async def viewcommands(_msg, _args):
		user = await getuser(_msg, parsearg(_args, 0))

		lst = ""
		for command in data["global"][user.id]["permitedcmds"]:
			lst += "`{0}{1}` ".format(data["servers"][_msg.server.id]["prefix"], command)

		await client.send_message(_msg.channel, embed=userembed("permited commands", lst, user))
	async def setmaxboost(_msg, _args):
		try:
			amount = int(parsearg(_args, 0))
		except:
			return
		user = await getuser(_msg, parsearg(_args, 1))

		data["global"][user.id]["maxboost"] = amount
		await client.send_message(_msg.channel, embed=initembed("Set max boost", "Changed **{1}**'s max boost to **{2:,}%**".format(const, user.name, amount)))
	
	# Special commands
	async def reboot(_msg, _args):
		savedata("data")
		savedata("idb")
		await client.close()
	async def fix(_msg, _args):
		await client.send_message(_msg.channel, embed=initembed("Data", "Nothing happened..."))
	async def _raise(_msg, _args):
		msg = parseargs(_args, 0)
		raise Exception(msg)

	##Bot Moderator commands | definitions
	async def setdiscs(_msg, _args):
		try:
			amount = getval(parsearg(_args, 0), signs=["Qd"], base=15)
		except:
			return
		user = await getuser(_msg, parsearg(_args, 1))

		if math.fabs(amount) > 10**45:
			await client.send_message(_msg.channel, embed=initembed("Too large", "Please don't use large numbers, that's just annoying to deal with .-."))
			return

		data["global"][user.id]["discs"] = amount
		await client.send_message(_msg.channel, embed=initembed("Set discs", "Changed **{1}**'s discs to **{2:,}{0[disc]}**".format(const, user.name, amount)))
	async def setbonus(_msg, _args):
		try:
			amount = getval(parsearg(_args, 0), signs=["Qd"], base=15)
		except:
			return
		user = await getuser(_msg, parsearg(_args, 1))

		if amount > 5000:
			amount = 5000
		if amount < -5000:
			amount = -5000

		data["global"][user.id]["bonus"] = amount
		data["global"][user.id]["tokentimer"] = (amount - 1) % 500
		await client.send_message(_msg.channel, embed=initembed("Set discs", "Changed **{0}**'s bonus to **{1}x**".format(user.name, amount)))
	async def setrank(_msg, _args):
		majorrank = parsearg(_args, 0).lower()
		try:
			minorrank = int(parsearg(_args, 1))
		except:
			minorrank = 0
		user = await getuser(_msg, parsearg(_args, 2))

		if majorrank not in [item.lower() for item in rank["name"]]:
			return

		majorindex = [item.lower() for item in rank["name"]].index(majorrank)

		if minorrank > 5:
			minorrank = 5
		if minorrank < 0:
			minorrank = 0

		if (majorindex + 1) > rank["number"]:
			if (rank["id"][majorindex - rank["number"]] is not None) and (rank["id"][majorindex - rank["number"]] != user.id):
				try:
					username = await getuser(_msg, rank["id"][majorindex - 10]).name
				except:
					username = None
				await client.send_message(_msg.channel, embed=initembed("Exclusive Rank", "That rank is exclusive to {0}".format("**{0}**.".format(username) if username is not None else "a specific user.")))
				return

		data["global"][user.id]["majorrank"] = majorindex + 1
		data["global"][user.id]["minorrank"] = minorrank
		await client.send_message(_msg.channel, embed=initembed("Set rank", "Changed **{0}**'s rank to **{1} {2}**".format(user.name, rank["name"][majorindex], int(minorrank))))
	async def settokens(_msg, _args):
		try:
			amount = getval(parsearg(_args, 0), signs=["Qd"], base=15)
		except:
			return
		user = await getuser(_msg, parsearg(_args, 1))

		if math.fabs(amount) > 10**30:
			await client.send_message(_msg.channel, embed=initembed("Too large", "Please don't use large numbers, that's just annoying to deal with .-."))
			return

		data["global"][user.id]["tokens"] = amount
		await client.send_message(_msg.channel, embed=initembed("Set tokens", "Changed **{1}**'s tokens to **{2:,}{0[token]}**".format(const, user.name, amount)))
	async def setnuclear(_msg, _args):
		try:
			amount = int(parsearg(_args, 0))
		except:
			return
		user = await getuser(_msg, parsearg(_args, 1))

		if amount > 10**6:
			amount = 10**6
		if amount < 0:
			amount = 0

		data["global"][user.id]["nuclearrank"] = amount
		await client.send_message(_msg.channel, embed=initembed("Set discs", "Changed **{0}**'s nuclear rank to **Nuclear +{1}**".format(user.name, amount)))
	async def giveitem(_msg, _args):
		item = parsearg(_args, 0)
		user = await getuser(_msg, parsearg(_args, 1))

		list = item.split(";")
		while "" in list:
			list.remove("")

		for i in list:
			data["global"][user.id]["items"].append(i)

		if len(list) > 0:
			await client.send_message(_msg.channel, embed=initembed("Give Item", "Gave {0} to **{1}**".format(", ".join(list), user.name)))
	async def takeitem(_msg, _args):
		item = parsearg(_args, 0)
		user = await getuser(_msg, parsearg(_args, 1))

		list = item.split(";")
		removed = []

		for i in list:
			try:
				data["global"][user.id]["items"].remove(i)
				removed.append(i)
			except:
				pass
		if len(removed) > 0:
			await client.send_message(_msg.channel, embed=initembed("Take Item", "Took {0} from **{1}**".format(", ".join(removed), user.name)))

	##Server Administrator commands | definitions
	async def prefix(_msg, _args):
		prefix = parsearg(_args, 0)

		await client.send_message(_msg.channel, embed=initembed("Command prefix", "The command prefix for the server is now `{0}`".format(prefix)))
		data["servers"][_msg.server.id]["prefix"] = prefix
	async def purge(_msg, _args):
		if not _msg.channel.permissions_for(_msg.server.me).manage_messages:
			await client.send_message(_msg.channel, embed=initembed("Missing Permission", "I'm missing the `Manage Messages` permission"))
			return

		try:
			messages = int(parsearg(_args, 0))
		except:
			return

		usertag = parsearg(_args, 1)
		user = None
		if not ((usertag is None) or (usertag == "")):
			user = getanyuser(usertag)

		if (messages < 1) or (messages > 100):
			await client.send_message(_msg.channel, embed=initembed("Invalid value", "You must chose a value between **1** and **100**"))
			return

		deleted = await client.purge_from(_msg.channel, limit=messages, check=lambda m: (m.timestamp.timestamp() > (_msg.timestamp.timestamp() - 1209600)) and (True if user is None else (m.author.id == user.id)))
		temp = await client.send_message(_msg.channel, embed=initembed("Purge", "Successfully deleted **{0}** message{1}!".format(len(deleted), "s" if len(deleted) > 1 else "")))
		await asyncio.sleep(2)
		await client.delete_message(temp)
	async def notify(_msg, _args):
		nonsleep = True if ((parsearg(_args, 0).lower() == "true") or (parsearg(_args, 0).lower() is None)) else False

		args = [x.lower() for x in parseargs(_args, 1).split(" ") if x.lower() in ["shop", "giveaway", "event", "message"]]
		if args == []:
			args = ["shop", "giveaway", "event", "message"]

		types = ""
		for arg in args:
			types += "`{0}` ".format(arg.capitalize())

		if _msg.channel.id not in data["servers"][_msg.server.id]["eventchannels"]:
			data["servers"][_msg.server.id]["eventchannels"][_msg.channel.id] = [0, args, nonsleep]
			await client.send_message(_msg.channel, embed=initembed("Notifications", "Notifications have been enabled for this channel!\nTypes enabled: {0}\n{1}".format(types, "Will stop sending notifications after 5 minutes of inactivity." if not nonsleep else "Will constantly send notifications.")))
		else:
			del data["servers"][_msg.server.id]["eventchannels"][_msg.channel.id]
			await client.send_message(_msg.channel, embed=initembed("Notifications", "Notifications have been disabled for this channel!"))

	##Miscellaneous commands | definitions
	async def create(_msg, _args):
		name = parsearg(_args, 0).lower().replace("\n", "")
		while name.startswith(data["servers"][_msg.server.id]["prefix"]):
			name = name[len(data["servers"][_msg.server.id]["prefix"]):]
		output = parseargs(_args, 1)
		if (len(output) > 300) or (output.count("\n") > 10):
			await client.send_message(_msg.channel, embed=initembed("Too long!", "The command output cannot be longer than **300 characters**, and may not have more than **10 lines**"))
			return

		blacklist = []
		for type in cmds:
			for command in cmds[type]["cmd"]:
				blacklist.append(command)
				for c in cmds[type]["cmd"][command][2]:
					blacklist.append(c)

		if (name == "") or (name in blacklist):
			await client.send_message(_msg.channel, embed=initembed("Blacklisted", "The command name you gave is blacklisted and cannot be used"))
			return

		await client.send_message(_msg.channel, embed=initembed("Personal command", "`{0}{1}` was successfully {2}!".format(data["servers"][_msg.server.id]["prefix"], name, "redefined" if name in data["servers"][_msg.server.id]["users"][_msg.author.id]["commands"] else "created")))
		data["servers"][_msg.server.id]["users"][_msg.author.id]["commands"][name] = output
	async def delete(_msg, _args):
		name = parsearg(_args, 0).lower().replace("\n", "")
		while name.startswith(data["servers"][_msg.server.id]["prefix"]):
			name = name[len(data["servers"][_msg.server.id]["prefix"]):]

		if (name in data["servers"][_msg.server.id]["users"][_msg.author.id]["commands"]):
			await client.send_message(_msg.channel, embed=initembed("Personal command", "`{0}{1}` was successfully deleted!".format(data["servers"][_msg.server.id]["prefix"], name)))
			del data["servers"][_msg.server.id]["users"][_msg.author.id]["commands"][name]
		else:
			await client.send_message(_msg.channel, embed=initembed("Invalid name", "The command name you gave is not valid"))
	async def help(_msg, _args):
		command = parsearg(_args, 0)
		available = {"cmds": {}}
		for type in cmds:
			if (cmds[type]["check"](_msg.author)) and (not cmds[type]["hidden"]):
				for cmd in cmds[type]["cmd"]:
					available["cmds"][cmd] = type

		for cmd in data["global"][_msg.author.id]["permitedcmds"]:
			type = data["global"][_msg.author.id]["permitedcmds"][cmd]
			if (cmd not in available["cmds"]):
				available["cmds"][cmd] = type

		embed = None
		if command in available["cmds"]:
			type = available["cmds"][command]
			embed = initembed("{0}{1} {2}".format(data["servers"][_msg.server.id]["prefix"], command, cmds[type]["cmd"][command][0]), cmds[type]["cmd"][command][1])
			aliases = ""
			for a in cmds[type]["cmd"][command][2]:
				aliases += "`{0}{1}` ".format(data["servers"][_msg.server.id]["prefix"], a)
			if aliases != "":
				embed.add_field(name="Aliases", value=aliases)
		else:
			organised = {}
			for command in available["cmds"]:
				if available["cmds"][command] not in organised:
					organised[available["cmds"][command]] = []
				organised[available["cmds"][command]].append(command)
			embed = initembed("Help", "Here is a list with all of the available commands. For more information about a specific command, do `{0}help [command]`.".format(data["servers"][_msg.server.id]["prefix"]))

			for type in organised:
				commands = ""
				for c in organised[type]:
					commands += "`{0}{1}` ".format(data["servers"][_msg.server.id]["prefix"], c)
				embed.add_field(name="{0} commands".format(cmds[type]["name"]), value=commands, inline=False)

			commands = ""
			for c in data["servers"][_msg.server.id]["users"][_msg.author.id]["commands"]:
				commands += "`{0}{1}` ".format(data["servers"][_msg.server.id]["prefix"], c)
			if commands != "":
				embed.add_field(name="Personal commands", value=commands, inline=False)

		await client.send_message(_msg.channel, embed=embed)
	async def invite(_msg, _args):
		link = "https://discordapp.com/oauth2/authorize?client_id=344155702987849748&permissions=27712&scope=bot"
		await client.send_message(_msg.channel, embed=initembed("Links", "**Neutronium's invite link :cd:** [**Bot Invite**]({0})\n\n**The Nuclear Shelter <:nucleartoken:411176834386886656>** [**Main Server**](https://discord.gg/4AGE5BC)\n**The Googleplex <:theShrine:342759959055826945>** [**Partner Server**](http://discord.gg/8jA7bvR)".format(link)))
	async def stats(_msg, _args):
		await client.send_message(_msg.channel, embed=initembed("Stats", "**Servers I'm on: {0:,}\nUsers who play: {1:,}**".format(len(client.servers), len(data["global"]))))

	##Currency commands | definitions
	async def info(_msg, _args):
		user = await getuser(_msg, parsearg(_args, 0))
		
		await check(user, data["global"][user.id])

		embed = userembed("information", None, user)

		embed.add_field(name="Discs", value="**{1}{0[disc]}**".format(const, shorten(data["global"][user.id]["discs"], signs=["Qd"], base=15)))
		embed.add_field(name="Nuclear Tokens", value="**{1}{0[token]}**".format(const, shorten(data["global"][user.id]["tokens"], signs=["Qd"], base=15)))
		embed.add_field(name="Bonus", value="**{0}x**".format(data["global"][user.id]["bonus"]))
		embed.add_field(name="Items", value="**{0} Item{1}**".format(len(data["global"][user.id]["items"]), "s" if len(data["global"][user.id]["items"]) != 1 else ""))
		embed.add_field(name="Gift Limit (Towards you)", value="**{1}{0[disc]}**".format(const, shorten(nextrank(user.id) * 2, signs=["Qd"], base=15)))
		if data["global"][user.id]["discs"] >= tokenprice(user.id):
			tokens = math.floor(data["global"][user.id]["discs"] / tokenprice(user.id))
			if tokens > 10:
				tokens = 10
			embed.add_field(name="Ascend", value="Ascend for **{1}{0[token]}**\n*1 token costs **{3}{0[disc]}***".format(const, tokens, shorten(tokenprice(user.id), signs=["Qd"], base=15)))

		await client.send_message(_msg.channel, embed=embed)
	async def cur(_msg, _args):
		user = await getuser(_msg, parsearg(_args, 0))
		
		await check(user, data["global"][user.id])
		
		embed = userembed("discs", "**{1:,}{0[disc]}**".format(const, data["global"][user.id]["discs"]), user)
		await client.send_message(_msg.channel, embed=embed)
	async def nuclear(_msg, _args):
		user = await getuser(_msg, parsearg(_args, 0))
		
		await check(user, data["global"][user.id])
		
		embed = userembed("nuclear tokens", "**{1:,}{0[token]}**".format(const, data["global"][user.id]["tokens"]), user)
		await client.send_message(_msg.channel, embed=embed)
	async def bonus(_msg, _args):
		user = await getuser(_msg, parsearg(_args, 0))
		
		await check(user, data["global"][user.id])
		
		embed = userembed("bonus", None, user)
		embed.add_field(name="Current (1x/{0}s)".format(bonusfreq(data["global"][user.id])), value="**{0}x**".format(data["global"][user.id]["bonus"]))
		embed.add_field(name="Token prize", value="**{0}x left**".format(500 - data["global"][user.id]["tokentimer"]))
		embed.add_field(name="DPM", value="**{1}{0[disc]}** ~ **{2}{0[disc]}**".format(const, shorten(calcdpm(user.id)[0], signs=["Qd"], base=15), shorten(calcdpm(user.id)[1], signs=["Qd"], base=15)))
		embed.add_field(name="Best", value="**{0}x**".format(data["global"][user.id]["bestbonus"]), inline=False)
		await client.send_message(_msg.channel, embed=embed)
	async def gamble(_msg, _args):
		val = parsearg(_args, 0).replace(",", "")
		if val == "all":
			val = data["global"][_msg.author.id]["discs"]
		try:
			input = getval(val, signs=["Qd"], base=15)
		except:
			return
		if (input > data["global"][_msg.author.id]["discs"]) or (input <= 0):
			return

		rng = random(1,100)
		if rng <= 45:
			await client.send_message(_msg.channel, embed=userembed("", "You won **{1}{0[disc]}**!".format(const, shorten(input, signs=["Qd"], base=15)), _msg.author, secondtitle="Nice!"))
			data["global"][_msg.author.id]["discs"] += input
		if (rng >= 46) and (rng <= 49):
			await client.send_message(_msg.channel, embed=userembed("", "You won **{1}{0[disc]}**!".format(const, shorten(input * 3, signs=["Qd"], base=15)), _msg.author, secondtitle="Whoa!"))
			data["global"][_msg.author.id]["discs"] += input * 3
		if rng == 50:
			await client.send_message(_msg.channel, embed=userembed("", "You won **{1}{0[disc]}**!".format(const, shorten(input * 5, signs=["Qd"], base=15)), _msg.author, secondtitle="Jackpot!"))
			data["global"][_msg.author.id]["discs"] += input * 5
		if rng >= 51:
			await client.send_message(_msg.channel, embed=userembed("", "You lost **{1}{0[disc]}**...".format(const, shorten(input, signs=["Qd"], base=15)), _msg.author, secondtitle="Welp..."))
			data["global"][_msg.author.id]["discs"] -= input
	async def rankup(_msg, _args):
		next = nextrank(_msg.author.id)

		if data["global"][_msg.author.id]["dialog"] > datetime.now().timestamp():
			return

		try:
			nextnuclear = rank["nuclear"][data["global"][_msg.author.id]["majorrank"]]
		except:
			nextnuclear = 0

		if (data["global"][_msg.author.id]["nuclearrank"] < nextnuclear) and (data["global"][_msg.author.id]["minorrank"] >= 5):
			embed = userembed("", "You still have more ranks to get! However, you need rank **Nuclear +{0}** to unlock the next one.\n\nYou can get **Nuclear** ranks by **Ascending**. (type `{1}ascend` to see more information about it)".format(nextnuclear, data["servers"][_msg.server.id]["prefix"]), _msg.author, secondtitle="Locked!")
			await client.send_message(_msg.channel, embed=embed)
			return

		if (data["global"][_msg.author.id]["majorrank"] > rank["number"]) or ((data["global"][_msg.author.id]["majorrank"] == rank["number"]) and (data["global"][_msg.author.id]["minorrank"] >= 5)):
			embed = userembed("", "You have reached the last rank!", _msg.author)
			embed.title = "Congratulations!"
			await client.send_message(_msg.channel, embed=embed)
			return

		if data["global"][_msg.author.id]["discs"] >= next:
			botmsg = await client.send_message(_msg.channel, embed=userembed("", "You have enough discs to rankup! **({1}{0[disc]})**\nWould you like to do it?\n\n*(React with **[Y]es** or **[N]o**)*".format(const, shorten(next, signs=["Qd"], base=15)), _msg.author))

			data["global"][_msg.author.id]["dialog"] = datetime.now().timestamp() + 60
			result = await getreaction(botmsg, _msg.author, ["🇾", "🇳"])
			data["global"][_msg.author.id]["dialog"] = datetime.now().timestamp()

			try:
				await client.delete_message(botmsg)
			except:
				pass

			if (data["global"][_msg.author.id]["discs"] < nextrank(_msg.author.id)):
				await client.send_message(_msg.channel, embed=userembed("", "You don't have enough discs to rankup...\n\n***{1}{0[disc]}** left to rankup*".format(const, shorten(nextrank(_msg.author.id) - data["global"][_msg.author.id]["discs"], signs=["Qd"], base=15)), _msg.author))
				return

			if result == "🇳":
				await client.send_message(_msg.channel, embed=userembed("", "Your request to rankup has been canceled", _msg.author))
				return
			elif result == "🇾":
				data["global"][_msg.author.id]["minorrank"] += 1
				if data["global"][_msg.author.id]["minorrank"] > 5:
					data["global"][_msg.author.id]["minorrank"] = 1
					data["global"][_msg.author.id]["majorrank"] += 1
				data["global"][_msg.author.id]["discs"] -= next
				await client.send_message(_msg.channel, embed=userembed("", "You just ranked up to **{0} {1}**!".format(rank["name"][data["global"][_msg.author.id]["majorrank"] - 1], data["global"][_msg.author.id]["minorrank"]), _msg.author, secondtitle="Congratulations!"))
				return
		else:
			await client.send_message(_msg.channel, embed=userembed("", "You don't have enough discs to rankup...\n\n***{1}{0[disc]}** left to rankup*".format(const, shorten(next - data["global"][_msg.author.id]["discs"], signs=["Qd"], base=15)), _msg.author))
			return
	async def item(_msg, _args):
		item = parsearg(_args, 0)

		if item in idb:
			embed = initembed(item, "**{0}**".format(idb[item]["description"]) if idb[item]["description"] is not None else "")
			embed.add_field(name="Rank", value="**{0}**".format(idb[item]["rank"]))
			embed.add_field(name="Boost", value="**+{0}% DPM**".format(idb[item]["boost"]))
			embed.add_field(name="Price", value="**{0}{1}**".format(shorten(idb[item]["price"], signs=["Qd"], base=15), const["token"] if idb[item]["nuclear"] else const["disc"]))
			embed.add_field(name="Available?", value="**Yes**" if item in data["shop"] else "**No**")
			if idb[item]["exclusive"] is not None:
				embed.add_field(name="Exclusive Server", value="**{0}**".format(client.get_server(idb[item]["exclusive"]).name))
			await client.send_message(_msg.channel, embed=embed)
		else:
			await client.send_message(_msg.channel, embed=initembed("Invalid Item", "That's not a valid item..."))
	async def shop(_msg, _args):
		shop = parsearg(_args, 0)
		nuclear = False
		if shop in ["nuclear", "n"]:
			nuclear = True
		embed = initembed("Shop", "Welcome to the **{0} Shop**, a place where you can buy items for {1}! Do `{2}buy [item]` to buy an item or `{2}sell [item]` to sell one. If you want to know more about a certain item, you can do `{2}item [item]`".format("Nuclear" if nuclear else "Normal", "nuclear tokens" if nuclear else "discs", data["servers"][_msg.server.id]["prefix"]))
		ordered = []

		for item in [item for item in data["shop"]]:
			if item not in idb:
				try:
					del data["shop"][item]
				except:
					pass

		if nuclear:
			ordered = sorted([item for item in data["shop"] if (idb[item]["nuclear"])], key=lambda x: idb[x]["price"])
		else:
			ordered = sorted([item for item in data["shop"] if (not idb[item]["nuclear"])], key=lambda x: idb[x]["price"])

		for item in ordered:
			embed.add_field(name="**{0} | {1} Item**".format(item, idb[item]["rank"]), value="**+{0}% DPM\n{1}{2}\n{3:,} Left{4}**".format(idb[item]["boost"], shorten(idb[item]["price"], signs=["Qd"], base=15), const["token"] if nuclear else const["disc"], data["shop"][item], "\n{0} Exclusive!".format(client.get_server(idb[item]["exclusive"])) if idb[item]["exclusive"] is not None else ""))

		await client.send_message(_msg.channel, embed=embed)
	async def buy(_msg, _args):
		item = parsearg(_args, 0)

		if (item in data["shop"]) and (item in idb):
			if idb[item]["exclusive"] is not None:
				if _msg.server.id != idb[item]["exclusive"]:
					server = client.get_server(idb[item]["exclusive"]).name
					await client.send_message(_msg.channel, embed=userembed("", "That item is **exclusive** to the **{0}**".format(server), _msg.author))
					return
			if data["shop"][item] <= 0:
				await client.send_message(_msg.channel, embed=userembed("", "That item is out of stock...", _msg.author))
				return
			if item in data["global"][_msg.author.id]["items"]:
				await client.send_message(_msg.channel, embed=userembed("", "You already have that item...", _msg.author))
				return
			price = idb[item]["price"]
			type = "tokens" if idb[item]["nuclear"] else "discs"
			if data["global"][_msg.author.id][type] >= price:
				data["global"][_msg.author.id][type] -= price
				data["shop"][item] -= 1
				data["global"][_msg.author.id]["items"].append(item)
				await client.send_message(_msg.channel, embed=userembed("", "You bought {0} for **{1}{2}**!".format(item, shorten(idb[item]["price"], signs=["Qd"], base=15), const["token"] if idb[item]["nuclear"] else const["disc"]), _msg.author, secondtitle="Hooray! :tada:"))
				return
			else:
				await client.send_message(_msg.channel, embed=userembed("", "You don't have enough {0} to buy that item...".format(type), _msg.author))
				return
		else:
			await client.send_message(_msg.channel, embed=userembed("", "The item you are looking for is not available or does not exist...", _msg.author))
			return
	async def sell(_msg, _args):
		item = parsearg(_args, 0)

		if data["global"][_msg.author.id]["dialog"] > datetime.now().timestamp():
			return

		if (item in data["global"][_msg.author.id]["items"]):
			if item in idb:
				value = 80 if item in data["shop"] else 50
				price = int(math.floor(idb[item]["price"] * value / 100))
				minrank = checkrank(price)
				if (minrank + 1) > data["global"][_msg.author.id]["majorrank"]:
					await client.send_message(_msg.channel, embed=userembed("", "You need to be at least **{0} 1** to sell that item.".format(rank["name"][minrank]), _msg.author))
					return
				currency = const["token"] if idb[item]["nuclear"] else const["disc"]
				botmsg = await client.send_message(_msg.channel, embed=userembed("", "If you sell that item, you will only get **{0}%** of it's value back **({1}{2})**\nAre you sure you want to sell it?".format(value, shorten(price, signs=["Qd"], base=15), currency), _msg.author))
			else:
				price = 0
				botmsg = await client.send_message(_msg.channel, embed=userembed("", "You won't get anything by selling that item, as it isn't valid.\nDo you still want to sell it?", _msg.author))

			data["global"][_msg.author.id]["dialog"] = datetime.now().timestamp() + 60
			result = await getreaction(botmsg, _msg.author, ["🇾", "🇳"])
			data["global"][_msg.author.id]["dialog"] = datetime.now().timestamp()

			if item in idb:
				minrank = checkrank(price)
				if (minrank + 1) > data["global"][_msg.author.id]["majorrank"]:
					await client.delete_message(botmsg)
					await client.send_message(_msg.channel, embed=userembed("", "You need to be at least **{0} 1** to sell that item.".format(rank["name"][minrank]), _msg.author))
					return

			if result == "🇳":
				await client.delete_message(botmsg)
				await client.send_message(_msg.channel, embed=userembed("", "Your request to sell the item has been canceled.", _msg.author))
				return
			elif result == "🇾":
				await client.delete_message(botmsg)
				if item in idb:
					await client.send_message(_msg.channel, embed=userembed("", "You sold {0} for **{1}{2}**!".format(item, shorten(price, signs=["Qd"], base=15), currency), _msg.author, secondtitle="Done!"))
					data["global"][_msg.author.id]["items"].remove(item)
					data["global"][_msg.author.id]["tokens" if idb[item]["nuclear"] else "discs"] += price
					if item in data["shop"]:
						data["shop"][item] += 1
				else:
					await client.send_message(_msg.channel, embed=userembed("", "You sold {0} for absolutely nothing!".format(item), _msg.author, secondtitle="Done!"))
					data["global"][_msg.author.id]["items"].remove(item)
				return
		else:
			await client.send_message(_msg.channel, embed=userembed("", "You can't sell something you don't have...".format(item), _msg.author))
			return
	async def inventory(_msg, _args):
		user = await getuser(_msg, parsearg(_args, 0))

		embed = userembed("items", "**Item boost: +{0}% DPM | Limit: +{1}% DPM**".format(itemboost(user.id), data["global"][user.id]["maxboost"]), user)
		for rank in itemrank:
			items = sorted([item for item in idb if (idb[item]["rank"] == rank) and (item in data["global"][user.id]["items"])], key=lambda x: idb[x]["price"])
			list = ""
			for item in items:
				list += "{0}{1} ".format(item, "(x{0})".format(data["global"][user.id]["items"].count(item)) if data["global"][user.id]["items"].count(item) > 1 else "")
			if list != "":
				embed.add_field(name="{0} Items".format(rank), value=list)
		list = ""
		for item in sorted(data["global"][user.id]["items"]):
			if (item not in idb):
				list += "{0} ".format(item)
		if list != "":
			embed.add_field(name="Unknown Items".format(rank), value=list)
		await client.send_message(_msg.channel, embed=embed)
	async def itemlist(_msg, _args):
		embed = initembed("Item List", "**{0} Unique items**".format(len(idb)))
		for rank in itemrank:
			items = sorted([item for item in idb if (idb[item]["rank"] == rank)], key=lambda x: idb[x]["price"])
			list = ""
			for item in items:
				list += "{0} ".format(item)
			if list != "":
				embed.add_field(name="{0} Items".format(rank), value=list)

		await client.send_message(_msg.channel, embed=embed)
	async def rank(_msg, _args):
		nuclear = True if ((parsearg(_args, 0) == "n") or (parsearg(_args, 0) == "nuclear")) else False
		user = await getuser(_msg, parsearg(_args, 1))
		
		await check(user, data["global"][user.id])

		sortedusers = sorted([m for m in data["global"] if not (getpermlevel(m) >= 1)], key=lambda x: data["global"][x]["nuclearrank" if nuclear else "discs"], reverse=True)
		if user.id in sortedusers:
			rank = sortedusers.index(user.id) + 1
			await client.send_message(_msg.channel, embed=userembed("global {0} rank".format("nuclear" if nuclear else "disc"), "**You are rank #{0}**".format(rank), user))
	async def leaderboard(_msg, _args):
		nuclear = True if ((parsearg(_args, 0) == "n") or (parsearg(_args, 0) == "nuclear")) else False

		sortedusers = sorted([m for m in data["global"] if not (getpermlevel(m) >= 1)], key=lambda x: data["global"][x]["nuclearrank" if nuclear else "discs"], reverse=True)

		embed = initembed("{0} Leaderboard".format("Nuclear" if nuclear else "Disc"), "Here are the top 10 users with the {0} in the world.".format("highest nuclear ranks" if nuclear else "most discs"))

		numbers = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "keycap_ten"]

		for n in range(10 if len(sortedusers) >= 10 else len(sortedusers)):
			user = await getuser(_msg, sortedusers[n])
			
			await check(user, data["global"][user.id])
			
			embed.add_field(name=":{0}: {1}".format(numbers[n], user.name), value="**{0}**".format("Nuclear +{0}".format(data["global"][sortedusers[n]]["nuclearrank"]) if nuclear else "{1}{0[disc]}".format(const, shorten(data["global"][sortedusers[n]]["discs"]))))

		await client.send_message(_msg.channel, embed=embed)
	async def ascend(_msg, _args):
		if data["global"][_msg.author.id]["dialog"] > datetime.now().timestamp():
			return

		if (data["global"][_msg.author.id]["nuclearrank"] >= 100):
			embed = userembed("", "You have reached the last nuclear rank!", _msg.author)
			embed.title = "Congratulations!"
			await client.send_message(_msg.channel, embed=embed)
			return

		tokens = int(math.floor(data["global"][_msg.author.id]["discs"] / tokenprice(_msg.author.id)))
		if tokens > 10:
			tokens = 10

		if tokens > 0:
			botmsg = await client.send_message(_msg.channel, embed=userembed("", "You can ascend now for **{1}{0[token]}**, however, you will lose **EVERYTHING** (excluding bonus, items, nuclear tokens and nuclear rank).\nAre you sure you want to do it?\n\n*(React with **[Y]es** or **[N]o**)*".format(const, tokens), _msg.author))

			data["global"][_msg.author.id]["dialog"] = datetime.now().timestamp() + 60
			result = await getreaction(botmsg, _msg.author, ["🇾", "🇳"])
			data["global"][_msg.author.id]["dialog"] = datetime.now().timestamp()

			tokens = int(math.floor(data["global"][_msg.author.id]["discs"] / tokenprice(_msg.author.id)))
			if tokens > 10:
				tokens = 10
			if data["global"][_msg.author.id]["discs"] < tokenprice(_msg.author.id):
				await client.delete_message(botmsg)
				await client.send_message(_msg.channel, embed=userembed("", "You don't have enough discs to ascend...\n**{1}{0[disc]}** left to get **1{0[token]}**".format(const, shorten(tokenprice(_msg.author.id) - data["global"][_msg.author.id]["discs"], signs=["Qd"], base=15)), _msg.author))
				return

			if result == "🇳":
				await client.delete_message(botmsg)
				await client.send_message(_msg.channel, embed=userembed("", "Your request to ascend has been canceled", _msg.author))
				return
			elif result == "🇾":
				data["global"][_msg.author.id]["discs"] = 500
				data["global"][_msg.author.id]["majorrank"] = 1
				data["global"][_msg.author.id]["minorrank"] = 1
				data["global"][_msg.author.id]["nuclearrank"] += 1
				data["global"][_msg.author.id]["tokens"] += tokens
				await client.delete_message(botmsg)
				await client.send_message(_msg.channel, embed=userembed("", "You have just ascended, and earned **{1}{0[token]}**".format(const, tokens), _msg.author, secondtitle="Congratulations!"))
				return
		else:
			await client.send_message(_msg.channel, embed=userembed("", "You don't have enough discs to ascend...\n**{1}{0[disc]}** left to get **1{0[token]}**".format(const, shorten(tokenprice(_msg.author.id) - data["global"][_msg.author.id]["discs"], signs=["Qd"], base=15)), _msg.author))
			return
	async def event(_msg, _args):
		specific = parseargs(_args, 0)

		if specific.lower() in [events[e]["name"].lower() for e in events]:
			evt = ""
			for e in events:
				if events[e]["name"].lower() == specific.lower():
					evt = e
			await client.send_message(_msg.channel, embed=initembed("{0} | {1}% Chance of occurring".format(events[evt]["name"], events[evt]["chance"]), events[evt]["description"].format(data["servers"][_msg.server.id]["prefix"])))
			return
		
		time = int(data["event"]["timer"] - datetime.now().timestamp())
		minutes = int(time / 60)
		seconds = time % 60
		m = "{0} minute{1}".format(minutes, "s" if minutes != 1 else "")
		s = "{0} second{1}".format(seconds, "s" if seconds != 1 else "")
		ms = "{0} and {1}".format(m, s) if minutes > 0 else s
		if data["event"]["ongoing"] is not None:
			evt = data["event"]["ongoing"]
			await client.send_message(_msg.channel, embed=initembed("Event", "Ongoing event: **{0}**\nTime left: **{1}**".format(events[evt]["name"], ms)))
		else:
			embed = initembed("Event", "No ongoing event...\nNext event in **{0}**".format(ms))
			evt = ""
			for e in events:
				evt += "**{0}**\n".format(events[e]["name"])
			embed.add_field(name="Available Events", value=evt)
			await client.send_message(_msg.channel, embed=embed)
	async def grab(_msg, _args):
		code = parsearg(_args, 0)
		try:
			if _msg.author.id not in data["event"]["data"]["joined"]:
				if data["event"]["ongoing"] == "grab":
					await client.send_message(_msg.channel, embed=userembed("", "You tried to grab the discs!", _msg.author))
					data["event"]["data"]["joined"].append(_msg.author.id)
				elif data["event"]["ongoing"] == "supergrab":
					embed = None
					if code == data["event"]["data"]["code"]:
						embed = userembed("", "You tried really hard to grab the discs!", _msg.author)
						data["event"]["data"]["joined"].append(_msg.author.id)
					else:
						embed = userembed("", "You failed to grab the discs...", _msg.author)
					await client.send_message(_msg.channel, embed=embed)
		except:
			pass
	async def giveaway(_msg, _args):
		if data["giveaway"]["item"] is not None:
			item = data["giveaway"]["item"]
			if item in idb:
				rank = idb[item]["rank"]
				boost = idb[item]["boost"]
			else:
				rank = "Unknown"
				boost = 0

			time = data["giveaway"]["time"] - datetime.now().timestamp()
			hours = int(time / 3600)
			minutes = int(time / 60) % 60
			seconds = int(time % 60)
			h = "{0} hour{1}".format(hours, "s" if hours != 1 else "")
			m = "{0} minute{1}".format(minutes, "s" if hours != 1 else "")
			s = "{0} second{1}".format(seconds, "s" if hours != 1 else "")
			hms = ("{0}, {1} and {2}".format(h, m, s) if hours > 0 else "{0} and {1}".format(m, s)) if minutes > 0 else "{0}".format(m)

			embed = initembed("Giveaway", "Type `{0}join` to join the giveaway!".format(data["servers"][_msg.server.id]["prefix"]))
			embed.add_field(name="Time left", value="**{0}**".format(hms))
			embed.add_field(name="Users Joined", value="**{0}**".format(len(data["giveaway"]["joined"])), inline=False)
			embed.add_field(name="Item", value="**{0}**".format(item))
			embed.add_field(name="Rank", value="**{0}**".format(rank))
			embed.add_field(name="Boost", value="**+{0}% Boost**".format(boost))
			await client.send_message(_msg.channel, embed=embed)
	async def join(_msg, _args):
		if data["giveaway"]["item"] is None:
			return

		if _msg.author.id in data["giveaway"]["joined"]:
			await client.send_message(_msg.channel, embed=userembed("", "You have already joined the giveaway...", _msg.author))
		elif getpermlevel(_msg.author.id) != 0:
			await client.send_message(_msg.channel, embed=userembed("", "You can't join the giveaway...", _msg.author))
		else:
			if data["giveaway"]["item"] in data["global"][_msg.author.id]["items"]:
				await client.send_message(_msg.channel, embed=userembed("", "You already have that item...", _msg.author))
				return
			await client.send_message(_msg.channel, embed=userembed("", "You joined the giveaway!", _msg.author, secondtitle="Joined! :tada:"))
			data["giveaway"]["joined"].append(_msg.author.id)
	async def gift(_msg, _args):
		val = parsearg(_args, 0).lower()
		user = await getuser(_msg, parsearg(_args, 1))

		if (val == "max"):
			amount = data["global"][_msg.author.id]["discs"]
			if amount > nextrank(user.id) * 2:
				amount = nextrank(user.id) * 2
		else:
			try:
				amount = getval(val, signs=["Qd"], base=15)
			except:
				return

		if amount <= 0:
			return

		if (user.id not in data["global"]) or (user == _msg.author) or (amount > data["global"][_msg.author.id]["discs"]):
			return

		if not giftable(data["global"][_msg.author.id]) and (getpermlevel(_msg.author.id) < 1):
			time = int(data["global"][_msg.author.id]["gift"] - datetime.now().timestamp())
			minutes = int(time / 60)
			seconds = time % 60
			m = "{0} minute{1}".format(minutes, "s" if minutes != 1 else "")
			s = "{0} second{1}".format(seconds, "s" if seconds != 1 else "")
			ms = "{0} and {1}".format(m, s) if minutes > 0 else s
			await client.send_message(_msg.channel, embed=userembed("", "You have to wait a while before gifting again...\nTime left: **{0}**".format(ms), _msg.author))
			return

		if amount > (nextrank(user.id) * 2):
			await client.send_message(_msg.channel, embed=userembed("", "You cannot gift more than **{1}{0[disc]}** to **{2}**".format(const, shorten((nextrank(user.id) * 2), signs=["Qd"], base=15), user.name), _msg.author))
			return

		data["global"][_msg.author.id]["gift"] = datetime.now().timestamp() + 60 * 5

		await client.send_message(_msg.channel, embed=userembed("", "You gifted **{1}{0}** to **{2}**".format(const["disc"], shorten(amount, signs=["Qd"], base=15), user.name), _msg.author, secondtitle="A gift!"))
		data["global"][_msg.author.id]["discs"] -= amount
		data["global"][user.id]["discs"] += amount
	async def ranklist(_msg, _args):
		lst = ""
		for r in [{"name": rank["name"][n], "nuclear": rank["nuclear"][n]} for n in range(rank["number"])]:
			lst += "**{0}** {1}\n".format(r["name"], "(requires **Nuclear +{0}**)".format(r["nuclear"]) if r["nuclear"] > 0 else "")

		await client.send_message(_msg.channel, embed=initembed("Rank List", "Here's a list of all the available ranks:\n\n{0}".format(lst)))

	cmds = {
		"botowner": {
			"name": "Bot Owner",
			"check": lambda x: getpermlevel(x.id) >= 3,
			"hidden": False,
			"cmd": {
				"setgiveaway": [
					"[item]",
					"Starts/Ends a giveaway.",
					["sg"],
					sgiveaway
				],
				"itemdatabase": [
					"[add/remove/simple/giveaway]",
					"Adds/Removes items to/from the item database.\n\n*Argument list:*\nadd [item] [price] [boost] [nuclear?] [exclusive?] [description]\nremove [item]\nsimple [item] [price] [nuclear?] [exclusive?] [description]\ngiveaway [item] [description]",
					["itemdb", "idb"],
					itemdb
				],
				"additem": [
					"[item] [amount]",
					"Adds an item to one of the shops.",
					["ai"],
					additem
				],
				"remitem": [
					"[item]",
					"Removes an item from one of the shops.",
					["ri"],
					remitem
				],
				"shuffleshop": [
					"",
					"Randomizes the items in the shop",
					["ss"],
					shuffleshop
				],
				"forceevent": [
					"",
					"Force starts an event",
					["fe"],
					forceevent
				],
				"senddm": [
					"[message] [user]",
					"Send's a DM to a specific user",
					[],
					senddm
				],
				"messageall": [
					"[message]",
					"Sends a message to everyone(?)",
					[],
					messageall
				],
				"permitcommand": [
					"[command] [user]",
					"Gives permition of any unpermited command to any user",
					["pc"],
					permitcommand
				],
				"unpermitcommand": [
					"[command] [user]",
					"Removes permition of any permited command from any user",
					["upc"],
					unpermitcommand
				],
				"init": [
					"[user]",
					"Initializes a user's data.",
					[],
					init
				],
				"viewcommands": [
					"[user]",
					"Shows a user's permited commands",
					["vc"],
					viewcommands
				],
				"setmaxboost": [
					"[amount] [user]",
					"Set max boost to a certain value.",
					["smb"],
					setmaxboost
				]
			}
		},
		"bothost": {
			"name": "Bot Host",
			"check": lambda x: getpermlevel(x.id) >= 3 or x.id == client.host,
			"hidden": False,
			"cmd": {
				"reboot": [
					"",
					"Reboots the bot.",
					[],
					reboot
				],
				"fix": [
					"",
					"Fixes data.",
					[],
					fix
				],
				"raise": [
					"[exception name]",
					"Raises an exception",
					[],
					_raise
				]
			}
		},
		"botadmin": {
			"name": "Bot Administrator",
			"check": lambda x: getpermlevel(x.id) >= 2,
			"hidden": False,
			"cmd": {
				"setperm": [
					"[user]",
					"Sets a user's permissions",
					[],
					setperm
				]
			}
		},
		"botmod": {
			"name": "Bot Moderator",
			"check": lambda x: getpermlevel(x.id) >= 1,
			"hidden": False,
			"cmd": {
				"setdiscs": [
					"[amount]",
					"Sets your discs to a certain value.",
					["sd"],
					setdiscs
				],
				"setbonus": [
					"[amount]",
					"Sets your bonus to a certain value.",
					["sb"],
					setbonus
				],
				"setrank": [
					"[majorrank] [minorrank]",
					"Sets your rank.",
					["sr"],
					setrank
				],
				"settokens": [
					"[amount]",
					"Sets your tokens",
					["st"],
					settokens
				],
				"setnuclear": [
					"[amount]",
					"Sets your nuclear rank",
					["sn"],
					setnuclear
				],
				"giveitem": [
					"[item] [user]",
					"Gives an item to a certain user",
					["gi"],
					giveitem
				],
				"takeitem": [
					"[item] [user]",
					"Takes an item from a certain user",
					["ti"],
					takeitem
				]
			}
		},
		"admin": {
			"name": "Administrator",
			"check": lambda x: (x.server_permissions.administrator) or (x.id == "300070444621627402"),
			"hidden": False,
			"cmd": {
				"neutroprefix": [
					"[new prefix]",
					"Changes the bot's prefix.",
					["prefix"],
					prefix
				],
				"purge": [
					"[messages] [optional - user]",
					"Deletes up to 100 messages.",
					[],
					purge
				],
				"notify": [
					"[optional - non-sleep] [optional - types]",
					"Activates/Deactivates notifications for this channel.\nNon-sleep defaults to `False`, and types defaults to `shop giveaway event message`",
					[],
					notify
				]
			}
		},
		"cash": {
			"name": "Currency",
			"check": lambda x: True,
			"hidden": False,
			"cmd": {
				"info": [
					"[optional - user]",
					"Displays your/someone's global currency information.",
					["i"],
					info
				],
				"currency": [
					"[optional - user]",
					"Displays your/someone's discs.",
					["c"],
					cur
				],
				"nuclear": [
					"[optional - user]",
					"Displays your/someone's nuclear tokens.",
					["n"],
					nuclear
				],
				"bonus": [
					"[optional - user]",
					"Displays your/someone's bonus.",
					["b"],
					bonus
				],
				"inventory": [
					"[optional - user]",
					"Displays your/someone's inventory.",
					["inv"],
					inventory
				],
				"globalrank": [
					"[(d)isc/(n)uclear] [optional - user]",
					"Displays your/someone's global rank",
					["gr"],
					rank
				],
				"leaderboard": [
					"[optional - (n)uclear]",
					"Shows the top 10 users on Neutronium.",
					["lb"],
					leaderboard
				],
				"rankup": [
					"",
					"Rank up to get more DPM and get greater gifts.",
					["r"],
					rankup
				],
				"ascend": [
					"",
					"Ascend to get nuclear tokens! However, once you ascend, you will lose everything (except items, tokens and nuclear ranks).",
					["a"],
					ascend
				],
				"gamble": [
					"[amount]",
					"Gamble some discs with a chance of winning them back or losing it all.\n\n**Odds**\n45% - 1x\n4% - 3x\n1% - 5x\n",
					["g"],
					gamble
				],
				"shop": [
					"[(n)uclear (optional)]",
					"Shows the available items in the shop.",
					[],
					shop
				],
				"buy": [
					"[item]",
					"Buy an item from one of the shops.",
					[],
					buy
				],
				"sell": [
					"[item]",
					"Sells an item to the shop for 80% of the original price. If the item is not in the shop, it will sell for 50% instead.",
					[],
					sell
				],
				"item": [
					"[item]",
					"Shows information about an item.",
					[],
					item
				],
				"itemlist": [
					"",
					"Shows a list with all of the existing items.",
					[],
					itemlist
				],
				"event": [
					"[event]",
					"Shows the ongoing event. If no event is ocurring, then it will show a timer with the time left for the next event.",
					["e"],
					event
				],
				"giveaway": [
					"",
					"Shows the ongoing giveaway. If there is no giveaway active, then it will not do anything.",
					[],
					giveaway
				],
				"gift": [
					"[amount] [user]",
					"Gift someone some discs",
					[],
					gift
				],
				"ranklist": [
					"",
					"Shows all of the available ranks",
					["rl"],
					ranklist
				]
			}
		},
		"misc": {
			"name": "Miscellaneous",
			"check": lambda x: True,
			"hidden": False,
			"cmd": {
				"help": [
					"[command]",
					"Help command",
					[],
					help
				],
				"create": [
					"[name] [output]",
					"Creates a personal command",
					["set"],
					create
				],
				"delete": [
					"[name]",
					"Deletes a personal command",
					["del"],
					delete
				],
				"invite": [
					"",
					"Shows the bot's invite link, so you can add it to your server =)",
					[],
					invite
				],
				"stats": [
					"",
					"Check bot's statistics",
					[],
					stats
				]
			}
		},
		"hidden": {
			"name": "",
			"check": lambda x: True,
			"hidden": True,
			"cmd": {
				"grab": [
					"",
					"",
					[],
					grab
				],
				"join": [
					"",
					"",
					["j"],
					join
				]
			}
		}
	}

	events = {
		"grab": {
			"name": "Grab the discs",
			"description": "Try grabbing the discs by typing `{0}grab`, however, you have to be fast! This event only lasts 10 seconds, and only the first 5 people can get the prize. You better hold tight to those discs!",
			"chance": 40,
			"time": 10,
			"onstart": [setcode, startgrab],
			"onend": [giftwinner, endgrab]
		},
		"supergrab": {
			"name": "Super grab",
			"description": "Try to grab the discs by typing `{0}grab *some code*`, however, you have to be super fast! Not only do you have 10 seconds to react, you also have to type out a special code. Only the first 5 people get the prize, and really great one!",
			"chance": 20,
			"time": 20,
			"onstart": [setcode, startgrab],
			"onend": [giftwinner, endgrab]
		},
		"dpm": {
			"name": "DPM Boost",
			"description": "Get 3x more DPM while this event is going on!",
			"chance": 35,
			"time": 5 * 60,
			"onstart": [None, None],
			"onend": [None, None]
		},
		"dpm10": {
			"name": "DPM Madness",
			"description": "Get 10x more DPM while this event is going on!",
			"chance": 5,
			"time": 5 * 60,
			"onstart": [None, None],
			"onend": [None, None]
		}
	}

	itemrank = [
		"Common",
		"Rare",
		"Legendary",
		"Mythical"
	]

	rank = {
		"number": 27,
		"name": [
			"Basic",

			"Bronze",
			"Silver",
			"Gold",

			"Amethyst",
			"Sapphire",
			"Emerald",
			"Ruby",
			"Diamond",

			"Quartz",
			"Marble",
			"Obsidian",

			"Cobalt",
			"Rhodium",
			"Platinum",
			"Tektite",
			"Iridium",
			"Osmium",
			"Palladium",
			"Viridium",

			"Deuterium",
			"Plutonium",
			"Ultimatum",
			"Polonium",
			"Ambrosia",
			"Flerovium",

			"Transcended",

			"Moderator",
			"Luminite",
			"naegins",
			"Skyla",
			"Cub",
			"Developer"
		],
		"color": [
			0x646464,

			0xd18221,
			0xdcdcdc,
			0xffe01c,

			0xc27fe9,
			0x7f82e9,
			0x7fe995,
			0xea6a6a,
			0x85c5ea,

			0xfbeed1,
			0xffffff,
			0x191919,

			0x3d65a5,
			0xf7d900,
			0xf2f2f2,
			0x912b2b,
			0xccdfff,
			0xf5f5f5,
			0x407a30,
			0x52c49a,

			0xf7cce7,
			0xccf7d9,
			0x000000,
			0x7852a9,
			0xf7f77e,
			0xfafafa,

			0xffffff,

			0xd7935b,
			0x7bf2d6,
			0xffffff,
			0xaab67b,
			0x686691,
			0x59d98f
		],
		"image": [
			"PyC8S6t",

			"Xmrlziq",
			"jYWY3FF",
			"z66dDCk",

			"fSx47SV",
			"gq8emqq",
			"dFd1aJi",
			"lSaJswC",
			"o0Abnqb",

			"LkGLjD4",
			"OSsrHH8",
			"URHGJ1p",

			"OvYm0TT",
			"BEzaG6L",
			"xoTwx59",
			"BYzPbrG",
			"cDEH8EA",
			"pVzH73D",
			"1bZLZQL",
			"3q22hJA",

			"2uNHKWp",
			"0OUIM5F",
			"OMe0Ds4",
			"XQv0X1U",
			"1SuBXs4",
			"d6g0DE0",

			"Ead3IVc",

			"gGbh15s",
			"AISuZMB",
			"iSWSocC",
			"d9ER63a",
			"XCyGRfY",
			"R5SvTUm"
		],
		"nuclear": [
			0,

			0,
			0,
			0,

			0,
			0,
			0,
			0,
			0,

			0,
			0,
			0,

			1,
			2,
			3,
			5,
			7,
			10,
			15,
			20,

			25,
			30,
			35,
			40,
			45,
			50,

			100
		],
		"id": [
			None,
			"407471712939278336",
			"338735994566344704",
			"398388189116497930",
			"236979113586458625",
			"300070444621627402"
		]
	}

	data = {
		"servers": {},
		"global": {},
		"shop": {},
		"reshuffle": 0,
		"event": {
			"timer": 120,
			"ongoing": None,
			"data": {}
		},
		"giveaway": {
			"item": None,
			"time": 0,
			"joined": [],
		},
		"backup": 0
	}

	idb = {}

	loaddata("data")
	loaddata("idb")

	data["default"] = {
		"discs": 500,
		"tokens": 0,
		"bonus": 1,
		"bestbonus": 1,
		"tokentimer": 0,
		"majorrank": 1,
		"minorrank": 1,
		"nuclearrank": 0,
		"dialog": False,
		"items": [],
		"permlevel": 0,
		"permitedcmds": {},
		"inactivityLim": 120,
		"activityT": 0,
		"bonusT": 121,
		"dpmT": 121,
		"checkT": 0,
		"gift": 0,
		"maxboost": 300
	}
	
	const = {
		"disc": ":cd:",
		"token": "<:nucleartoken:411176834386886656>",
		"bonustime": lambda x: int(math.ceil(60/((x/50)+1))),
		"log": "459318682183794708",
		"permlevels": ["regular user", "Bot Moderator", "Bot Administrator", "Bot Owner"]
	}

async def check(user, player):
	now = datetime.now().timestamp()
	lim = player["activityT"] + player["inactivityLim"]
	
	bonusFreq = bonusfreq(player)
	
	while player["checkT"] < now and player["checkT"] < lim:
		player["checkT"] = min([lim, now, player["dpmT"]])
		if (player["checkT"] >= player["bonusT"]):
			bonusI = int((player["checkT"] - player["bonusT"]) / bonusFreq) + 1
			lastbonus = player["bonus"]
			player["bonus"] += bonusI
			player["tokentimer"] += bonusI
			player["bonusT"] += bonusI * bonusFreq
			if math.floor(player["bonus"] / 500) > math.floor(lastbonus / 500):
				await logbonus(user, player["bonus"])
		if (player["bonus"] > 5000):
			player["bonus"] = 5000
		if (player["checkT"] >= player["dpmT"]):
			player["discs"] += random(*absdpm(player, now)) * player["bonus"]
			player["dpmT"] += 60
			
	if (player["bonus"] > player["bestbonus"]):
		player["bestbonus"] = player["bonus"]
			
	if (player["checkT"] >= lim):
		player["dpmT"] = now + 60
		player["bonusT"] = now + bonusFreq
		player["bonus"] = 1
		player["tokentimer"] = 0
	
	if (player["tokentimer"] > 500):
		player["tokentimer"] = 0
		player["tokens"] += 5
	return now
async def update(user, player):
	player["activityT"] = await check(user, player)
def giftable(player):
	return datetime.now().timestamp() > player["gift"]
def bonusfreq(player):
	bonusFreq = int((60 / ((player["nuclearrank"] / 50) + 1)) * 100) / 100
	return bonusFreq if bonusFreq > 1 else 1
def absdpm(player, now):
	eventbonus = 10 if data["event"]["ongoing"] == "dpm10" else (3 if data["event"]["ongoing"] == "dpm" else 1)
	
	boost = sum([idb[item]["boost"] for item in player["items"] if item in idb])
	boost = player["maxboost"] if boost > player["maxboost"] else boost
	boost = boost/100+1
	
	majorrank = (player["majorrank"] - 1) if player["majorrank"] <= rank["number"] else (rank["number"] - 1)
	
	ret = 7**majorrank * player["minorrank"] * 10 * boost * eventbonus
	return sorted([int(ret * 0.75), int(ret)])
	
async def getreaction(botmessage, user, emotes):
	for emote in emotes:
		await client.add_reaction(botmessage, emote)
	ret = await client.wait_for_reaction(emotes, user=user, message=botmessage, timeout=60.0)
	try:
		await client.clear_reactions(botmessage)
	except:
		pass
	if ret is not None:
		ret = str(ret.reaction.emoji)
	return ret

def itemboost(userid):
	global data, idb
	boost = 0
	for item in data["global"][userid]["items"]:
		if item in idb:
			boost += idb[item]["boost"]
	if boost > data["global"][userid]["maxboost"]:
		boost = data["global"][userid]["maxboost"]
	return boost
def calcdpm(userid):
	bonus = data["global"][userid]["bonus"]
	majorrank = (data["global"][userid]["majorrank"] - 1) if data["global"][userid]["majorrank"] <= rank["number"] else (rank["number"] - 1)
	minorrank = data["global"][userid]["minorrank"]
	eventbonus = 10 if data["event"]["ongoing"] == "dpm10" else (3 if data["event"]["ongoing"] == "dpm" else 1)
	dpm = (10 * (7**majorrank) * minorrank) * bonus * (itemboost(userid) / 100 + 1) * eventbonus
	return sorted([int(dpm * 0.75), int(dpm * 1)])
def nextrank(userid):
	global data
	majorrank = data["global"][userid]["majorrank"] - 1
	minorrank = data["global"][userid]["minorrank"]
	return 10000 * (8**majorrank) * minorrank
def checkrank(price):
	global rank
	for i in range(rank["number"]):
		if price < (50000 * (8**i)):
			return i
def tokenprice(userid):
	global data, rank
	nuclearrank = data["global"][userid]["nuclearrank"]
	n = -1
	for nuclear in rank["nuclear"]:
		if (nuclearrank >= nuclear):
			n += 1
	return 50000 * (8**n)
def getpermlevel(userid):
	global const, data
	return 3 if (userid in client.owners) else data["global"][userid]["permlevel"]

def getanyuser(usertag):
	id = usertag.replace("@", "").replace("<", "").replace(">", "").replace("!", "")
	for member in client.get_all_members():
		if member.id == id:
			return member
async def getuser(msg, userval, indata=True):
	global data
	user = userval
	if user.startswith("dr#"):
		try:
			user = sorted([m for m in data["global"] if getpermlevel(m) < 1], key=lambda x: data["global"][x]["discs"], reverse=True)[int(user[3:]) - 1]
		except:
			pass
	if user.startswith("nr#"):
		try:
			user = sorted([m for m in data["global"] if getpermlevel(m) < 1], key=lambda x: data["global"][x]["nuclearrank"], reverse=True)[int(user[3:]) - 1]
		except:
			pass

	ret = getanyuser(user)
	if ret is None:
		try:
			ret = await client.get_user_info(user)
		except discord.errors.NotFound:
			if user in data["global"]:
				del data["global"][user]
		except:
			pass
	if ret is None:
		ret = msg.author
	if (ret.id not in data["global"]) and indata:
		ret = msg.author
	return ret

def loaddata(name):
	if os.path.exists("Data/{0}.json".format(name)):
		f = open("Data/{0}.json".format(name), "r")
		globals()[name] = json.load(f)
		f.close()
def savedata(name):
	dump = json.dumps(globals()[name], sort_keys=True, indent=4)
	f = open("Data/{0}.wrt.json".format(name), "w")
	f.write(dump)
	f.close()
	shutil.copyfile("Data/{0}.wrt.json".format(name), "Data/{0}.json".format(name))

def makebackup(dir, names=["data", "idb"]):
	try:
		os.makedirs(dir)
	except:
		pass
	for name in names:
		shutil.copyfile("Data/{0}.json".format(name), dir + "/{0}.json".format(name))

def initembed(title, description):
	rgb_c = colorsys.hls_to_rgb(random(0, 255) / 255, 170/255, 219/255)
	hex_c = "{0:02X}{1:02X}{2:02X}".format(round(rgb_c[0] * 255), round(rgb_c[1] * 255), round(rgb_c[2] * 255))
	embed = discord.Embed(title=title, description=description, color=int(hex_c, 16))
	embed.set_footer(text="{0} | Official Server: https://discord.gg/4AGE5BC".format(str(datetime.now().strftime("%c"))))
	embed.set_author(name="Neutronium", icon_url=client.user.avatar_url)
	return embed
def userembed(title, description, user, secondtitle=None):
	global data, rank, const
	majorrank = data["global"][user.id]["majorrank"]
	embed = initembed(None, description)
	embed.color = rank["color"][majorrank - 1]
	embed.set_author(name="{0}{1} {2} | {3} {4}{5}{6}".format(user.name, "'s" if title != "" else "", title, rank["name"][data["global"][user.id]["majorrank"] - 1], data["global"][user.id]["minorrank"] if data["global"][user.id]["minorrank"] > 0 else "", " | Nuclear +{0}".format(data["global"][user.id]["nuclearrank"]) if data["global"][user.id]["nuclearrank"] > 0 else "", " | {0}".format(const["permlevels"][getpermlevel(user.id)]) if getpermlevel(user.id) > 0 else ""), icon_url=user.avatar_url)
	embed.set_thumbnail(url="https://i.imgur.com/{0}.png".format(rank["image"][majorrank - 1]))
	if secondtitle is not None:
		embed.title = secondtitle
	return embed

def parsearg(c, arg):
	try:
		return c.split(" ")[arg]
	except:
		return ""
def parseargs(c, start):
	skip = 0
	for n in range(0, start):
		skip += len(parsearg(c, n)) + 1
	try:
		return c[skip:]
	except:
		return ""

def remdupes(list):
	ret = []
	for item in list:
		if item not in ret:
			ret.append(item)
	return ret

async def startevent():
	rand = random(1,100)
	i = 0
	evt = None
	for event in events:
		if rand > i and rand <= (i + events[event]["chance"]):
			evt = event
		i += events[event]["chance"]

	data["event"]["data"] = {}
	data["event"]["timer"] = datetime.now().timestamp() + events[evt]["time"]
	data["event"]["ongoing"] = evt

	if events[evt]["onstart"][0] is not None:
		events[evt]["onstart"][0]()

	for server in data["servers"]:
		for channel in data["servers"][server]["eventchannels"]:
			if notifytype(server, channel, ["event"]):
				if client.get_channel(channel) is not None:
					if events[evt]["onstart"][1] is None:
						try:
							await client.send_message(client.get_channel(channel), embed=initembed("Event", "The **{0}** event has just started! Type `{1}event {0}` to get more details about the event.".format(events[evt]["name"], data["servers"][server]["prefix"])))
						except:
							pass
					else:
						await events[evt]["onstart"][1](client.get_channel(channel))
async def endevent():
	evt = data["event"]["ongoing"]

	final = None

	if events[evt]["onend"][0] is not None:
		final = events[evt]["onend"][0]()

	for server in data["servers"]:
		for channel in data["servers"][server]["eventchannels"]:
			if notifytype(server, channel, ["event"]):
				if client.get_channel(channel) is not None:
					if events[evt]["onend"][1] is None:
						try:
							await client.send_message(client.get_channel(channel), embed=initembed("Event", "The **{0}** event ended".format(events[evt]["name"])))
						except:
							pass
					else:
						await events[evt]["onend"][1](client.get_channel(channel), final)

	data["event"]["timer"] = datetime.now().timestamp() + random(2 * 60, 3 * 60)
	data["event"]["ongoing"] = None
	data["event"]["data"] = {}

async def logcommand(user, type, command, args):
	global const, cmds
	try:
		channel = client.get_channel(const["log"])
	except:
		return
	await client.send_message(channel, embed=initembed("{0} command used by {1}".format(cmds[type]["name"], user.name), "Tag > {0}\nID > {1}\nCommand > `{2}`{3}".format(user.mention, user.id, command, "\nArguments > `{0}`".format(args) if args != "" else "")))
async def logbonus(user, bonus):
	global const
	try:
		channel = client.get_channel(const["log"])
	except:
		return
	await client.send_message(channel, embed=initembed("Specific bonus reached by {0}".format(user.name), "Tag > {0}\nID > {1}\nBonus > {2}x".format(user.mention, user.id, bonus)))

def notifytype(server, channel, types):
	return ((datetime.now().timestamp() < data["servers"][server]["eventchannels"][channel][0]) or data["servers"][server]["eventchannels"][channel][2]) and any([(x in types) for x in data["servers"][server]["eventchannels"][channel][1]])

##################
# Internal Loops #
##################
@client.add_loop(1)
async def mainloop():
	if (int(datetime.now().timestamp()) > data["giveaway"]["time"]) and (data["giveaway"]["item"] is not None):
		if data["giveaway"]["joined"] != []:
			winner = choice(data["giveaway"]["joined"])
			data["global"][winner]["items"].append(data["giveaway"]["item"])
			try:
				user = getanyuser(winner).name
			except:
				user = "Unknown"
		else:
			winner = None

		embed = initembed("Giveaway ended! :tada:", "The winner of this giveaway was...")
		if winner is None:
			embed.add_field(name="No one?", value="No one entered the giveaway...")
		else:
			embed.add_field(name=user, value="Item recieved: {0}!".format(data["giveaway"]["item"]))

		for server in data["servers"]:
			for channel in data["servers"][server]["eventchannels"]:
				if notifytype(server, channel, ["giveaway"]):
					try:
						await client.send_message(client.get_channel(channel), embed=embed)
					except:
						pass
		data["giveaway"]["item"] = None
		data["giveaway"]["joined"] = []
@client.add_loop(1)
async def events():
	now = datetime.now().timestamp()
	if (now >= data["event"]["timer"]) and (data["event"]["ongoing"] is None):
		await startevent()
	elif (now >= data["event"]["timer"]) and (data["event"]["ongoing"] is not None):
		await endevent()
@client.add_loop(120)
async def saveloop():
	data["backup"] += 1
	if data["backup"] >= 720:
		makebackup(datetime.now().strftime("Backups/%d-%m-%Y"))
		olddir = datetime.fromtimestamp(datetime.now().timestamp() - 24*3*60*60).strftime("Backups/%d-%m-%Y")
		if os.path.exists(olddir):
			shutil.rmtree(olddir)
		print("Backed up data!")
		data["backup"] = 0
	try:
		savedata("data")
		savedata("idb")
	except:
		return
@client.add_loop(2)
async def garbageloop():
	print("Garbage collected:", gc.collect(), "\r", end="")
@client.add_loop(60)
async def consolecleaner():
	os.system("cls")
	print("Screen cleared\n", end="")
	
############################
# On message event handler #
############################
@client.event
async def on_message(msg):
	await client.wait_until_ready()
	
	if (msg.channel.type != discord.ChannelType.text) or (msg.author.bot) or (not msg.channel.permissions_for(msg.server.me).send_messages):
		return

	if msg.server.id not in data["servers"]:
		data["servers"][msg.server.id] = {
			"prefix": "$",
			"users": {},
			"eventchannels": {}
		}

	if msg.channel.id in data["servers"][msg.server.id]["eventchannels"]:
		data["servers"][msg.server.id]["eventchannels"][msg.channel.id][0] = datetime.now().timestamp() + 5 * 60

	if msg.author.id not in data["servers"][msg.server.id]["users"]:
		data["servers"][msg.server.id]["users"][msg.author.id] = {"commands": {}}

	if msg.author.id not in data["global"]:
		data["global"][msg.author.id] = copy.deepcopy(data["default"])

	await update(msg.author, data["global"][msg.author.id])

	if (msg.content.lower() == "{0} prefix?".format(client.user.mention)) or (msg.content.startswith(data["servers"][msg.server.id]["prefix"])):
		missing = ""
		for perms in msg.channel.permissions_for(msg.server.me):
			required = ["embed_links", "add_reactions"]
			if perms[0] in required:
				if not perms[1]:
					missing += "`{0}`\n".format(perms[0].replace("_", " ").capitalize())

		if missing != "":
			await client.send_message(msg.channel, "The bot is missing the following permissions:\n{0}".format(missing))
			return

	if msg.content.lower() == "{0} prefix?".format(client.user.mention):
		await client.send_message(msg.channel, embed=initembed("Prefix", "The prefix for this server is `{0}`".format(data["servers"][msg.server.id]["prefix"])))

	if msg.content.startswith(data["servers"][msg.server.id]["prefix"]):
		cmd = msg.content[len(data["servers"][msg.server.id]["prefix"]):].split(" ")[0].lower()
		args = msg.content[1 + len(data["servers"][msg.server.id]["prefix"]) + len(cmd):]

		for type in cmds:
			if cmds[type]["check"](msg.author):
				for command in cmds[type]["cmd"]:
					if (cmd == command) or (cmd in cmds[type]["cmd"][command][2]):
						if (type in ["botowner", "botadmin", "botmod"]):
							await logcommand(msg.author, type, command, args)
						await cmds[type]["cmd"][command][3](msg, args)
						return

		for command in data["global"][msg.author.id]["permitedcmds"]:
			type = data["global"][msg.author.id]["permitedcmds"][command]
			if (cmd == command) or (cmd in cmds[type]["cmd"][command][2]):
				if (type in ["botowner", "botadmin", "botmod"]):
					await logcommand(msg.author, type, command, args)
				await cmds[type]["cmd"][command][3](msg, args)
				return

		for command in data["servers"][msg.server.id]["users"][msg.author.id]["commands"]:
			if cmd == command:
				await client.send_message(msg.channel, embed=userembed("", data["servers"][msg.server.id]["users"][msg.author.id]["commands"][command], msg.author))
				return

setup()
print("Waiting...\n")
client.run(token())
print("\nShutting down...\n")
