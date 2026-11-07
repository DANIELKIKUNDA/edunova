from __future__ import annotations

from app.modules.assistant.application.service import AssistantService
from app.modules.assistant.domain.model import ModelProfile
from app.modules.assistant.infrastructure.memory import InMemoryAssistantCache, StaticModelCatalog, FakeLlmProvider, CommerceCreditGate
from app.modules.assistant.infrastructure.redis_cache import RedisAssistantCache
from app.modules.assistant.infrastructure.scientific import SympyScientificSolver
from app.modules.assistant.infrastructure.budget import InMemoryDailyAiBudgetGate, RedisDailyAiBudgetGate
from app.modules.assistant.infrastructure.sqlalchemy_knowledge import SqlAlchemyKnowledgeRepository
from app.modules.assistant.infrastructure.provider_config import load_external_ai_providers

from app.modules.sync.application.service import SyncService
from app.modules.sync.infrastructure.sqlalchemy_repo import SqlAlchemySyncRepository
from app.modules.library.application.service import LibraryService
from app.modules.library.infrastructure.sqlalchemy_repo import SqlAlchemyLibraryRepository
from app.modules.library.infrastructure.access import CommerceLibraryAccess, HmacResourceDelivery
from app.modules.delivery.application.service import DeliveryService
from app.modules.delivery.infrastructure.storage import LocalFileDeliveryStorage, S3PresignedDeliveryStorage
from app.modules.engagement.application.service import EngagementService
from app.modules.engagement.infrastructure.sqlalchemy_repo import SqlAlchemyEngagementRepository, SqlAlchemyPushRegistry
from app.modules.engagement.infrastructure.push import DisabledPushSender, FirebaseAdminPushSender
from app.modules.analytics.application.service import AnalyticsService

from app.modules.editorial.application.service import EditorialService
from app.modules.editorial.infrastructure.sqlalchemy_repo import SqlAlchemyEditorialRepository
from app.modules.editorial.infrastructure.library_projector import LibraryPublicationProjector
from app.modules.editorial.domain.model import EditorialMember, EditorialRole

