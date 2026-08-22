"""Toàn bộ chữ giao diện của StudyFlow Simple nằm trong file này."""

TEXT = {
    "en": {
        "window": "StudyFlow Simple — Teaching Edition",
        "language": "Language",
        "dashboard": "Dashboard",
        "subjects": "Subjects",
        "tasks": "Tasks",
        "subject_count": "Subjects",
        "pending_count": "Pending tasks",
        "today_count": "Due today",
        "recommendation": "Simple recommendation",
        "no_tasks": "No pending task. Add a task to receive a recommendation.",
        "study_today": "Study {subject} today. The task “{task}” is due {deadline}.",
        "subject_library": "Subject library",
        "custom_subject": "Other / Custom subject",
        "name_en": "English name",
        "name_vi": "Vietnamese name",
        "add_subject": "Add subject",
        "delete_subject": "Delete selected subject",
        "task_title": "Task title",
        "subject": "Subject",
        "deadline": "Deadline",
        "add_task": "Add task",
        "complete_task": "Complete selected task",
        "delete_task": "Delete selected task",
        "id": "ID",
        "name": "Name",
        "title": "Title",
        "status": "Status",
        "todo": "To do",
        "completed": "Completed",
        "message": "StudyFlow",
        "fill_names": "Enter both English and Vietnamese names.",
        "subject_exists": "This subject already exists.",
        "select_subject": "Select a subject first.",
        "enter_title": "Enter a task title.",
        "select_row": "Select a row first.",
        "subject_in_use": "This subject is being used by a task and cannot be deleted.",
    },
    "vi": {
        "window": "StudyFlow Simple — Phiên bản giảng dạy",
        "language": "Ngôn ngữ",
        "dashboard": "Tổng quan",
        "subjects": "Môn học",
        "tasks": "Nhiệm vụ",
        "subject_count": "Số môn học",
        "pending_count": "Nhiệm vụ chưa xong",
        "today_count": "Đến hạn hôm nay",
        "recommendation": "Gợi ý đơn giản",
        "no_tasks": "Chưa có nhiệm vụ cần làm. Hãy thêm nhiệm vụ để nhận gợi ý.",
        "study_today": "Hôm nay hãy học {subject}. Nhiệm vụ “{task}” có hạn {deadline}.",
        "subject_library": "Thư viện môn học",
        "custom_subject": "Môn khác / Tự thêm",
        "name_en": "Tên tiếng Anh",
        "name_vi": "Tên tiếng Việt",
        "add_subject": "Thêm môn",
        "delete_subject": "Xóa môn đã chọn",
        "task_title": "Tên nhiệm vụ",
        "subject": "Môn học",
        "deadline": "Hạn chót",
        "add_task": "Thêm nhiệm vụ",
        "complete_task": "Hoàn thành nhiệm vụ đã chọn",
        "delete_task": "Xóa nhiệm vụ đã chọn",
        "id": "ID",
        "name": "Tên",
        "title": "Tiêu đề",
        "status": "Trạng thái",
        "todo": "Cần làm",
        "completed": "Hoàn thành",
        "message": "StudyFlow",
        "fill_names": "Hãy nhập cả tên tiếng Anh và tên tiếng Việt.",
        "subject_exists": "Môn học này đã tồn tại.",
        "select_subject": "Hãy chọn môn học trước.",
        "enter_title": "Hãy nhập tên nhiệm vụ.",
        "select_row": "Hãy chọn một hàng trước.",
        "subject_in_use": "Môn này đang được nhiệm vụ sử dụng nên chưa thể xóa.",
    },
}


SUBJECT_LIBRARY = [
    {"key": "mathematics", "en": "Mathematics", "vi": "Toán học"},
    {"key": "literature", "en": "Literature", "vi": "Ngữ văn"},
    {"key": "english", "en": "English", "vi": "Tiếng Anh"},
    {"key": "physics", "en": "Physics", "vi": "Vật lý"},
    {"key": "chemistry", "en": "Chemistry", "vi": "Hóa học"},
    {"key": "biology", "en": "Biology", "vi": "Sinh học"},
    {"key": "history", "en": "History", "vi": "Lịch sử"},
    {"key": "geography", "en": "Geography", "vi": "Địa lý"},
    {"key": "informatics", "en": "Informatics", "vi": "Tin học"},
]


def translate(language, key, **values):
    """Lấy câu theo ngôn ngữ và thay các biến trong câu."""
    sentence = TEXT[language].get(key, key)
    return sentence.format(**values)


def library_subject(key):
    """Tìm một môn trong thư viện bằng key."""
    for subject in SUBJECT_LIBRARY:
        if subject["key"] == key:
            return subject
    return None
