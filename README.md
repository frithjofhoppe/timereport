# TimeReport

This script creates a time tracking report of all issues of a GitLab group or subgroup as Excel file `TimeReport.xlsx` with 3 sheets:

- Detail: detail logged time on issues,
- Weekly: reports logged time on a weekly basis,
- Monthly: reports logged time on a monthly basis

## Prerequisites

Python 3.11 

```
pip install -r requirements.txt
```

## Usage

```
python TimeReport.py [-h] [--from FROM] [--to TO] team token
```
### Arguments

| Argument | Description |
| :------  | :---------  |
| --from   | an optional start date: YYYY-MM-DD |
| --to   | an optional end date: YYYY-MM-DD |
| team   | namespace portion of the URL of the GitLab group, i.e. ip34-22vt (all teams) or ip34-22vt/ip34-22vt_letsparty (specific team) |
| token  | a personal or a group access token |

