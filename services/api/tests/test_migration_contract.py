import re
from pathlib import Path

from app.shared.infrastructure.database import Base
# Import mapped modules so SQLAlchemy metadata is populated.
from app.modules.assistant.infrastructure import sqlalchemy_knowledge  # noqa: F401
from app.modules.commerce.infrastructure import sqlalchemy_repo  # noqa: F401
from app.modules.commerce.application import campus_paid_checkout  # noqa: F401
from app.modules.commerce.application import campus_offers  # noqa: F401
from app.modules.platform_governance.infrastructure import institution_registry, central_operations  # noqa: F401
from app.modules.campus_services.infrastructure import event_registration_repo  # noqa: F401
from app.modules.identity.infrastructure import sqlalchemy_repo as identity_sqlalchemy  # noqa: F401
from app.modules.sync.infrastructure import sqlalchemy_repo as sync_sqlalchemy  # noqa: F401
from app.modules.library.infrastructure import sqlalchemy_repo as library_sqlalchemy  # noqa: F401
from app.modules.engagement.infrastructure import sqlalchemy_repo as engagement_sqlalchemy  # noqa: F401
from app.modules.editorial.infrastructure import sqlalchemy_repo as editorial_sqlalchemy  # noqa: F401
from app.modules.ingestion.infrastructure import sqlalchemy_repo as ingestion_sqlalchemy  # noqa: F401
from app.modules.publication.infrastructure import sqlalchemy_repo as publication_sqlalchemy  # noqa: F401
from app.modules.learning_experience.infrastructure import sqlalchemy_repo as learning_sqlalchemy  # noqa: F401
from app.modules.adaptive_learning.infrastructure import sqlalchemy_repo as adaptive_sqlalchemy  # noqa: F401
from app.modules.study_orchestration.infrastructure import sqlalchemy_repo as planner_sqlalchemy  # noqa: F401
from app.modules.assessment.infrastructure import sqlalchemy_repo as assessment_sqlalchemy  # noqa: F401
from app.modules.remediation.infrastructure import sqlalchemy_repo as remediation_sqlalchemy  # noqa: F401
from app.modules.knowledge_graph.infrastructure import sqlalchemy_repo as knowledge_graph_sqlalchemy  # noqa: F401
from app.modules.tutor.infrastructure import sqlalchemy_repo as tutor_sqlalchemy  # noqa: F401
from app.modules.campus.infrastructure import sqlalchemy_repo as campus_sqlalchemy  # noqa: F401
from app.modules.academic_catalog.infrastructure import sqlalchemy_repo as academic_catalog_sqlalchemy  # noqa: F401
from app.modules.jury.infrastructure import sqlalchemy_repo as jury_sqlalchemy  # noqa: F401
from app.modules.placements.infrastructure import sqlalchemy_repo as placements_sqlalchemy  # noqa: F401
from app.modules.research.infrastructure import sqlalchemy_repo as research_sqlalchemy  # noqa: F401
from app.modules.student_success.infrastructure import sqlalchemy_repo as student_success_sqlalchemy  # noqa: F401
from app.modules.service_desk.infrastructure import sqlalchemy_repo as service_desk_sqlalchemy  # noqa: F401
from app.modules.official_documents.infrastructure import sqlalchemy_repo as official_documents_sqlalchemy  # noqa: F401
from app.modules.academic_delivery.infrastructure import sqlalchemy_repo as academic_delivery_sqlalchemy  # noqa: F401
from app.modules.teaching.infrastructure import sqlalchemy_repo as teaching_sqlalchemy  # noqa: F401
from app.modules.assignments.infrastructure import sqlalchemy_repo as assignments_sqlalchemy  # noqa: F401
from app.modules.gradebook.infrastructure import sqlalchemy_repo as gradebook_sqlalchemy  # noqa: F401
from app.modules.campus_operations.infrastructure import sqlalchemy_repo as campus_operations_sqlalchemy  # noqa: F401
from app.modules.campus_services.infrastructure import sqlalchemy_repo as campus_services_sqlalchemy  # noqa: F401
from app.modules.campus_services.infrastructure import alumni_repo as campus_alumni_sqlalchemy  # noqa: F401
from app.modules.campus_services.infrastructure import physical_library_repo as campus_physical_library_sqlalchemy  # noqa: F401
from app.modules.institutional_analytics.infrastructure import sqlalchemy_repo as institutional_analytics_sqlalchemy  # noqa: F401
from app.modules.trust_governance.infrastructure import sqlalchemy_repo as trust_governance_sqlalchemy  # noqa: F401
from app.modules.content_factory.infrastructure import sqlalchemy_repo as factory_sqlalchemy  # noqa: F401
from app.modules.pilot_readiness.infrastructure import sqlalchemy_repo as pilot_readiness_sqlalchemy  # noqa: F401
from app.modules.platform_governance.infrastructure import sqlalchemy_repo as platform_sqlalchemy  # noqa: F401
from app.modules.admissions_catalog.infrastructure import sqlalchemy_repo as admissions_catalog_sqlalchemy  # noqa: F401
from app.modules.applications.infrastructure import sqlalchemy_repo as applications_sqlalchemy  # noqa: F401
from app.modules.admissions_center.infrastructure import sqlalchemy_repo as admissions_center_sqlalchemy  # noqa: F401
from app.modules.student_records.infrastructure import sqlalchemy_repo as student_records_sqlalchemy  # noqa: F401
from app.modules.student_finance.infrastructure import sqlalchemy_repo as student_finance_sqlalchemy  # noqa: F401
from app.modules.payment_gateway.infrastructure import sqlalchemy_repo as payment_gateway_sqlalchemy  # noqa: F401
from app.modules.pedagogical_intelligence import infrastructure as pedagogical_intelligence_sqlalchemy  # noqa: F401
from app.shared.infrastructure import audit as audit_sqlalchemy  # noqa: F401


