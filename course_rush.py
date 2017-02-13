import matplotlib
matplotlib.use('Agg')

import pandas as pd


df = pd.read_csv('log/circuit_training-2017-02-20.txt',
                 sep='\t',
                 names=['cnt', 'max', 'time'])
df.set_index(pd.DatetimeIndex(df['time']), inplace=True)

df = df[df['cnt'] > 0][['cnt', 'max']]

ax = df.plot(y='cnt',
             style=['o-'],
             legend=False,
             title='Circuit training (2016-02-20)')
ax.set_xlabel('time')
ax.set_ylabel('#registrations')
xticks = df.index[::11]
ax.set_xticklabels([t.strftime('%m-%d %H:%M') for t in xticks])

fig = ax.get_figure()


fig.savefig('imgs/circuit_training-2016-02-20.pdf')
