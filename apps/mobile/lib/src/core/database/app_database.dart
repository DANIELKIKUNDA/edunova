import 'package:drift/drift.dart';

import 'connection/connection.dart' as connection;

part 'app_database.g.dart';

class LocalAcademicProfiles extends Table {
  TextColumn get id => text()();
  TextColumn get faculty => text()();
  TextColumn get program => text()();
  TextColumn get level => text()();
  TextColumn get semester => text()();
  TextColumn get institution => text().nullable()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

class LocalPersonalDocuments extends Table {
  TextColumn get id => text()();
  TextColumn get title => text()();
  TextColumn get originalFileName => text()();
  TextColumn get documentType => text()();
  TextColumn get localUri => text()();
  TextColumn get mimeType => text()();
  IntColumn get sizeBytes => integer()();
  TextColumn get courseName => text().nullable()();
  TextColumn get level => text().nullable()();
  TextColumn get academicYear => text().nullable()();
  BoolColumn get isImage => boolean().withDefault(const Constant(false))();
  TextColumn get ocrStatus => text().withDefault(const Constant('notRequested'))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

class LocalCourseRecords extends Table {
  TextColumn get id => text()();
  TextColumn get title => text()();
  TextColumn get faculty => text()();
  TextColumn get program => text()();
  TextColumn get level => text()();
  TextColumn get semester => text()();
  TextColumn get source => text()();
  RealColumn get progress => real().withDefault(const Constant(0))();
  BoolColumn get availableOffline => boolean().withDefault(const Constant(false))();
  TextColumn get localDocumentId => text().nullable()();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

class LocalAssessmentRecords extends Table {
  TextColumn get id => text()();
  TextColumn get courseId => text()();
  TextColumn get title => text()();
  TextColumn get kind => text()();
  TextColumn get source => text()();
  DateTimeColumn get scheduledAt => dateTime()();
  TextColumn get localDocumentId => text().nullable()();

  @override
  Set<Column<Object>> get primaryKey => {id};
}


class LocalDocumentAnalyses extends Table {
  TextColumn get documentId => text()();
  TextColumn get fingerprintSha256 => text().nullable()();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  IntColumn get pageCount => integer().withDefault(const Constant(0))();
  IntColumn get nativeTextPages => integer().withDefault(const Constant(0))();
  IntColumn get ocrPages => integer().withDefault(const Constant(0))();
  RealColumn get textQuality => real().withDefault(const Constant(0))();
  TextColumn get lastError => text().nullable()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column<Object>> get primaryKey => {documentId};
}

class LocalDocumentSections extends Table {
  TextColumn get id => text()();
  TextColumn get documentId => text()();
  TextColumn get title => text()();
  IntColumn get level => integer().withDefault(const Constant(1))();
  IntColumn get startPage => integer()();
  IntColumn get endPage => integer()();
  TextColumn get parentId => text().nullable()();
  IntColumn get ordinal => integer()();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

class LocalDocumentTextChunks extends Table {
  TextColumn get id => text()();
  TextColumn get documentId => text()();
  TextColumn get sectionId => text().nullable()();
  IntColumn get startPage => integer()();
  IntColumn get endPage => integer()();
  IntColumn get ordinal => integer()();
  TextColumn get textContent => text()();
  IntColumn get tokenEstimate => integer().withDefault(const Constant(0))();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

class LocalDocumentAnnotations extends Table {
  TextColumn get id => text()();
  TextColumn get documentId => text()();
  TextColumn get kind => text()();
  IntColumn get pageNumber => integer()();
  TextColumn get excerpt => text().nullable()();
  TextColumn get note => text().nullable()();
  TextColumn get anchorJson => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

class LocalReadingProgress extends Table {
  TextColumn get documentId => text()();
  IntColumn get pageNumber => integer().withDefault(const Constant(1))();
  RealColumn get pageProgress => real().withDefault(const Constant(0))();
  IntColumn get totalPages => integer().withDefault(const Constant(0))();
  DateTimeColumn get lastOpenedAt => dateTime()();
  IntColumn get secondsSpent => integer().withDefault(const Constant(0))();

