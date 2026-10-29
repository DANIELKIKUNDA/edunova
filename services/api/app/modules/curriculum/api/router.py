from fastapi import APIRouter,HTTPException,Query
from app.modules.curriculum.application.service import CurriculumCatalogService
router=APIRouter()
service=CurriculumCatalogService()
@router.get('/medicine')
def medicine_catalog(): return service.catalog()
@router.get('/medicine/semesters')
def medicine_semesters(cycle:str|None=None,level:str|None=None): return service.semesters(cycle=cycle,level=level)
@router.get('/medicine/semesters/{semester}')
def medicine_semester(semester:int):
 x=service.semester(semester)
 if not x: raise HTTPException(404,'curriculum_semester_not_found')
 return x
@router.get('/medicine/search')
def medicine_search(q:str=Query(min_length=1,max_length=120)): return service.find_entries(q)
@router.get('/medicine/audit')
def medicine_audit(): return service.audit()