from app.modules.ingestion.application.service import IngestionService
from app.modules.ingestion.application.preflight import PreflightPolicy, PreflightValidator
from app.modules.ingestion.infrastructure.sqlalchemy_repo import SqlAlchemyIngestionRepository
from app.modules.ingestion.infrastructure.storage import LocalStagingStorage, S3StagingStorage
from app.modules.ingestion.infrastructure.security import DisabledMalwareScanner, ClamAvTcpScanner
from app.modules.ingestion.infrastructure.editorial_bridge import EditorialIngestionBridge
from app.modules.content_factory.application.service import ContentFactoryService
from app.modules.content_factory.infrastructure.sqlalchemy_repo import SqlAlchemyContentFactoryRepository
from app.modules.publication.application.service import PublicationService
from app.modules.publication.infrastructure.sqlalchemy_repo import SqlAlchemyPublicationRepository
from app.modules.learning_experience.application.service import LearningExperienceService
from app.modules.learning_experience.infrastructure.sqlalchemy_repo import SqlAlchemyLearningRepository
from app.modules.adaptive_learning.application.service import AdaptiveLearningService
from app.modules.adaptive_learning.infrastructure.sqlalchemy_repo import SqlAlchemyAdaptiveLearningRepository
from app.modules.study_orchestration.application.service import StudyPlannerService
from app.modules.study_orchestration.infrastructure.sqlalchemy_repo import SqlAlchemyStudyPlannerRepository
from app.modules.assessment.application.service import AssessmentService
from app.modules.assessment.infrastructure.sqlalchemy_repo import SqlAlchemyAssessmentRepository
from app.modules.remediation.application.service import RemediationService
from app.modules.remediation.infrastructure.sqlalchemy_repo import SqlAlchemyRemediationRepository
from app.modules.knowledge_graph.application.service import KnowledgeGraphService
from app.modules.knowledge_graph.infrastructure.sqlalchemy_repo import SqlAlchemyKnowledgeGraphRepository
from app.modules.tutor.application.service import TutorService
from app.modules.tutor.infrastructure.sqlalchemy_repo import SqlAlchemyTutorRepository
from app.modules.campus.application.service import CampusService
from app.modules.campus.infrastructure.sqlalchemy_repo import SqlAlchemyCampusRepository
from app.modules.teaching.application.service import TeachingService
from app.modules.teaching.infrastructure.sqlalchemy_repo import SqlAlchemyTeachingRepository
from app.modules.assignments.application.service import AssignmentService
from app.modules.assignments.infrastructure.sqlalchemy_repo import SqlAlchemyAssignmentRepository
from app.modules.gradebook.application.service import GradebookService
from app.modules.gradebook.infrastructure.sqlalchemy_repo import SqlAlchemyGradebookRepository
from app.modules.campus_services.application.service import CampusServicesService
from app.modules.campus_services.application.alumni_service import CampusAlumniService
from app.modules.campus_services.infrastructure.alumni_repo import SqlCampusAlumniRepository
from app.modules.campus_services.infrastructure.sqlalchemy_repo import SqlCampusServicesRepository
from app.modules.campus_services.application.physical_library_service import PhysicalLibraryService
from app.modules.campus_services.infrastructure.physical_library_repo import SqlPhysicalLibraryRepository
from app.modules.campus_services.infrastructure.event_registration_repo import SqlCampusEventRegistrationRepository
from app.modules.campus_services.application.event_registration_service import CampusEventRegistrationService
from app.modules.campus_services.infrastructure.campus_alerts_repo import SqlCampusAlertsRepository
from app.modules.campus_services.application.campus_alerts_service import CampusAlertsService
from app.modules.campus_operations.application.service import CampusOperationsService
from app.modules.campus_operations.infrastructure.sqlalchemy_repo import SqlAlchemyCampusOperationsRepository
from app.modules.institutional_analytics.application.service import InstitutionalAnalyticsService
from app.modules.institutional_analytics.infrastructure.sqlalchemy_repo import SqlAlchemyInstitutionalAnalyticsRepository
from app.modules.trust_governance.application.service import TrustGovernanceService
from app.modules.trust_governance.infrastructure.sqlalchemy_repo import SqlTrustGovernanceRepository
from app.modules.trust_governance.infrastructure.mfa import MfaVault
from app.modules.platform_governance.application.service import PlatformGovernanceService
from app.modules.platform_governance.infrastructure.sqlalchemy_repo import SqlPlatformGovernanceRepository
from app.modules.platform_governance.infrastructure.institution_registry import InstitutionControlRepository
from app.modules.platform_governance.infrastructure.central_operations import CentralOperationsRepository, PlatformSupportTicketRow
from app.modules.academic_catalog.application.service import AcademicCatalogService
from app.modules.academic_catalog.infrastructure.sqlalchemy_repo import SqlAcademicCatalogRepository
from app.modules.admissions_catalog.application.service import AdmissionsCatalogService
from app.modules.admissions_catalog.infrastructure.sqlalchemy_repo import SqlAdmissionsCatalogRepository
from app.modules.applications.application.service import ApplicationService
from app.modules.applications.infrastructure.sqlalchemy_repo import SqlApplicationRepository
from app.modules.admissions_center.application.service import AdmissionCenterService
from app.modules.admissions_center.infrastructure.sqlalchemy_repo import SqlAdmissionReviewRepository
from app.modules.student_records.application.service import StudentRecordService
from app.modules.student_records.infrastructure.sqlalchemy_repo import SqlStudentRecordRepository
from app.modules.student_finance.application.service import StudentFinanceService
from app.modules.student_finance.infrastructure.sqlalchemy_repo import SqlStudentFinanceRepository
from app.modules.payment_gateway.application.service import PaymentGatewayService
from app.modules.payment_gateway.infrastructure.sqlalchemy_repo import SqlPaymentGatewayRepository
from app.modules.placements.application.service import PlacementService
from app.modules.placements.infrastructure.sqlalchemy_repo import SqlPlacementRepository
from app.modules.research.application.service import ResearchService
from app.modules.research.infrastructure.sqlalchemy_repo import SqlResearchRepository
from app.modules.student_success.application.service import StudentSuccessService
from app.modules.student_success.infrastructure.sqlalchemy_repo import SqlSuccessRepository
from app.modules.service_desk.application.service import ServiceDeskService
from app.modules.service_desk.infrastructure.sqlalchemy_repo import SqlServiceDeskRepository
from app.modules.official_documents.infrastructure.sqlalchemy_repo import SqlOfficialDocumentRepository
from app.modules.official_documents.application.service import OfficialDocumentService
from app.modules.jury.application.service import JuryService
from app.modules.jury.infrastructure.sqlalchemy_repo import SqlJuryRepository
from app.modules.academic_delivery.application.service import AcademicDeliveryService
from app.modules.academic_delivery.infrastructure.sqlalchemy_repo import SqlAcademicDeliveryRepository
from app.modules.curriculum.application.service import CurriculumCatalogService
from app.modules.pedagogical_intelligence.infrastructure import SqlObjectiveEvidenceRepository
from app.modules.pedagogical_intelligence.application.service import CanonicalPedagogicalIntelligenceService
import os
from datetime import UTC, datetime

