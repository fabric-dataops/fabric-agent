import json
from pathlib import Path
path = Path('/Users/antonfernando/Dev/fabric-agent/data/activity_events/json/2026-01-28/2026-01-28_activity_events_all_10.json')
with path.open() as f:
    data = json.load(f)
rows = []
for item in data:
    if item.get('UserId') == 'gowtamibhanage@nbnco.com.au':
        rows.append({
            'CreationTime': item.get('CreationTime',''),
            'Operation': item.get('Operation',''),
            'Activity': item.get('Activity',''),
            'UserId': item.get('UserId',''),
            'DataflowName': item.get('DataflowName','')
        })
rows.sort(key=lambda r: r['CreationTime'])
cols = ['CreationTime','Operation','Activity','UserId','DataflowName']
print('| ' + ' | '.join(cols) + ' |')
print('|' + '|'.join(['---']*len(cols)) + '|')
for r in rows:
    print('| ' + ' | '.join(r[c].replace('\n',' ') if isinstance(r[c], str) else str(r[c]) for c in cols) + ' |')
print('\nTotal:', len(rows))
