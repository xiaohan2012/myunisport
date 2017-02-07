import requests
import pandas as pd
from time import sleep
from datetime import datetime


course_name = "Circuit Training"
date = '2017-02-20'
delay_secs = 60

eventr_list_url = "https://unisport.fi/yol/web/en/crud/read/event.json?date={}&sportHierarchies=825079,6247560".format(date)

p = requests.get(eventr_list_url)
courses = p.json()['items']

df = pd.DataFrame.from_records(courses)

event_id = df[df['name'] == course_name]['id']
event_id = event_id.iloc[0]

event_url = 'https://unisport.fi/yol/web/en/crud/read/reservable.json?id={}&details=true'.format(event_id)

output_path = '/home/cloud-user/code/unisport/log/{}-{}.txt'.format('_'.join(course_name.lower().split()), date)

while True:
    p = requests.get(event_url)
    c = p.json()['items'][0]
    resv = c['reservations']
    resv_max = c['maxReservations']
    print('write')
    with open(output_path, 'a') as f:
        f.write('{}\t{}\t{}\n'.format(resv,
                                      resv_max,
                                      datetime.now().strftime('%Y-%m-%dT%H:%M:%S')))
    sleep(delay_secs)
