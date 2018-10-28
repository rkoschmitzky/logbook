import logging

from collections import OrderedDict
from functools import partial

from Qt import QtWidgets, QtCore

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
    
    _handler = LogbookHandler()

    def __init__(self, parent=None):
        super(LogbookWidget, self).__init__(parent)

        self._threadpool = QtCore.QThreadPool()
        self._filter_regex = ".*"
        self._setup_ui()
        self._setup_signals()

    def _setup_ui(self):
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
                "QToolButton:checked {background-color: rgba(%s, %s, %s, %s);}" % (
                    self.LEVEL_COLORS[level_name][0],
                    self.LEVEL_COLORS[level_name][1],
                    self.LEVEL_COLORS[level_name][2],
                    self.LEVEL_COLORS[level_name][3],
                )
            )

            level_buttons_layout.addWidget(button)
            self.level_buttons.append(button)

        level_buttons_layout.addWidget(v_separator)

        background_highlight_toggle = QtWidgets.QCheckBox("Coloring")
        level_buttons_layout.addWidget(background_highlight_toggle)

        level_buttons_layout.addStretch()

        options_layout.addWidget(h_separator)

        # === filter field ===
        filter_layout = QtWidgets.QHBoxLayout()
        options_layout.addLayout(filter_layout)

        filter_label = QtWidgets.QLabel("Filter: ")
        filter_label.setFixedWidth(self.LABEL_WIDTH)
        filter_layout.addWidget(filter_label)

        filter_edit = QtWidgets.QLineEdit(self._filter_regex)
        filter_edit.setStyleSheet("""QWidget {border: none} """)
        filter_layout.addWidget(filter_edit)

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
        self.handler.signals.signal_record.connect(self.add_record)
        for level_button in self.level_buttons:
            level_button.toggled.connect(
                partial(self._on_level_button_toggled, level_button)
            )
        self.clear_records_button.clicked.connect(self.records_list.clear)

    def _on_level_button_toggled(self, button, state):
        """ handles show states of LogRecordItems """
        for row in xrange(self.records_list.count()):
            item = self.records_list.item(row)
            if item.level == button.property("level_name"):
                if state:
                    self.records_list.setItemHidden(item, False)
                else:
                    self.records_list.setItemHidden(item, True)

    def add_record(self, log_record):
        """ adds a LogRecord object to the records list widget"""

        def _add_item():
            item = LogRecordItem(log_record)
            self.records_list.addItem(item)
            self.records_list.scrollToItem(item)

        worker = Worker(_add_item)
        self._threadpool.start(worker)

    @property
    def handler(self):
        return self._handler


if __name__ == '__main__':
    import logging
    from multiprocessing.pool import ThreadPool
    pool = ThreadPool(1)

    def emit(*args):
        for i in range(10):
            LOG.info("info %s" % i)
        for i in range(5):
            LOG.debug("debug %s" % i)
        for i in range(3):
            LOG.warning("warning %s" % i)
        for i in range(2):
            LOG.error("error %s", i)

    application = QtWidgets.QApplication([])
    logbook = LogbookWidget()
    logbook.show()

    LOG = logging.getLogger("test")
    LOG.setLevel(logging.DEBUG)

    LOG.addHandler(logbook.handler)
    pool.map(emit, range(1))

    application.exec_()