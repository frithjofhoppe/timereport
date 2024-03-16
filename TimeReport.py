from requests import get
from pandas import json_normalize, ExcelWriter, to_datetime
from argparse import ArgumentParser
from datetime import date

parser = ArgumentParser(
    description='''creates a time tracking report as Excel file with 3 sheets:
      Detail: detail logged time on issues,
      Weekly: reports logged time on a weekly basis,
      Monthly: reports logged time on a monthly basis,
''')
parser.add_argument(
    'team',
    help='''namespace portion of the URL of the GitLab group,
    i.e. ip34-22vt (all teams)
    or ip34-22vt/ip34-22vt_letsparty (specific team)''')
parser.add_argument(
    'token',
    help='''your personal access token''')
parser.add_argument('--from', type=date.fromisoformat, help='an optional start date')
parser.add_argument('--to', type=date.fromisoformat, help='an optional end date')

args = vars(parser.parse_args())


def run_query(uri, query, variables, statusCode, headers):
    request = get(uri, json={'query': query, 'variables': variables}, headers=headers)
    if request.status_code == statusCode:
        return request.json()
    else:
        raise Exception(f'Unexpected status code returned: {request.status_code}')


gitlabURI = 'https://gitlab.fhnw.ch/api/graphql'
gitlabToken = args['token']
gitlabHeaders = {'Authorization': 'Bearer ' + gitlabToken}
gitlabStatusCode = 200

gitlabQuery = '''
query ($team: ID!, $cursor: String!) {
  group(fullPath: $team) {
    timelogs(after: $cursor) {
      nodes {
        issue {
          title
          labels {
              nodes {
                title
          			}
          		}
        }
        user {
          username
        }
        spentAt
        timeSpent
      }
      pageInfo {
       	endCursor
       	hasNextPage
      }
    }
  }
}
'''

# collect all time logs, GraphQL only returns 100 elements per query call
hasNext: bool = True
cursor = ""
timeLogs = []

while hasNext:
    gitlabQueryVariables = {'team': args['team'], 'cursor': cursor}
    result = run_query(gitlabURI, gitlabQuery, gitlabQueryVariables, gitlabStatusCode, gitlabHeaders)
    # something went wrong
    if result['data']['group'] is None:
        raise Exception(f'No result')

    timeLogs.append(
        result['data']['group']['timelogs']
    )
    cursor = result['data']['group']['timelogs']['pageInfo']['endCursor']
    hasNext = result['data']['group']['timelogs']['pageInfo']['hasNextPage']

# create report from all time logs
report = json_normalize(timeLogs, ['nodes'])

report = report[['user.username', 'spentAt', 'timeSpent', 'issue.title', 'issue.labels.nodes']]
report = report.rename(columns={'user.username': 'user', 'issue.title': 'issue', 'issue.labels.nodes': 'labels'})
report['timeSpent'] = (report['timeSpent'] / 3600.00).round(2)
report['spentAt'] = to_datetime(report['spentAt'], utc=True)
report['year'] = report['spentAt'].dt.year
report['month'] = report['spentAt'].dt.month
report['week'] = report['spentAt'].dt.isocalendar().week
report['spentAt'] = report['spentAt'].dt.date

fromDate = args['from']
toDate = args['to']
if fromDate:
    report = report[report['spentAt'] >= fromDate]
if toDate:
    report = report[report['spentAt'] <= toDate]

detail = report[['user', 'spentAt', 'timeSpent', 'labels', 'issue']]

weekly = report.pivot_table(
    values='timeSpent',
    index='user',
    columns=['year', 'week'],
    aggfunc='sum',
    fill_value=0)
weekly['total'] = weekly.sum(axis=1)
cols = weekly.columns.tolist()
cols = [cols[-1]] + cols[:-1]
weekly = weekly.reindex(columns=cols)

monthly = report.pivot_table(
    values='timeSpent',
    index='user',
    columns=['year', 'month'],
    aggfunc='sum',
    fill_value=0)
monthly['total'] = monthly.sum(axis=1)
cols = monthly.columns.tolist()
cols = [cols[-1]] + cols[:-1]
monthly = monthly.reindex(columns=cols)

with ExcelWriter('TimeReport.xlsx') as writer:
    detail.to_excel(writer, sheet_name='Detail')
    weekly.to_excel(writer, sheet_name='Weekly')
    monthly.to_excel(writer, sheet_name='Monthly')

print('TimeReport.xlsx created')
