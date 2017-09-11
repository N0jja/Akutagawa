key='INSERT OSU API KEY HERE' #Change this
import json
from jsondiff import diff
import jsondiff
import aiohttp
import asyncio
import discord
import botutils

async def check_user(user):
	"""
	This function calls osu api to check if a given user exists
	It handles spaces and underscore
	We actually dont parse the json, but just check response length
	Returns 1 if user exists
	Returns -1 on network fail or any Exception
	Returns 0 if user not found
	"""
	try:
		async with aiohttp.get('https://osu.ppy.sh/api/get_user?k='+key+'&u='+user+'') as r:
			if len(await r.text()) > 4:
				return 1
	except Exception as e:
		print("In Check user:")
		print(e)
		return -1
	return 0

async def track_user(user):
	"""
	This function calls osu api to get bests scores of a given user
	It compares the fresh json with the old one stored as a file in data folder
	if theres a mismatch, it means there is a new score
	in that case, the bot extracts the new play(s) of the fresh file
	overwrites the data file
	and returns data as a tuple with it being (success flag, number of new top plays, data as dict)
	if file is the same it continues and returns 0
	if file is empty it adds data in the file, and skips to avoid spamming
	every time a user is added
	returns -1 if fail
	"""
	try:
		async with aiohttp.get('https://osu.ppy.sh/api/get_user_best?k='+key+'&u='+user+'&limit=100') as r:
			raw_r = await r.text()
			if len(raw_r) > 4:
				jr = json.loads(raw_r)
				with open('data/'+user, 'r') as myfile:
					jdata = json.load(myfile)
				if jr != jdata :
					e = diff(jdata, jr)
					if jsondiff.insert in e:
						play = e[jsondiff.insert]
						with open('data/'+user, "w") as raw:
							raw.write(raw_r)
						return (1,len(e[jsondiff.insert]),play)
					with open('data/'+user, "w") as raw:
						raw.write(raw_r)
	except Exception as e:
		print("In Track_user:")
		print(e)
		return -1
	return 0

async def print_play(play, user):
	"""
	Function used to format a play data dict to an
	embed discord obect
	Beatmap data and play data are separated
	so it first calls get_map() to retrieve bm data
	if get_beatmap returns -1, its a fail so 
	the whole function returns -1
	On success it continues by computing the accuracy
	then format all the useful data
	and returns the embed object
	If this whole process fails it returns -1 too
	"""
	map = await get_map(str(play['beatmap_id']))
	if map == -1:
		return -1
	try:
		acc = str(compute_acc(str(play['countmiss']), str(play['count50']), str(play['count100']), str(play['count300'])))
		acc = acc[2:][:2]+','+acc[4:][:2]+' %'
		score = " ".join(str(play['score'])[::-1][i:i+3] for i in range(0, len(str(play['score'])), 3))[::-1]
		embedz = discord.Embed(title=str(map['title'])+" \["+str(map['version'])+"\]", url='https://osu.ppy.sh/b/'+str(map['beatmap_id']), color=0xB46BCF)
		embedz.set_author(name=str(user).title()+" just made a new top play on :")
		embedz.set_thumbnail(url="https://b.ppy.sh/thumb/"+str(map['beatmapset_id'])+"l.jpg")
		embedz.add_field(name='PP', value=str(play['pp']), inline=True)
		embedz.add_field(name='Rank', value=str(play['rank']), inline=True)
		embedz.add_field(name='Accuracy', value=str(acc), inline=True)
		embedz.add_field(name='Score', value=str(score), inline=True)
		embedz.add_field(name='Combo', value=str(play['maxcombo'])+'/'+str(map['max_combo']), inline=True)
		embedz.add_field(name='Mods', value=str(get_mods(int(play['enabled_mods']))), inline=True)
		embedz.add_field(name='Stars', value=str(map['difficultyrating'])[:4]+"☆", inline=True)
		embedz.add_field(name='Miss', value=str(play['countmiss']), inline=True)
		embedz.add_field(name='Date', value=str(play['date']), inline=True)
		embedz.set_footer(text = "Akutagawa bot, made by Ayato_k", icon_url='https://raw.githubusercontent.com/ppy/osu-resources/51f2b9b37f38cd349a3dd728a78f8fffcb3a54f5/osu.Game.Resources/Textures/Menu/logo.png')
	except Exception as e:
		print('In Print play:')
		print(e)
		return -1
	return embedz

async def get_map(map_id):
	"""
	This function gets data of a given beatmap ID on osu api
	and returns it as a dict created from the parsed json
	returns dict on success
	returns -1 on fail
	"""
	async with aiohttp.get('https://osu.ppy.sh/api/get_beatmaps?k='+key+'&b='+map_id+'&m=0') as r:
		raw_r = await r.text()
		if len(raw_r) > 4:
			try:
				jr = json.loads(raw_r)
			except Exception as e:
				print("in get_map:")
				print(e)
				return -1
			return jr[0]
	return -1

