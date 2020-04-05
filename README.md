[![Build Status](https://travis-ci.com/rkoschmitzky/logbook.svg?branch=master)](https://travis-ci.com/rkoschmitzky/logbook) [![Coverage Status](https://coveralls.io/repos/github/rkoschmitzky/logbook/badge.svg?branch=master)](https://coveralls.io/github/rkoschmitzky/logbook?branch=master) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Logbook
A simple Qt widget to improve the pleasure of reading log messages.

### Table of Contents
- [Logging](#logging)
- [Prerequisites](#prerequisites)
- [The Interface](#the-logbook-graphical-user-interface)
- [Communication](#let-your-loggers-communicate-with-the-logbook)
- [Customization](#customization)
  - [Attributes](#attributes)
  - [Formatting](#recorditems-formatting)
  - [Custom Levels](#custom-levels)
  - [Exception ToolTips](#exception-tooltips)
  - [Custom Signals](#custom-signals)

### Logging
The Logging module is awesome! However, if multiple people/tools setup numerous loggers and handlers, it can make reading and filtering log messages hard.

-----

### Prerequisites
You need to ensure the [Qt.py](https://github.com/mottosso/Qt.py) wrapper is available, which supports PySide2, PyQt5, PySide and PyQt4.

-----

### The Logbook graphical user interface
The Logbook user interface is focused on making it simple for you, to search for information quickly.

<img src="https://github.com/rkoschmitzky/logbook/blob/master/.graphics/user_interface.gif" width="400">

It exposes
- an arbitrary number of checkable buttons for defined log levels
- a checkbox to enable corresponding background colors per record item
- a field for a filter regular expression
- the actual list that holds the catched log records
- a button to clear this list

-----

### Let your loggers communicate with the Logbook
To catch log records you only have to attach the provided Logbook handler to your loggers of choice.

```python
import logging

from logbook import LogbookWidget

# acquire a logger
my_logger = logging.getLogger("foo")
my_logbook_instance = LogbookWidget()

# the `handler` property holds the required handler
my_logger.addHandler(my_logbook_instance.handler)

# show the logbook gui
my_logbook_instance.show()
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
| `INITIAL_FILTER_REGEX`  | `str`    | A regular expression that will be used when launching the logbook.
| `IGNORE_FORMATTER`      | `bool`   | If a formatter was set to the handler, it can be explicitly ignored by setting this to `True`. This means, the formatter will not be considered as the recorditem's text. Instead it will only use the `LogRecord.msg` directly.
| `EXCEPTION_FORMATTER`   | `logging.Formatter` |  A formatter instance that will be used to format the `exc_info` tuple that will be dispayed inside the ToolTips of recorditems.

#### Recorditems Formatting
By default the logbook handlers doesn't use a formatting. It will use the `LogRecord.msg` attribute as the recorditem's text.
A formatter can be set easily by using the `handler` property on the logbook instance.

```python
my_logbook.handler.setFormatter("%(asctime)s %(message)s")
```

#### Custom Levels
You can provide custom levels for the Logbook.
```python
from logbook import LogbookWidget

# the order inside the `LOG_LEVELS` list matters, the buttons will be added from left to right
# we would like to introduce the "paranoid" level, that is below `logging.DEBUG`
LogbookWidget.LOG_LEVELS.insert(0, "paranoid")
# a corresponding level and color must be defined
LogbookWidget.LEVEL_VALUES["paranoid"] = 5
# an alpha value is optional
LogbookWidget.LEVEL_COLORS["paranoid"] = (125, 80, 125)
```

<img src="https://github.com/rkoschmitzky/logbook/blob/master/.graphics/custom_level.gif" width="400">

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
# the event gets triggered via RMB click on a LogRecordItem
# it will pass the global cursor position, a list of underlying/selected `LogRecordItem` instances 
# and the LogRecordsListWidget

class MyMenu(QtWidgets.QMenu):
    def __init__(self, pos, record_items, records_list_widget):
        super(MyMenu, self).__init__()
        for record_item in record_items:
            self.addAction("{}| {}".format(record_item.record.levelname, record_item.record.msg))
        self.exec_(pos)

my_logbook_instance.signals.record_context_request.connect(MyMenu)
```
<img src="https://github.com/rkoschmitzky/logbook/blob/master/.graphics/context_menu.gif" width="400">