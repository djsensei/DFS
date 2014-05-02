'''
Fantasy Football Data Scraper

Takes data from http://football14.myfantasyleague.com/2013/export

Dan Morris
Last Updated 5/1/2014
'''
import simplejson as json
from urllib2 import urlopen

url_base = 'http://football.myfantasyleague.com/'
url_export = '/export?JSON=1'
url_lang = {'type': 'TYPE', 'league': 'L', 'week': 'W', \
            'franchises': 'FRANCHISES', 'ppr': 'IS_PPR', 'mock': 'IS_MOCK'}
url_vals = {'draft': 'draftResults', 'roster': 'rosters'}
test_league = '10002'
first_year = 1999
last_year = 2014 # Not 2013 because it makes range(first, last) functions work

### - Processing Functions
def simplify_players_json(year, players_json):
  # Takes raw players json and builds an easily-referenced file
  players = players_json['players']['player']
  with open('players_json_'+str(year)+'.txt','w') as wf:
    pd = {}
    for i in players:
      pid = i['id']
      name = name_correct(i['name'])
      pd[pid] = {'name':name,'position':i['position'],'team':i['team']}
    json.dump(pd, wf, indent=0)
  print 'Players JSON for year ' + str(year) + ' complete.'
  return

def name_correct(name):
  # Turns 'Last, First' into 'First Last'
  name = name.split(',')
  name[0].strip(' ')
  name[1].strip(' ')
  return name[1] + ' ' + name[0]

def simplify_leagues_info():
  leagues = {}
  with open('leagues_raw_12teams.txt') as rf:
    l = json.loads(rf.read())
    l = l['adp']['leagues']['league']
    league_ids12 = []
    for i in l:
      league_ids12.append(i['id'])
  leagues['12teams'] = league_ids12
  with open('leagues_raw_10teams.txt') as rf:
    l = json.loads(rf.read())
    l = l['adp']['leagues']['league']
    league_ids10 = []
    for i in l:
      league_ids10.append(i['id'])
  leagues['10teams'] = league_ids10
  with open('league_ids_2013.txt','w') as wf:
    json.dump(leagues, wf, indent=0)

def simplify_draft_results(draft_json):
  # Returns a list of {pick, round, player, franchise} dicts
  draft = draft_json['draftResults']['draftUnit']['draftPick']
  for pick in draft:
    del pick['timestamp']
    del pick['comments']
  return draft

def simplify_roster(roster_json):
  # Gets to the meat of roster data
  # Returns a dict: {franchise:[playerid, playerid, ...]}
  roster = roster_json['rosters']['franchise']
  d = {}
  for f in roster:
    l = [] # list of player IDs
    owner = f['id']
    for p in f['player']:
      l.append(p['id'])
    d[owner] = l
  return d

def simplify_adp(adp_json):
  # Returns a list of {id, averagePick} dicts and the count of total leagues
  league_count = int(adp_json['adp']['totalDrafts'])
  adp = adp_json['adp']['player']
  for p in adp:
    del p['minPick']
    del p['maxPick']
    del p['draftsSelectedIn']
  return adp, league_count

def ids_to_players(l, year):
  # Replaces player id with readable player info in a list of player dicts
  for row in l:
    id = row['id']
    info = get_player_info(id, year)
    if info != None:
      del row['id']
      for i in info:
        row[i] = info[i]
  return l
###
### - CSV Functions
def list_to_csv(l, fname, header=None):
  # Converts a list of dicts into a csv file
  # If no header string is given, uses keys of first row as headings
  with open(fname,'w') as wf:
    if header == None:
      header = ''
      header_keys = l[0].keys()
      for k in header_keys:
        header += k + ','
      header = header[:-1]
    else:
      header_keys = header.split(',')
    wf.write(header+'\n')
    for row in l:
      ws = ''
      for k in header_keys:
        ws += str(row.get(k,'')) + ','
      ws = ws[:-1]
      wf.write(ws+'\n')
  print 'Finished writing ' + fname
  return
###
### - Loading Functions
def load_players_dict():
  # players_dict[year][player_id]
  players_dict = {}
  for year in range(first_year, last_year):
    with open('players/players_json_'+str(year)+'.txt') as rf:
      players_dict[str(year)] = json.loads(rf.read())
  return players_dict

def get_leagues(nteams='12', year='2013'):
  # Returns a list of all league ids from that year with that number of teams
  nteams = str(nteams)
  year = str(year)
  with open('league_ids_'+year+'.txt') as rf:
    l = json.loads(rf.read())
    league_list = l[nteams+'teams']
  return league_list

def get_player_info(player_id, year):
  # Retrieves player info
  # {name, position, team}
  try:
    return players_dict[str(year)][player_id]
  except:
    print 'Bad player id: ' + player_id + \
          ' not found in players_dict_'+str(year)+'.'
    return None
###
### - Webscraper Functions - You Have One Job
def html_to_json(url):
  # Loads url, loads its JSON content, returns the JSON dict
  try:
    r = urlopen(url)
  except:
    print 'URL loading issue with url = ' + url
    return
  try:
    j = json.loads(r.read())
  except:
    print 'JSON loading issue...'
  if 'error' in j.keys():
    print 'Bad URL. Check inputs.'
  return j

def url_specify(year, kvlist):
  # Adds strings to the url query to specify the results desired
  # kvlist is a list of (key, value) tuples
  url_add = ''
  for kv in kvlist:
    key = kv[0]
    value = kv[1]
    if key not in url_lang:
      print 'Bad key for URL specification...'
    else:
      url_add += '&' + url_lang[key] + '=' + str(value)
  url = url_base + str(year) + url_export + url_add
  return url

def pull_players(year):
  url = url_specify(year, [('type', 'players')])
  players_json = html_to_json(url)
  simplify_players_json(year, players_json)
  return

def pull_draft(league, year=2013):
  url = url_specify(year, [('type', url_vals['draft']), ('league', league)])
  draft_json = html_to_json(url)
  draft_list = simplify_draft_results(draft_json)
  return draft_list

def pull_roster(league=test_league, year=2013, week=1):
  url = url_specify(year, [('type', url_vals['roster']), ('league', league), \
                   ('week', week)])
  roster_json = html_to_json(url)
  roster_dict = simplify_roster(roster_json)
  return roster_dict

def pull_adp(year=2013, franchises=12, ppr=0, mock=0):
  url = url_specify(year, [('type', 'adp'), ('franchises', franchises), \
                           ('ppr', ppr), ('mock', mock)])
  adp_json = html_to_json(url)
  adp_list, league_count = simplify_adp(adp_json)
  return adp_list, league_count
###
### - Big Scraper Functions - One Run Does It All
def process_all_adp():
  # Scrapes and CSVs a full complement of ADP files
  # TODO - Load player dicts for each year.
  counts = []
  for year in range(first_year, last_year):
    for ppr in [0,1]:
      for franchises in [10,12]:
        l, c = pull_adp(year, franchises, ppr)
        counts.append({'year':year, 'ppr':ppr, 'franchises':franchises, \
                       'league_count':c})
        l = ids_to_players(l, year)
        fname = 'adp_'+str(year)+'_'+str(franchises)+'_ppr'+str(ppr)+'.csv'
        print 'processing ' + fname + ' ...'
        list_to_csv(l, fname)
  list_to_csv(counts, 'league_counts.csv', 'year,franchises,ppr,league_count')
  print 'all done!'
  return

def process_all_players():
  for year in range(first_year, last_year):
    pull_players(year)
  return
###

if __name__=='__main__':
  players_dict = load_players_dict()
  process_all_adp()
