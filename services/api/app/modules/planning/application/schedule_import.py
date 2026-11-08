from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from app.modules.planning.domain.model import TimetableEntry


@dataclass(frozen=True, slots=True)
class ParsedScheduleRow:
    weekday: int
    start_minute: int
    end_minute: int
    label: str
    confidence: float


class ScheduleTextParser:
    """Conservative parser for OCR/text timetables.

    It never publishes automatically: parsed rows are drafts to be reviewed by the
    student before insertion. This avoids silently corrupting an OCR'd timetable.
    """

    DAYS = {
        'lundi':1,'lun':1,'mardi':2,'mar':2,'mercredi':3,'mer':3,
        'jeudi':4,'jeu':4,'vendredi':5,'ven':5,'samedi':6,'sam':6,'dimanche':7,'dim':7,
    }
    line_re = re.compile(
        r"^\s*(?P<day>[A-Za-zÀ-ÿ]+)\s+(?P<h1>\d{1,2})[:hH](?P<m1>\d{2})\s*[-–—]\s*(?P<h2>\d{1,2})[:hH](?P<m2>\d{2})\s+(?P<label>.+?)\s*$"
    )

    @staticmethod
    def _norm(value: str) -> str:
        value = unicodedata.normalize('NFKD', value)
        return ''.join(ch for ch in value if not unicodedata.combining(ch)).casefold()

    def parse(self, text: str) -> tuple[ParsedScheduleRow, ...]:
        rows: list[ParsedScheduleRow] = []
        for raw in text.splitlines():
            match = self.line_re.match(raw)
            if not match:
                continue
            day = self.DAYS.get(self._norm(match.group('day')))
            if day is None:
                continue
            h1,m1,h2,m2 = (int(match.group(k)) for k in ('h1','m1','h2','m2'))
            start,end = h1*60+m1,h2*60+m2
            if not 0 <= start < end <= 1440:
                continue
            label = match.group('label').strip()
            if not label:
                continue
            rows.append(ParsedScheduleRow(day,start,end,label,.95))
        return tuple(rows)
