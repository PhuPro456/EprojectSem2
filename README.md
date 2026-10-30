# BookStore Pro - Fullstack Boilerplate & Production-Grade FastAPI Project
> **Phiên bản Mở Rộng Chuyên Nghiệp (Production-Ready Edition)**  
> **Môn học:** Building Backend API with Python and AI  
> **Phạm vi bài giảng:** Session 01-02 (kiến trúc & định tuyến) → Session 05 (PostgreSQL)
> → Session 06 (JWT) → Session 10 (bảo mật AI Key)

---

## 🌟 Giới Thiệu Dự Án

Dự án này là phiên bản nâng cấp hoàn chỉnh từ bài thực hành cơ bản, được cấu trúc theo **chuẩn kiến trúc công nghiệp thực tế (Production-Ready Architecture)**

Khác với các ví dụ viết dồn vào một file `main.py`, dự án này tách biệt rõ ràng các tầng trách nhiệm (**Separation of Concerns**), sử dụng hệ thống định tuyến phân cụm **`APIRouter`**, phiên bản hóa API (**API Versioning `/api/v1`**) và tích hợp sẵn một **Demo Frontend Client** hiện đại (HTML/CSS Glassmorphism/Vanilla JS) 
**mô hình Client - Server** vận hành trong thực tế.

---

## 📂 Cấu Trúc Thư Mục Chuẩn Doanh Nghiệp (Project Structure)

```text
BookProject/
├── docker-compose.yml                  # PostgreSQL cho cả lớp, chạy bằng 1 lệnh
├── .env.example                        # Mẫu biến môi trường (copy thành .env)
├── requirements.txt                    # Thư viện phụ thuộc
├── requests_test.http                  # Bộ test gửi trực tiếp trong VS Code / Postman
│
├── app/                                # Mã nguồn Backend
│   ├── main.py                         # Khởi tạo FastAPI, lifespan, CORS, mount routers
│   │
│   ├── core/                           # Cấu hình & bảo mật dùng chung
│   │   ├── config.py                   # Settings đọc từ .env (pydantic-settings)
│   │   ├── security.py                 # Băm mật khẩu, JWT, mã hóa AI key
│   │   └── ai_providers.py             # Danh mục ChatGPT / Gemini / Grok / DeepSeek
│   │
│   ├── db/                             # Tầng kết nối cơ sở dữ liệu
│   │   ├── session.py                  # [SYNC]  engine, SessionLocal, Base, get_db
│   │   ├── session_async.py            # [ASYNC] async_engine, AsyncSessionLocal
│   │   ├── init_db.py                  # Tạo bảng + nạp dữ liệu mẫu lúc khởi động
│   │   └── mock_data.py                # Dữ liệu mẫu, nay dùng làm nguồn seed
│   │
│   ├── models/                         # SQLAlchemy Model - cấu trúc BẢNG dưới database
│   │   ├── book.py                     # Category, Book
│   │   ├── user.py                     # User
│   │   └── ai_key.py                   # AIKey
│   │
│   ├── schemas/                        # Pydantic Schema - hình dạng JSON qua đường mạng
│   │   ├── book.py    user.py    ai_key.py
│   │
│   ├── crud/                           # Tầng truy vấn dùng lại được (Repository)
│   │   ├── book.py    user.py    ai_key.py
│   │
│   ├── services/                       # Nghiệp vụ gọi ra bên ngoài
│   │   └── ai_verify.py                # Gọi thử nhà cung cấp AI kiểm tra key
│   │
│   └── api/                            # Tầng định tuyến
│       ├── deps.py                     # get_current_user - bảo vệ endpoint
│       └── v1/
│           ├── api.py                  # Gom các Sub-router
│           └── endpoints/
│               ├── health.py           # /health (có kiểm tra kết nối database)
│               ├── books.py            # [SYNC]  CRUD sách
│               ├── books_async.py      # [ASYNC] bản đối chiếu của chính các truy vấn đó
│               ├── auth.py             # /auth/register, /auth/login, /auth/me
│               └── ai_keys.py          # CRUD AI key theo từng người dùng
│
├── frontend/                           # Giao diện Demo Client
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
│
└── .gitignore
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy Nhanh

### 1. Di chuyển vào thư mục dự án
```bash
cd Demos/BookProject
```

### 2. Khởi động PostgreSQL bằng Docker
```bash
docker compose up -d        # Bật database
docker compose ps           # Chờ tới khi cột STATUS hiện chữ (healthy)
```
> Database chạy ở cổng **5433** của máy thật (không phải 5432) để tránh đụng
> PostgreSQL sẵn có trên máy. Dữ liệu được giữ trong Docker volume nên tắt máy
> bật lại vẫn còn nguyên.

### 3. Tạo file cấu hình `.env`
```bash
cp .env.example .env
```
> Ứng dụng sẽ **từ chối khởi động** nếu thiếu file này. Đó là chủ ý: không bao giờ
> có "khóa bí mật mặc định" trong mã nguồn.

### 4. Khởi tạo và kích hoạt Môi trường ảo (`venv`)
* **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```

