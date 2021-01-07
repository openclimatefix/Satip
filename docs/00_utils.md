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
    'Repository Helpers': {
        'Directory': 'notebooks',
        'Number': '00',
        'Description': 'Code for keeping the repository tidy',
        'Maintainer': 'Ayrton Bourn'
    },
    'EUMETSAT API Wrapper': {
        'Directory': 'notebooks',
        'Number': '01',
        'Description': 'Development of the API wrapper for ems',
        'Maintainer': 'Ayrton Bourn'
    },
    'Data Transformation': {
        'Directory': 'notebooks',
        'Number': '02',
        'Description': 'Intial EDA and transformation comparisons',
        'Maintainer': 'Ayrton Bourn'
    },
    # usage_examples
    'EUMETSAT Download': {
        'Directory': 'usage_examples',
        'Number': '00',
        'Description': 'Guidance for using the ems download manager',
        'Maintainer': 'Ayrton Bourn'
    },
}

nb_table_str = create_markdown_table(notebook_info)

print(nb_table_str)
```

    | Id                   | Directory      |   Number | Description                                 | Maintainer   |
    |:---------------------|:---------------|---------:|:--------------------------------------------|:-------------|
    | Repository Helpers   | notebooks      |       00 | Code for keeping the repository tidy        | Ayrton Bourn |
    | EUMETSAT API Wrapper | notebooks      |       01 | Development of the API wrapper for ems      | Ayrton Bourn |
    | Data Transformation  | notebooks      |       02 | Intial EDA and transformation comparisons   | Ayrton Bourn |
    | EUMETSAT Download    | usage_examples |       00 | Guidance for using the ems download manager | Ayrton Bourn |
    

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
