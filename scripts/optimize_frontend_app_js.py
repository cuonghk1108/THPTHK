import sys

with open('static/app.js', 'rb') as f:
    text = f.read().decode('utf-8').replace('\r\n', '\n')

# 1. Debounce onDashboardSearch
old_dash_search = '''function onDashboardSearch(keyword) {

  _dashboardData.searchTerm = (keyword || '').toLowerCase().trim();

  if (_dashboardData.snapshot && _dashboardData.snapshot.classes) {

    renderDashboardTable(_dashboardData.snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod, _dashboardData.searchTerm);

  }

}'''

new_dash_search = '''let _dashSearchTimer = null;
function onDashboardSearch(keyword) {
  clearTimeout(_dashSearchTimer);
  _dashSearchTimer = setTimeout(() => {
    _dashboardData.searchTerm = (keyword || '').toLowerCase().trim();
    if (_dashboardData.snapshot && _dashboardData.snapshot.classes) {
      renderDashboardTable(_dashboardData.snapshot.classes, _dashboardData.selectedGrade, _dashboardData.selectedPeriod, _dashboardData.searchTerm);
    }
  }, 180);
}'''

if '_dashSearchTimer' not in text:
    assert old_dash_search in text, 'old_dash_search not found'
    text = text.replace(old_dash_search, new_dash_search, 1)

# 2. Debounce filterClassesBySearch
old_class_search = '''function filterClassesBySearch() {

  renderTeacherClassesBar();

}'''

new_class_search = '''let _classQuickSearchTimer = null;
function filterClassesBySearch() {
  clearTimeout(_classQuickSearchTimer);
  _classQuickSearchTimer = setTimeout(() => {
    renderTeacherClassesBar();
  }, 150);
}'''

if '_classQuickSearchTimer' not in text:
    assert old_class_search in text, 'old_class_search not found'
    text = text.replace(old_class_search, new_class_search, 1)

# 3. Debounce filterRulesReferenceTable
old_rules_filter = '''function filterRulesReferenceTable() {

  const tbody = document.getElementById('rules-reference-tbody');'''

new_rules_filter = '''let _rulesFilterTimer = null;
function filterRulesReferenceTable() {
  clearTimeout(_rulesFilterTimer);
  _rulesFilterTimer = setTimeout(() => {
    _doExecuteRulesReferenceFilter();
  }, 150);
}

function _doExecuteRulesReferenceFilter() {
  const tbody = document.getElementById('rules-reference-tbody');'''

if '_rulesFilterTimer' not in text:
    assert old_rules_filter in text, 'old_rules_filter not found'
    text = text.replace(old_rules_filter, new_rules_filter, 1)

# 4. loadTeacherClassesModule - avoid redundant re-fetch on tab click
old_teacher_load = '''async function loadTeacherClassesModule(force = false) {

  try {

    const roleBadgeText = document.getElementById('teacher-role-badge-text');'''

new_teacher_load = '''async function loadTeacherClassesModule(force = false) {

  try {
    if (!force && teacherAssignedClasses && teacherAssignedClasses.length > 0) {
      renderTeacherClassesBar();
      if (activeTeacherClass) {
        selectTeacherClass(activeTeacherClass.id);
      }
      return;
    }

    const roleBadgeText = document.getElementById('teacher-role-badge-text');'''

if 'if (!force && teacherAssignedClasses && teacherAssignedClasses.length > 0)' not in text:
    assert old_teacher_load in text, 'old_teacher_load not found'
    text = text.replace(old_teacher_load, new_teacher_load, 1)

# 5. loadCompetitionScores race condition sequence
old_scores_load = '''async function loadCompetitionScores() {

  if (!selectedPeriodId) {'''

new_scores_load = '''let _compScoresReqSeq = 0;
async function loadCompetitionScores() {
  const currentReqSeq = ++_compScoresReqSeq;

  if (!selectedPeriodId) {'''

if '_compScoresReqSeq' not in text:
    assert old_scores_load in text, 'old_scores_load not found'
    text = text.replace(old_scores_load, new_scores_load, 1)

old_scores_fetch_json = '''    const data = await res.json();

    currentPeriod = data.period;'''

new_scores_fetch_json = '''    const data = await res.json();
    if (currentReqSeq !== _compScoresReqSeq) return;

    currentPeriod = data.period;'''

if 'if (currentReqSeq !== _compScoresReqSeq) return;' not in text:
    assert old_scores_fetch_json in text, 'old_scores_fetch_json not found'
    text = text.replace(old_scores_fetch_json, new_scores_fetch_json, 1)

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(text)

print('Successfully optimized static/app.js with debouncing and race-condition guards!')