### 5. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 6. Khởi chạy máy chủ
```bash
uvicorn app.main:app --reload
```
> Lần chạy đầu tiên, ứng dụng tự tạo bảng và nạp 9 cuốn sách mẫu vào PostgreSQL.
> Đặt `SQL_ECHO=True` trong `.env` để nhìn thấy tận mắt từng câu SQL mà ORM sinh ra.

### Các lệnh Docker hay dùng khi giảng dạy
```bash
docker compose logs -f postgres    # Xem log database
docker compose down                # Tắt database, dữ liệu vẫn còn
docker compose down -v             # Xóa sạch làm lại từ đầu (mất hết dữ liệu)

# Vào thẳng dòng lệnh psql để sinh viên nhìn dữ liệu thật:
docker exec -it bookstore-postgres psql -U bookstore -d bookstore_db
#   \dt                 liệt kê các bảng
#   SELECT * FROM books;
#   SELECT provider, label, key_hint, encrypted_key FROM ai_keys;
```

---

## 🌐 Các Điểm Truy Cập Hệ Thống

| Mục đích | Địa chỉ URL | Mô tả |
| :--- | :--- | :--- |
| **Giao diện Demo Client** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | Ứng dụng Web App trực quan kết nối trực tiếp với Backend |
| **Swagger UI Interactive Docs** | [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs) | Trang tài liệu tương tác tự động chuẩn OpenAPI v1 |
| **ReDoc Documentation** | [http://127.0.0.1:8000/api/v1/redoc](http://127.0.0.1:8000/api/v1/redoc) | Giao diện tài liệu dạng đặc tả kỹ thuật |
| **Health Check Endpoint** | [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health) | Kiểm tra Backend **và kết nối PostgreSQL** |
| **Bản Sync (luồng chính)** | `GET /api/v1/books` | Truy vấn sách kiểu đồng bộ |
| **Bản Async (đối chiếu)** | `GET /api/v1/books-async` | Cùng kết quả, thực thi bất đồng bộ |

---

## 💎 Các Tính Năng Đột Phá Được Triển Khai

### 1. Kiến trúc phân tầng và `APIRouter` (Session 02 - Slide 06 & 09)
* Thay vì gắn toàn bộ decorator vào biến `app` toàn cục, mỗi nhóm tính năng được định nghĩa qua `router = APIRouter()`.
* File `app/api/v1/api.py` gom nhóm các route con với tiền tố rõ ràng (`prefix="/books"`). Khi cần nâng cấp lên `v2`, chỉ cần tạo thêm thư mục `v2/` mà không ảnh hưởng code cũ.

### 2. Tránh "Bẫy thứ tự định tuyến" (Session 02 - Slide 10)
Trong file `app/api/v1/endpoints/books.py`, các Static Route:
* `GET /books/categories`
* `GET /books/bestseller`
* `GET /books/stats`
được định nghĩa **hoàn toàn phía trên** Dynamic Route:
* `GET /books/{book_id}`
Đảm bảo các chuỗi như `"categories"` hoặc `"bestseller"` không bao giờ bị bóc nhầm thành `{book_id}`.

### 3. Bộ lọc Query Parameters chuyên sâu (Session 02 - Slide 12 & 13)
Route `GET /api/v1/books` hỗ trợ đầy đủ các kỹ thuật lọc nâng cao:
* **Tìm kiếm từ khóa (`keyword`):** Tìm kiếm không phân biệt hoa thường trong cả tiêu đề và tên tác giả.
* **Lọc theo thể loại (`category`):** `it`, `ai`, `business`, `skills`.
* **Lọc theo giá tối đa (`max_price`):** Ràng buộc `ge=0`.
* **Lọc trạng thái còn hàng (`is_available`):** `true`/`false`.
* **Sắp xếp (`sort_by` & `order`):** Hỗ trợ sắp theo `id`, `price`, `rating`, `year` theo chiều tăng hoặc giảm.
* **Phân trang (`skip` & `limit`):** Giới hạn `ge=1, le=50` để chống tấn công làm quá tải RAM máy chủ.

### 4. Tầng Cơ sở dữ liệu PostgreSQL (Session 05)
Dữ liệu không còn nằm trong RAM mà tồn tại vĩnh viễn trên đĩa:
* **Tách bạch `models/` và `schemas/`:** nhìn cây thư mục là hiểu ngay ranh giới giữa
  SQLAlchemy Model (cấu trúc bảng dưới database) và Pydantic Schema (hình dạng JSON trên đường mạng).
* **Khóa ngoại thật:** `books.category` trỏ tới `categories.code`, PostgreSQL tự chặn thể loại không tồn tại.
* **`Numeric` cho tiền tệ, không dùng `Float`:** tránh sai số cộng dồn kiểu `0.1 + 0.2 != 0.3`.
* **Lọc / sắp xếp / phân trang chạy dưới database:** chỉ đúng số bản ghi của trang hiện tại
  được truyền lên, thay vì kéo cả kho sách vào RAM rồi mới cắt bằng Python.
* **Thống kê bằng một câu truy vấn gộp** dùng cú pháp `FILTER (WHERE ...)` của PostgreSQL.
* **Health check thật:** database chết thì `/health` trả **503**, không phải 200 kèm dòng chữ báo lỗi.

### 5. Đối chiếu SYNC và ASYNC trong cùng một dự án
Hai file đặt cạnh nhau, trả về kết quả **giống hệt nhau**, khác đúng 4 điểm:

| # | Sync (`books.py`, `session.py`) | Async (`books_async.py`, `session_async.py`) |
|---|---|---|
| 1 | `def list_books(...)` | `async def list_books(...)` |
| 2 | `create_engine` / `sessionmaker` | `create_async_engine` / `async_sessionmaker` |
| 3 | `Session = Depends(get_db)` | `AsyncSession = Depends(get_async_db)` |
| 4 | `db.execute(stmt)` | `await db.execute(stmt)` |

Điểm mấu chốt cần sinh viên nhận ra: hàm dựng truy vấn `build_books_query()` được **dùng
chung y hệt** cho cả hai bản. Sync và Async không khác nhau ở cách **viết** truy vấn, mà chỉ
khác ở khoảnh khắc **thực thi**. Gọi thử để tự kiểm chứng:
```bash
curl "http://127.0.0.1:8000/api/v1/books?category=it&limit=3"
curl "http://127.0.0.1:8000/api/v1/books-async?category=it&limit=3"
```
> Cùng một chuỗi kết nối và cùng driver `psycopg` phục vụ được cả hai chế độ,
> nên **không cần cài thêm `asyncpg`**.

### 6. Xác thực người dùng bằng JWT (Session 06)
* `POST /auth/register` - mật khẩu được **băm một chiều** bằng bcrypt, phản hồi không bao giờ chứa `hashed_password`.
* `POST /auth/login` - theo chuẩn OAuth2 nên nút **Authorize** trên Swagger UI dùng được ngay.
* `Depends(get_current_user)` - thêm một dòng là endpoint bất kỳ trở thành endpoint được bảo vệ.

### 7. Quản lý AI Key theo từng người dùng (Session 06 + Session 10)
Hỗ trợ **ChatGPT (OpenAI), Google Gemini, Grok (xAI), DeepSeek**. Ba bài học bảo mật:

**a) Mã hóa hai chiều, không phải băm**

