from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class SignalKind(StrEnum):
    ATTENDANCE='attendance'; PERFORMANCE='performance'; SUBMISSION='submission'; DELIVERY='delivery'
class SignalSeverity(StrEnum): INFO='info'; WATCH='watch'; HIGH='high'

@dataclass(frozen=True, slots=True)
class InstitutionalSignal:
    kind:SignalKind; severity:SignalSeverity; subject_type:str; subject_id:str; title:str; explanation:str; evidence:tuple[str,...]

@dataclass(frozen=True, slots=True)
class MetricDefinition:
    code:str; version:int; label:str; description:str; numerator:str; denominator:str|None; privacy_class:str='institutional'

METRICS=(
 MetricDefinition('attendance.rate',1,'Taux de présence','Présent + retard sur enregistrements de présence clôturés','present + late','all attendance records'),
 MetricDefinition('attendance.absence_rate',1,"Taux d'absence",'Absences non justifiées sur enregistrements de présence clôturés','absent','all attendance records'),
 MetricDefinition('assignments.submission_rate',1,'Taux de remise','Étudiants ayant au moins une remise sur opportunités de remise','students with submission','active enrollments × published/closed assignments'),
 MetricDefinition('gradebook.pass_rate',1,'Taux de réussite','Résultats complets atteignant le seuil du gradebook','complete passing results','complete results'),
 MetricDefinition('teaching.completion_rate',1,'Réalisation des séances','Séances terminées sur séances non annulées','completed teaching sessions','planned + completed teaching sessions'),
)
