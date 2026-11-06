import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.shared.security.http_headers import SecurityHeadersMiddleware
from app.shared.infrastructure.observability import RequestContextMiddleware, configure_logging
from app.version import __version__
from app.modules.operations.api.router import router as operations_router

from app.modules.readiness.api.router import router as readiness_router
from app.modules.pedagogy.api.router import router as pedagogy_router
from app.modules.planning.api.router import router as planning_router
from app.modules.identity.api.router import router as identity_router
from app.modules.commerce.api.router import router as commerce_router
from app.modules.assistant.api.router import router as assistant_router
from app.modules.sync.api.router import router as sync_router
from app.modules.library.api.router import router as library_router
from app.modules.delivery.api.router import router as delivery_router
from app.modules.engagement.api.router import router as engagement_router
from app.modules.analytics.api.router import router as analytics_router
from app.modules.editorial.api.router import router as editorial_router
from app.modules.ingestion.api.router import router as ingestion_router
from app.modules.content_factory.api.router import router as content_factory_router
from app.modules.publication.api.router import router as publication_router
from app.modules.learning_experience.api.router import router as learning_experience_router
from app.modules.adaptive_learning.api.router import router as adaptive_learning_router
from app.modules.study_orchestration.api.router import router as study_orchestration_router
from app.modules.assessment.api.router import router as assessment_router
from app.modules.remediation.api.router import router as remediation_router
from app.modules.knowledge_graph.api.router import router as knowledge_graph_router
from app.modules.tutor.api.router import router as tutor_router
from app.modules.campus.api.router import router as campus_router
from app.modules.teaching.api.router import router as teaching_router
from app.modules.assignments.api.router import router as assignments_router
from app.modules.gradebook.api.router import router as gradebook_router
from app.modules.campus_services.api.router import router as campus_services_router
from app.modules.campus_services.api.physical_library_router import router as physical_library_router
from app.modules.campus_operations.api.router import router as campus_operations_router
from app.modules.institutional_analytics.api.router import router as institutional_analytics_router
from app.modules.trust_governance.api.router import router as trust_governance_router
from app.modules.platform_governance.api.router import router as platform_governance_router
from app.modules.curriculum.api.router import router as curriculum_router
from app.modules.academic_catalog.api.router import router as academic_catalog_router
from app.modules.admissions_catalog.api.router import router as admissions_catalog_router
from app.modules.applications.api.router import router as applications_router
from app.modules.admissions_center.api.router import router as admissions_center_router
from app.modules.student_records.api.router import router as student_records_router
from app.modules.student_finance.api.router import router as student_finance_router
from app.modules.payment_gateway.api.router import router as payment_gateway_router
from app.modules.placements.api.router import router as placements_router
from app.modules.research.api.router import router as research_router
from app.modules.student_success.api.router import router as student_success_router
from app.modules.pedagogical_intelligence.api.router import router as pedagogical_intelligence_router
from app.modules.service_desk.api.router import router as service_desk_router
from app.modules.official_documents.api.router import router as official_documents_router
from app.modules.jury.api.router import router as jury_router
from app.modules.academic_delivery.api.router import router as academic_delivery_router

configure_logging()

app = FastAPI(
    title="EduNova API",
    version=__version__,
    description="Backend hexagonal du compagnon universitaire EduNova.",
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-EduNova-Sandbox-Signature"],
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "edunova-api", "version": __version__}


app.include_router(operations_router, prefix="/v1/operations", tags=["operations"])
app.include_router(identity_router, prefix="/v1/identity", tags=["identity"])
app.include_router(commerce_router, prefix="/v1/commerce", tags=["commerce"])
app.include_router(assistant_router, prefix="/v1/assistant", tags=["assistant"])
app.include_router(sync_router, prefix="/v1/sync", tags=["sync"])
app.include_router(library_router, prefix="/v1/library", tags=["library"])
app.include_router(delivery_router, prefix="/v1/delivery", tags=["delivery"])
app.include_router(readiness_router, prefix="/v1/readiness", tags=["readiness"])
app.include_router(pedagogy_router, prefix="/v1/pedagogy", tags=["pedagogy"])
app.include_router(planning_router, prefix="/v1/planning", tags=["planning"])

