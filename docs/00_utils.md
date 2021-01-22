# Repository Helpers



<br>

### Loading Environment Variables

First we'll load the the environment variables

```python
env_vars_fp = '../.env'
dotenv.load_dotenv(env_vars_fp)

slack_id = os.environ.get('slack_id')
slack_webhook_url = os.environ.get('slack_webhook_url')
```

<br>

### Notebook Information

<br>

We can now easily construct markdown tables

```python
notebook_info = {
    # development
    'Utilities': {
        'Directory': 'nbs',
        'Number': '00',
        'Description': 'Code for keeping the repository tidy',
        'Maintainer': 'Ayrton Bourn'
    },
    'EUMETSAT': {
        'Directory': 'nbs',
        'Number': '01',
        'Description': 'Development of the API wrapper for ems',
        'Maintainer': 'Ayrton Bourn'
    },
    'Reprojection': {
        'Directory': 'nbs',
        'Number': '02',
        'Description': 'Development of the reprojection operator',
        'Maintainer': 'Ayrton Bourn'
    },
    'Zarr': {
        'Directory': 'nbs',
        'Number': '03',
        'Description': 'Development of wrappers for loading/saving to Zarr',
        'Maintainer': 'Ayrton Bourn'
    },
    'GCP': {
        'Directory': 'nbs',
        'Number': '04',
        'Description': 'Development of GCP interface wrappers',
        'Maintainer': 'Laurence Watson'
    },
    'Pipeline': {
        'Directory': 'nbs',
        'Number': '05',
        'Description': 'Development of the pipeline processes',
        'Maintainer': 'Ayrton Bourn'
    },   
    'Downloading': {
        'Directory': 'nbs',
        'Number': '101',
        'Description': 'Guidance for using the ems download manager',
        'Maintainer': 'Ayrton Bourn'
    },
    'Reprojecting': {
        'Directory': 'nbs',
        'Number': '102',
        'Description': 'Guidance for using the reprojection operator',
        'Maintainer': 'Ayrton Bourn'
    },
    'Loading': {
        'Directory': 'nbs',
        'Number': '103',
        'Description': 'Guidance for retrieving saved data from Zarr',
        'Maintainer': 'Ayrton Bourn'
    },
    'Documentation': {
        'Directory': 'docs',
        'Number': '-',
        'Description': 'Automated generation of docs from notebooks',
        'Maintainer': 'Ayrton Bourn'
    },
}

nb_table_str = create_markdown_table(notebook_info)

print(nb_table_str)
```

    | Id            | Directory   | Number   | Description                                        | Maintainer      |
    |:--------------|:------------|:---------|:---------------------------------------------------|:----------------|
    | utils         | nbs         | 00       | Code for keeping the repository tidy               | Ayrton Bourn    |
    | EUMETSAT      | nbs         | 01       | Development of the API wrapper for ems             | Ayrton Bourn    |
    | Reprojection  | nbs         | 02       | Development of the reprojection operator           | Ayrton Bourn    |
    | Zarr          | nbs         | 03       | Development of wrappers for loading/saving to Zarr | Ayrton Bourn    |
    | GCP           | nbs         | 04       | Development of GCP interface wrappers              | Laurence Watson |
    | Pipeline      | nbs         | 05       | Development of the pipeline processes              | Ayrton Bourn    |
    | Downloading   | nbs         | 101      | Guidance for using the ems download manager        | Ayrton Bourn    |
    | Reprojecting  | nbs         | 102      | Guidance for using the reprojection operator       | Ayrton Bourn    |
    | Loading       | nbs         | 103      | Guidance for retrieving saved data from Zarr       | Ayrton Bourn    |
    | Documentation | docs        | -        | Automated generation of docs from notebooks        | Ayrton Bourn    |
    

<br>

### Logging

<br>

We'll now initialise the logger and make a test log

```python
logger = set_up_logging(__name__, 
                        '.', 
                        slack_id=slack_id,
                        slack_webhook_url=slack_webhook_url)

logger.log(logging.INFO, 'This will output to file and Jupyter but not to Slack as it is not critical')
```

    2020-11-12 09:58:41,301 - INFO - This will output to file and Jupyter but not to Slack as it is not critical
    

<br>

We'll now shutdown the logger handlers and then delete the log file we just made

```python
handlers = logger.handlers[:]

for handler in handlers:
    handler.close()
    logger.removeHandler(handler)

os.remove(f'{__name__}.txt')
```

<br>

Finally we'll export the specified functions to the utils.py module
