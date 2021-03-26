# CI/CD



```
#exports
import os
import re
import typer
import logging
from warnings import warn
from configparser import ConfigParser
```

<br>

### Initialising CLI 

```
#exports
app = typer.Typer()
```

<br>

### Incrementing the Package Version

We'll start by retrieving the current package version specified in `settings.ini`

```
#exports
@app.command()
def get_current_package_version(settings_fp: str='settings.ini'):
    config = ConfigParser(delimiters=['='])
    config.read(settings_fp)
    version = config.get('DEFAULT', 'version')
    
    return version
```

```
settings_fp = '../settings.ini'

original_version = get_current_package_version(settings_fp)

original_version
```




    '1.0.2'



<br>

We'll now increment the package version

```
#exports
@app.command()
def increment_package_version(old_version: str, increment_level: str='micro'):
    increment = lambda rev: str(int(rev)+1)
    
    major, minor, micro = old_version.split('.') # naming from - https://the-hitchhikers-guide-to-packaging.readthedocs.io/en/latest/specification.html#sequence-based-scheme
    
    if increment_level == 'major':
        major = increment(major)
    elif increment_level == 'minor':
        minor = increment(minor)
    elif increment_level == 'micro':
        micro = increment(micro)
        
    new_version = '.'.join([major, minor, micro])
    
    return new_version
```

```
increment_package_version(original_version)
```




    '1.0.3'



<br>

But what about if we've made large changes to the code-base and wish to express the size of these revisions in the version? For that we can specify the `increment_level`.

```
increment_package_version(original_version, increment_level='major')
```




    '2.0.2'



<br>

And finally we can set the version

```
#exports
@app.command()
def set_current_package_version(version: str, settings_fp: str='settings.ini'):
    version = version.replace('v', '')
    
    config = ConfigParser(delimiters=['='])
    config.read(settings_fp)

    config.set('DEFAULT', 'version', version)

    with open(settings_fp, 'w') as configfile:
        config.write(configfile)
        
    logger = logging.getLogger('package_release')
    logger.setLevel('INFO')
    logger.info(f'The package version has to be updated to {version}')
    
    return 
```

```
set_current_package_version('9.9.9', settings_fp)
get_current_package_version(settings_fp)
```




    '9.9.9'



<br>

Before we move on we'll change the version on file back to the original

```
set_current_package_version(original_version, settings_fp)
get_current_package_version(settings_fp)
```




    '1.0.2'



<br>

Finally we need to ensure the CLI app is available when the module is loaded.

N.b. we've included the condition `'__file__' in globals()` to make sure this isn't when inside the notebook

```
#exports
if __name__ == '__main__' and '__file__' in globals():
    app()
```
