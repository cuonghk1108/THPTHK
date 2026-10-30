import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = r"C:\Users\Xuan Cuong\Desktop\hk-student-hub"

views_path = os.path.join(BASE_DIR, "core", "views.py")
with open(views_path, "r", encoding="utf-8") as f:
    code = f.read()

# Fix 1: Remove @action from _sync_user_role_and_assignments and place it on def review
old_target = """    @action(detail=True, methods=['post'], url_path='review-class-change')
    def review_class_change(self, request, pk=None):
        target_user = self.get_object()
        action_type = request.data.get('action') or 'approve'
        reason = (request.data.get('reason') or '').strip()
        internal_notes = (request.data.get('internal_notes') or '').strip()
        return self._handle_class_change_review(request, target_user, action_type, reason, internal_notes)

    @action(detail=True, methods=['post'], url_path='review')
    def _sync_user_role_and_assignments(self, target_user, assigned_role, data, request):"""

new_target = """    @action(detail=True, methods=['post'], url_path='review-class-change')
    def review_class_change(self, request, pk=None):
        target_user = self.get_object()
        action_type = request.data.get('action') or 'approve'
        reason = (request.data.get('reason') or '').strip()
        internal_notes = (request.data.get('internal_notes') or '').strip()
        return self._handle_class_change_review(request, target_user, action_type, reason, internal_notes)

    def _sync_user_role_and_assignments(self, target_user, assigned_role, data, request):"""

old_target_review = """    def review(self, request, pk=None):
        \"\"\"
        Quy trình xét duyệt toàn diện của Admin:"""

new_target_review = """    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        \"\"\"
        Quy trình xét duyệt toàn diện của Admin:"""

norm_code = code.replace("\r\n", "\n")
norm_old_target = old_target.replace("\r\n", "\n")
norm_new_target = new_target.replace("\r\n", "\n")
norm_old_target_review = old_target_review.replace("\r\n", "\n")
norm_new_target_review = new_target_review.replace("\r\n", "\n")

if norm_old_target in norm_code and norm_old_target_review in norm_code:
    norm_code = norm_code.replace(norm_old_target, norm_new_target)
    norm_code = norm_code.replace(norm_old_target_review, norm_new_target_review)
    with open(views_path, "w", encoding="utf-8") as f:
        f.write(norm_code)
    print("SUCCESS: Fixed @action on review in core/views.py")
else:
    print("WARNING: Could not find exact target strings in core/views.py")
