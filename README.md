# Jira Automation master
Service to automate jira simple issues, the idea is to implement a service that will read classes from the adapter folder and can be customized for the types of tickets that you have.<br><br>
You can connect on Jira and use any tool for automation that you want, so the purpose of this repository is to provide a base program for the automation of repetitive tasks.

<div align="center">

[Prerequisites](#prerequisites) •
[Configuration](#configuration) •
[Usage](#usage)

</div>

## Prerequisites
----
As listed on the file [requirements.txt](requirements.txt) the following libraries are needed:
```python
dataclasses
jira
pandas
cx_Oracle
```

You can install it using the following command:
```shell
$ pip install -r requirements.txt
```
## Configuration
----
The configuration is located on the folder `config` and the configuration is exemplifiyed by the files [`config.ini.example`](config/config.ini.example) and [config_handlers.json.example](config/config_handlers.json.example).

### config.ini
The file `config.ini` is the main configuration file for the service, for the options related to the configuration of database connection, Jira connection and some options related to the execution of the service as demonstrated below, so before the start the file `config.ini` must exists.
```ini
[JIRA]
user = rubens.ferreira
password = admin
server = http://jira.local
jql_master = createdDate >= startOfMonth() and project = TESTE and key = "TESTE-2866" and assignee in (EMPTY) order by updated DESC

[ORACLE]
user = system
password = oracle
host = localhost
port = 1521
sid = orcl

[SETUP]
process_queue_size = 10
sleep_time = 1
mail_list_lookup_code = JIRA_AUTOMATION_MASTER
```

### config_handlers.json
The file `config_handlers.json` is the configuration file for the import of the handler classes. <br><br>
As demontrated below, the file must contain the keys `plugins` and `handlers`, on key plugins the value should be a list with the imports that are contained on the folder handlers, the key handlers is the connection between the summary pattern of the ticket and the Handler class.<br>

```json
{
    "plugins": [
        "handlers.user_creation_handler",
        "handlers.update_xpto_handler"
    ],
    "handlers":{    
        "TESTE: Registrar usuario": "UserCreationHandler",
        "TESTE: Atualização de Xpto": "UpdateXptoHandler"
    }
}
```

## Usage
----
The service can be executed using the following command:
```shell
$ python main.py
```



[comment]: <> (# TODO: create a setup file)
[comment]: <> (# TODO: create a docker setup)
[comment]: <> (# TODO: create a docker-compose file)
