#!/usr/bin/python3.5

import discord
import asyncio
import botutils
import osu

client = discord.Client()

@client.event
async def on_ready():
	"""
	Async function that is triggered when bot is ready and connected
	Prints Name and id of the bot
	Returns nothing
	"""
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)
	print('------')

@client.event
async def on_message(message):
	"""
	Async function that is triggered by any message on the discord
	Actually enters the conditions if message starts with !, you can change it here
	It handles all the text interactions between user and bot
	Returns nothing
	"""
	if message.content.startswith('!'):
		# ------------Process The Message------------------ #
		#
		# Splits the message in a list to avoid bad user input
		#
		split_message = []
		if ' ' in message.content:
			split_message = message.content.split(' ')
		# ------------------------------------------------- #
		#
		# -----------Del user tracking--------------------- #
		#
		# When this condition is met, it enters a process
		# used to delete a user from the tracked users
		# file and its data
		#
		if message.content.startswith('!trackdel'):
			if botutils.is_admin(message.author.id) :
				if len(split_message) > 0:
					user = "_".join(split_message[1:])
					user_raw = " ".join(split_message[1:])
					await client.send_message(message.channel, '```Checking if user \''+user_raw+'\' exists```')
					if botutils.check_user_del(user) == 1:
						await client.send_message(message.channel, '```User \''+user_raw+'\' found, deleting...```')
						if botutils.del_user(user) == 1:
							await client.send_message(message.channel, '```User successfuly deleted```')
						else:
							await client.send_message(message.channel, '```Error while deleting, this sucks...\nDumping file content to stdout...```')
					else:
						await client.send_message(message.channel, '```User \''+user_raw+'\' not found```')
				else :
					await client.send_message(message.channel, '```Check your syntax with !help !trackdel```')
			else :
				await client.send_message(message.channel, '```You need to be Admin of the bot to do this, ask Ayato_k```')
		# ------------------------------------------------- #
		#
		# ----------Track list----------------------------- #
		#
		# When this condition is met, it enters a process
		# used to list all the tracked users
		#
		elif message.content.startswith('!tracklist'):
			tracklist = '\n'
			with open('tracked_users', 'r') as myfile:
				for line in myfile.readlines(): #This is strange but if i use read() it skips first line
					tracklist += line
			myfile.close()
			await client.send_message(message.channel, '```Here\'s the list of tracked users:'+tracklist+'```')
		# ------------------------------------------------- #
		#
		# ----------Add users to tracking------------------ #
		#
		# When this condition is met, it enters a process
		# used to add a user to the tracked users
		# We call the api to check if the user exists first
		# if user isnt found, the bot prints an err message
		# if user found, the bot adds it and prints a success
		# message
		#
		elif message.content.startswith('!track'):
			if botutils.is_admin(message.author.id) :
				if len(split_message) > 0:
					user = str("_".join(split_message[1:])).lower()
					user_raw = " ".join(split_message[1:])
					await client.send_message(message.channel, '```Checking if user \''+user_raw+'\' exists```')
					if botutils.check_user_del(user) == 0:
						if await osu.check_user(user) == 1:
							await client.send_message(message.channel, '```User \''+user_raw+'\' exists, adding it to tracking```')
							try:
								with open("tracked_users", "a") as myfile:
									myfile.write(user+'\n')
								with open('data/'+user, 'a') as nf:
									nf.write('[]')
								await client.send_message(message.channel, '```User \''+user_raw+'\' Succesfuly added to tracking```')
							except Exception as e:
								print('[!ERROR!] In Adduser tracking')
								print(e)
						elif await osu.check_user(user) == -1:
							await client.send_message(message.channel, '```Osu servers are laggy atm, try again later```')
						else:
							await client.send_message(message.channel, '```User \''+user_raw+'\' not found```')
					else:
						await client.send_message(message.channel, '```User \''+user_raw+'\' already in tracking file```')
				else :
					await client.send_message(message.channel, '```Check your syntax with !help !track```')
			else :
				await client.send_message(message.channel, '```You need to be Admin of the bot to do this, ask Ayato_k```')

		# ------------------------------------------------- #
		#
		# ------------------Show user stats---------------- #
		#
		# When this condition is met, it enters a process
		# used to print statistics for a given user
		#
		elif message.content.startswith('!user'):
			if len(split_message) > 0:
				user = str("_".join(split_message[1:])).lower()
				dic_ret = await osu.get_user_info(user)
				embed = await osu.embed_user_info(dic_ret)
				await client.send_message(message.channel, embed=embed)


async def background_loop():
	"""
	Async function that runs forever
	It is used to call osu api to check for new scores
	of the tracked users.
	the function is set to pause every 2 minutes
	(Refresh rate)
	I advice you dont change it, it causes the bot to overlap and crash
	if the refresh rate is too low, i plan on adding threading on this
	Doesnt returns anything
	"""
	await client.wait_until_ready()
	while not client.is_closed:
		try:
			channel = client.get_channel('Channel ID')
			user_file = open('tracked_users', 'r')
			for user_r in user_file:
				user = user_r[:-1]
				ret = await osu.track_user(user)
				if isinstance(ret, tuple):
					garbage, nbplays, plays = ret
					for x in range(0,nbplays):
						embed = await osu.print_play(plays[x][1], user)
						if embed != -1:
							await client.send_message(channel, embed=embed)
		except Exception as e:
			print('in BG Loop')
			print(e)
		await asyncio.sleep(120)

client.loop.create_task(background_loop()) # Launches the user check loop
client.run('INSERT YOUR BOT TOKEN HERE') # Runs the discord client
