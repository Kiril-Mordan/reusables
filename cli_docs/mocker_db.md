``` bash
mockerdb --help
```

```
Usage: mockerdb [OPTIONS] COMMAND [ARGS]...

  Package Auto Assembler CLI tool.

Options:
  --help  Show this message and exit.

Commands:
  init-config  Initialize config file for api
```


MockerDB API can be run through [`package-auto-assembler`](https://kiril-mordan.github.io/reusables/package_auto_assembler/) functionality using the following command:

```
paa run-api-routes --package mocker_db
```

To change default config values, a file named `.mockerdb.api.config` needs to be located in path the `paa` command is run. By initializing config, you can see defailt config and edit it.

``` bash
mockerdb init-config  --help
```

```
Usage: mockerdb init-config [OPTIONS]

  Initialize config file for api

Options:
  --help  Show this message and exit.
```