from app.modules.commerce.application.service import CommerceService
from app.modules.commerce.domain.model import Money, Plan
from app.modules.commerce.infrastructure.memory import FakeMobileMoneyProvider, StaticPlanCatalog
from app.modules.commerce.infrastructure.sqlalchemy_repo import (
    SqlAlchemyAiWalletRepository,
    SqlAlchemyEntitlementRepository,
    SqlAlchemyPaymentRepository,
    SqlAlchemyReceiptRepository,
    SqlAlchemyWebhookInbox,
    SqlAlchemyCommerceSettlement,
    SqlAlchemyCommercialRepository,
)
from app.modules.commerce.application.commercial_service import CommercialService
from app.modules.identity.application.auth_context import Authenticator
from app.modules.identity.application.service import IdentityService
from app.modules.identity.infrastructure.security import Argon2PasswordHasher, JwtTokenIssuer
from app.modules.identity.infrastructure.memory import InMemoryVerificationSender, DisabledVerificationSender
from app.modules.identity.infrastructure.sqlalchemy_repo import SqlAlchemyAccountRepository, SqlAlchemySessionRepository, SqlAlchemyRecoveryChallengeRepository
from app.shared.infrastructure.database import Base, build_engine, build_session_factory
from app.shared.infrastructure.audit import SqlAuditSink
from app.shared.security.rate_limit import InMemoryRateLimiter, RedisRateLimiter
from app.modules.operations.application.health import OperationalHealthService
from app.modules.operations.infrastructure.probes import database_probe, redis_probe
from app.version import __version__


def _now():
    return datetime.now(UTC)


PRODUCTION_LIKE_ENVS = frozenset({"production", "staging", "preproduction"})


def is_production_like_env(value: str) -> bool:
    return value.strip().lower() in PRODUCTION_LIKE_ENVS


