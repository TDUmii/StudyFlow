# GIÁO TRÌNH STUDYFLOW SIMPLE

## Khóa Python ứng dụng — 17 tuần

Giáo trình này dùng bản `teaching/` làm dự án học tập chính. Học sinh xây app theo từng lát cắt nhỏ, luôn có sản phẩm chạy được cuối mỗi tuần. Bản StudyFlow đầy đủ trong `app/` chỉ được dùng làm tài liệu mở rộng ở giai đoạn cuối.

## 1. Mục tiêu đầu ra

Sau khóa học, học sinh có thể:

- dùng biến, kiểu dữ liệu, `if`, vòng lặp, list và dictionary;
- chia chương trình thành hàm và module;
- đọc, ghi và cập nhật CSV bằng UTF-8;
- tạo giao diện PySide6 có form, nút, bảng và tab;
- nối sự kiện giao diện với logic Python;
- thực hiện CRUD thật;
- xử lý quan hệ môn học — nhiệm vụ;
- tìm kiếm, lọc, sắp xếp và tổng hợp dữ liệu;
- viết quy tắc gợi ý có thể giải thích;
- kiểm tra dữ liệu và xử lý lỗi đầu vào;
- viết pytest cho logic quan trọng;
- sử dụng Git/GitHub theo từng commit nhỏ;
- trình bày được luồng dữ liệu của ứng dụng.

## 2. Sản phẩm cuối khóa

Học sinh hoàn thiện StudyFlow Simple với ba trang:

1. **Tổng quan** — thống kê số môn, số nhiệm vụ và gợi ý hôm nay.
2. **Môn học** — chọn thư viện song ngữ hoặc thêm môn riêng.
3. **Nhiệm vụ** — thêm, hoàn thành và xóa nhiệm vụ.

Dữ liệu được lưu trong ba file:

```text
subjects.csv
tasks.csv
settings.csv
```

Luồng chính:

```text
Học sinh nhập trên UI
        ↓
Python lấy text/value
        ↓
Tạo dictionary
        ↓
Ghi vào CSV
        ↓
Đọc lại list of dictionaries
        ↓
Làm mới bảng và dashboard
```

## 3. Cách tổ chức mỗi buổi

Thời lượng gợi ý: 2 buổi/tuần, mỗi buổi 90 phút.

Một buổi học:

1. 10 phút — ôn kiến thức tuần trước.
2. 20 phút — giáo viên minh họa một ví dụ nhỏ ngoài dự án.
3. 35 phút — học sinh ghép kiến thức vào StudyFlow.
4. 15 phút — kiểm thử bằng thao tác thật và xem CSV.
5. 10 phút — commit Git và viết nhật ký học tập.

Không đưa sẵn toàn bộ lời giải ngay đầu tuần. Giáo viên chia code thành các bước 5–20 dòng, chạy sau từng bước.

---

# TUẦN 1 — BIẾN, KIỂU DỮ LIỆU VÀ BÀI TOÁN STUDYFLOW

## Mục tiêu

- Hiểu app sẽ giải quyết vấn đề gì.
- Dùng `str`, `int`, `bool` và biến.
- Phân biệt dữ liệu hiển thị và dữ liệu lưu trữ.

## Nội dung

```python
student_name = "Minh"
subject_name = "Toán học"
pending_tasks = 3
is_completed = False
```

Thảo luận vì sao `pending_tasks` là số còn `subject_name` là chuỗi. Cho học sinh tạo một “thẻ tổng quan” bằng lệnh `print()`.

## Bài thực hành

- In tên học sinh.
- In tên môn đang học.
- Tính tổng số phút học của ba buổi.
- Đổi trạng thái nhiệm vụ từ `False` sang `True`.

## Sản phẩm cuối tuần

File console nhỏ in được thông tin học tập đúng kiểu dữ liệu.

## Câu hỏi kiểm tra

