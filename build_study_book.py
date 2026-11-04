from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT = Path('Sach_hoc_va_thuyet_trinh_BookStore_Pro.docx')

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), fill); tcPr.append(shd)

def borders(table):
    tblPr = table._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        e = OxmlElement(f'w:{edge}'); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'4'); e.set(qn('w:color'),'D9D9D9'); b.append(e)
    tblPr.append(b)

def set_cell(cell, text, bold=False, color=None):
    cell.text = ''
    p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text); r.bold = bold; r.font.size = Pt(9)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

doc = Document()
sec = doc.sections[0]
sec.top_margin = Inches(.7); sec.bottom_margin = Inches(.7); sec.left_margin = Inches(.75); sec.right_margin = Inches(.75)

styles = doc.styles
styles['Normal'].font.name = 'Aptos'; styles['Normal']._element.rPr.rFonts.set(qn('w:ascii'), 'Aptos'); styles['Normal']._element.rPr.rFonts.set(qn('w:hAnsi'), 'Aptos'); styles['Normal'].font.size = Pt(10.5)
for n, size in [('Title',25),('Heading 1',16),('Heading 2',13),('Heading 3',11)]:
    s=styles[n]; s.font.name='Aptos Display' if n!='Normal' else 'Aptos'; s.font.size=Pt(size); s.font.color.rgb=RGBColor(0,0,0)

