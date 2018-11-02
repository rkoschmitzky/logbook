import logging

from collections import OrderedDict
from difflib import context_diff
from functools import partial
import re

from Qt import (QtGui,
                QtWidgets,
                QtCore
                )

from handler import LogbookHandler


class Worker(QtCore.QRunnable):
    def __init__(self, func, *func_args, **func_kwargs):
        super(Worker, self).__init__()
        self.func = func
        self.func_args = func_args
        self.func_kwargs = func_kwargs

    @QtCore.Slot()
    def run(self):
        return self.func(*self.func_args, **self.func_kwargs)


class LogRecordItem(QtWidgets.QListWidgetItem):
    def __init__(self, record):
        super(LogRecordItem, self).__init__(record.msg)

        self._record = record

    @property
    def level(self):
        return self._record.levelname.lower()

    @property
    def record(self):
        return self._record


class LogbookWidget(QtWidgets.QWidget):
    """ A simple widget that makes log reading more pleasant. """

    LOG_LEVELS = [
        "debug",
        "info",
        "warning",
        "error",
        "critical"
    ]

    LEVEL_VALUES = OrderedDict(
        sorted(
            {
                LOG_LEVELS[0]: logging.DEBUG,
                LOG_LEVELS[1]: logging.INFO,
                LOG_LEVELS[2]: logging.WARNING,
                LOG_LEVELS[3]: logging.ERROR,
                LOG_LEVELS[4]: logging.CRITICAL
            }.items(),
            key=lambda _: _[1]
        )
    )

    LEVEL_COLORS = {
        LOG_LEVELS[0]: (255, 255, 255, 100),
        LOG_LEVELS[1]: (204, 236, 242, 100),
        LOG_LEVELS[2]: (152, 210, 217, 100),
        LOG_LEVELS[3]: (223, 57, 57, 100),
        LOG_LEVELS[4]: (182, 60, 66, 100)
    }

    LABEL_WIDTH = 70
    LEVEL_BUTTON_WIDTH = 60

    INITIAL_FILTER_REGEX = r""

    _handler = LogbookHandler()

    def __init__(self, parent=None):
        super(LogbookWidget, self).__init__(parent)

        # if somebody wants to customize the levels ensure he does it properly
        # to avoid issues downstream
        self._validate_levels()

        self._filter_regex = re.compile(r"{}".format(self.INITIAL_FILTER_REGEX))

        self._threadpool = QtCore.QThreadPool()
        self._filter_regex_compiled = re.compile(self.INITIAL_FILTER_REGEX)
        self._colors = {k: QtGui.QColor(*v) for k, v in self.LEVEL_COLORS.items()}
        self._setup_ui()
        self._setup_signals()

    @classmethod
    def _validate_levels(cls):
        """ ensure we allow flexible level addition but give proper guidance """
        _missing_key_msg = "Missing key '{}' in '{}' attribute."
        _keys_number_msg = "Level name entries in '{}' attribute not matching: \n {}."
        _type_msg = "Given level for level name '{}' must be of type {}. Got {}."
        _invalid_rgba_msg = "Given value {} is not a proper RGB(A) color using values 0-255[0-100]."

        # check for equal keys
        _level_names_sorted = sorted(cls.LOG_LEVELS)
        _level_values_keys_sorted = sorted(cls.LEVEL_VALUES.keys())
        _level_colors_keys_sorted = sorted(cls.LEVEL_COLORS.keys())
        if _level_names_sorted != _level_values_keys_sorted:
            raise ValueError(_keys_number_msg.format(
                "LEVEL_VALUES",
                # todo: maybe not helpful enough
                "".join(context_diff(_level_names_sorted, _level_values_keys_sorted))
                )
            )
        if _level_names_sorted != _level_colors_keys_sorted:
            raise ValueError(_keys_number_msg.format(
                "LEVEL_COLORS",
                "".join(context_diff(_level_names_sorted, _level_colors_keys_sorted))
                )
            )

        for level_name in cls.LOG_LEVELS:
            if level_name not in cls.LEVEL_VALUES:
                raise KeyError(_missing_key_msg.format(level_name, "LEVEL_VALUES"))
            if level_name not in cls.LEVEL_COLORS:
                raise KeyError(_missing_key_msg.format(level_name, "LEVEL_COLORS"))
            
            # check log level values
            if not isinstance(cls.LEVEL_VALUES[level_name], int):
                raise TypeError(_type_msg.format(
                        level_name,
                        "int",
                        type(cls.LEVEL_VALUES[level_name])
                    )
                )
            if cls.LEVEL_VALUES[level_name] < 1:
                raise ValueError("A log level for level name '{}' must be defined with a value <= 1.".format(
                        level_name    
                    )
                )
            # check log level colors
            if not isinstance(cls.LEVEL_COLORS[level_name], (list, tuple)):
                raise TypeError(_type_msg.format(
                        level_name,
                        "tuple or int",
                        type(cls.LEVEL_COLORS[level_name])
                    )
                )
            
            # check RGBA values
            if [True, True, True] != [_ >= 0 and _ <= 255 for _ in cls.LEVEL_COLORS[level_name][:3]]:
                raise ValueError(_invalid_rgba_msg.format(
                    cls.LEVEL_COLORS[level_name]
                    )
                )
            if len(cls.LEVEL_COLORS[level_name]) == 4:
                if cls.LEVEL_COLORS[level_name][-1] <= 0 or cls.LEVEL_COLORS[level_name][-1] > 100:
                    raise ValueError(_invalid_rgba_msg.format(
                        cls.LEVEL_COLORS[level_name]
                        )
                    )
            elif len(cls.LEVEL_COLORS[level_name]) > 4:
                raise ValueError(_invalid_rgba_msg.format(cls.LEVEL_COLORS[level_name]))

    def _setup_ui(self):
        """ build the actual ui """
        h_separator = QtWidgets.QFrame()
        h_separator.setFrameStyle(QtWidgets.QFrame.HLine | QtWidgets.QFrame.Raised)
        v_separator = QtWidgets.QFrame()
        v_separator.setFrameStyle(QtWidgets.QFrame.VLine | QtWidgets.QFrame.Raised)

        container_layout = QtWidgets.QVBoxLayout(self)

        self.setLayout(container_layout)

        options_group = QtWidgets.QGroupBox("Options")
        container_layout.addWidget(options_group)

        # === level buttons section ===
        options_layout = QtWidgets.QVBoxLayout()
        options_group.setLayout(options_layout)

        level_buttons_layout = QtWidgets.QHBoxLayout()

        options_layout.addLayout(level_buttons_layout)

        levels_label = QtWidgets.QLabel("Levels: ")
        levels_label.setFixedWidth(self.LABEL_WIDTH)
        level_buttons_layout.addWidget(levels_label)

        self.level_buttons = []
        for level_name, level_value in self.LEVEL_VALUES.items():
            button = QtWidgets.QToolButton()
            button.setText(level_name)
            button.setCheckable(True)
            button.setFixedHeight(20)
            button.setProperty("level_name", level_name)
            button.setChecked(True)
            button.setFixedWidth(self.LEVEL_BUTTON_WIDTH)

            button.setStyleSheet(
                "QToolButton:checked {background-color: rgba(%s, %s, %s, %s)}" % (
                    self.LEVEL_COLORS[level_name][0],
                    self.LEVEL_COLORS[level_name][1],
                    self.LEVEL_COLORS[level_name][2],
                    self.LEVEL_COLORS[level_name][3],
                )
            )

            level_buttons_layout.addWidget(button)
            self.level_buttons.append(button)

        level_buttons_layout.addWidget(v_separator)

        self.background_coloring_checkbox = QtWidgets.QCheckBox("Coloring")
        level_buttons_layout.addWidget(self.background_coloring_checkbox)

        level_buttons_layout.addStretch()

        options_layout.addWidget(h_separator)

        # === filter field ===
        filter_layout = QtWidgets.QHBoxLayout()
        options_layout.addLayout(filter_layout)

        filter_label = QtWidgets.QLabel("Filter: ")
        filter_label.setFixedWidth(self.LABEL_WIDTH)
        filter_layout.addWidget(filter_label)

        self.filter_edit = QtWidgets.QLineEdit(self.INITIAL_FILTER_REGEX)
        self.filter_edit.setStyleSheet("""QWidget {border: none} """)
        filter_layout.addWidget(self.filter_edit)

        records_group = QtWidgets.QGroupBox("Records")
        container_layout.addWidget(records_group)

        # === records list ===
        records_layout = QtWidgets.QVBoxLayout()
        records_group.setLayout(records_layout)

        self.records_list = QtWidgets.QListWidget()
        self.records_list.setStyleSheet("""QWidget {border: none} """)
        records_layout.addWidget(self.records_list)

        self.clear_records_button = QtWidgets.QPushButton("Clear Records")
        self.clear_records_button.setFixedWidth(90)

        records_layout.addWidget(self.clear_records_button)

    def _setup_signals(self):
        """ setup all Qt signals """
        self.handler.signals.signal_record.connect(self.add_record)
        for level_button in self.level_buttons:
            level_button.toggled.connect(
                partial(self._on_level_button_toggled, level_button)
            )
        self.clear_records_button.clicked.connect(self.records_list.clear)
        self.background_coloring_checkbox.toggled.connect(self._toggle_coloring)
        self.filter_edit.textChanged.connect(self._on_filter_changed)

    def _on_level_button_toggled(self, button, state):
        """ handles show states of LogRecordItems """
        self._revert_filter_states()
        for item in self._record_items:
            self._filter(item)

    def _on_filter_changed(self, text):
        """ performs a regex match on all record items and filter out items that will not match """
        self._filter_regex = re.compile(r"{}".format(text))
        self._revert_filter_states()
        for item in self._record_items:
            self._filter(item)

    def _revert_filter_states(self):
        for item in self._record_items:
            self.records_list.setItemHidden(item, False)

    def _toggle_coloring(self, state):
        """ activates or deactivates background coloring for record items """
        for item in self._record_items:
            self._set_background_color(item)

    def _set_background_color(self, item):
        """ actives or deactivates background coloring
        
        This is based on the check state of the coloring checkbox.
        """
        if self.background_coloring_checkbox.isChecked():
            item.setBackgroundColor(self._colors[item.level])
        else:
            item.setBackgroundColor(QtGui.QColor(0, 0, 0, 0))

    def _filter(self, item):
        """ set visibility state based on filter regex match and active levels """
        _match = self._filter_regex.search(item.text())
        if not _match or item.level not in self._active_levels:
            self.records_list.setItemHidden(item, True)

    @property
    def _active_levels(self):
        return [_.property("level_name") for _ in self.level_buttons if _.isChecked()]

    @property
    def _record_items(self):
        """ all available record items """
        for row in xrange(self.records_list.count()):
            yield self.records_list.item(row)

    def add_record(self, log_record):
        """ adds a LogRecord object to the records list widget"""

        def _add_item():
            item = LogRecordItem(log_record)
            self.records_list.addItem(item)
            self._filter(item)
            self._set_background_color(item)

        worker = Worker(_add_item)
        self._threadpool.start(worker)

    @property
    def handler(self):
        """ THE handler somebody has to add to the logger he wants to catch messages for.

        Examples:
            >>> import logging
            >>> my_logger = logging.getLogger("cool.stuff")
            >>> logbook = LogbookWidget()
            >>> my_logger.addHandler(logbook.handler)
        """
        return self._handler


if __name__ == '__main__':
    import logging
    import time
    from multiprocessing.pool import ThreadPool
    pool = ThreadPool(1)

    def emit(*args):
        for i in range(2):
            LOG.debug("debug %s" % i)
        for i in range(5):
            LOG.info("info %s" % i)
        for i in range(1):
            LOG.warning("warning %s" % i)
        for i in range(2):
            LOG.error("error %s" % i)
        time.sleep(0.3)

    application = QtWidgets.QApplication([])
    logbook = LogbookWidget()
    logbook.show()

    LOG = logging.getLogger("test")
    LOG.setLevel(logging.DEBUG)

    LOG.addHandler(logbook.handler)
    pool.map_async(emit, range(50))

    application.exec_()
