/**
 * View grouping index for gradual migration.
 * 
 * Domain structure:
 *   autotest/    - AutoTest, CaseList, CaseEditorDrawer, ScenarioEditor, ScenarioList,
 *                  ApiDebugger, InterfaceLibrary, DataFactory, JmeterAssistant,
 *                  ExecutionResultDialog, BackupManager
 *   learning/    - LearningPaths, LearningPathDetail, LearningPathLesson, Exercises,
 *                  ExerciseDetail, Exam, ExamList, ExamResult, Certificates,
 *                  Leaderboard, SkillAnalysis, WeeklyReport, WrongAnswers,
 *                  ProjectPractice, OnboardingAssessment
 *   ai/          - AITutor, InterviewSimulate, InterviewDetail, InterviewMy,
 *                  InterviewQuestionBank, CodePlayground, Community, PostDetail
 *   common/      - Home, Login, Register, ForgotPassword, Profile, NotFound,
 *                  Notifications, Favorites, SearchResults, TestingTools, JsonEditor
 * 
 * Current: All views remain flat in views/ for backward compatibility.
 * To migrate: Move files into subdirectories and update router imports.
 */