| | Mật khẩu | AI API Key |
|---|---|---|
| Hệ thống cần gì | Chỉ cần **so sánh** | Cần **đọc lại** để gọi nhà cung cấp |
| Kỹ thuật | Băm một chiều (bcrypt) | Mã hóa hai chiều (Fernet) |
| Lộ database thì sao | An toàn tuyệt đối | An toàn, vì khóa giải mã nằm ở `.env`, **ngoài** database |

Câu hỏi kiểm tra: *"Sao không băm luôn AI key cho chắc?"* → Vì băm xong thì chính chúng ta
cũng không đọc lại được key để gọi AI.

**b) Key chỉ đi vào một chiều**
Không endpoint nào trả về key gốc. Người dùng chỉ thấy chuỗi gợi nhớ `sk-...9f2a`. Muốn đổi
thì tạo key mới hoặc xoay key - đúng cách GitHub, OpenAI, Google Cloud đang làm.
Mở psql xem tận mắt database chỉ chứa một mớ ký tự vô nghĩa:
```bash
docker exec -it bookstore-postgres psql -U bookstore -d bookstore_db \
  -c "SELECT provider, label, key_hint, left(encrypted_key, 40) FROM ai_keys;"
```

**c) Chống lỗ hổng IDOR**
Mọi truy vấn AI key đều bắt buộc kèm `user_id`. Xem **Phần 7** trong `requests_test.http`:
tài khoản Bình dùng token hợp lệ của mình để đọc key của An và nhận về **404** - chứ không
phải 403, vì 403 là vô tình xác nhận với kẻ tấn công rằng key đó có tồn tại.