- Vì sao ID nên là số nguyên?
- Vì sao ngày có thể lưu thành chuỗi `YYYY-MM-DD`?
- Khi nào dùng `bool`?

---

# TUẦN 2 — IF / ELIF / ELSE VÀ QUY TẮC HỌC TẬP

## Mục tiêu

- Viết điều kiện rõ ràng.
- Tạo gợi ý không dùng AI/API.

## Ví dụ

```python
days_left = 0

if days_left < 0:
    message = "Nhiệm vụ đã quá hạn"
elif days_left == 0:
    message = "Nhiệm vụ đến hạn hôm nay"
else:
    message = "Vẫn còn thời gian"
```

## Bài thực hành

- Phân loại điểm quiz: yếu, trung bình, tốt.
- Chọn câu gợi ý dựa trên hạn chót.
- Không gợi ý nhiệm vụ đã hoàn thành.

## Sản phẩm cuối tuần

Hàm `make_message(status, days_left)` trả về câu phù hợp.

---

# TUẦN 3 — LIST VÀ VÒNG LẶP

## Mục tiêu

- Lưu nhiều môn/nhiệm vụ trong list.
- Duyệt dữ liệu bằng `for`.
- Đếm và lọc thủ công.

## Ví dụ

```python
subjects = ["Toán học", "Tiếng Anh", "Vật lý"]

for subject in subjects:
    print(subject)
```

## Bài thực hành

- Đếm nhiệm vụ chưa hoàn thành.
- Tạo list chỉ chứa nhiệm vụ môn Toán.
- Tìm nhiệm vụ có hạn gần nhất mà chưa dùng `min()`.

## Sản phẩm cuối tuần

Dashboard console cho biết số môn và số nhiệm vụ cần làm.

---

# TUẦN 4 — DICTIONARY VÀ MÔ HÌNH DỮ LIỆU

## Mục tiêu

- Biểu diễn một bản ghi bằng dictionary.
- Hiểu key/value.
- Hiểu quan hệ qua `subject_id`.

## Ví dụ

```python
subject = {
    "id": "1",
    "key": "mathematics",
    "name_en": "Mathematics",
    "name_vi": "Toán học",
}

task = {
    "id": "1",
    "title": "Làm bài tập đại số",
    "subject_id": "1",
    "deadline": "2026-08-25",
    "status": "TODO",
}
```

## Bài thực hành

- Lấy tên tiếng Việt từ dictionary môn học.
- Tìm môn của một nhiệm vụ qua `subject_id`.
- Đổi `status` từ `TODO` sang `COMPLETED`.

## Sản phẩm cuối tuần

List of dictionaries mô tả được ít nhất hai môn và ba nhiệm vụ.

---

# TUẦN 5 — HÀM VÀ PHÂN RÃ BÀI TOÁN

## Mục tiêu

- Tránh viết một khối code dài.
- Hiểu tham số, giá trị trả về và phạm vi biến.

## Các hàm mục tiêu

```python
def next_id(rows):
    ...

def subject_name(subject, language):
    ...

def count_pending(tasks):
    ...
```

## Bài thực hành

- Viết `find_subject(subjects, subject_id)`.
- Viết `count_tasks_due_today(tasks, today)`.
- Mỗi hàm chỉ làm một việc và có tên mô tả đúng hành động.

## Sản phẩm cuối tuần

Logic tuần 1–4 được chia thành các hàm có thể gọi lại.

---

# TUẦN 6 — MODULE, PACKAGE VÀ CẤU TRÚC BẢN SIMPLE

## Mục tiêu

- Hiểu vì sao tách file.
- Biết `import` hàm từ module khác.
- Không tách mỗi hàm thành một file.

## Cấu trúc

```text
teaching/
├── csv_helper.py
├── translations.py
└── main.py
```

## Bài thực hành

- Chuyển các câu giao diện vào `translations.py`.
- Chuyển hàm CSV vào `csv_helper.py`.
- Import và gọi thử từ `main.py`.

## Sản phẩm cuối tuần

