# Logbook
A simple Qt widget to improve the plesure of reading log messages.

### Table of Contents

- [Logging](#logging)
- [The Interface](#the-logbook-graphical-user-interface)
- [Communication](#let-your-loggers-communicate-with-the-logbook)
- [Customization](#customization)
  - [Attributes](#attributes)
  - [Formatting](#recorditems-formatting)
  - [Exception ToolTips](#exception-tooltips)
  - [Custom Signals](#custom-signals)

### Logging
The Logging module is awesome! However if multiple people/tools setup numerous loggers and handlers it can make reading and filtering log messages hard.

-----

### The Logbook graphical user interface
The Logbook user interface is focused on making it simple for you to find information quickly.

<img src="https://github.com/rkoschmitzky/logbook/blob/master/.graphics/user_interface.gif" width="400">

It exposes
- checkable buttons for defined log levels
- checkbox to enable corresponding background colors per record item
- a field to add a filter regex
- the actual list of catched log records
- a button to clear this list

-----

### Let your loggers communicate with the Logbook
To catch log records you only have to attach the provided Logbook handlers to your loggers of choice.

```python
import logging

from logbook import LogbookWidget

# acquire a logger
my_logger = logging.getLogger("foo")
my_logbook = LogbookWidget()

# the `handler` property holds the required handler
my_logger.attachHandler(my_logbook.handler)
```
As soon as your handler was attached, the log records will be catched within a background thread to keep the UI respsonsive.

<img src="https://github.com/rkoschmitzky/logbook/blob/master/.graphics/record_addition.gif" width="400">

-----

### Customization

#### Attributes

| Attribute               | Type     | Description
|:------------------------|:---------|:------------
| `LEVEL_BUTTON_WIDTH`    | `int`    | Defines the width of the level buttons.
| `LOG_LEVELS`            | `list`   | A list with levels that will correspond to the checkable level buttons that will be added. default: `["debug", "info", "warning", "error", "critical"]`. When changed the `LEVEL_VALUES` and `LEVEL_COLORS` attribute needs to be adjusted too.
| `LEVEL_VALUES`          | `dict`   | A dictionary with corresponding level numbers to the defined `LOG_LEVELS`. default: `{"debug": 10, "info": 20, "warning": 30, error: "40", "critical": 50}`.
| `LEVEL_COLORS`          | `dict`   | A dictionary with coreresponding colors to the defined `LOG_LEVELS`. Expects RGB values from 0-255 and an optional alpha value from 0-100. default: `        "debug": (255, 255, 255, 100), "info": (204, 236, 242, 100), "warning": (152, 210, 217, 100), "error": (223, 57, 57, 100), "critical": (182, 60, 66, 100)}`
| `INITIAL_FILTER_REGEX`  | `str`   | A regular expression that will be used when launching the logbook.
| `IGNORE_FORMATTER`      | `bool`  | If a formatter was set to the handler it can be explicitly ignored by setting this to `True`. This means, the formatter will not be considered as the record item's text. Instead it will use the `LogRecord.msg` directly.
| `EXCEPTION_FORMATTER`   | `logging.Formatter` |  A formatter instance that will be used to format the exc_info tuple that will be dispayed inside the ToolTips of recorditems.

#### Recorditems Formatting
By default the logbook handlers doesn't use a formatting. It will use the `LogRecord.msg` attribute as the recorditem's text.
A formatter can be set easily by using the `handler` property on the logbook instance.

```python
my_logbook.handler.setFormatter("%(asctime)s %(message)s")
```

#### Exception ToolTips
Whenever a catched `LogRecord` includes an `exc_info` tuple, it will display a ToolTip with the underlying exception.
By default `logging.Formatter().formatException(record)` will be used to format the exception. However a custom formatter can be set via `EXCEPTION_FORMATTER` attribute.

```python
from logging import Formatter

from logbook import LogbookWidget

class MyExceptionFormatter(Formatter):
    def formatException(exc_info):
        # setup the actual formatting here

# override the formatter used to format the underlying exception info tuple
LogbookWidget.EXCEPTION_FORMATTER = MyExceptionFormatter()
```
<img src="https://github.com/rkoschmitzky/logbook/blob/master/.graphics/exception_tooltip.gif" width="400">

#### Custom Signals
The following signals can be connected to extend functionality of the loogbook.

```python
# example shows how to call a custom QMenu
# the event gets triggered via RMB click on a recorditem
# it will pass the global cursor position and underlying `LogRecord` instance

class MyMenu(QtWidgets.QMenu):
    def __init__(self, pos, record):
        super(MyMenu, self).__init__()
        self.addAction("{}| {}".format(record.levelname, record.msg))
        self.exec_(pos)

my_logbook.signals.record_context_request.connect(MyMenu)
```
<img src="https://github.com/rkoschmitzky/logbook/blob/master/.graphics/context_menu.gif" width="400">