### 8. Giao diện Frontend Trực Quan với "Realtime API Inspector"
Giao diện Web App tích hợp thanh công cụ sư phạm độc đáo:
* Mỗi khi người dùng bấm nút lọc, xem chi tiết sách hoặc chuyển trang, bảng **Realtime API Inspector** bên phải sẽ tự động hiển thị:
  * **HTTP Method:** `GET`
  * **Đường dẫn Request URL thực tế:** (kèm toàn bộ chuỗi Query Parameters)
  * **Mã trạng thái phản hồi (Status Code):** `200 OK`, `404 NOT FOUND`, `422 UNPROCESSABLE ENTITY`.
  * **Thời gian phản hồi (Latency):** tính bằng mili-giây (ms).
  * **Nội dung JSON thô (Raw JSON Payload):** giúp sinh viên thấy rõ cách dữ liệu di chuyển từ Backend lên Frontend.

### 9. Khu vực Thử nghiệm Lỗi (Simulated Error Playground)
Tích hợp sẵn các nút bấm kích hoạt nhanh các lỗi kinh điển để giảng viên biểu diễn:
* **🚨 Nút Test 404 (ID không tồn tại):** Gọi `GET /api/v1/books/999` ➡️ Trình diễn cách `HTTPException` trả về JSON thông báo lỗi.
* **🛑 Nút Test 422 (Sai Type Hints):** Gọi `GET /api/v1/books/sach-ai-khong-phai-so` ➡️ Trình diễn cách FastAPI chặn dữ liệu rác trước khi chạm vào code Python.
* **🛑 Nút Test 422 (Ràng buộc Range):** Gọi `GET /api/v1/books?limit=100` ➡️ Trình diễn cách `Query(le=50)` bảo vệ Backend khỏi request vượt quá ngưỡng.

---

## 👨‍🏫 Kịch Bản Đề Xuất Cho Giảng Viên Khi Lên Lớp

### Buổi 01-02: Kiến trúc và Định tuyến
1. Mở [http://127.0.0.1:8000/](http://127.0.0.1:8000/) cho sinh viên xem giao diện và bảng
   **Realtime API Inspector**: mỗi cú click chuột biến thành một gói tin HTTP.
2. Đối chiếu cây thư mục `core/`, `api/`, `db/` với mô hình chuẩn trong slide.
3. Bấm 3 nút trong **Error Playground** để xem lỗi 404 và 422.

### Buổi 05: Cơ sở dữ liệu
1. `docker compose down -v` rồi `up -d` ngay trên lớp: cả lớp thấy database được dựng lại từ số không.
2. Đặt `SQL_ECHO=True`, gọi `GET /books?category=it`, chỉ vào terminal cho sinh viên đọc câu SQL
   mà ORM vừa sinh ra.
3. Mở song song `session.py` và `session_async.py` trong VS Code, gọi `/books` và `/books-async`
   với cùng tham số để chứng minh kết quả giống hệt nhau.
4. **Trình diễn health check:** `docker compose stop postgres` → gọi `/health` → nhận **503**.
   Bật lại → gọi lại → **200**, mà không cần khởi động lại server (nhờ `pool_pre_ping`).

### Buổi 06 + 10: Bảo mật và AI Key
1. Chạy `requests_test.http` **Phần 5**: đăng ký xong, chỉ vào phản hồi và hỏi
   *"hashed_password đâu rồi?"* → dẫn vào vai trò của `response_model`.
2. Dán token lên [jwt.io](https://jwt.io) cho sinh viên đọc trực tiếp nội dung bên trong
   → chốt lại: **JWT là ký số chống làm giả, không phải mã hóa che giấu**.
3. Chạy **Phần 6**: thêm AI key rồi mở psql xem database chỉ lưu chuỗi mã hóa.
4. Chạy **Phần 7** (kịch bản tấn công IDOR): Bình đọc key của An → nhận 404.
   Sau đó xóa điều kiện `user_id` trong `app/crud/ai_key.py` và chạy lại → Bình đọc được key
   của An. Đây là khoảnh khắc sư phạm mạnh nhất của cả buổi học.

---

## 🗺️ Lộ Trình Mở Rộng Tiếp Theo

| Session | Nội dung | Trạng thái |
| :--- | :--- | :--- |
| 01-02 | Kiến trúc phân tầng, APIRouter, Query Parameters | ✅ Đã có |
| 03-04 | Pydantic Schema, CRUD đầy đủ | ✅ Đã có |
| 05 | PostgreSQL + SQLAlchemy (cả Sync và Async) | ✅ Đã có |
| 06 | JWT, băm mật khẩu, bảo vệ endpoint | ✅ Đã có |
| 07 | Exception handler tập trung, logging có che thông tin nhạy cảm | ⏳ Chưa |
| 08 | Kiểm thử tự động với Pytest | ⏳ Chưa |
| 10-11 | Gọi AI thật bằng key của từng người dùng, đếm token và chi phí | ⏳ Chưa |
| 12 | Alembic migration, triển khai production | ⏳ Chưa |
