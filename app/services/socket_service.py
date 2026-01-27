# app/services/socket_service.py
from flask_socketio import emit
from ..extensions import db, socketio
from ..models.models_model import MatchRequest, MatchSession, SkillUser, User
from ..services.transaction_service import get_user_balance, hold_credits

# --- QUẢN LÝ TRẠNG THÁI ONLINE (STATE) ---
# Biến này nên để ở Service để các hàm logic truy xuất được
online_users = {}

def add_online_user(user_id, sid):
    """Lưu user vào danh sách online"""
    online_users[user_id] = sid
    print(f"🔔 Service: User {user_id} online with ID {sid}")
    # Có thể bắn noti cho bạn bè tại đây nếu muốn


def remove_online_user(sid):
    """Xóa user khỏi danh sách online khi disconnect"""
    user_to_remove = None
    for uid, socket_id in online_users.items():
        if socket_id == sid:
            user_to_remove = uid
            break

    if user_to_remove:
        del online_users[user_to_remove]
        print(f"❌ Service: User {user_to_remove} disconnected.")
    return user_to_remove


def process_find_tutor(data, sid):
    """Xử lý logic tìm người dạy"""
    student_id = data.get('student_id')
    skill_id = data.get('skill_id')
    budget = data.get('budget', 0)

    # 1. Validate tiền
    if get_user_balance(student_id) < budget:
        emit('search_error', {'message': 'Số dư không đủ!'}, to=sid)  # ✅ Đổi
        return

    # 2. Lưu DB
    try:
        new_req = MatchRequest(
            student_id=student_id,
            skill_id=skill_id,
            topic=data.get('topic'),
            description=data.get('description'),
            budget_credits=budget
        )
        db.session.add(new_req)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        emit('search_error', {'message': 'Lỗi DB'}, to=sid)  # ✅ Đổi
        return

    # 3. Tìm Mentor Online & Bắn thông báo
    mentors = db.session.query(SkillUser.user_id).filter_by(skill_id=skill_id).all()
    count = 0

    for (m_id,) in mentors:
        if m_id != student_id and m_id in online_users:
            mentor_sid = online_users[m_id]
            emit('new_request_available', {
                'request_id': new_req.id,
                'topic': new_req.topic,
                'budget': new_req.budget_credits,
                'student_id': student_id
            }, to=mentor_sid)
            count += 1

    if count > 0:
        emit('server_message', {'data': f'Đã gửi tới {count} mentor!'}, to=sid)
    else:
        emit('search_error', {'message': 'Không có mentor nào online.'}, to=sid)  # ✅ Đổi

def process_accept_request(data, sid):
    """Xử lý logic chấp nhận kèo (Có trừ tiền tạm giữ)"""
    tutor_id = data.get('tutor_id')
    request_id = data.get('request_id')

    # 1. Validate Request
    req = MatchRequest.query.get(request_id)
    if not req or req.status != 'pending':
        emit('error', {'message': 'Kèo này không còn khả dụng (đã ghép hoặc bị hủy)!'}, to=sid)
        return

    # Check không cho tự nhận kèo của chính mình (đề phòng hack)
    if req.student_id == tutor_id:
        emit('error', {'message': 'Bạn không thể tự nhận kèo của mình!'}, to=sid)
        return

    # 2. Bắt đầu Transaction DB (Để đảm bảo: Tạo session + Trừ tiền phải cùng thành công)
    try:
        # --- [LOGIC MỚI] TRỪ TIỀN TẠM GIỮ (ESCROW) ---
        # Nếu student không đủ tiền, hàm này sẽ báo lỗi -> Nhảy xuống except -> Rollback hết
        if req.budget_credits > 0:
            hold_credits(
                user_id=req.student_id,
                amount=req.budget_credits,
                description=f"Tạm giữ cho phiên học {req.topic}",
                related_id=tutor_id
            )
        # ----------------------------------------------

        # Cập nhật trạng thái Request
        req.status = 'matched'

        # Tạo Session mới
        new_session = MatchSession(
            request_id=request_id,
            tutor_id=tutor_id,
            room_id=f"room_{request_id}"  # ID phòng tạm thời
        )
        db.session.add(new_session)

        # Chốt đơn: Lưu tất cả vào DB (Cả trừ tiền và tạo session)
        db.session.commit()

    except ValueError as ve:
        db.session.rollback()
        # Lỗi do logic (ví dụ: Không đủ tiền)
        print(f"❌ Escrow failed: {ve}")
        emit('error', {'message': f'Giao dịch thất bại: {str(ve)}'}, to=sid)
        return
    except Exception as e:
        db.session.rollback()
        # Lỗi hệ thống
        print(f"❌ System error: {e}")
        emit('error', {'message': 'Lỗi hệ thống khi tạo phiên học'}, to=sid)
        return

    # 3. Thông báo thành công (Code cũ)
    match_data = {
        'message': 'Ghép đôi thành công! Tiền đã được tạm giữ.',
        'room_id': new_session.room_id,
        'partner_id': tutor_id
    }

    # Gửi cho Tutor
    emit('match_success', match_data, to=sid)

    # Gửi cho Student
    student_sid = online_users.get(req.student_id)
    if student_sid:
        match_data['partner_id'] = req.student_id
        emit('match_success', match_data, to=student_sid)


def process_cancel_request(data, sid):
    """
    Xử lý khi Student đang tìm mà muốn Hủy (Bấm nút X trên giao diện đếm giờ)
    """
    student_id = data.get('student_id')

    # 1. Tìm cái Request đang 'pending' của student này
    # Lấy cái mới nhất
    req = MatchRequest.query.filter_by(student_id=student_id, status='pending') \
        .order_by(MatchRequest.created_at.desc()).first()

    if not req:
        emit('error', {'message': 'Bạn không có yêu cầu nào đang chờ.'}, to=sid)
        return

    try:
        # 2. Đổi trạng thái sang cancelled
        req.status = 'cancelled'
        db.session.commit()

        emit('server_message', {'data': 'Đã hủy tìm kiếm thành công.'}, to=sid)
        print(f"🚫 Student {student_id} cancelled request {req.id}")

        # (Nâng cao) Nếu muốn xịn hơn: Bắn tin cho các Mentor Online bảo là "Kèo nãy hủy rồi nhé, đừng bấm nữa"
        # Nhưng tạm thời chưa cần, vì bên Mentor khi bấm nhận ta đã check status != pending rồi.

    except Exception as e:
        db.session.rollback()
        emit('error', {'message': 'Lỗi hệ thống khi hủy'}, to=sid)