app.include_router(engagement_router, prefix="/v1/engagement", tags=["engagement"])
app.include_router(analytics_router, prefix="/v1/analytics", tags=["analytics"])

app.include_router(editorial_router, prefix="/v1/editorial", tags=["editorial"])
app.include_router(ingestion_router, prefix="/v1/ingestion", tags=["ingestion"])
app.include_router(content_factory_router, prefix="/v1/content-factory", tags=["content-factory"])

app.include_router(publication_router, prefix="/v1/publication", tags=["publication"])

app.include_router(learning_experience_router, prefix="/v1/learning", tags=["learning-experience"])
app.include_router(adaptive_learning_router, prefix="/v1/adaptive-learning", tags=["adaptive-learning"])
app.include_router(study_orchestration_router, prefix="/v1/study-planner", tags=["study-planner"])

app.include_router(assessment_router, prefix="/v1/assessment", tags=["assessment"])
app.include_router(remediation_router, prefix="/v1/remediation", tags=["remediation"])

app.include_router(knowledge_graph_router, prefix="/v1/knowledge-graph", tags=["knowledge-graph"])

app.include_router(tutor_router, prefix="/v1/tutor", tags=["tutor-2"])

app.include_router(campus_router, prefix="/v1/campus", tags=["campus-core"])

app.include_router(teaching_router, prefix="/v1/teaching", tags=["teaching-course-delivery"])

app.include_router(assignments_router, prefix="/v1/assignments", tags=["assignments-submissions-grading"])

app.include_router(gradebook_router, prefix="/v1/gradebook", tags=["assessments-gradebook-results"])

app.include_router(campus_operations_router, prefix="/v1/campus-operations", tags=["campus-operations-attendance"])
app.include_router(campus_services_router, prefix="/v1/campus-services", tags=["campus-physical-services"])
app.include_router(physical_library_router, prefix="/v1/campus-services", tags=["campus-physical-library"])
app.include_router(institutional_analytics_router, prefix="/v1/institutional-analytics", tags=["institutional-analytics"])

app.include_router(trust_governance_router, prefix="/v1/trust", tags=["trust-privacy-governance"])

app.include_router(platform_governance_router, prefix="/v1/platform", tags=["platform-governance"])
app.include_router(curriculum_router, prefix="/v1/curricula", tags=["curricula"])
app.include_router(academic_catalog_router, prefix="/v1/academic", tags=["academic-catalog"])
app.include_router(admissions_catalog_router, prefix="/v1/admissions-catalog", tags=["admissions-public-catalog"])
app.include_router(applications_router, prefix="/v1/admissions", tags=["candidate-applications"])
app.include_router(admissions_center_router, prefix="/v1/admission-center", tags=["admission-center"])

app.include_router(student_records_router, prefix="/v1/student-records", tags=["student-records-enrollment"])
app.include_router(student_finance_router, prefix="/v1/student-finance", tags=["student-finance"])

app.include_router(payment_gateway_router, prefix="/v1/payments", tags=["mobile-money-payments"])
app.include_router(academic_delivery_router, prefix="/v1/academic-delivery", tags=["academic-delivery-consolidation"])

app.include_router(jury_router, prefix="/v1/jury", tags=["jury-deliberations"])

app.include_router(placements_router, prefix="/v1/placements", tags=["placements-internships"])

app.include_router(research_router, prefix="/v1/research", tags=["research-thesis-defense"])
app.include_router(service_desk_router, prefix="/v1/service-desk", tags=["student-digital-service-desk"])

app.include_router(official_documents_router, prefix="/v1/official-documents", tags=["official-documents"])

app.include_router(student_success_router, prefix="/v1/student-success", tags=["student-success"])
app.include_router(pedagogical_intelligence_router, prefix="/v1/pedagogical-intelligence", tags=["pedagogical-intelligence"])