def title(text, subtitle=None):
    p=doc.add_paragraph(style='Title'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run(text)
    if subtitle:
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(subtitle); r.italic=True; r.font.size=Pt(12)
    doc.add_paragraph()

def h(text, level=1): doc.add_heading(text, level=level)
def p(text='', boldlead=None):
    x=doc.add_paragraph()
    x.paragraph_format.space_after=Pt(6)
    if boldlead:
        r=x.add_run(boldlead); r.bold=True
    x.add_run(text)
    return x
def bullet(text, level=0):
    x=doc.add_paragraph(style='List Bullet' if level==0 else 'List Bullet 2'); x.add_run(text); return x
def code(text):
    x=doc.add_paragraph(); x.paragraph_format.left_indent=Inches(.2); x.paragraph_format.space_after=Pt(5)
    r=x.add_run(text); r.font.name='Consolas'; r._element.rPr.rFonts.set(qn('w:ascii'),'Consolas'); r.font.size=Pt(8.5); return x
def table(headers, rows, widths=None):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.style='Table Grid'; borders(t)
    for i,x in enumerate(headers): shade(t.rows[0].cells[i], '1F4D3B'); set_cell(t.rows[0].cells[i],x,True,'FFFFFF')
    for n,row in enumerate(rows):
        cells=t.add_row().cells
        for i,x in enumerate(row):
            if n%2: shade(cells[i],'F4F7F5')
            set_cell(cells[i],str(x))
    if widths:
        for row in t.rows:
            for i,w in enumerate(widths): row.cells[i].width=Inches(w)
    doc.add_paragraph()
    return t

title('Sách học và thuyết trình BookStore Pro','Tài liệu ôn code theo luồng nghiệp vụ cho bài bảo vệ công nghệ thông tin FPT')
p('Cuốn này giúp em giải thích dự án bằng ngôn ngữ của người làm sản phẩm: người dùng làm gì, dữ liệu đi đâu, mã nào chịu trách nhiệm và vì sao thiết kế đó an toàn. Không cần học thuộc từng dòng; hãy nắm luồng, tên file và lý do kỹ thuật.')
h('Cách dùng cuốn sách',1)
table(['Khi nào','Em đọc phần nào','Mục tiêu'],[
['Ôn nhanh trước bảo vệ','Chương 1, 2, 9, 10','Nói được dự án làm gì và demo không lạc luồng'],
['Bị hỏi backend','Chương 3 đến 6','Giải thích request đi qua router, schema, CRUD và database'],
['Bị hỏi frontend','Chương 7','Giải thích SPA, state, API client và từng màn hình'],
['Bị hỏi triển khai','Chương 8','Giải thích Docker, nginx, health check và Kubernetes'],
['Muốn đọc code','Bảng bản đồ file ở từng chương','Mở đúng file, đọc theo thứ tự đã gợi ý'],
])
h('Mục lục',1)
for x in ['1. Bức tranh tổng thể','2. Luồng nghiệp vụ phải thuộc','3. Backend khởi tạo và cấu hình','4. Dữ liệu và tầng CRUD','5. API và bảo mật','6. AI, nhận xét và phân tích','7. Frontend JavaScript','8. Chạy và triển khai','9. Giải thích tất cả file còn lại','10. Kịch bản thuyết trình thực tế','11. Câu hỏi phản biện và đáp án','12. Phiếu ôn 15 phút']:
    bullet(x)

h('1 Bức tranh tổng thể',1)
p('BookStore Pro là website bán sách mẫu. Khách có thể xem danh mục, lọc, đăng ký hoặc đăng nhập, thêm sách vào giỏ, tạo đơn, xem đơn, gửi đánh giá và nhận gợi ý. Quản trị viên còn quản lý sách, đơn, khách, đánh giá và trang phân tích.')
code('Trình duyệt  <->  frontend JS  <->  /api/v1 FastAPI  <->  SQLAlchemy  <->  PostgreSQL hoặc SQLite')
p('Khi chạy Docker, nginx phục vụ frontend và chuyển các đường dẫn /api, /docs, /health sang API. Khi chạy python run.py, FastAPI vừa phục vụ API vừa mount thư mục frontend.')
table(['Tầng','Việc chính','Không nên làm ở tầng này'],[
['Frontend','Hiển thị, nhận thao tác, gọi API, lưu giỏ cục bộ','Không tin frontend để phân quyền hoặc trừ kho'],
['Endpoint router','Nhận HTTP, kiểm tra quyền, đổi lỗi thành status HTTP','Không viết truy vấn SQL dài hoặc nghiệp vụ lớn'],
['CRUD service','CRUD, transaction, tính tổng, gợi ý, cảm xúc','Không tự đọc HTTP request'],
['Model và DB','Ràng buộc dữ liệu bền vững, quan hệ, lưu trữ','Không trả thẳng ra Internet'],
['Schema','Hợp đồng JSON, xác thực kiểu và giới hạn dữ liệu','Không phải bảng database'],
])
h('Điểm quan trọng để nói đúng',2)
bullet('Dự án dùng JavaScript thuần và hash router, không dùng React/Vue. index.html chỉ là cái vỏ; nội dung được app.js render vào #app.')
bullet('AI chatbot và gợi ý đang chạy bằng luật và dữ liệu trong database, không gọi API AI thật. Mục đích là demo ổn định, không tốn key. Phần AI key chỉ lưu và kiểm tra định dạng key.')
bullet('Số tiền lưu bằng Numeric và Decimal trong database để tránh lỗi Float; schema đổi sang float khi trả JSON cho trình duyệt.')

h('2 Luồng nghiệp vụ phải thuộc',1)
h('Luồng A Khách tìm và mua sách',2)
code('Catalog -> api.listBooks -> GET /api/v1/books -> books.py -> crud/book.py -> SELECT books -> JSON -> giao diện')
p('Catalog đọc query trong URL hash như #/catalog?category=fantasy&page=2. Nó đưa filter thành query parameter. books.py dùng Query để FastAPI kiểm tra giới hạn, sau đó crud.build_books_query tạo Select và database lọc, sắp xếp, phân trang. Kết quả có total để frontend vẽ phân trang.')
code('Cart -> localStorage -> Checkout -> POST /orders -> create_order -> SELECT ... FOR UPDATE -> trừ stock + tạo Order + OrderItem -> COMMIT')
p('Điểm đáng nói nhất là with_for_update: database khóa các dòng sách lúc checkout. Nhờ vậy hai người không cùng mua vượt quá số lượng kho. Một transaction tạo đơn, tạo từng dòng OrderItem, cập nhật kho, tính total rồi commit; nếu có lỗi trước commit, transaction không hoàn tất.')
h('Luồng B Đăng nhập và phân quyền',2)
code('POST /auth/login -> verify_password -> create_access_token(sub=user.id) -> JWT -> localStorage -> Authorization Bearer token -> get_current_user')
p('Mật khẩu được băm một chiều bằng pwdlib/Argon2. JWT có subject là id người dùng và thời hạn. deps.py giải mã JWT, lấy user từ database và còn kiểm tra is_active. get_current_admin chỉ nhận user có role admin. Backend mới là nơi quyết định quyền, không dựa vào nút ẩn/hiện trên frontend.')
h('Luồng C Đánh giá và AI',2)
code('POST /books/{id}/reviews -> ReviewCreate -> analyze_sentiment(text, rating) -> Review -> database')
p('sentiment.py tách từ bằng regex, cộng điểm từ từ tích cực/tiêu cực, xử lý phủ định trong ba từ trước và tăng trọng số khi có từ nhấn mạnh. Rating cộng thêm hoặc trừ bớt một điểm. Đây là heuristic, không phải mô hình học máy.')

h('3 Backend khởi tạo và cấu hình',1)
table(['File','Đọc như thế nào','Ý chính'],[
['backend/app/main.py','Điểm vào FastAPI','lifespan gọi initialize_database trước khi nhận request; gắn api_router ở /api/v1; có /health; mount frontend nếu thư mục tồn tại.'],
['backend/app/core/config.py','Nguồn cấu hình','Settings đọc .env hoặc ../.env; bắt buộc database_url và secret_key; kiểm tra secret ít nhất 32 ký tự; cache bằng lru_cache.'],
['backend/app/db/session.py','Kết nối sync','Tạo Base, engine, SessionLocal và dependency get_db. pool_pre_ping phát hiện kết nối database chết. SQLite có check_same_thread False; memory dùng StaticPool cho test.'],
['backend/app/db/session_async.py','Kết nối async','Tạo AsyncEngine, factory AsyncSession và get_async_db. Chỉ books-async dùng bản này để đối chiếu.'],
['backend/app/api/v1/api.py','Bộ gom router','include_router cho auth, admin, books, books_async, orders, reviews, AI, AI keys, analytics.'],
['backend/app/api/deps.py','Cổng bảo vệ','OAuth2 bearer token; _user_from_token xác thực JWT và user; cung cấp current, optional và admin user.'],
])
h('Hai khái niệm dễ nhầm',2)
table(['Khái niệm','Nghĩa trong bài'],[['lifespan','Hàm chạy khi app bắt đầu/kết thúc; bài dùng để tạo bảng và seed dữ liệu.'],['Depends','Cơ chế FastAPI tự cấp dependency, ví dụ Session hoặc user đã đăng nhập, cho endpoint.'],['Annotated','Gắn type hint với metadata Depends/Query mà vẫn dễ đọc.'],['lru_cache','Giữ lại Settings/engine đã tạo để không tạo lại mỗi request.']])

h('4 Dữ liệu và tầng CRUD',1)
h('4 1 Models là bảng database',2)
table(['File','Bảng và quan hệ','Điểm trả lời khi bị hỏi'],[
['models/book.py','Category(code,name); Book có category_code khóa ngoại, title, author, price, stock, cover','CheckConstraint giữ price và stock không âm; category dùng RESTRICT nên không xóa thể loại đang được sách dùng.'],
['models/user.py','User: email unique, hashed_password, role, is_active','Database chỉ chứa hash password, không chứa password gốc.'],
['models/order.py','Order thuộc User; OrderItem thuộc Order và tham chiếu Book','OrderItem lưu title và unit_price tại lúc mua: lịch sử đơn không đổi nếu sách sau này đổi giá/tên.'],
['models/review.py','Review thuộc Book; user_id có thể null nếu user bị xóa','JSON keywords chứa các từ khóa; rating 1 đến 5 và sentiment bị giới hạn bằng constraint.'],
['models/ai_key.py','AIKey thuộc User','Lưu encrypted_key và key_hint; response không có encrypted_key hoặc key gốc.'],
])
h('4 2 Schemas là hợp đồng JSON',2)
p('Các file schemas/book.py, auth.py, order.py, review.py, ai.py, ai_key.py, analytics.py mô tả dữ liệu vào/ra. Field kiểm tra min/max, Decimal, EmailStr, Literal. ConfigDict(from_attributes=True) cho Pydantic đọc thuộc tính từ SQLAlchemy model. response_model lọc trường nhạy cảm: UserRead không có hashed_password, AIKeyRead không có encrypted_key.')
table(['Schema tiêu biểu','Tác dụng'],[['BookCreate / BookUpdate / BookRead','Tách create, update một phần và dữ liệu trả về; BookRead có computed is_available từ stock.'],['RegisterRequest / TokenResponse / UserRead','Kiểm tra email và password; trả JWT; không lộ password hash.'],['OrderCreate / OrderItemCreate','Giới hạn quantity 1 đến 20 và số dòng 1 đến 50.'],['ReviewCreate','Kiểm tra rating và text 3 đến 2000 ký tự trước khi vào nghiệp vụ.'],['AIKeyCreate / AIKeyRead','Nhận key tạm thời để mã hóa; chỉ trả provider, label, hint, thời gian.']])
h('4 3 CRUD và transaction',2)
table(['File','Hàm chính','Điều cần hiểu'],[
['crud/book.py','build_books_query, list_books, stats, categories, create/update/delete','Tách dựng query dùng chung cho sync và async. ilike tìm title/author, offset/limit phân trang, allowlist SORT_COLUMNS tránh sắp xếp tùy ý.'],
['crud/user.py','get_user_by_email, create_customer','Lowercase email, hash password rồi commit/refresh. Endpoint vẫn xử lý IntegrityError để chống race condition.'],
['crud/order.py','create_order, list_orders, update_order_status','Gộp item trùng, khóa stock, kiểm tra thiếu hàng, tạo snapshot item. Hủy đơn trả stock. ALLOWED_TRANSITIONS là state machine.'],
['crud/review.py','list, summary, create, keyword_counts','Dùng Counter tổng hợp sentiment và keyword; create gọi service phân tích trước khi lưu.'],
['crud/ai_key.py','list/get/create/delete','Mọi get/list đều lọc theo user_id; đây là chống IDOR. create mã hóa key và chỉ giữ hint.'],
['crud/analytics.py','build_overview','Tổng hợp doanh thu, đơn, tồn kho, khách và chuỗi dữ liệu biểu đồ cho admin.'],
])

h('5 API và bảo mật',1)
h('Đọc endpoint theo mẫu 5 câu hỏi',2)
p('Khi mở bất kỳ endpoint nào, hãy trả lời: URL là gì? Ai được gọi? Input được schema nào kiểm tra? Nó gọi CRUD/service nào? Lỗi nào trả về? Đây là cách giải thích đầy đủ mà không cần đọc từng ký tự decorator.')
table(['Endpoint file','Những route chính','Quyền và xử lý'],[
['endpoints/books.py','GET categories/stats/list/{id}; POST, PATCH, DELETE','Đọc công khai; sửa catalog cần admin. Static routes đặt trên /{book_id} để categories không bị coi là id.'],
['endpoints/books_async.py','Bộ route /books-async tương đương','Khác ở async def và await db.execute/scalars/commit. Dùng cùng hàm dựng query ở CRUD.'],
['endpoints/auth.py','register, login, me','Login dùng OAuth2PasswordRequestForm để Swagger Authorize hoạt động; sai thông tin trả 401.'],
['endpoints/orders.py','tạo đơn, đơn của tôi, chi tiết đơn','Phải login. Người dùng chỉ thấy đơn của mình; admin được xem mọi đơn chi tiết. Không tồn tại hoặc không có quyền đều trả 404 để hạn chế dò dữ liệu.'],
['endpoints/reviews.py','GET/POST /books/{id}/reviews','Đọc công khai, ghi cần login; kiểm tra book tồn tại trước.'],
['endpoints/admin.py','users, đổi role, orders, đổi status, reviews dashboard','Toàn router cần admin. Không tự hạ role admin và không hạ admin cuối cùng.'],
['endpoints/analytics.py','GET /analytics/overview','Admin-only, trả data đã chuẩn bị cho chart.'],
['endpoints/ai.py','providers, recommendations, chat','Có optional user nên khách chưa login vẫn dùng được nhưng recommendation cá nhân hóa khi có token.'],
['endpoints/ai_keys.py','list/create/delete/verify key','Phải login; key luôn được lấy cùng user_id; verify chỉ kiểm tra giải mã và format, không gọi nhà cung cấp.'],
])
h('Bảo mật nói thật, không phóng đại',2)
bullet('Có: Argon2 hash password, JWT HMAC HS256 có expiry, role check, input validation, database constraint, transaction, key encryption Fernet, và ownership filter.')
bullet('Chưa có/đáng bổ sung cho production: refresh token hoặc revoke token, rate limit, CSRF nếu chuyển sang cookie, logging/audit, migration Alembic, test đầy đủ, secrets manager và gọi AI provider thật có timeout/cost control.')

h('6 AI nhận xét và phân tích',1)
table(['File','Nó làm gì','Cách nói ngắn'],[
['core/ai_providers.py','Dataclass khai báo OpenAI, Gemini, Grok, DeepSeek; mask_key tạo hint như sk-...9f2a','Danh mục provider tập trung để frontend không hard-code.'],
['core/security.py','hash/verify password, tạo JWT, biến SECRET_KEY thành Fernet key, encrypt/decrypt','Password chỉ so sánh nên hash; API key phải dùng lại nên encrypt đối xứng.'],
['services/ai_verify.py','Kiểm tra provider tồn tại, prefix và độ dài key','Đây là format validation, không xác nhận key còn tiền/quyền thật.'],
['services/sentiment.py','Lexicon positive/negative, negation, intensifier, tokenize, score','AI nhẹ chạy offline; kết quả minh bạch nhưng kém ngôn ngữ tự nhiên hơn LLM.'],
['services/recommender.py','Tính popularity từ OrderItem, lọc sách có stock, cá nhân hóa theo category đã mua, hiểu genre/budget bằng regex','Chatbot là rule based retrieval: hiểu vài ý định rồi trả sách từ catalog thật.'],
['crud/analytics.py','Tạo KPI và mảng điểm theo tháng, category, product, status, customer','Backend trả dữ liệu thô có cấu trúc; frontend chỉ vẽ chart, không tự tính KPI quan trọng.'],
])
h('Câu hỏi bảo mật AI key',2)
p('Nếu bị hỏi “tại sao không hash API key?”: vì server cần đọc lại key để gọi provider, nên hashing một chiều không dùng được. Ta dùng Fernet encrypt; database bị lộ thì key vẫn không đọc được nếu SECRET_KEY ở môi trường không bị lộ. Nếu SECRET_KEY thay đổi, key cũ không giải mã được và verify trả invalid_format.')

h('7 Frontend JavaScript',1)
p('Frontend là ES module. index.html tải css/style.css và js/app.js. app.js là bộ điều phối: theo dõi hashchange, render layout chung, gọi module view phù hợp; đồng thời subscribe state để cập nhật header/giỏ. Không có framework nên các view tự tạo innerHTML và đăng ký event listener.')
table(['File','Vai trò','Ví dụ giải thích'],[
['index.html','Vỏ tối thiểu: #app, modalRoot, toastRoot','SPA thay nội dung #app, không tải một HTML mới cho mỗi trang.'],
['js/api.js','Fetch wrapper và danh mục API','request thêm Bearer token, encode JSON/form, đổi lỗi API thành ApiError. api object là một nơi duy nhất biết URL endpoint.'],
['js/store.js','State token/user/cart và observer','Giỏ và token ở localStorage. emit thông báo UI khi auth/cart đổi. cartAdd không vượt stock đã biết, nhưng backend vẫn kiểm tra lúc checkout.'],
['js/ui.js','Hàm UI tái dùng','esc ngăn HTML injection khi render dữ liệu; money, bookCard, toast, modal, loading, error/empty view.'],
['js/app.js','Hash router, layout header/footer, drawer giỏ, route guard','Chọn view theo URL #/, #/catalog, #/book/id, #/login, #/orders, #/admin, #/ai, #/analytics.'],
['views/home.js','Trang chủ','Promise.all lấy category và hai page sách song song; dựng tile và sách nổi bật.'],
['views/catalog.js','Tìm/lọc/sắp xếp/phân trang','Đọc/ghi query hash; debounce input 260ms; map sort UI sang sort_by/order API.'],
['views/book.js','Chi tiết, thêm giỏ, review','Lấy book, gọi cartAdd, tải review và gửi form review khi đã login.'],
['views/auth.js','Login/register/demo account','Gọi api.login/register, setToken, loadUser rồi quay lại route trước.'],
['views/orders.js','Danh sách đơn cá nhân','Gọi myOrders và định dạng ngày/tổng từng order item.'],
['views/admin.js','Admin UI','CRUD inventory, quản lý role/order/review bằng các API admin.'],
['views/ai.js','Chat, recommendations, quản lý AI key','Chat cục bộ qua endpoint; key UI không hiển thị raw key sau khi tạo.'],
['views/analytics.js','KPI và biểu đồ','Gọi analytics của admin và tạo biểu đồ bằng SVG/HTML từ dữ liệu backend.'],
['css/style.css','Design system và responsive layout','Không chứa logic nghiệp vụ; chỉ định hình trang và trạng thái UI.'],
])
h('Hai điểm nên tự kiểm tra',2)
bullet('Luôn gọi esc() cho dữ liệu đưa vào innerHTML. Nếu bỏ esc, title/review chứa thẻ HTML có thể gây XSS.')
bullet('localStorage tiện cho demo nhưng token XSS-sensitive. Production có thể cân nhắc access token ngắn hạn và cookie HttpOnly cùng CSRF protection.')

h('8 Chạy và triển khai',1)
table(['File','Nhiệm vụ','Điểm nói khi demo'],[
['run.py','Launcher Python một lệnh','Đọc .env, chọn Python venv, kiểm tra port, bật riêng postgres Docker nếu cần, chờ port, chạy uvicorn và mở browser. --sqlite bỏ Docker.'],
['start.bat','Lối tắt Windows','Gọi run.py để người dùng không cần gõ lệnh dài.'],
['docker-compose.yml','Ba service postgres, api, frontend','Health check tạo thứ tự postgres khỏe -> api khỏe -> frontend. DB host 5433, trong network dùng postgres:5432. Volume giữ dữ liệu.'],
['backend/Dockerfile','Đóng gói API','Build image Python để chạy FastAPI độc lập môi trường máy.'],
['frontend/Dockerfile','Đóng gói website','Đưa static frontend vào nginx image.'],
['frontend/nginx.conf','Serve SPA và reverse proxy','Cùng origin nên frontend gọi /api/v1, tránh CORS trong demo.'],
['k8s/*.yaml','Manifest tham khảo K8s','Deployment giữ replica/pod, Service tạo địa chỉ nội bộ, ConfigMap chứa config không nhạy cảm, Ingress nhận traffic ngoài.'],
['powerbi/documentation.md','Hướng dẫn Power BI','Tài liệu cho dashboard BI ngoài web app.'],
])
h('9 Giải thích tất cả file còn lại',1)
p('Những file dưới đây không phải logic request hằng ngày nhưng vẫn nên biết để trả lời “file này để làm gì?”.')
table(['Nhóm','File','Giải thích'],[
['Khởi tạo dữ liệu','db/init_db.py','Import toàn bộ model để metadata biết bảng; create_all; seed category, 100 sách, admin, khách demo, đơn và review nếu database còn trống.'],
['Khởi tạo dữ liệu','db/mock_data.py','Danh sách 100 sách mẫu dùng cho seed. Đây là data fixture, không phải nghiệp vụ.'],
['Tiện ích','backend/create_admin.py','CLI tạo hoặc nâng quyền admin mà không phải sửa database thủ công.'],
['Tiện ích','backend/scripts/generate_covers.py','Sinh lại ảnh bìa SVG với đúng tên sách.'],
['Kiểm thử','backend/test/test_auth.py','Pytest kiểm tra hành vi xác thực; là nền để tránh sửa code làm hỏng login.'],
['Phụ thuộc','backend/requirements.txt','Khai báo FastAPI, SQLAlchemy, psycopg, Pydantic, JWT, crypto, test.'],
['Tài nguyên','frontend/static/covers/*.svg và Resource_Demo/Covers/*.svg','100 ảnh bìa, dữ liệu tĩnh được hiển thị; không cần giải thích từng file SVG.'],
['Bản demo cũ','Resource_Demo/Front_End và Demo_Web','Tài nguyên/thử nghiệm giao diện tham khảo; ứng dụng chính hiện tại nằm ở frontend và backend.'],
['Tài liệu','README.md','Tài liệu tổng quan, cài đặt, route, tài khoản demo và kịch bản giảng dạy.'],
['Tài liệu','powerbi/documentation.md','Cách dùng Power BI cho dữ liệu phân tích.'],
['Log/database local','backend/dev.db, server stdout/stderr log','Artifact chạy local, không phải source code để trình bày; tránh commit log/key thật.'],
])
h('10 Kịch bản thuyết trình thực tế',1)
p('Thời lượng đề xuất 8 đến 10 phút. Đừng mở đầu bằng cây thư mục; hãy cho hội đồng thấy một nhu cầu thật rồi chứng minh code giải quyết nó.')
table(['Phút','Em làm gì trên màn hình','Lời thoại gợi ý'],[
['0:00-0:40','Mở trang chủ','“Đây là BookStore Pro, mô phỏng luồng bán sách từ catalog đến checkout và dashboard quản trị. Điểm em tập trung là phân tầng backend, an toàn dữ liệu và khả năng triển khai.”'],
['0:40-1:40','Catalog: tìm, lọc, sang trang, mở chi tiết','“Mỗi thao tác đổi filter thành query parameter. Backend lọc trực tiếp trong database, không tải toàn bộ catalog về trình duyệt.”'],
['1:40-2:40','Thêm giỏ, đăng nhập tài khoản demo, checkout','“Giỏ là trải nghiệm phía client; lúc tạo đơn backend mới kiểm kho, khóa dòng sách và trừ kho trong một transaction.”'],
['2:40-3:30','Mở đơn vừa tạo và code crud/order.py','“OrderItem lưu đơn giá tại thời điểm mua nên lịch sử không thay đổi khi giá catalog đổi. Nếu cancel, state machine hoàn kho.”'],
['3:30-4:30','Mở đăng nhập và deps.py/security.py','“Password hash bằng Argon2, sau login server cấp JWT. Endpoint quản trị dùng Depends(get_current_admin), nên đổi URL trên browser cũng không vượt quyền.”'],
['4:30-5:30','Gửi review, mở dashboard review/AI','“Review được kiểm tra schema rồi sentiment chạy offline bằng luật từ vựng. Chat và recommendation là rule-based trên catalog, không giả vờ gọi LLM.”'],
['5:30-6:40','Đăng nhập admin, admin/analytics','“Analytics được tính ở backend và chỉ admin gọi được. Frontend chủ yếu trình bày dữ liệu đã tổng hợp.”'],
['6:40-7:40','Mở Docker compose và kiến trúc','“Triển khai tách postgres, API và nginx. Health check bảo đảm dependency khỏe trước khi service sau khởi động.”'],
['7:40-8:30','Chốt hạn chế và kế hoạch','“Bản tiếp theo sẽ thêm migration, rate limit, refresh token, test coverage và provider AI thật có quản lý chi phí.”'],
])
h('Cách đứng trình bày',2)
bullet('Mỗi lần click phải nói đủ ba vế: hành động người dùng, API được gọi, dữ liệu/kiểm tra nào diễn ra. Ví dụ: “Bấm thanh toán -> POST /orders -> transaction khóa stock và tạo đơn”.')
bullet('Khi mở code, chỉ mở đúng 1 file endpoint và 1 file CRUD. Đừng cuộn nhiều file liên tục; hội đồng cần thấy mối nối chứ không cần thấy hết chữ.')
bullet('Nếu demo có lỗi mạng/DB, chuyển ngay sang Swagger /docs hoặc code luồng. Luôn chuẩn bị --sqlite để không phụ thuộc Docker.')

h('11 Câu hỏi phản biện và đáp án',1)
table(['Câu hỏi','Trả lời gọn và đúng'],[
['Model khác schema thế nào?','Model ánh xạ bảng database; schema kiểm tra/định nghĩa JSON qua API. Tách ra để không vô tình lộ hashed_password hoặc encrypted_key.'],
['Vì sao cần response_model?','Vừa tạo tài liệu OpenAPI vừa lọc output và validation. Ví dụ UserRead không có hashed_password.'],
['Vì sao static route trước /{id}?','Router so khớp theo thứ tự; nếu để sau, categories có thể bị parse như book_id và trả 422.'],
['Sync khác async?','Query logic có thể giống nhau. Async khác ở engine/session và await lúc chờ I/O; phù hợp khi cần phục vụ nhiều I/O đồng thời.'],
['Vì sao server phải kiểm stock dù client đã kiểm?','Client có thể bị sửa hoặc dữ liệu cũ. Server là nguồn đáng tin và with_for_update giải quyết cạnh tranh khi checkout.'],
['JWT có mã hóa nội dung không?','Không nhất thiết. Bài ký JWT để chống sửa giả; payload không nên chứa bí mật.'],
['Tại sao AI key encrypt thay vì hash?','Cần giải mã để gọi provider; hash thì không khôi phục được.'],
['Có phải chatbot là AI thật không?','Không phải LLM. Nó là recommendation/chatbot rule-based chạy offline, minh bạch và phù hợp demo; key management chuẩn bị cho tích hợp AI thật.'],
['Một nhược điểm bảo mật?','Token localStorage có rủi ro XSS; production sẽ giảm bề mặt XSS, dùng token ngắn hạn/cookie HttpOnly và CSRF phù hợp.'],
])

h('12 Phiếu ôn 15 phút',1)
table(['Thời gian','Việc ôn'],[['3 phút','Vẽ sơ đồ browser -> API -> CRUD -> DB; nói luồng checkout không nhìn sách.'],['3 phút','Mở main.py, api.py, deps.py; nói lifespan, prefix, Depends và JWT.'],['3 phút','Mở models/order.py + crud/order.py; nói snapshot giá, transaction, lock stock, cancel hoàn kho.'],['3 phút','Mở api.js + store.js; nói fetch, Bearer, localStorage, frontend không phải nơi phân quyền.'],['3 phút','Đọc câu hỏi phản biện; chọn 3 câu trả lời thành lời của chính mình.']])
h('Checklist trước khi bảo vệ',2)
for x in ['Chạy thử python run.py --sqlite --no-browser hoặc Docker trước giờ trình bày.', 'Có sẵn URL /docs, một tài khoản admin và một tài khoản customer.', 'Tạo sẵn một đơn mới để dashboard có thay đổi nhìn thấy được.', 'Không dùng API key thật trong demo; chỉ nói về luồng mã hóa/format.', 'Nói rõ phần nào là demo rule-based và phần nào là kế hoạch production.']:
    bullet('□ ' + x)
p('Kết luận: Bài này mạnh nhất khi em trình bày như một hệ thống có dữ liệu thật và ranh giới trách nhiệm rõ: frontend tạo trải nghiệm, FastAPI kiểm soát request và quyền, CRUD/service xử lý nghiệp vụ, còn database bảo vệ tính đúng đắn cuối cùng.')

for section in doc.sections:
    footer=section.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=footer.add_run('BookStore Pro - Tài liệu ôn tập'); r.font.size=Pt(8); r.font.color.rgb=RGBColor(90,90,90)

doc.save(OUT)
print(OUT.resolve())
