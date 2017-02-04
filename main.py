import requests
import string
import pandas as pd
import re
import argparse
import pygal

from pygal.style import Style
from pyquery import PyQuery as pq

AALTO = 'aalto'
UH = 'uh'
MALE = 'male'
FEMALE = 'female'


parser = argparse.ArgumentParser()
parser.add_argument('-u', '--username', required=True)
parser.add_argument('-p', '--password', required=True)
parser.add_argument('-s', '--school', choices=(AALTO, UH), required=True)
parser.add_argument('-g', '--gender', choices=(MALE, FEMALE), required=True)

args = parser.parse_args()


latex_string = """

\\tikzset{
  define color/.code 2 args={
    \\definecolor{#1}{RGB}{#2}
        
  },
  /mystyle/.style={
    define color={gold}{252, 210, 1},
    define color={silver}{204, 204, 204},
    define color={bronze}{239, 167, 83},
"""

show_legend = False

univ = args.school
gender = args.gender

# print(data['items'][0])
if univ == AALTO:
    payload = {
        'j_username': args.username,
        'j_password': args.password,
        '_eventId_proceed': ''
    }
    url1 = "https://unisport.fi/Shibboleth.sso/AaltoLogin?target=https%3A%2F%2Funisport.fi%2Fyol%2Fweb%2Ffi%2FshibbolethLogin.do%3Fsite%3DCLIENT%26authenticationType%3DSHIBBOLETH%26target%3Dhttps%253A%252F%252Funisport.fi%252F%2523login"
    univ_url = "https://idp.aalto.fi"
elif univ == UH:
    payload = {
        'j_username': args.username,
        'j_password': args.password,
        '_eventId_proceed': ''
    }
    url1 = "https://unisport.fi/Shibboleth.sso/HYLogin?target=https%3A%2F%2Funisport.fi%2Fyol%2Fweb%2Ffi%2FshibbolethLogin.do%3Fsite%3DCLIENT%26authenticationType%3DSHIBBOLETH%26target%3Dhttps%253A%252F%252Funisport.fi%252F%2523login"
    univ_url = "https://login.helsinki.fi"


with requests.Session() as s:
    p = s.get(url1)

    doc = pq(p.text)
    url_rel = doc.find('form').attr('action')

    p = s.post(univ_url + url_rel, data=payload)
    doc = pq(p.text.replace('xmlns="http://www.w3.org/1999/xhtml"', ''))

    field1 = doc.find('input:eq(0)')
    field2 = doc.find('input:eq(1)')

    p = s.post('https://unisport.fi/Shibboleth.sso/SAML2/POST',
           data={
               field1.attr('name'): field1.attr('value'),
               field2.attr('name'): field2.attr('value')
           })

    p = s.get("https://unisport.fi/yol/web/en/crud/read/registration.json?user=authenticated")
    rows = p.json()['items']


start_date = '2016-01-01'
end_date = '2016-12-31'

df = pd.DataFrame.from_records(rows)
df.set_index(pd.DatetimeIndex(df['date']), inplace=True)

start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)

regex = re.compile('\d{2}')

df['name'] = df['name'].map(
    lambda s: s.lower().replace('in english', '').replace('time change:', '').replace('class change:', '').replace('new!', '').replace('new in autumn!', '').replace('new in spring', '').replace('®', '')).map(
        lambda s: regex.sub('', s).strip())

print(df['name'].unique())
print(df['name'].unique().shape)

df = df[start_date: end_date]

print(df['name'].value_counts())

top_k = 9

counts = df['name'].value_counts()

if len(counts) > top_k:
    counts = counts[:top_k].append(pd.Series(counts[top_k:].sum(), index=['others']))
    # counts.sort_values(ascending=True, inplace=True)

all_colors = ['#a6cee3','#1f78b4','#b2df8a','#33a02c','#fb9a99','#e31a1c','#fdbf6f','#ff7f00','#cab2d6','#6a3d9a','#ffff99','#b15928']

define_colors = []
for i, c in zip(string.ascii_lowercase, all_colors[:top_k+2]):
    rgb = ','.join(map(str, pygal.colors.parse_color(c)[:3]))
    define_colors.append('define color={{course{}}}{{{}}}'.format(i, rgb))
latex_string += ',\n'.join(define_colors)
latex_string += """\n  }
}"""

font_family = 'Calibri'
style = Style(
    title_font_family=font_family,
    legend_font_family=font_family,
    value_font_family=font_family,
    title_font_size=36,
    value_font_size=36,
    legend_font_size=36,
    label_font_size=18,
    value_colors=['#666'] * len(df['name'].unique()),
    colors=all_colors[:top_k+1],
    background='transparent'
)


g = pygal.Pie(print_values=True,
              style=style,
              truncate_legend=25,
              show_legend=show_legend)

# g.title = 'Class frequency'

name_defines = []
for i, (name, count) in zip(string.ascii_lowercase, counts.iteritems()):
    g.add(name, [{'value': count, 'label': name}])
    name_defines.append("""\\newcommand{{\\coursename{}}}{{{}}}""".format(i, name))

latex_string += '\n'
latex_string += '\n'.join(name_defines)

g.render_to_png('imgs/pie.png')


# Stacked area plot
g = pygal.StackedBar(style=style,
                     truncate_legend=25,
                     show_legend=show_legend,
                     show_y_guides=False)
# g.title = 'Frequency over months'
all_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
g.x_labels = all_months

pd.date_range(start_date, end_date, freq='MS')

rows = []
for name, subdf in df.groupby('name'):
    cnts = subdf.groupby(pd.TimeGrouper('MS')).count()['date']
    dts = [dt for dt in pd.date_range(start_date, end_date, freq='MS') if dt not in cnts.index]
    cnts = cnts.append(pd.Series([0]*len(dts), index=dts))
    cnts.sort_index(inplace=True)
    rows.append((name, cnts.values, cnts.values.sum()))
    
time_df = pd.DataFrame(rows, columns=['name', 'freqs', 'sum'])

time_df.sort_values(by='sum', inplace=True, ascending=False)

for i, r in time_df.iloc[:top_k].iterrows():
    g.add(r['name'], r['freqs'])

g.render_to_png('imgs/stacked.png')


latex_string += '\n'
latex_string += "\\newcommand{{\\totaltrainings}}{{{}}}\n".format(df.shape[0])
latex_string += "\\newcommand{{\\meandays}}{{{:.1f}}}\n".format(365/df.shape[0])

active_month = df.groupby(pd.TimeGrouper('MS')).count()['name'].argmax().month
inactive_month = df.groupby(pd.TimeGrouper('MS')).count()['name'].argmin().month

latex_string += "\\newcommand{{\\mostactivemonth}}{{{}}}\n".format(all_months[active_month-1])
latex_string += "\\newcommand{{\\mostinactivemonth}}{{{}}}\n".format(all_months[inactive_month-1])

latex_string += "\\newcommand{{\\titlebgcolor}}{{{}}}\n".format('blue' if gender == MALE else 'pink')

with open('defines.tex', 'w') as f:
    f.write(latex_string)