def get_mods(number):
	"""
	This function is used to compute the mods used
	Mods are reported by the api as a number
	with in binary, each bit represents a flag for a given mod
	with 0 being nomod
	so if mod number is lets say 3 in binary its 11 so flag 1 is set and flag 2 is set
	so it means mods are NF + EZ
	So we take the number, put it in binary list, read it backwards, if list object is 1 
	corresponding mod is added to the final string
	returns final string on success
	returns an error string on fail
	"""
	try:
		mod_list = ['NF', 'EZ', 'NV', 'HD', 'HR', 'SD', 'DT', '128', 'HT', 'NC', 'FL', 'AutoPlay', 'SO', 'AP', 'PF', '4K', '5K', '6K', '7K', '8K', 'KM', 'FI', 'RanD', 'LM', 'FM', '9K', '10K', '1K', '3K', '2K']
		if number <= 0:
			return 'No Mod'
		bin_list = [int(x) for x in bin(number)[2:]]
		i=0
		mod_str = ''
		for y in reversed(bin_list):
			if y == 1:
				mod_str += mod_list[i]
			i+=1
	except Exception as e:
		print('[!ERROR!] in get_mods:')
		print(e)
		return 'Fail to find mods'
	return mod_str

def compute_acc(cmiss, c50, c100, c300):
	"""
	returns the accuracy based on the official formula :
	Accuracy = Total points of hits / (Total number of hits * 300)
	With :
	Total points of hits = Number of 50s * 50 + Number of 100s * 100 + Number of 300s * 300
	Total number of hits = Number of misses + Number of 50 + Number of 100 + Number of 300
	returns acc string on success
	returns -1 on fail
	"""
	try:
		acc = str(float((int(c50)*50 + int(c100)*100 + int(c300)*300) / ((int(cmiss)+int(c50)+int(c100)+int(c300))*300)))
	except Exception as e:
		print('[!ERROR!] in compute_acc:')
		print('e')
		return 'unkwn'
	return acc

async def get_user_info(user):
	"""
	This function gets data of a given user ID on osu api
	and returns it as a dict created from the parsed json
	returns dict on success
	returns -1 on fail

	"""
	async with aiohttp.get('https://osu.ppy.sh/api/get_user?k='+key+'&u='+user.lower()) as r:
		raw_r = await r.text()
		if len(raw_r) > 4:
			try:
				jr = json.loads(raw_r)
			except Exception as e:
				print("in get_map:")
				print(e)
				return -1
			return jr[0]
	return -1

async def embed_user_info(user):
	"""
	Function used to format user data dict to an
	embed discord obect
	The color of the embed message is set
	according to the user profile pic main color
	using dl_image() and av_color()
	On success it continues by filling the embed obj
	flag() is galled to return the unicode obj 
	of the flag of the user s country.
	Returns the embed object
	If this whole process fails it returns -1
	"""
	# ----- Compute color and create embed obj ----- #
	try:
		try:
			ret = await botutils.dl_image('https://a.ppy.sh/'+str(user['user_id'])+'_api.jpg', str(user['user_id'])+'.jpg')
			if ret == -1:
				raise NameError('Fail dl')
			chex = botutils.av_color('data/tmp/'+str(user['user_id'])+'.jpg')
			print(chex)
			if chex == -1:
				raise NameError('Fail color calc')
			embed=discord.Embed(title="https://osu.ppy.sh/u/"+str(user['user_id']), url='https://osu.ppy.sh/u/'+str(user['user_id']), color=chex)
		except Exception as e:
			print('In embed user info')
			print(e)
			embed=discord.Embed(title="https://osu.ppy.sh/u/"+str(user['user_id']), url='https://osu.ppy.sh/u/'+str(user['user_id']))
		embed.set_author(name=str(user['username'])+'\'s profile:')
		embed.set_thumbnail(url='https://a.ppy.sh/'+str(user['user_id'])+'_api.jpg')
		# ----- Try digit sep World wide rank ----- #
		try:
			wwr = ".".join(str(user['pp_rank'])[::-1][i:i+3] for i in range(0, len(str(user['pp_rank'])), 3))[::-1]
			embed.add_field(name="World Wide Rank", value="#"+wwr, inline=True)
		except Exception as e:
			print('[!Error!] in wwr digit separation')
			print(e)
			embed.add_field(name="World Wide Rank", value="#"+str(user['pp_rank']), inline=True)
		embed.add_field(name="Raw pp", value=str(user['pp_raw']), inline=True)
		# ----- Try digit sep Country rank ----- #
		try:
			cr = ".".join(str(user['pp_country_rank'])[::-1][i:i+3] for i in range(0, len(str(user['pp_country_rank'])), 3))[::-1]
			embed.add_field(name="Country Rank", value="#"+cr+' '+botutils.flag(str(user['country']).upper()), inline=True)
		except Exception as e:
			print('[!Error!] in cr digit separation')
			print(e)
			embed.add_field(name="Country Rank", value="#"+str(user['pp_country_rank'])+' '+botutils.flag(str(user['country'])), inline=True)
		embed.add_field(name="Level", value=str(user['level'])[:5], inline=True)
		# ----- Try digit sep Playcount ------ #
		try:
			playcount = " ".join(str(user['playcount'])[::-1][i:i+3] for i in range(0, len(str(user['playcount'])), 3))[::-1]
			embed.add_field(name="Play count", value=str(playcount), inline=True)
		except Exception as e:
			print('[!Error!] in playcount digit separation')
			print(e)
			embed.add_field(name="Play count", value=str(user['playcount']), inline=True)
		embed.add_field(name="Accuracy", value=str(user['accuracy'])[:5]+"%", inline=True)
		embedz.set_footer(text = "Akutagawa bot, made by Ayato_k", icon_url='https://raw.githubusercontent.com/ppy/osu-resources/51f2b9b37f38cd349a3dd728a78f8fffcb3a54f5/osu.Game.Resources/Textures/Menu/logo.png')
		return embed
	except Exception as e:
		print('[!ERROR!] in embed_user_info:')
		print(e)
		return -1