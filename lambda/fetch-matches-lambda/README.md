# Fetch Matches Lambda

Lambda responsible for fetching matches for a day

## Description

Lambda will fetch matches on event.

## Run

Event body:
```json
{
  "data": {
    "jobs": [
      {
        "params": {
          "league_id": "1609",
          "date": "2020-07-23"
        },
        "status": "new"
      },
      {
        "params": {
          "league_id": "1609",
          "date": "2020-07-24"
        },
        "status": "new"
      }
    ]
  }
}
```

Where league_id:
```json
{
    "1609": "DENMARK, SUPERLIGAEN",
    "974": "AUSTRALIA, ALEAGUE"
}
```

Execution:
```
aws lambda invoke \
--function-name fetch-match-stats-lambda \
--payload "<EVENT_JSON>" outfile.txt
```