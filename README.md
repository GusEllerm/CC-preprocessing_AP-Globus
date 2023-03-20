# Flask action provider

Executes common_crawl_corpus pre-processing developed [here](https://github.com/jonathandunn/common_crawl_corpus "Common Crawl Corpus").

## Use

To get information regarding this AP's (Action Provider) actions, run a GET request to the server to /cc. This produces the output: 

```json
{
  "admin_contact": "ael56@uclive.ac.nz",
  "administered_by": [
    "ael56@uclive.ac.nz"
  ],
  "api_version": "1.0",
  "description": "Get suitable description from Jonathan",
  "event_types": null,
  "globus_auth_scope": "https://auth.globus.org/scopes/27c72d0c-9a46-4a5d-a6a5-bd2cd35bc574/action_all",
  "input_schema": {
    "example": {
      "path": "common_crawl_download/CC-MAIN-2022-40/CC-MAIN-2022-40-wet.paths.gz",
      "prefix_list": "CC-MAIN-2017-09"
    },
    "properties": {
      "path": {
        "description": "Path to data from the CC corpus",
        "title": "Path to wet.path.gz file",
        "type": "string"
      },
      "prefix_list": {
        "description": "Segement to process, E.G 'CC-MAIN-2017-09'",
        "title": "Selected segment to process",
        "type": "string"
      }
    },
    "required": [
      "path",
      "prefix_list"
    ],
    "title": "ActionProviderInput",
    "type": "object"
  },
  "keywords": [
    "Common Crawl",
    "NLP",
    "productivity"
  ],
  "log_supported": false,
  "maximum_deadline": "P30D",
  "runnable_by": [
    "all_authenticated_users"
  ],
  "subtitle": "Get suitable subtitle from Jonathan",
  "synchronous": true,
  "title": "Common Crawl pre-processing",
  "types": [
    "ACTION"
  ],
  "visible_to": [
    "public"
  ]
}
```

## Context

TODO: regarding context of the AP, expected orcestration, and how to transfer outputs.