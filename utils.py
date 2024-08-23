import os
from Analyzer import Analyzer
from AnalyzerSNCF import Analyzer_calendar_dates
from Analyzer_calendar import AnalyzerCalendar


def load_class_analyzer(path: str) -> Analyzer:
    check_file = os.path.isfile(os.path.join("Data", path, "calendar.txt"))
    if check_file:
        return AnalyzerCalendar(path)
    else:
        return Analyzer_calendar_dates(path)