Chạy được `python -m teaching.main` mà không lỗi import.

---

# TUẦN 7 — ĐỌC VÀ GHI CSV

## Mục tiêu

- Hiểu header, row, `DictReader` và `DictWriter`.
- Dùng UTF-8 và `newline=""`.
- Theo dõi luồng dictionary ↔ CSV.

## Phần code học

Đọc toàn bộ `teaching/csv_helper.py`. Giáo viên viết lại từng hàm trên file thử nghiệm nhỏ trước khi dùng trong app.

## Bài thực hành

- Tạo `subjects.csv` có header.
- Ghi một môn tiếng Việt.
- Đóng chương trình, mở lại và đọc đúng dấu.
- Thử nội dung có dấu phẩy và dấu nháy kép.

## Sản phẩm cuối tuần

Hai hàm `read_csv()` và `write_csv()` chạy được độc lập.

---

# TUẦN 8 — CRUD VÀ GHI FILE AN TOÀN

## Mục tiêu

- Phân biệt Create, Read, Update, Delete.
- Biết vì sao update/delete phải ghi lại danh sách.
- Dùng file tạm trước khi thay file cũ.

## Bài thực hành

- Create: `append()` dictionary vào list rồi ghi CSV.
- Read: đọc toàn bộ list.
- Update: tìm ID rồi đổi status.
- Delete: tạo list mới không chứa ID cần xóa.

## Cảnh báo thực tế

Không chỉnh file giữa chừng bằng cách ghi đè trực tiếp. Nếu chương trình dừng khi đang ghi, dữ liệu có thể hỏng. Bản Simple dùng `.tmp` rồi `os.replace()`.

## Sản phẩm cuối tuần

CRUD console hoàn chỉnh cho nhiệm vụ.

---

# TUẦN 9 — PYSIDE6 CƠ BẢN

## Mục tiêu

- Tạo `QApplication`, `QMainWindow`, `QWidget` và layout.
- Hiểu widget cha/con.
- Chạy event loop.

## Ví dụ tối thiểu

```python
app = QApplication([])
window = QMainWindow()
window.setWindowTitle("StudyFlow Simple")
window.show()
app.exec()
```

## Bài thực hành

- Tạo cửa sổ 850 × 560.
- Thêm tiêu đề.
- Thêm `QTabWidget` có ba tab trống.
- Không làm logic CSV trong tuần này.

## Sản phẩm cuối tuần

Khung giao diện mở và đóng bình thường.

---

# TUẦN 10 — FORM, BUTTON VÀ SIGNAL

## Mục tiêu

- Dùng `QLineEdit`, `QComboBox`, `QDateEdit`, `QPushButton`.
- Nối `clicked.connect()` với hàm Python.
- Đọc dữ liệu từ widget.

## Bài thực hành

- Form môn học có thư viện, tên Anh và tên Việt.
- Nút “Thêm môn” gọi `add_subject()`.
- Kiểm tra ô trống trước khi ghi.
- Dùng `QMessageBox` báo lỗi dễ hiểu.

## Sản phẩm cuối tuần

Thêm được môn vào CSV từ giao diện.

---

# TUẦN 11 — HIỂN THỊ DỮ LIỆU BẰNG TABLE

## Mục tiêu

- Tạo `QTableWidget`.
- Thêm hàng và ô bằng vòng lặp.
- Chọn toàn bộ hàng.
- Không cho sửa dữ liệu trực tiếp trong table.

## Bài thực hành

- Đọc subjects.csv.
- Xóa các hàng cũ trên UI bằng `setRowCount(0)`.
- Thêm lại từng hàng.
- Lấy ID từ hàng được chọn.

## Sản phẩm cuối tuần

Bảng môn học luôn khớp với CSV sau khi thêm/xóa.

---

# TUẦN 12 — QUAN HỆ MÔN HỌC VÀ NHIỆM VỤ

## Mục tiêu

