# Fetch Match Stats Lambda

Lambda responsible for fetching match basic statistics.
Match must be in the past

## Description

Lambda will fetch match stats data on event.

## Run

`This lambda is triggered via dynamo event`
Event body:

```
{
    "Records": [
        {
            "dynamodb": {
                "Keys": {
                    "match_id": {"N": "61332946"}
                },
                'NewImage': {
                    'team_one_id': {'S': '12334'},
                    ...
                }
            }
        }
    ]
}
```

Execution:

```
aws lambda invoke \
--function-name fetch-match-stats-lambda \
--payload "<EVENT_JSON>" outfile.txt
```
