# Backend: cấu trúc và luồng chạy

Backend dùng FastAPI, SQLAlchemy 2 và PostgreSQL. API hiện thực phần đăng ký,
đăng nhập JWT và phân quyền `customer` / `admin`.

## Cấu trúc thư mục

```text
backend/
├── .env.example                 # Mẫu cấu hình; sao chép thành .env
├── Dockerfile                   # Đóng gói API FastAPI
├── requirements.txt             # Thư viện chạy và kiểm thử
├── app/
│   ├── main.py                  # Tạo FastAPI, khởi tạo bảng, gắn router
│   ├── create_admin.py          # CLI tạo tài khoản admin ban đầu
│   ├── core/
│   │   ├── config.py            # Đọc và kiểm tra biến môi trường
│   │   └── security.py          # Băm mật khẩu, cấp JWT
│   ├── db/
│   │   ├── session.py           # SQLAlchemy engine, Base, dependency DB
│   │   └── init_db.py           # Khởi tạo bảng
│   ├── models/
│   │   └── user.py              # Bảng users
│   ├── schemas/
│   │   └── auth.py              # Kiểm tra request và định dạng response
│   ├── crud/
│   │   └── user.py              # Truy vấn và tạo tài khoản customer
│   └── api/
│       ├── deps.py              # Lấy user hiện tại và kiểm tra admin
│       └── v1/
│           ├── api.py           # Gom router phiên bản v1
│           └── endpoints/
│               ├── auth.py      # Đăng ký, đăng nhập, hồ sơ hiện tại
│               └── admin.py     # Danh sách user và đổi role
└── tests/
    └── test_auth.py             # Kiểm thử đăng nhập và phân quyền
```

## Luồng xử lý

### Đăng ký

1. `POST /api/v1/auth/register` nhận tên, email và mật khẩu.
2. Pydantic kiểm tra dữ liệu; email được chuẩn hóa chữ thường.
3. CRUD kiểm tra email trùng; mật khẩu được băm Argon2 trước khi ghi database.
4. Tài khoản mới luôn có role `customer`. Trường role gửi thêm từ client không
   cấp quyền admin.
5. Response chỉ trả dữ liệu hồ sơ công khai, không trả mật khẩu hoặc hash.

### Đăng nhập và xác thực request

1. `POST /api/v1/auth/login` nhận form OAuth2: `username` là email và `password`
   là mật khẩu. Swagger UI có thể dùng endpoint này qua nút **Authorize**.
2. Backend so sánh mật khẩu với hash đã lưu; thông tin sai trả `401`.
3. Khi đăng nhập thành công, backend ký JWT HS256 chứa ID user và thời gian hết
   hạn. Không đưa role vào token; role được đọc từ database mỗi request để quyền
   thay đổi có hiệu lực ngay.
4. Client đính kèm JWT trong HTTP Authorization header. `get_current_user` kiểm
   tra chữ ký, hạn token, tài khoản và trạng thái hoạt động.
5. `/api/v1/admin/*` gọi thêm `get_current_admin`; customer nhận `403`.

### Quản lý role

- Admin xem tài khoản qua `GET /api/v1/admin/users`.
- Admin đổi role qua `PATCH /api/v1/admin/users/{user_id}/role` với
  `{"role": "customer"}` hoặc `{"role": "admin"}`.
- Không thể tự hạ quyền hoặc hạ quyền admin cuối cùng.
- Tạo admin đầu tiên bằng CLI có dấu nhắc nhập mật khẩu ẩn:

  ```powershell
  cd backend
  Copy-Item .env.example .env
  # Thay SECRET_KEY bằng giá trị ngẫu nhiên dài tối thiểu 32 ký tự.
  pip install -r requirements.txt
  python -m app.create_admin
  ```

Tạo secret an toàn trong PowerShell (đặt giá trị kết quả vào `SECRET_KEY` trong
`.env`):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Từ thư mục gốc `EprojectSem2`, khởi động PostgreSQL:

```powershell
docker compose up -d
```

Đảm bảo PostgreSQL trong `docker-compose.yml` đang chạy trước khi tạo admin.
Ứng dụng tạo bảng khi khởi động lần đầu; với môi trường production nên chuyển
sang Alembic migrations.

## Chạy và kiểm thử

Từ thư mục `backend`, sau khi tạo `.env` và bật PostgreSQL:

```powershell
uvicorn app.main:app --reload
```

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- Kiểm thử: `pytest`

Không commit `.env`; `SECRET_KEY` phải là bí mật riêng của môi trường.