  @override
  Set<Column<Object>> get primaryKey => {documentId};
}


class LocalSummaries extends Table {
  TextColumn get id => text()();
  TextColumn get courseId => text()();
  TextColumn get sectionId => text().nullable()();
  TextColumn get kind => text()();
  TextColumn get title => text()();
  TextColumn get bodyMarkdown => text()();
  IntColumn get estimatedMinutes => integer().withDefault(const Constant(5))();
  TextColumn get status => text().withDefault(const Constant('reviewRequired'))();
  TextColumn get sourceRefsJson => text()();
  TextColumn get modelId => text().nullable()();
  TextColumn get promptVersion => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}
class LocalFlashcards extends Table {
  TextColumn get id => text()(); TextColumn get courseId => text()(); TextColumn get sectionId => text().nullable()();
  TextColumn get front => text()(); TextColumn get back => text()(); IntColumn get difficulty => integer().withDefault(const Constant(3))();
  TextColumn get status => text().withDefault(const Constant('reviewRequired'))(); TextColumn get sourceRefsJson => text()();
  TextColumn get modelId => text().nullable()(); TextColumn get promptVersion => text().nullable()(); DateTimeColumn get createdAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}
class LocalFlashcardStates extends Table {
  TextColumn get flashcardId => text()(); IntColumn get repetitions => integer().withDefault(const Constant(0))();
  RealColumn get easeFactor => real().withDefault(const Constant(2.5))(); IntColumn get intervalDays => integer().withDefault(const Constant(0))();
  DateTimeColumn get dueAt => dateTime().nullable()(); IntColumn get lapses => integer().withDefault(const Constant(0))();
  @override Set<Column<Object>> get primaryKey => {flashcardId};
}
class LocalQuizQuestions extends Table {
  TextColumn get id => text()(); TextColumn get courseId => text()(); TextColumn get sectionId => text().nullable()(); TextColumn get kind => text()();
  TextColumn get prompt => text()(); TextColumn get optionsJson => text().withDefault(const Constant('[]'))(); TextColumn get answerJson => text()();
  TextColumn get explanation => text().withDefault(const Constant(''))(); IntColumn get difficulty => integer().withDefault(const Constant(3))();
  TextColumn get status => text().withDefault(const Constant('reviewRequired'))(); TextColumn get sourceRefsJson => text()();
  TextColumn get modelId => text().nullable()(); TextColumn get promptVersion => text().nullable()(); DateTimeColumn get createdAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}
class LocalQuizAttempts extends Table {
  TextColumn get id => text()(); TextColumn get courseId => text()(); TextColumn get assessmentId => text().nullable()(); IntColumn get scorePercent => integer()();
  IntColumn get totalQuestions => integer()(); IntColumn get correctQuestions => integer()(); DateTimeColumn get startedAt => dateTime()(); DateTimeColumn get completedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}
class LocalQuizAnswers extends Table {
  TextColumn get id => text()(); TextColumn get attemptId => text()(); TextColumn get questionId => text()(); TextColumn get answerJson => text()();
  BoolColumn get isCorrect => boolean()(); RealColumn get score => real()(); DateTimeColumn get answeredAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}
class LocalErrorLedgerItems extends Table {
  TextColumn get questionId => text()(); TextColumn get courseId => text()(); DateTimeColumn get firstFailedAt => dateTime()(); DateTimeColumn get lastFailedAt => dateTime()();
  IntColumn get failureCount => integer().withDefault(const Constant(1))(); IntColumn get recoveryStreak => integer().withDefault(const Constant(0))(); DateTimeColumn get recoveredAt => dateTime().nullable()();
  @override Set<Column<Object>> get primaryKey => {questionId};
}
class LocalPedagogyJobs extends Table {
  TextColumn get id => text()(); TextColumn get documentId => text()(); TextColumn get task => text()(); TextColumn get status => text().withDefault(const Constant('queued'))();
  RealColumn get progress => real().withDefault(const Constant(0))(); TextColumn get lastError => text().nullable()(); DateTimeColumn get createdAt => dateTime()(); DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalLearningObjectives extends Table {
  TextColumn get id => text()();
  TextColumn get courseId => text()();
  TextColumn get sectionId => text().nullable()();
  TextColumn get title => text()();
  TextColumn get cognitiveLevel => text()();
  TextColumn get prerequisiteIdsJson => text().withDefault(const Constant('[]'))();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalObjectiveMastery extends Table {
  TextColumn get objectiveId => text()();
  RealColumn get mastery => real().withDefault(const Constant(0))();
  IntColumn get evidenceCount => integer().withDefault(const Constant(0))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {objectiveId};
}

class LocalPedagogyContentScopes extends Table {
  TextColumn get contentId => text()();
  TextColumn get contentType => text()();
  TextColumn get scope => text().withDefault(const Constant('personal'))();
  TextColumn get sourceFingerprint => text().nullable()();
  TextColumn get ownerId => text().nullable()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {contentId, contentType};
}

class LocalFlashcardReviewEvents extends Table {
  TextColumn get id => text()();
  TextColumn get flashcardId => text()();
  TextColumn get rating => text()();
  IntColumn get intervalBeforeDays => integer()();
  IntColumn get intervalAfterDays => integer()();
  DateTimeColumn get reviewedAt => dateTime()();
  DateTimeColumn get dueAtAfter => dateTime().nullable()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalQuizSessionStates extends Table {
  TextColumn get attemptId => text()();
  TextColumn get courseId => text()();
  TextColumn get mode => text().withDefault(const Constant('practice'))();
  IntColumn get currentIndex => integer().withDefault(const Constant(0))();
  TextColumn get selectedAnswersJson => text().withDefault(const Constant('{}'))();
  IntColumn get correctCount => integer().withDefault(const Constant(0))();
  TextColumn get status => text().withDefault(const Constant('inProgress'))();
  DateTimeColumn get startedAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {attemptId};
}

class LocalQuizAnswerTelemetry extends Table {
  TextColumn get answerId => text()();
  IntColumn get responseTimeMs => integer().withDefault(const Constant(0))();
  IntColumn get confidence => integer().nullable()();
  @override Set<Column<Object>> get primaryKey => {answerId};
}

class LocalTimetableEntries extends Table {
  TextColumn get id => text()();
  TextColumn get courseId => text().nullable()();
  TextColumn get title => text()();
  IntColumn get weekday => integer()();
  IntColumn get startMinute => integer()();
  IntColumn get endMinute => integer()();
  TextColumn get location => text().nullable()();
  TextColumn get source => text().withDefault(const Constant('personal'))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalAcademicEvents extends Table {
  TextColumn get id => text()();
  TextColumn get courseId => text().nullable()();
  TextColumn get title => text()();
  TextColumn get kind => text()();
  DateTimeColumn get startsAt => dateTime()();
  DateTimeColumn get endsAt => dateTime().nullable()();
  TextColumn get source => text().withDefault(const Constant('personal'))();
  TextColumn get notes => text().nullable()();
  BoolColumn get isActive => boolean().withDefault(const Constant(true))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalStudyPlanTasks extends Table {
  TextColumn get id => text()();
  TextColumn get dayKey => text()();
  TextColumn get courseId => text()();
  TextColumn get title => text()();
  TextColumn get kind => text()();
  IntColumn get minutes => integer()();
  IntColumn get priority => integer()();
  TextColumn get reasonsJson => text().withDefault(const Constant('[]'))();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  DateTimeColumn get generatedAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalPlanningPreferences extends Table {
  TextColumn get id => text().withDefault(const Constant('default'))();
  IntColumn get dailyBudgetMinutes => integer().withDefault(const Constant(30))();
  IntColumn get maxNotificationsPerDay => integer().withDefault(const Constant(2))();
  IntColumn get quietStartMinute => integer().withDefault(const Constant(1320))();
  IntColumn get quietEndMinute => integer().withDefault(const Constant(420))();
  IntColumn get maxContinuousMinutes => integer().withDefault(const Constant(50))();
  IntColumn get breakMinutes => integer().withDefault(const Constant(10))();
  IntColumn get maxCoursesPerDay => integer().withDefault(const Constant(4))();
  IntColumn get maxCourseSwitches => integer().withDefault(const Constant(5))();
  IntColumn get targetReadiness => integer().withDefault(const Constant(80))();
  IntColumn get planningHorizonDays => integer().withDefault(const Constant(14))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalNotificationIntents extends Table {
  TextColumn get id => text()();
  TextColumn get eventId => text()();
  TextColumn get dedupeKey => text().nullable()();
  DateTimeColumn get fireAt => dateTime()();
  DateTimeColumn get expiresAt => dateTime().nullable()();
  TextColumn get title => text()();
  TextColumn get body => text()();
  TextColumn get category => text()();
  TextColumn get deepLink => text().withDefault(const Constant(''))();
  IntColumn get priority => integer().withDefault(const Constant(50))();
  TextColumn get status => text().withDefault(const Constant('planned'))();
  DateTimeColumn get deliveredAt => dateTime().nullable()();
  DateTimeColumn get interactedAt => dateTime().nullable()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalScheduleImportDrafts extends Table {
  TextColumn get id => text()();
  TextColumn get sourceDocumentId => text().nullable()();
  TextColumn get rawText => text().nullable()();
  TextColumn get detectedEntriesJson => text().withDefault(const Constant('[]'))();
  RealColumn get confidence => real().withDefault(const Constant(0))();
  TextColumn get status => text().withDefault(const Constant('reviewRequired'))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}


class LocalStudyAvailabilityRules extends Table {
  TextColumn get id => text()();
  IntColumn get weekday => integer()();
  IntColumn get startMinute => integer()();
  IntColumn get endMinute => integer()();
  TextColumn get energy => text().withDefault(const Constant('medium'))();
  BoolColumn get isActive => boolean().withDefault(const Constant(true))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalAssessmentScopes extends Table {
  TextColumn get id => text()();
  TextColumn get eventId => text()();
  TextColumn get courseId => text()();
  TextColumn get sectionIdsJson => text().withDefault(const Constant('[]'))();
  IntColumn get targetReadiness => integer().withDefault(const Constant(80))();
  TextColumn get importance => text().withDefault(const Constant('normal'))();
  IntColumn get requiredMinutes => integer().withDefault(const Constant(0))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalPlanningDebts extends Table {
  TextColumn get courseId => text()();
  IntColumn get overdueMinutes => integer().withDefault(const Constant(0))();
  IntColumn get deferredCount => integer().withDefault(const Constant(0))();
  DateTimeColumn get lastDeferredAt => dateTime().nullable()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {courseId};
}

class LocalPlanRevisions extends Table {
  TextColumn get id => text()();
  TextColumn get dayKey => text()();
  TextColumn get reason => text()();
  TextColumn get fingerprint => text()();
  DateTimeColumn get generatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalAdaptiveStudyBlocks extends Table {
  TextColumn get id => text()();
  TextColumn get revisionId => text()();
  TextColumn get taskId => text()();
  TextColumn get courseId => text()();
  TextColumn get title => text()();
  TextColumn get kind => text()();
  DateTimeColumn get startsAt => dateTime()();
  DateTimeColumn get endsAt => dateTime()();
  IntColumn get priority => integer()();
  TextColumn get reasonsJson => text().withDefault(const Constant('[]'))();
  TextColumn get status => text().withDefault(const Constant('planned'))();
  BoolColumn get pinned => boolean().withDefault(const Constant(false))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalStudySessions extends Table {
  TextColumn get id => text()();
  TextColumn get blockId => text().nullable()();
  TextColumn get courseId => text()();
  TextColumn get taskId => text().nullable()();
  DateTimeColumn get startedAt => dateTime()();
  DateTimeColumn get endedAt => dateTime().nullable()();
  IntColumn get plannedMinutes => integer().withDefault(const Constant(0))();
  IntColumn get actualMinutes => integer().withDefault(const Constant(0))();
  TextColumn get outcome => text().withDefault(const Constant('started'))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalPlanActions extends Table {
  TextColumn get id => text()();
  TextColumn get blockId => text()();
  TextColumn get action => text()();
  TextColumn get payloadJson => text().withDefault(const Constant('{}'))();
  DateTimeColumn get occurredAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}


class LocalEntitlementSnapshots extends Table {
  TextColumn get id => text().withDefault(const Constant('current'))();
  BoolColumn get premium => boolean().withDefault(const Constant(false))();
  DateTimeColumn get premiumUntil => dateTime().nullable()();
  IntColumn get aiCreditsRemaining => integer().withDefault(const Constant(0))();
  DateTimeColumn get issuedAt => dateTime()();
  DateTimeColumn get offlineValidUntil => dateTime()();
  TextColumn get revision => text()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalPaymentIntents extends Table {
  TextColumn get id => text()();
  TextColumn get planCode => text()();
  IntColumn get amountCdf => integer()();
  TextColumn get provider => text()();
  TextColumn get providerReference => text().nullable()();
  TextColumn get phoneNumber => text()();
  TextColumn get state => text()();
  TextColumn get actionType => text().nullable()();
  TextColumn get actionValue => text().nullable()();
  TextColumn get userMessage => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();
  DateTimeColumn get expiresAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalReceipts extends Table {
  TextColumn get id => text()();
  TextColumn get paymentId => text()();
  IntColumn get amountCdf => integer()();
  DateTimeColumn get issuedAt => dateTime()();
  TextColumn get description => text()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalAiUsageEvents extends Table {
  TextColumn get id => text()();
  IntColumn get credits => integer()();
  TextColumn get purpose => text()();
  DateTimeColumn get occurredAt => dateTime()();
  TextColumn get syncStatus => text().withDefault(const Constant('pending'))();
  @override Set<Column<Object>> get primaryKey => {id};
}


class LocalAssistantConversations extends Table {
  TextColumn get id => text()();
  TextColumn get title => text()();
  TextColumn get contextType => text()();
  TextColumn get contextId => text().nullable()();
  TextColumn get subjectDomain => text().withDefault(const Constant('general'))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalAssistantMessages extends Table {
  TextColumn get id => text()();
  TextColumn get conversationId => text()();
  TextColumn get role => text()();
  TextColumn get textContent => text()();
  TextColumn get citationsJson => text().withDefault(const Constant('[]'))();
  BoolColumn get grounded => boolean().withDefault(const Constant(false))();
  RealColumn get confidence => real().withDefault(const Constant(0))();
  IntColumn get creditsCharged => integer().withDefault(const Constant(0))();
  TextColumn get provider => text().nullable()();
  TextColumn get model => text().nullable()();
  BoolColumn get abstained => boolean().withDefault(const Constant(false))();
  BoolColumn get cacheHit => boolean().withDefault(const Constant(false))();
  TextColumn get safetyFlagsJson => text().withDefault(const Constant('[]'))();
  TextColumn get routeReason => text().nullable()();
  RealColumn get groundingCoverage => real().withDefault(const Constant(0))();
  IntColumn get sourceCount => integer().withDefault(const Constant(0))();
  TextColumn get promptVersion => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalOutboxItems extends Table {
  TextColumn get id => text()();
  TextColumn get aggregateType => text()();
  TextColumn get aggregateId => text()();
  TextColumn get eventType => text()();
  TextColumn get payloadJson => text()();
  DateTimeColumn get occurredAt => dateTime()();
  IntColumn get retryCount => integer().withDefault(const Constant(0))();
  TextColumn get status => text().withDefault(const Constant('pending'))();

  @override
  Set<Column<Object>> get primaryKey => {id};
}


class LocalCloudSyncStates extends Table {
  TextColumn get id => text().withDefault(const Constant('current'))();
  TextColumn get accountId => text().nullable()();
  TextColumn get deviceId => text()();
  IntColumn get serverCursor => integer().withDefault(const Constant(0))();
  IntColumn get ackedCursor => integer().withDefault(const Constant(0))();
  IntColumn get retainedFloor => integer().withDefault(const Constant(0))();
  BoolColumn get registered => boolean().withDefault(const Constant(false))();
  DateTimeColumn get lastSyncAt => dateTime().nullable()();
  DateTimeColumn get lastBootstrapAt => dateTime().nullable()();
  TextColumn get lastError => text().nullable()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalCloudMutations extends Table {
  TextColumn get id => text()();
  TextColumn get accountId => text().nullable()();
  TextColumn get entityType => text()();
  TextColumn get entityId => text()();
  TextColumn get operation => text().withDefault(const Constant('upsert'))();
  TextColumn get payloadJson => text().withDefault(const Constant('{}'))();
  IntColumn get baseVersion => integer().nullable()();
  DateTimeColumn get clientModifiedAt => dateTime()();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  IntColumn get retryCount => integer().withDefault(const Constant(0))();
  DateTimeColumn get nextAttemptAt => dateTime().nullable()();
  TextColumn get lastError => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalSyncEntityVersions extends Table {
  TextColumn get entityType => text()();
  TextColumn get entityId => text()();
  IntColumn get version => integer()();
  IntColumn get serverSeq => integer()();
  TextColumn get payloadJson => text().withDefault(const Constant('{}'))();
  BoolColumn get deleted => boolean().withDefault(const Constant(false))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {entityType, entityId};
}

class LocalAccountSyncEntityVersions extends Table {
  TextColumn get accountId => text()();
  TextColumn get entityType => text()();
  TextColumn get entityId => text()();
  IntColumn get version => integer()();
  IntColumn get serverSeq => integer()();
  TextColumn get payloadJson => text().withDefault(const Constant('{}'))();
  BoolColumn get deleted => boolean().withDefault(const Constant(false))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {accountId, entityType, entityId};
}

class LocalSyncConflicts extends Table {
  TextColumn get id => text()();
  // Nullable only for migration compatibility with v11 rows. New v12 conflicts always set accountId.
  TextColumn get accountId => text().nullable()();
  TextColumn get mutationId => text()();
  TextColumn get entityType => text()();
  TextColumn get entityId => text()();
  TextColumn get localPayloadJson => text().withDefault(const Constant('{}'))();
  TextColumn get canonicalPayloadJson => text().withDefault(const Constant('{}'))();
  IntColumn get canonicalVersion => integer()();
  TextColumn get reason => text()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get resolvedAt => dateTime().nullable()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalLibraryCourses extends Table {
  TextColumn get id => text()();
  TextColumn get facultyDomain => text()();
  TextColumn get program => text()();
  TextColumn get level => text()();
  TextColumn get semester => text()();
  TextColumn get title => text()();
  TextColumn get slug => text()();
  TextColumn get description => text().withDefault(const Constant(''))();
  BoolColumn get premiumRequired => boolean().withDefault(const Constant(false))();
  TextColumn get activeVersionId => text().nullable()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalLibraryCourseVersions extends Table {
  TextColumn get id => text()();
  TextColumn get courseId => text()();
  TextColumn get label => text()();
  TextColumn get academicYear => text().nullable()();
  TextColumn get sourceFingerprint => text()();
  TextColumn get changelog => text().withDefault(const Constant(''))();
  DateTimeColumn get publishedAt => dateTime().nullable()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalLibraryResources extends Table {
  TextColumn get id => text()();
  TextColumn get versionId => text()();
  TextColumn get kind => text()();
  TextColumn get title => text()();
  TextColumn get mimeType => text().nullable()();
  IntColumn get sizeBytes => integer().nullable()();
  TextColumn get checksumSha256 => text().nullable()();
  BoolColumn get premiumRequired => boolean().withDefault(const Constant(false))();
  BoolColumn get offlineAllowed => boolean().withDefault(const Constant(false))();
  TextColumn get access => text().withDefault(const Constant('locked'))();
  TextColumn get deliveryToken => text().nullable()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalLibraryCourseFollows extends Table {
  TextColumn get courseId => text()();
  BoolColumn get followed => boolean().withDefault(const Constant(true))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {courseId};
}

class LocalLibraryCatalogStates extends Table {
  TextColumn get cacheKey => text()();
  TextColumn get etag => text().nullable()();
  TextColumn get nextCursor => text().nullable()();
  DateTimeColumn get lastRefreshAt => dateTime().nullable()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {cacheKey};
}

class LocalLibraryDownloadStates extends Table {
  TextColumn get resourceId => text()();
  TextColumn get state => text().withDefault(const Constant('notDownloaded'))();
  TextColumn get localUri => text().nullable()();
  TextColumn get tempUri => text().nullable()();
  TextColumn get checksumSha256 => text().nullable()();
  TextColumn get etag => text().nullable()();
  IntColumn get bytesDownloaded => integer().withDefault(const Constant(0))();
  IntColumn get totalBytes => integer().nullable()();
  IntColumn get retryCount => integer().withDefault(const Constant(0))();
  TextColumn get lastError => text().nullable()();
  BoolColumn get pinned => boolean().withDefault(const Constant(false))();
  BoolColumn get resumeSupported => boolean().withDefault(const Constant(true))();
  DateTimeColumn get downloadedAt => dateTime().nullable()();
  DateTimeColumn get verifiedAt => dateTime().nullable()();
  DateTimeColumn get lastAccessedAt => dateTime().nullable()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {resourceId};
}

class LocalOfflinePackages extends Table {
  TextColumn get id => text()();
  TextColumn get courseId => text()();
  TextColumn get versionId => text()();
  TextColumn get title => text()();
  TextColumn get state => text().withDefault(const Constant('planned'))();
  IntColumn get totalBytes => integer().withDefault(const Constant(0))();
  IntColumn get readyBytes => integer().withDefault(const Constant(0))();
  IntColumn get resourceCount => integer().withDefault(const Constant(0))();
  IntColumn get readyResourceCount => integer().withDefault(const Constant(0))();
  BoolColumn get pinned => boolean().withDefault(const Constant(false))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalDownloadQueueItems extends Table {
  TextColumn get id => text()();
  TextColumn get courseId => text()();
  TextColumn get resourceId => text()();
  IntColumn get priority => integer().withDefault(const Constant(50))();
  TextColumn get state => text().withDefault(const Constant('queued'))();
  IntColumn get attempts => integer().withDefault(const Constant(0))();
  DateTimeColumn get nextAttemptAt => dateTime().nullable()();
  TextColumn get lastError => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalContentCachePolicies extends Table {
  TextColumn get id => text().withDefault(const Constant('default'))();
  IntColumn get maxCacheBytes => integer().withDefault(const Constant(2147483648))();
  IntColumn get minFreeBytes => integer().withDefault(const Constant(536870912))();
  BoolColumn get wifiOnlyLargeDownloads => boolean().withDefault(const Constant(true))();
  IntColumn get largeDownloadThresholdBytes => integer().withDefault(const Constant(52428800))();
  BoolColumn get autoCleanup => boolean().withDefault(const Constant(true))();
  BoolColumn get keepFollowedCourses => boolean().withDefault(const Constant(true))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalLibraryResourceChunks extends Table {
  TextColumn get resourceId => text()();
  IntColumn get chunkIndex => integer()();
  BlobColumn get bytes => blob()();
  IntColumn get byteOffset => integer()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {resourceId, chunkIndex};
}


class LocalEngagementPreferences extends Table {
  TextColumn get id => text().withDefault(const Constant('current'))();
  IntColumn get quietStartMinute => integer().withDefault(const Constant(1320))();
  IntColumn get quietEndMinute => integer().withDefault(const Constant(420))();
  IntColumn get maxDailyNotifications => integer().withDefault(const Constant(2))();
  IntColumn get preferredStudyMinute => integer().withDefault(const Constant(1140))();
  IntColumn get timezoneOffsetMinutes => integer().withDefault(const Constant(0))();
  IntColumn get dailyGoalMinutes => integer().withDefault(const Constant(30))();
  BoolColumn get assessmentEnabled => boolean().withDefault(const Constant(true))();
  BoolColumn get studyPlanEnabled => boolean().withDefault(const Constant(true))();
  BoolColumn get flashcardsEnabled => boolean().withDefault(const Constant(true))();
  BoolColumn get streakEnabled => boolean().withDefault(const Constant(false))();
  BoolColumn get contentEnabled => boolean().withDefault(const Constant(true))();
  BoolColumn get pushEnabled => boolean().withDefault(const Constant(true))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalEngagementDailyStats extends Table {
  TextColumn get dayKey => text()();
  IntColumn get activeMinutes => integer().withDefault(const Constant(0))();
  IntColumn get completedTasks => integer().withDefault(const Constant(0))();
  IntColumn get quizQuestions => integer().withDefault(const Constant(0))();
  IntColumn get flashcardsReviewed => integer().withDefault(const Constant(0))();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {dayKey};
}

class LocalAudioPlaybackStates extends Table {
  TextColumn get id => text()();
  TextColumn get courseId => text()();
  TextColumn get summaryId => text().nullable()();
  TextColumn get title => text()();
  IntColumn get characterOffset => integer().withDefault(const Constant(0))();
  RealColumn get speechRate => real().withDefault(const Constant(1.0))();
  BoolColumn get completed => boolean().withDefault(const Constant(false))();
  DateTimeColumn get lastPlayedAt => dateTime().nullable()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalAudioBookmarks extends Table {
  TextColumn get id => text()();
  TextColumn get playbackId => text()();
  IntColumn get characterOffset => integer()();
  TextColumn get label => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {id};
}

class LocalAnalyticsCourseSnapshots extends Table {
  TextColumn get courseId => text()();
  TextColumn get dayKey => text()();
  IntColumn get readiness => integer().nullable()();
  RealColumn get quizMastery => real().nullable()();
  RealColumn get coverage => real().nullable()();
  IntColumn get openErrors => integer().withDefault(const Constant(0))();
  IntColumn get studyMinutes => integer().withDefault(const Constant(0))();
  DateTimeColumn get generatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {courseId, dayKey};
}

class LocalAnalyticsRecommendationFeedback extends Table {
  TextColumn get recommendationId => text()();
  TextColumn get state => text()();
  DateTimeColumn get snoozedUntil => dateTime().nullable()();
  DateTimeColumn get updatedAt => dateTime()();
  @override Set<Column<Object>> get primaryKey => {recommendationId};
}

@DriftDatabase(
  tables: [
    LocalAcademicProfiles,
    LocalPersonalDocuments,
    LocalCourseRecords,
    LocalAssessmentRecords,
    LocalDocumentAnalyses,
    LocalDocumentSections,
    LocalDocumentTextChunks,
    LocalDocumentAnnotations,
    LocalReadingProgress,
    LocalSummaries,
    LocalFlashcards,
    LocalFlashcardStates,
    LocalQuizQuestions,
    LocalQuizAttempts,
    LocalQuizAnswers,
    LocalErrorLedgerItems,
    LocalPedagogyJobs,
    LocalLearningObjectives,
    LocalObjectiveMastery,
    LocalPedagogyContentScopes,
    LocalFlashcardReviewEvents,
    LocalQuizSessionStates,
    LocalQuizAnswerTelemetry,
    LocalTimetableEntries,
    LocalAcademicEvents,
    LocalStudyPlanTasks,
    LocalPlanningPreferences,
    LocalNotificationIntents,
    LocalScheduleImportDrafts,
    LocalStudyAvailabilityRules,
    LocalAssessmentScopes,
    LocalPlanningDebts,
    LocalPlanRevisions,
    LocalAdaptiveStudyBlocks,
    LocalStudySessions,
    LocalPlanActions,
    LocalEntitlementSnapshots,
    LocalPaymentIntents,
    LocalReceipts,
    LocalAiUsageEvents,
    LocalAssistantConversations,
    LocalAssistantMessages,
    LocalCloudSyncStates,
    LocalCloudMutations,
    LocalSyncEntityVersions,
    LocalAccountSyncEntityVersions,
    LocalSyncConflicts,
    LocalLibraryCourses,
    LocalLibraryCourseVersions,
    LocalLibraryResources,
    LocalLibraryCourseFollows,
    LocalLibraryCatalogStates,
    LocalLibraryDownloadStates,
    LocalOfflinePackages,
    LocalDownloadQueueItems,
    LocalContentCachePolicies,
    LocalLibraryResourceChunks,
    LocalEngagementPreferences,
    LocalEngagementDailyStats,
    LocalAudioPlaybackStates,
    LocalAudioBookmarks,
    LocalAnalyticsCourseSnapshots,
    LocalAnalyticsRecommendationFeedback,
    LocalOutboxItems,
  ],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(connection.openConnection());

  @override
  int get schemaVersion => 16;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) async => m.createAll(),
        onUpgrade: (m, from, to) async {
          if (from < 2) {
            await m.createTable(localDocumentAnalyses);
            await m.createTable(localDocumentSections);
            await m.createTable(localDocumentTextChunks);
            await m.createTable(localDocumentAnnotations);
            await m.createTable(localReadingProgress);
          }
          if (from < 3) {
            await m.createTable(localSummaries);
            await m.createTable(localFlashcards);
            await m.createTable(localFlashcardStates);
            await m.createTable(localQuizQuestions);
            await m.createTable(localQuizAttempts);
            await m.createTable(localQuizAnswers);
            await m.createTable(localErrorLedgerItems);
            await m.createTable(localPedagogyJobs);
          }
          if (from < 4) {
            await m.createTable(localLearningObjectives);
            await m.createTable(localObjectiveMastery);
            await m.createTable(localPedagogyContentScopes);
            await m.createTable(localFlashcardReviewEvents);
            await m.createTable(localQuizSessionStates);
            await m.createTable(localQuizAnswerTelemetry);
          }
          if (from < 5) {
            await m.createTable(localTimetableEntries);
            await m.createTable(localAcademicEvents);
            await m.createTable(localStudyPlanTasks);
            await m.createTable(localPlanningPreferences);
            await m.createTable(localNotificationIntents);
            await m.createTable(localScheduleImportDrafts);
          }
          if (from < 6) {
            await m.addColumn(localPlanningPreferences, localPlanningPreferences.maxContinuousMinutes);
            await m.addColumn(localPlanningPreferences, localPlanningPreferences.breakMinutes);
            await m.addColumn(localPlanningPreferences, localPlanningPreferences.maxCoursesPerDay);
            await m.addColumn(localPlanningPreferences, localPlanningPreferences.maxCourseSwitches);
            await m.addColumn(localPlanningPreferences, localPlanningPreferences.targetReadiness);
            await m.addColumn(localPlanningPreferences, localPlanningPreferences.planningHorizonDays);
            await m.createTable(localStudyAvailabilityRules);
            await m.createTable(localAssessmentScopes);
            await m.createTable(localPlanningDebts);
            await m.createTable(localPlanRevisions);
            await m.createTable(localAdaptiveStudyBlocks);
            await m.createTable(localStudySessions);
            await m.createTable(localPlanActions);
          }
          if (from < 7) {
            await m.createTable(localEntitlementSnapshots);
            await m.createTable(localPaymentIntents);
            await m.createTable(localReceipts);
            await m.createTable(localAiUsageEvents);
          }
          if (from < 8) {
            await m.createTable(localAssistantConversations);
            await m.createTable(localAssistantMessages);
          }
          if (from < 9) {
            await m.addColumn(localAssistantMessages, localAssistantMessages.abstained);
            await m.addColumn(localAssistantMessages, localAssistantMessages.cacheHit);
            await m.addColumn(localAssistantMessages, localAssistantMessages.safetyFlagsJson);
            await m.addColumn(localAssistantMessages, localAssistantMessages.routeReason);
          }
          if (from < 10) {
            await m.addColumn(localAssistantMessages, localAssistantMessages.groundingCoverage);
            await m.addColumn(localAssistantMessages, localAssistantMessages.sourceCount);
            await m.addColumn(localAssistantMessages, localAssistantMessages.promptVersion);
          }
          if (from < 11) {
            await m.createTable(localCloudSyncStates);
            await m.createTable(localCloudMutations);
            await m.createTable(localSyncEntityVersions);
            await m.createTable(localSyncConflicts);
            await m.createTable(localLibraryCourses);
            await m.createTable(localLibraryCourseVersions);
            await m.createTable(localLibraryResources);
            await m.createTable(localLibraryDownloadStates);
          }
          if (from < 12) {
            await m.addColumn(localCloudSyncStates, localCloudSyncStates.accountId);
            await m.addColumn(localCloudSyncStates, localCloudSyncStates.ackedCursor);
            await m.addColumn(localCloudSyncStates, localCloudSyncStates.retainedFloor);
            await m.addColumn(localCloudSyncStates, localCloudSyncStates.lastBootstrapAt);
            await m.addColumn(localCloudMutations, localCloudMutations.accountId);
            await m.addColumn(localCloudMutations, localCloudMutations.nextAttemptAt);
            await m.addColumn(localCloudMutations, localCloudMutations.lastError);
            await m.addColumn(localSyncConflicts, localSyncConflicts.accountId);
            await m.createTable(localAccountSyncEntityVersions);
            await m.createTable(localLibraryCatalogStates);
          }
          if (from < 13) {
            await m.createTable(localLibraryCourseFollows);
          }
          if (from < 14) {
            await m.addColumn(localLibraryDownloadStates, localLibraryDownloadStates.tempUri);
            await m.addColumn(localLibraryDownloadStates, localLibraryDownloadStates.etag);
            await m.addColumn(localLibraryDownloadStates, localLibraryDownloadStates.totalBytes);
            await m.addColumn(localLibraryDownloadStates, localLibraryDownloadStates.retryCount);
            await m.addColumn(localLibraryDownloadStates, localLibraryDownloadStates.lastError);
            await m.addColumn(localLibraryDownloadStates, localLibraryDownloadStates.pinned);
            await m.addColumn(localLibraryDownloadStates, localLibraryDownloadStates.resumeSupported);
            await m.addColumn(localLibraryDownloadStates, localLibraryDownloadStates.verifiedAt);
            await m.addColumn(localLibraryDownloadStates, localLibraryDownloadStates.lastAccessedAt);
            await m.createTable(localOfflinePackages);
            await m.createTable(localDownloadQueueItems);
            await m.createTable(localContentCachePolicies);
            await m.createTable(localLibraryResourceChunks);
          }
          if (from < 15) {
            await m.addColumn(localNotificationIntents, localNotificationIntents.dedupeKey);
            await m.addColumn(localNotificationIntents, localNotificationIntents.expiresAt);
            await m.addColumn(localNotificationIntents, localNotificationIntents.deepLink);
            await m.addColumn(localNotificationIntents, localNotificationIntents.priority);
            await m.addColumn(localNotificationIntents, localNotificationIntents.deliveredAt);
            await m.addColumn(localNotificationIntents, localNotificationIntents.interactedAt);
            await m.createTable(localEngagementPreferences);
            await m.createTable(localEngagementDailyStats);
            await m.createTable(localAudioPlaybackStates);
            await m.createTable(localAudioBookmarks);
          }
          if (from < 16) {
            await m.createTable(localAnalyticsCourseSnapshots);
            await m.createTable(localAnalyticsRecommendationFeedback);
          }
        },
      );
}