CREATE_TABLE = re.compile(r"CREATE TABLE(?: IF NOT EXISTS)?\s+([a-zA-Z0-9_]+)", re.I)


def test_production_migrations_cover_all_sqlalchemy_tables_exactly_once():
    migration_dir = Path(__file__).resolve().parents[1] / "migrations"
    files = sorted(migration_dir.glob("*.sql"))
    assert [p.name for p in files] == [
        "0001_identity_commerce.sql",
        "0002_commerce_hardening_v0_6_1.sql",
        "0003_assistant_rag_v0_7_0.sql",
        "0004_sync_library_v0_8_0.sql",
        "0005_sync_hardening_v0_8_1.sql",
        "0006_engagement_notifications_v0_10_0.sql",
        "0007_editorial_governance_v0_12_0.sql",
        "0008_editorial_hardening_v0_12_1.sql",
        "0009_ingestion_industrielle_v0_13_0.sql",
        "0010_ingestion_manifest_integrity_v0_13_1.sql",
        "0011_content_factory_v0_14_0.sql",
        "0012_academic_publication_v0_15_0.sql",
        "0013_publication_hardening_v0_15_1.sql",
        "0014_learning_experience_v0_16_0.sql",
        "0015_learning_experience_hardening_v0_16_1.sql",
        "0016_adaptive_learning_v0_17_0.sql",
        "0017_adaptive_learning_hardening_v0_17_1.sql",
        "0018_adaptive_study_planner_v0_18_0.sql",
        "0019_study_planner_hardening_v0_18_1.sql",
        "0020_assessment_exam_engine_v0_19_0.sql",
        "0021_assessment_hardening_v0_19_1.sql",
        "0022_assessment_cognitive_intelligence_v0_19_2.sql",
        "0023_question_intelligence_factory_v0_19_3.sql",
        "0024_intelligent_remediation_v0_20_0.sql",
        "0025_remediation_tutor_intelligence_v0_20_1.sql",
        "0026_remediation_orchestration_hardening_v0_20_2.sql",
        "0027_knowledge_graph_v0_21_0.sql",
        "0028_knowledge_graph_extraction_governance_v0_21_1.sql",
        "0029_knowledge_graph_snapshot_impact_v0_21_2.sql",
        "0030_tutor_2_v0_22_0.sql",
        "0031_campus_core_v0_23_0.sql",
        "0032_campus_core_enterprise_hardening_v0_23_1.sql",
        "0033_teaching_course_delivery_v0_24_0.sql",
        "0034_teaching_delivery_maximal_v0_24_1.sql",
        "0035_teaching_industrial_closure_v0_24_2.sql",
        "0036_assignments_submissions_grading_v0_25_0.sql",
        "0037_assignment_workflow_groups_autograding_v0_25_1.sql",
        "0038_assignment_results_industrial_closure_v0_25_2.sql",
        "0039_academic_gradebook_results_v0_26_0.sql",
        "0040_gradebook_maximal_v0_26_1.sql",
        "0041_gradebook_industrial_closure_v0_26_2.sql",
        "0042_campus_operations_attendance_v0_27_0.sql",
        "0043_attendance_signed_proximity_v0_27_1.sql",
        "0044_campus_operations_complete_v0_27_2.sql",
        "0045_institutional_analytics_v0_28_0.sql",
        "0046_institutional_analytics_snapshots_v0_28_1.sql",
        "0047_institutional_pedagogical_intelligence_v0_28_2.sql",
        "0048_trust_privacy_security_governance_v0_29_0.sql",
        "0049_commerce_mobile_money_campus_licensing_v0_30_0.sql",
        "0050_pilot_readiness_v0_32_0.sql",
        "0051_platform_governance_roles_v0_34_0.sql",
        "0052_platform_governance_audit_indexes_v0_34_0.sql",
        "0053_academic_curriculum_foundation_v0_36_0.sql",
        "0054_admissions_public_catalog_v0_37_0.sql",
        "0055_academic_admissions_deepening_v0_37_1.sql",
        "0056_candidate_applications_v0_38_0.sql",
        "0057_resumable_application_uploads_v0_38_0.sql",
        "0058_application_integrity_and_admission_center_v0_39_0.sql",
        "0059_admissions_center_max_depth_v0_39_1.sql",
        "0060_student_records_enrollment_v0_40_0.sql",
        "0061_student_records_max_depth_v0_40_1.sql",
        "0062_student_finance_v0_41_0.sql",
        "0063_student_finance_max_depth_v0_41_1.sql",
        "0064_mobile_money_gateway_v0_42_0.sql",
        "0065_mobile_money_max_depth_v0_42_1.sql",
        "0066_academic_delivery_consolidation_v0_43_0.sql",
        "0067_jury_deliberations_foundation_v0_44_0.sql",
        "0068_jury_commission_governance_v0_44_1.sql",
        "0069_placements_foundation_v0_45_0.sql",
        "0070_research_workflow_v0_45_1.sql",
        "0071_student_service_desk_v0_46_0.sql",
        "0072_official_documents_v0_47_0.sql",
        "0073_official_documents_provenance_v0_47_1.sql",
        "0074_published_academic_results_provenance_v0_47_2.sql",
        "0075_official_document_issuer_snapshot_v0_47_4.sql",
        "0076_official_document_lifecycle_v0_47_5.sql",
        "0077_official_document_template_governance_v0_47_6.sql",
        "0078_student_success_foundation_v0_48_0.sql",
        "0079_student_success_early_warning_v0_48_1.sql",
        "0080_student_success_action_plans_v0_48_2.sql",
        "0081_student_success_reassessment_v0_48_3.sql",
        "0082_pedagogical_objective_evidence_v0_49_2.sql",
        "0083_assessment_auto_sum_evidence_contract_v0_49_11.sql",
        "0084_assessment_grading_snapshot_v0_49_12.sql",
        "0085_institutional_analytics_temporal_release_v0_50_7.sql",
        "0086_campus_physical_resources_v0_51_0.sql",
        "0087_campus_physical_library_v0_51_1.sql",
        "0088_campus_library_circulation_policy_v0_51_2.sql",
        "0089_campus_library_tenant_policy_v0_51_3.sql",
        "0090_campus_library_copy_incidents_v0_51_4.sql",
        "0091_campus_resource_maintenance_v0_51_5.sql",
        "0092_campus_event_registrations_v0_51_6.sql",
        "0093_campus_academic_resource_allocations_v0_51_8.sql",
        "0094_campus_alumni_v0_51_8.sql",
        "0095_campus_teaching_room_allocations_v0_51_8.sql",
        "0096_platform_institution_controls_v0_52_3.sql",
        "0097_platform_support_tickets_v0_52_7.sql",
        "0098_campus_commercial_offers_v0_53_14.sql",
        "0099_campus_paid_orders_v0_53_15.sql",
    ]
    occurrences: dict[str, int] = {}
    for file in files:
        for table in CREATE_TABLE.findall(file.read_text()):
            occurrences[table] = occurrences.get(table, 0) + 1
    mapped = set(Base.metadata.tables)
    assert set(occurrences) == mapped
    assert all(count == 1 for count in occurrences.values())
