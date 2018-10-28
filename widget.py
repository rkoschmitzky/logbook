from Qt import QtWidgets

from handler import LogbookHandler


class LogbookWidget(QtWidgets.QWidget):
    """ A simple widget that makes log reading more pleasant. """

    LOG_LEVELS = {
        "debug": 10,
        "info": 20,
        "warning": 30,
        "error": 40,
        "critical": 50
    }
    LABEL_WIDTH = 70
    LEVEL_BUTTON_WIDTH = 60
    
    _handler = LogbookHandler()

    def __init__(self, parent=None):
        super(LogbookWidget, self).__init__(parent)

        self._filter_regex = ".*"
        self._setup_ui()
        self._setup_connections()

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

        for level_name, level_value in self.LOG_LEVELS.items():
            button = QtWidgets.QPushButton(level_name)
            button.setStyleSheet("""QWidget {border: none} """)
            button.setFixedWidth(self.LEVEL_BUTTON_WIDTH)
            level_buttons_layout.addWidget(button)

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

        records_list = QtWidgets.QListWidget()
        records_list.setStyleSheet("""QWidget {border: none} """)
        records_layout.addWidget(records_list)

        clear_records_button = QtWidgets.QPushButton("Clear Records")
        clear_records_button.setFixedWidth(90)

        records_layout.addWidget(clear_records_button)

    def _setup_connections(self):
        self.handler.signals.signal_record.connect(self._add_record)

    def _add_record(self, log_record):
        """ adds a LogRecord object to the records list widget"""
        print log_record

    @property
    def handler(self):
        return self._handler


if __name__ == '__main__':
    import logging

    application = QtWidgets.QApplication([])
    logbook = LogbookWidget()
    logbook.show()

    LOG = logging.getLogger("test")
    logging.basicConfig(level=logging.DEBUG)

    LOG.addHandler(logbook.handler)
    LOG.info("Hello Logbook")

    application.exec_()
