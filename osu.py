key='INSERT OSU API KEY HERE' #Change this
import requests
import json
from jsondiff import diff
import jsondiff
import aiohttp
import asyncio


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
		print("[!ERROR!] In Check user:")
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
		async with aiohttp.get('https://osu.ppy.sh/api/get_user_best?k='+key+'&u='+user+'&limit=100')as r:
			raw_r = await r.text()
			if len(raw_r) > 4:
				jr = await r.json()
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
		print("[!ERROR!] In Track_user:")
		print(e)
		return -1
	return 0

async def print_play(play, user):
	"""
	Function used to format a play data dict to a string
	Beatmap data and play data are separated
	so it first calls get map to retrieve bm data
	if get_beatmap returns -1, its a fail so it returns -1
	On success it continues by computing the accuracy
	then format score by grouping number by 3
	and returns the formatted string
	If this whole process fails it returns -1 too
	"""
	map = await get_map(str(play['beatmap_id']))
	if map == -1:
		return -1
	try:
		acc = str(compute_acc(str(play['countmiss']), str(play['count50']), str(play['count100']), str(play['count300'])))
		acc = acc[2:][:2]+','+acc[4:][:2]+' %' #acc is returned as a numer smaller than 1 with 1 being 100 acc so we format it
		score = " ".join(str(play['score'])[i:i+3] for i in range(0, len(str(play['score'])), 3)) #Group score by 3
		# main string format
		bot_str = '```Congratz! '+str(user)+' got a new top play :\nMap: '+str(map['title'])+'\nRank: '+str(play['rank'])+'   Mods: '+str(get_mods(int(play['enabled_mods'])))+'\nPP: '+str(play['pp'])+'    Combo:'+str(play['maxcombo'])+'/'+str(map['max_combo'])+'\nScore: '+str(score)+'\nAcc: '+str(acc)+'  Stars: '+str(map['difficultyrating'])[:4]+'```'
	except Exception as e:
		print("[!ERROR!] In Print play:")
		print(e)
		return -1
	return bot_str

async def get_map(map_id):
	"""
	This function gets data of a given beatmap ID on osu api
	and returns it as a dict created from the parsed json
	returns dict on success
	returns -1 on fail
	"""
	async with aiohttp.get('https://osu.ppy.sh/api/get_beatmaps?k='+key+'&b='+map_id+'&m=0') as r:
		raw_r = await r.text()
		if len(raw_r) > 4: #Check if at least json is filled with data
			try:
				jr = await r.json()
			except Exception as e:
				print("[!ERROR!] in get_map:")
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
