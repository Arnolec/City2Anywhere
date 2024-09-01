import os
import pandas as pd

from app.analyzer import Analyzer
from app.analyzerCalendar import AnalyzerCalendar
from app.analyzerSNCF import AnalyzerCalendarDates
from app.analyzerEuro import AnalyzerCalendarDates_not_parent


def load_class_analyzer(path: str) -> Analyzer:
    check_file = os.path.isfile(os.path.join("Data", path, "calendar.txt"))
    if check_file:
        return AnalyzerCalendar(path)
    else:
        if path not in ["TGV, TER, INTERCITE"]:
            return AnalyzerCalendarDates_not_parent(path)
        else:
            return AnalyzerCalendarDates(path)


def find_best_name(names):
    # Idée facile mais pas efficace, à remplacer : on garde le nom le plus court
    return min(names, key=len)


def round_to_precision_003(value: float) -> float:
    return round(value / 0.03) * 0.03


def round_to_precision_005(value: float) -> float:
    return round(value / 0.05) * 0.05


def round_to_precision_007(value: float) -> float:
    return round(value / 0.07) * 0.07