class Runtime:
    def __init__(self) -> None:
        self.env = os.getenv("EDUNOVA_ENV", "development").lower()
        self.production_like = is_production_like_env(self.env)
        self.engine = build_engine()
        self.sessions = build_session_factory(self.engine)
        self.redis = None
        if self.production_like:
            import redis
            self.redis = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
            self.rate_limiter = RedisRateLimiter(self.redis)
        else:
            self.rate_limiter = InMemoryRateLimiter()
        # Production schema must be migrated before API rollout; auto-create is dev/test only.
        if not self.production_like:
            Base.metadata.create_all(self.engine)

        self.audit = SqlAuditSink(self.sessions)
        self.operations = OperationalHealthService({"database": database_probe(self.engine), "redis": redis_probe(self.redis)}, version=__version__)
        # LOT 22 — institutional multi-tenant Campus Core.
        self.campus_repo = SqlAlchemyCampusRepository(self.sessions)
        self.campus = CampusService(self.campus_repo, _now, audit=self.audit)
        self.academic_catalog_repo = SqlAcademicCatalogRepository(self.sessions)
        self.academic_catalog = AcademicCatalogService(self.academic_catalog_repo, self.campus, self.campus_repo, CurriculumCatalogService(), _now, audit=self.audit)
        self.admissions_catalog_repo = SqlAdmissionsCatalogRepository(self.sessions)
        self.admissions_catalog = AdmissionsCatalogService(self.admissions_catalog_repo, self.campus, self.campus_repo, self.academic_catalog_repo, _now, audit=self.audit)
        self.teaching_repo = SqlAlchemyTeachingRepository(self.sessions)
        self.teaching = TeachingService(self.teaching_repo, self.campus_repo, _now, audit=self.audit)
        self.assignment_repo = SqlAlchemyAssignmentRepository(self.sessions)
        self.assignments = AssignmentService(self.assignment_repo, self.campus_repo, self.teaching_repo, _now, audit=self.audit)
        self.gradebook_repo = SqlAlchemyGradebookRepository(self.sessions)
        self.gradebook = GradebookService(self.gradebook_repo, self.campus_repo, self.teaching_repo, self.assignment_repo, _now, audit=self.audit)
        self.campus_services_repo = SqlCampusServicesRepository(self.sessions)
        self.campus_services = CampusServicesService(self.campus_services_repo, self.campus_repo, _now, audit=self.audit)
        self.campus_alumni = CampusAlumniService(
            SqlCampusAlumniRepository(self.sessions), self.campus_repo, _now, audit=self.audit)
        self.physical_library_repo = SqlPhysicalLibraryRepository(self.sessions)
        self.physical_library = PhysicalLibraryService(self.physical_library_repo, self.campus_repo, _now, audit=self.audit)
        self.campus_operations_repo = SqlAlchemyCampusOperationsRepository(self.sessions)
        attendance_secret = os.getenv('ATTENDANCE_QR_SECRET')
        if self.production_like and not attendance_secret:
            raise RuntimeError('ATTENDANCE_QR_SECRET is mandatory in production')
        proximity_secret = os.getenv('ATTENDANCE_PROXIMITY_SECRET')
        if self.production_like and not proximity_secret:
            raise RuntimeError('ATTENDANCE_PROXIMITY_SECRET is mandatory in production')
        self.campus_operations = CampusOperationsService(self.campus_operations_repo, self.campus_repo, self.teaching_repo, _now, audit=self.audit, secret=attendance_secret, proximity_secret=proximity_secret)
        self.campus_event_registration_repo = SqlCampusEventRegistrationRepository(self.sessions)
        self.campus_events = CampusEventRegistrationService(
            self.campus_event_registration_repo, self.campus_services,
            self.campus_operations, _now, audit=self.audit)
        self.campus_alerts = CampusAlertsService(
            SqlCampusAlertsRepository(self.sessions), self.campus_services, _now)
        self.institutional_analytics_repo = SqlAlchemyInstitutionalAnalyticsRepository(self.sessions)
        self.institutional_analytics = InstitutionalAnalyticsService(self.institutional_analytics_repo, self.campus_repo, self.teaching_repo, audit=self.audit)
        self.trust_governance_repo = SqlTrustGovernanceRepository(self.sessions)
        mfa_key = os.getenv('MFA_ENCRYPTION_KEY')
        if self.production_like and not mfa_key:
            raise RuntimeError('MFA_ENCRYPTION_KEY is mandatory in production')
        self.mfa_vault = MfaVault(mfa_key or 'development-mfa-key-change-me-32-characters')
        self.trust_governance = TrustGovernanceService(self.trust_governance_repo, _now, self.mfa_vault)
        self.platform_governance_repo = SqlPlatformGovernanceRepository(self.sessions)
        self.platform_institution_controls = InstitutionControlRepository(self.sessions)
        self.platform_central_operations = CentralOperationsRepository(self.sessions)
        self.platform_governance = PlatformGovernanceService(self.platform_governance_repo, _now, audit=self.audit)
        platform_owner = os.getenv('PLATFORM_OWNER_ACCOUNT_ID')
        if platform_owner:
            self.platform_governance.bootstrap_owner(platform_owner)
        self.tutor_repo = SqlAlchemyTutorRepository(self.sessions)
        self.tutor = TutorService(self.tutor_repo, _now)
        self.accounts = SqlAlchemyAccountRepository(self.sessions)
        self.refresh_sessions = SqlAlchemySessionRepository(self.sessions)
        self.password_hasher = Argon2PasswordHasher()
        self.recovery_challenges = SqlAlchemyRecoveryChallengeRepository(self.sessions)
        self.verification_sender = InMemoryVerificationSender() if self.env in {"development", "test"} else DisabledVerificationSender()
        secret = os.getenv("JWT_SECRET")
        if not secret and self.production_like:
            raise RuntimeError("JWT_SECRET is mandatory in production")
        secret = secret or "development-secret-change-me-32-characters-minimum"
        self.token_issuer = JwtTokenIssuer(secret=secret)
        self.identity = IdentityService(
            accounts=self.accounts,
            sessions=self.refresh_sessions,
            hasher=self.password_hasher,
            tokens=self.token_issuer,
            now=_now,
            recovery=self.recovery_challenges,
            verification_sender=self.verification_sender,
        )
        self.authenticator = Authenticator(accounts=self.accounts, tokens=self.token_issuer)

        self.payments = SqlAlchemyPaymentRepository(self.sessions)
        self.entitlements = SqlAlchemyEntitlementRepository(self.sessions)
        self.ai_wallets = SqlAlchemyAiWalletRepository(self.sessions)
        self.receipts = SqlAlchemyReceiptRepository(self.sessions)
        self.webhook_inbox = SqlAlchemyWebhookInbox(self.sessions)
        self.commerce_settlement = SqlAlchemyCommerceSettlement(self.sessions)
        self.commercial_repo = SqlAlchemyCommercialRepository(self.sessions)
        self.commercial = CommercialService(self.commercial_repo, self.campus_repo, _now, audit=self.audit)
        from app.modules.commerce.application.campus_offers import CampusOfferService
        self.campus_offers = CampusOfferService(self.sessions, self.platform_governance, _now)
        from app.modules.commerce.application.campus_paid_checkout import CampusPaidCheckoutService
        self.campus_paid = CampusPaidCheckoutService(self.sessions, self.commercial, {}, _now)

        price = int(os.getenv("PREMIUM_PRICE_CDF", "3000"))
        ai_credits = int(os.getenv("PREMIUM_AI_CREDITS", "25"))
        products = [Plan(code="premium-30d", name="Premium", price=Money(price), kind="subscription", duration_days=30, included_ai_credits=ai_credits, max_personal_documents=100, offline_enabled=True)]
        pack10_price = int(os.getenv("AI_PACK_10_PRICE_CDF", "0"))
        pack25_price = int(os.getenv("AI_PACK_25_PRICE_CDF", "0"))
        if pack10_price > 0:
            products.append(Plan(code="ai-pack-10", name="Pack IA 10", price=Money(pack10_price), kind="ai_pack", duration_days=0, included_ai_credits=10, max_personal_documents=0, offline_enabled=False))
        if pack25_price > 0:
            products.append(Plan(code="ai-pack-25", name="Pack IA 25", price=Money(pack25_price), kind="ai_pack", duration_days=0, included_ai_credits=25, max_personal_documents=0, offline_enabled=False))
        self.catalog = StaticPlanCatalog(products)
        sandbox = FakeMobileMoneyProvider()
        self.payment_providers = {sandbox.name: sandbox} if self.env in {"development", "test"} else {}
        self.campus_paid.providers = self.payment_providers
        self.commerce = CommerceService(
            payments=self.payments,
            entitlements=self.entitlements,
            wallets=self.ai_wallets,
            receipts=self.receipts,
            inbox=self.webhook_inbox,
            catalog=self.catalog,
            providers=self.payment_providers,
            settlement=self.commerce_settlement,
            now=_now,
        )

        # LOT 6 — Assistant/RAG. Shared-course knowledge is server-side; personal
        # document context is supplied ephemerally by the client and never indexed here.
        self.knowledge = SqlAlchemyKnowledgeRepository(self.sessions)
        self.assistant_cache = RedisAssistantCache(self.redis) if self.redis is not None else InMemoryAssistantCache()
        profiles = []
        providers = {}
        if self.env in {"development", "test"}:
            flash = FakeLlmProvider("sandbox-ai", "flash")
            reasoning = FakeLlmProvider("sandbox-ai", "reasoning")
            providers[(flash.name, flash.model)] = flash
            providers[(reasoning.name, reasoning.model)] = reasoning
            profiles = [
                ModelProfile(provider="sandbox-ai",model="flash",quality_tier=1,cost_units=1,max_context_tokens=8000,capabilities=frozenset({"chat"})),
                ModelProfile(provider="sandbox-ai",model="reasoning",quality_tier=2,cost_units=2,max_context_tokens=16000,capabilities=frozenset({"chat","reasoning","high_reliability"})),
            ]
        else:
            providers, loaded_profiles = load_external_ai_providers()
            profiles.extend(loaded_profiles)
        self.assistant_models = StaticModelCatalog(tuple(profiles))
        if self.production_like:
            daily_budget = int(os.getenv("AI_DAILY_CREDIT_BUDGET", "0"))
            self.assistant_global_budget = RedisDailyAiBudgetGate(self.redis, daily_limit_units=daily_budget) if daily_budget > 0 else RedisDailyAiBudgetGate(self.redis, daily_limit_units=0)
            allow_personal_remote = os.getenv("AI_ALLOW_PERSONAL_DOCUMENTS", "false").strip().lower() in {"1", "true", "yes"}
        else:
            self.assistant_global_budget = InMemoryDailyAiBudgetGate()
            allow_personal_remote = True
        self.assistant_personal_documents_allowed = allow_personal_remote
        self.assistant = AssistantService(
            retriever=self.knowledge,
            providers=providers,
            models=self.assistant_models,
            cache=self.assistant_cache,
            credits=CommerceCreditGate(self.commerce),
            scientific_solver=SympyScientificSolver(),
            global_budget=self.assistant_global_budget,
            allow_personal_remote=allow_personal_remote,
        )


        # LOT 7 — lightweight cloud synchronization and shared EduNova library.
        self.sync_repository = SqlAlchemySyncRepository(self.sessions)
        self.sync = SyncService(self.sync_repository, now=_now)
        self.library_repository = SqlAlchemyLibraryRepository(self.sessions)
        delivery_secret = os.getenv("RESOURCE_DELIVERY_SECRET")
        if not delivery_secret and self.production_like:
            raise RuntimeError("RESOURCE_DELIVERY_SECRET is mandatory in production")
        delivery_secret = delivery_secret or "development-resource-secret-change-me"
        self.library_access = CommerceLibraryAccess(self.commerce)
        self.resource_delivery = HmacResourceDelivery(delivery_secret)
        self.library = LibraryService(
            repository=self.library_repository,
            access=self.library_access,
            delivery=self.resource_delivery,
        )

        # LOT 8 — object delivery. Production prefers direct short-lived S3/R2 URLs
        # so the small VPS never becomes the bandwidth bottleneck. Development/test
        # use an app-owned local object root with real HTTP Range support.
        if self.production_like:
            storage_backend = os.getenv("CONTENT_STORAGE_BACKEND", "s3").strip().lower()
            if storage_backend != "s3":
                raise RuntimeError("CONTENT_STORAGE_BACKEND must be s3 in production")
            bucket = os.getenv("CONTENT_STORAGE_BUCKET")
            if not bucket:
                raise RuntimeError("CONTENT_STORAGE_BUCKET is mandatory in production")
            self.delivery_storage = S3PresignedDeliveryStorage(
                bucket=bucket,
                endpoint_url=os.getenv("CONTENT_STORAGE_ENDPOINT"),
                region=os.getenv("CONTENT_STORAGE_REGION"),
            )
        else:
            self.delivery_storage = LocalFileDeliveryStorage(os.getenv("CONTENT_STORAGE_LOCAL_ROOT", "/tmp/edunova-content"))
        self.delivery = DeliveryService(
            library_repository=self.library_repository,
            library_access=self.library_access,
            token_verifier=self.resource_delivery,
            storage=self.delivery_storage,
            now=_now,
        )

        # LOT 9 — engagement and notification policy. Personal reminders stay local
        # on the device; this server module stores preferences, push registrations
        # and lightweight engagement aggregates only.
        self.engagement_repository = SqlAlchemyEngagementRepository(self.sessions)
        self.push_registry = SqlAlchemyPushRegistry(self.sessions)
        push_sender = FirebaseAdminPushSender() if self.production_like and os.getenv("FCM_ENABLED", "false").lower() in {"1","true","yes"} else None

        # LOT 10 — deterministic learning analytics and recommendations.
        # No LLM is required; the engine consumes aggregate learning signals only.
        self.analytics = AnalyticsService()
        self.engagement = EngagementService(self.engagement_repository, self.push_registry, now=_now, push_sender=push_sender)
        self.campus_operations.engagement = self.engagement

        # LOT 11 — private editorial back-office. These are EduNova internal roles,
        # never university roles. Production owner bootstrap is explicit by account id.
        self.editorial_repository = SqlAlchemyEditorialRepository(self.sessions)
        self.editorial = EditorialService(self.editorial_repository, audit=self.audit, projector=LibraryPublicationProjector(self.library_repository), now=_now)
        owner_id = os.getenv("EDITORIAL_OWNER_ACCOUNT_ID")
        if owner_id and self.editorial_repository.get_member(owner_id) is None:
            self.editorial_repository.save_member(EditorialMember(account_id=owner_id, role=EditorialRole.OWNER, active=True))

        # LOT 12 — industrial content ingestion. API only stages and schedules work;
        # OCR/extraction runs in a dedicated worker with DB leases and heartbeats.
        self.ingestion_repository = SqlAlchemyIngestionRepository(self.sessions)
        if self.production_like:
            bucket = os.getenv("INGESTION_STORAGE_BUCKET") or os.getenv("CONTENT_STORAGE_BUCKET")
            if not bucket:
                raise RuntimeError("INGESTION_STORAGE_BUCKET is mandatory in production")
            self.ingestion_storage = S3StagingStorage(
                bucket=bucket, endpoint_url=os.getenv("CONTENT_STORAGE_ENDPOINT"),
                region=os.getenv("CONTENT_STORAGE_REGION"), prefix=os.getenv("INGESTION_STORAGE_PREFIX", "ingestion")
            )
            self.ingestion_scanner = ClamAvTcpScanner(
                host=os.getenv("CLAMAV_HOST", "clamav"),
                port=int(os.getenv("CLAMAV_PORT", "3310")),
                timeout_seconds=float(os.getenv("CLAMAV_TIMEOUT_SECONDS", "30")),
            )
        else:
            self.ingestion_storage = LocalStagingStorage(os.getenv("INGESTION_STAGING_DIR", "/tmp/edunova-ingestion"))
            self.ingestion_scanner = DisabledMalwareScanner()
        self.application_repo = SqlApplicationRepository(self.sessions)
        self.applications = ApplicationService(self.application_repo, self.admissions_catalog_repo, self.campus_repo, self.ingestion_storage, _now, audit=self.audit, scanner=self.ingestion_scanner)
        self.admission_review_repo = SqlAdmissionReviewRepository(self.sessions)
        self.admission_center = AdmissionCenterService(self.admission_review_repo, self.applications, self.campus, _now, audit=self.audit)
        self.admission_center.catalog = self.admissions_catalog_repo
        self.student_record_repo = SqlStudentRecordRepository(self.sessions)
        self.academic_delivery_repo = SqlAcademicDeliveryRepository(self.sessions)
        self.academic_delivery = AcademicDeliveryService(self.academic_delivery_repo, self.campus_repo, self.teaching_repo, self.academic_catalog_repo, self.student_record_repo, _now, audit=self.audit)
        self.placement_repo = SqlPlacementRepository(self.sessions)
        self.placements = PlacementService(self.placement_repo,self.campus_repo,self.student_record_repo,_now,audit=self.audit)
        self.research_repo = SqlResearchRepository(self.sessions)
        self.research = ResearchService(self.research_repo,self.campus_repo,self.student_record_repo,_now,audit=self.audit)
        self.student_success_repo = SqlSuccessRepository(self.sessions)
        self.student_success = StudentSuccessService(self.student_success_repo,self.campus_repo,self.student_record_repo,_now)
        self.pedagogical_intelligence_repo = SqlObjectiveEvidenceRepository(self.sessions)
        self.pedagogical_intelligence = CanonicalPedagogicalIntelligenceService(self.pedagogical_intelligence_repo,self.campus_repo,self.teaching_repo)
        self.service_desk_repo = SqlServiceDeskRepository(self.sessions)
        self.service_desk = ServiceDeskService(self.service_desk_repo,self.campus_repo,self.student_record_repo,_now,audit=self.audit)
        self.official_document_repo = SqlOfficialDocumentRepository(self.sessions)
        self.jury_repo = SqlJuryRepository(self.sessions)
        self.official_documents = OfficialDocumentService(self.official_document_repo,self.service_desk,self.campus_repo,self.student_record_repo,_now,jury=self.jury_repo,audit=self.audit,academic_delivery_repo=self.academic_delivery_repo)
        self.jury = JuryService(self.jury_repo,self.campus_repo,self.student_record_repo,_now,audit=self.audit,academic=self.academic_catalog_repo)
        self.gradebook.delivery = self.academic_delivery
        self.campus_operations.delivery = self.academic_delivery
        self.student_records = StudentRecordService(self.student_record_repo, self.campus, self.campus_repo, self.admission_center, self.applications, self.admissions_catalog_repo, self.academic_catalog_repo, _now, audit=self.audit)
        self.student_finance_repo = SqlStudentFinanceRepository(self.sessions)
        self.student_finance = StudentFinanceService(self.student_finance_repo, self.campus, self.campus_repo, self.student_record_repo, _now, audit=self.audit)
        self.payment_gateway_repo = SqlPaymentGatewayRepository(self.sessions)
        gateway_secrets = {"sandbox": os.getenv("PAYMENT_SANDBOX_SECRET", "edunova-sandbox-secret")}
        self.payment_gateway = PaymentGatewayService(self.payment_gateway_repo, self.student_finance, self.student_record_repo, self.campus, _now, audit=self.audit, secrets=gateway_secrets)

        ingestion_actor = os.getenv("INGESTION_SYSTEM_ACCOUNT_ID") or None
        if ingestion_actor and self.editorial_repository.get_member(ingestion_actor) is None:
            self.editorial_repository.save_member(EditorialMember(account_id=ingestion_actor, role=EditorialRole.EDITOR, active=True))
        self.ingestion = IngestionService(
            repository=self.ingestion_repository, storage=self.ingestion_storage, scanner=self.ingestion_scanner,
            preflight=PreflightValidator(PreflightPolicy(
                max_file_bytes=int(os.getenv("INGESTION_MAX_FILE_BYTES", str(80 * 1024 * 1024))),
                max_pdf_pages=int(os.getenv("INGESTION_MAX_PDF_PAGES", "600")),
                max_image_pixels=int(os.getenv("INGESTION_MAX_IMAGE_PIXELS", "70000000")),
            )),
            editorial=self.editorial, editorial_bridge=EditorialIngestionBridge(self.editorial), now=_now,
            max_batch_files=int(os.getenv("INGESTION_MAX_BATCH_FILES", "1000")),
            max_attempts=int(os.getenv("INGESTION_MAX_ATTEMPTS", "3")),
            lease_seconds=int(os.getenv("INGESTION_LEASE_SECONDS", "180")),
            sla_pending_minutes=int(os.getenv("INGESTION_PENDING_SLA_MINUTES", "30")),
            processing_actor_id=ingestion_actor,
            audit=self.audit,
        )


        # LOT 13 — industrial pedagogical Content Factory. It consumes only successfully
        # processed LOT 12 artifacts and emits source-grounded drafts with page evidence.
        # Its terminal success state is READY_FOR_REVIEW, never PUBLISHED.
        self.content_factory_repository = SqlAlchemyContentFactoryRepository(self.sessions)
        factory_actor = os.getenv("CONTENT_FACTORY_SYSTEM_ACCOUNT_ID") or None
        if factory_actor and self.editorial_repository.get_member(factory_actor) is None:
            self.editorial_repository.save_member(EditorialMember(account_id=factory_actor, role=EditorialRole.EDITOR, active=True))
        self.content_factory = ContentFactoryService(
            self.content_factory_repository, self.ingestion_repository, self.ingestion_storage,
            self.editorial, now=_now, audit=self.audit,
            lease_seconds=int(os.getenv("CONTENT_FACTORY_LEASE_SECONDS", "300")),
            max_attempts=int(os.getenv("CONTENT_FACTORY_MAX_ATTEMPTS", "3")),
        )

        # LOT 14 — controlled academic publishing and catalog distribution.
        self.publication_repository = SqlAlchemyPublicationRepository(self.sessions)
        self.publication = PublicationService(self.publication_repository, self.editorial_repository, self.library_repository, audit=self.audit, now=_now)

        # LOT 15 — student Learning Experience Engine / Study Workspace.
        self.learning_repository = SqlAlchemyLearningRepository(self.sessions)
        self.learning_experience = LearningExperienceService(self.learning_repository, now=_now, audit=self.audit)
        self.adaptive_learning_repository=SqlAlchemyAdaptiveLearningRepository(self.sessions)
        self.adaptive_learning=AdaptiveLearningService(self.learning_repository,self.adaptive_learning_repository,_now)
        # LOT 17 — adaptive daily/weekly academic orchestration.
        self.study_planner_repository=SqlAlchemyStudyPlannerRepository(self.sessions)
        self.study_planner=StudyPlannerService(self.study_planner_repository,self.adaptive_learning,self.learning_repository,_now,audit=self.audit)
        # LOT 18 — versioned assessment and exam simulation engine.
        self.assessment_repository=SqlAlchemyAssessmentRepository(self.sessions)
        self.assessment=AssessmentService(self.assessment_repository,_now,audit=self.audit)
        self.remediation_repository=SqlAlchemyRemediationRepository(self.sessions)
        self.remediation=RemediationService(self.remediation_repository,self.learning_repository,self.adaptive_learning,_now,audit=self.audit)
        self.knowledge_graph_repository=SqlAlchemyKnowledgeGraphRepository(self.sessions)
        self.knowledge_graph=KnowledgeGraphService(self.knowledge_graph_repository,_now)

runtime = Runtime()