- Hiểu foreign key theo cách đơn giản.
- Không lưu lặp tên môn trong tasks.csv.
- Ngăn xóa môn đang được sử dụng.

## Bài thực hành

- Combo nhiệm vụ hiển thị tên môn nhưng lưu `subject_id`.
- Tạo dictionary `subject_names[id] = name`.
- Khi hiển thị task, đổi ID thành tên.
- Duyệt nhiệm vụ trước khi xóa môn.

## Sản phẩm cuối tuần

Thêm nhiệm vụ gắn đúng môn và bảo vệ quan hệ dữ liệu.

---

# TUẦN 13 — TÌM KIẾM, LỌC VÀ SẮP XẾP

## Mục tiêu

- Dùng `casefold()` để tìm không phân biệt hoa/thường.
- Dùng list comprehension sau khi đã hiểu vòng lặp thường.
- Dùng `sort(key=...)`.

## Bài thực hành mở rộng

- Thêm ô tìm kiếm nhiệm vụ.
- Lọc `TODO` và `COMPLETED`.
- Sắp xếp theo deadline.
- So sánh kết quả với cách viết vòng lặp dài.

## Sản phẩm cuối tuần

Học sinh tự thêm tìm kiếm/lọc vào bản Simple mà không chép từ bản đầy đủ.

---

# TUẦN 14 — SONG NGỮ VÀ DỮ LIỆU ỔN ĐỊNH

## Mục tiêu

- Phân biệt mã nội bộ và chữ hiển thị.
- Hiểu vì sao không lưu “Toán học” làm khóa duy nhất.
- Chuyển ngôn ngữ mà không đổi quan hệ dữ liệu.

## Bài thực hành

- Đọc `translations.py`.
- `mathematics` luôn là key.
- Hiển thị `Mathematics` khi English và `Toán học` khi Tiếng Việt.
- Môn tự thêm phải có `name_en` và `name_vi`.
- Lưu ngôn ngữ trong settings.csv.

## Sản phẩm cuối tuần

Đổi ngôn ngữ và mở lại app vẫn giữ lựa chọn; môn và nhiệm vụ không bị nhân đôi.

---

# TUẦN 15 — DASHBOARD VÀ GỢI Ý THEO QUY TẮC

## Mục tiêu

- Tổng hợp dữ liệu bằng vòng lặp và điều kiện.
- Viết gợi ý có nguồn gốc rõ ràng.
- Không giả vờ dùng AI.

## Quy tắc bản Simple

1. Lấy các nhiệm vụ chưa hoàn thành.
2. Sắp xếp theo deadline.
3. Chọn nhiệm vụ có hạn gần nhất.
4. Tìm tên môn qua `subject_id`.
5. Điền dữ liệu vào mẫu câu.

## Bài thực hành

- Đếm nhiệm vụ đến hạn hôm nay.
- Hiển thị nhiệm vụ gần nhất.
- Thêm quy tắc “quá hạn” như bài nâng cao.
- Yêu cầu học sinh giải thích từng dòng mà không dùng từ “AI hiểu”.

## Sản phẩm cuối tuần

Dashboard phản ánh dữ liệu thật và thay đổi ngay sau CRUD.

---

# TUẦN 16 — TESTING, LỖI VÀ CHẤT LƯỢNG

## Mục tiêu

- Viết pytest cho hàm thuần và luồng chính.
- Kiểm tra persistence.
- Phân biệt test logic và test giao diện.

## Test bắt buộc

- CSV giữ đúng tiếng Việt, dấu phẩy, dấu nháy và dòng mới.
- `next_id()` đúng khi list rỗng và khi đã xóa ID.
- Thêm môn thư viện lưu đúng key.
- Thêm task lưu đúng subject_id.
- Đổi ngôn ngữ hiển thị đúng tên môn.
- Đóng/mở lại vẫn giữ dữ liệu và ngôn ngữ.

## Kiểm tra thủ công

