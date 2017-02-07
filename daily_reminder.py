import requests
import pandas as pd
from datetime import datetime, timedelta

tomorrow = datetime.now() + timedelta(days=1)
date = tomorrow.strftime('%Y-%m-%d')

PORTHANIA = 'Porthania'
TOOLO = 'Töölö Sports Centre'
KUMPULA = 'Kumpula Sports Centre'
MEILAHTI = 'Meilahti Sports Centre',
EETALO = 'EE-talo'
VIIKI = 'Exercise facilities at Viikki Teacher Training School'
OTANIEMI = 'Otahalli Sport Centre'


# personalization
start_time_earlist = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 9)
start_time_latest = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 18, 30)

target_locations = {PORTHANIA, TOOLO}
target_course_names = {'hiit', 'bodypump', 'total training', 'circuit training', 'pilates'}

# crawling
url = 'https://unisport.fi/yol/web/en/crud/read/event.json?date={}&sportHierarchies=825079,6247560'.format(date)
courses = requests.get(url).json()['items']

# filtering
df = pd.DataFrame.from_records(courses)

df = df[df['venue'].apply(lambda v: v in target_locations)]


df = df[df['name'].apply(
    lambda v: any(map(lambda n: n in v.lower(),
                      target_course_names)))]

df['startTime'] = df['startTime'].apply(lambda s: datetime.strptime(s, '%Y-%m-%dT%H:%M'))
df = df[df['startTime'].apply(lambda s:
                              (s >= start_time_earlist) and (s <= start_time_latest))]