- Nhấn mọi nút.
- Thử form rỗng.
- Thử xóa môn đang được task sử dụng.
- Chọn hàng và kiểm tra chữ không biến mất.
- Mở CSV sau mỗi thao tác.

## Sản phẩm cuối tuần

Test tự động đạt và có checklist kiểm thử thủ công.

---

# TUẦN 17 — GIT, TRÌNH BÀY VÀ NÂNG CẤP

## Mục tiêu

- Hoàn thiện README.
- Dùng commit nhỏ, có ý nghĩa.
- Trình bày kiến trúc bằng ngôn ngữ của học sinh.
- Biết đường nâng cấp lên bản đầy đủ.

## Chuỗi commit gợi ý

```text
Create StudyFlow console data model
Add CSV read and write functions
Add PySide6 application shell
Add subject management
Add task management
Add bilingual interface
Add dashboard recommendation
Add tests and teaching documentation
```

## Nội dung báo cáo cuối khóa

1. Vấn đề app giải quyết.
2. Cấu trúc ba file chính.
3. Luồng UI → dictionary → CSV → UI.
4. Quan hệ subject_id.
5. Cách đổi ngôn ngữ.
6. Quy tắc gợi ý.
7. Một lỗi đã gặp và cách kiểm thử.
8. Demo đóng/mở app vẫn giữ dữ liệu.

## Bài nâng cấp tự chọn

- Tìm kiếm nhiệm vụ.
- Bộ lọc trạng thái.
- Ưu tiên LOW/MEDIUM/HIGH.
- Thời lượng học.
- Biểu đồ Matplotlib.
- Flashcard.
- Quiz.

Học sinh chỉ mở bản đầy đủ trong `app/` sau khi hoàn thành bản Simple. Giáo viên chỉ ra cách mỗi phần Simple được tách thành model, repository, service và page khi dự án lớn lên.

---

# 4. Rubric chấm điểm cuối khóa

| Nhóm | Điểm | Yêu cầu |
|---|---:|---|
| Python cơ bản | 20 | Biến, điều kiện, vòng lặp, list/dict và hàm đúng |
| CSV | 20 | Đọc/ghi/cập nhật/xóa, UTF-8, dữ liệu còn sau restart |
| Giao diện | 20 | Form, table, signal và validation hoạt động thật |
| Logic ứng dụng | 15 | Quan hệ môn-task, dashboard và gợi ý đúng dữ liệu |
| Testing | 10 | Có test tự động và checklist thủ công |
| Git/README | 10 | Commit rõ, hướng dẫn chạy đầy đủ |
| Trình bày | 5 | Học sinh tự giải thích được code |

Tổng: **100 điểm**.

# 5. Tiêu chí “học sinh thật sự hiểu”

Không chấm chỉ dựa trên việc app chạy. Học sinh phải làm được ít nhất bốn việc sau mà không nhìn đáp án:

1. Thêm một field mới vào task và cập nhật CSV/UI.
2. Viết lại hàm lọc nhiệm vụ chưa hoàn thành.
3. Giải thích vì sao task lưu subject_id thay vì tên môn.
4. Sửa một validation và viết test cho nó.
5. Thêm một câu dịch ở cả English và Tiếng Việt.

# 6. Ghi chú cho giáo viên

- Bản Simple là code học; bản đầy đủ là code tham khảo nâng cao.
- Không dạy 439 dòng `main.py` theo thứ tự từ trên xuống trong một buổi.
- Mỗi tuần xây lại một phần trong branch hoặc thư mục bài tập riêng.
- Luôn yêu cầu học sinh dự đoán CSV trước khi mở file kiểm tra.
- Khi học sinh mắc lỗi, ưu tiên in/quan sát dữ liệu thay vì sửa hộ ngay.
- Chỉ giới thiệu repository/service sau khi học sinh thấy `main.py` bắt đầu dài và tự nêu nhu cầu tách lớp.
- Đây là thời điểm tự nhiên để chuyển từ StudyFlow Simple sang kiến trúc đầy đủ.
