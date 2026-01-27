# app/socket_events.py
from flask import request
from flask_socketio import emit, join_room, leave_room
from .extensions import socketio, db
from .models.models_model import User, MatchRequest, MatchSession, SkillUser
from .services.transaction_service import get_user_balance

# --- BỘ NHỚ TẠM (RAM) ---
# Lưu danh sách user đang online: { 'user_id_của_db': 'socket_id_phiên_kết_nối' }
# Vì socket_id thay đổi mỗi lần F5, nên phải map với user_id cố định.
online_users = {}


@socketio.on('connect')
def handle_connect():
    print(f"✅ Client connected: {request.sid}")
    # Lưu ý: Ở môi trường thật, Client sẽ gửi Token kèm theo để ta biết họ là ai ngay lúc connect.
    # Nhưng tạm thời để đơn giản, ta sẽ dùng sự kiện 'register' bên dưới để định danh.


@socketio.on('disconnect')
def handle_disconnect():
    # Tìm và xóa user khỏi danh sách online khi họ mất kết nối
    user_to_remove = None
    for uid, sid in online_users.items():
        if sid == request.sid:
            user_to_remove = uid
            break

    if user_to_remove:
        del online_users[user_to_remove]
        print(f"❌ User {user_to_remove} disconnected.")


# 1. ĐĂNG KÝ ONLINE (Client báo danh: "Tôi là User A, tôi đang online")
@socketio.on('register')
def handle_register(data):
    user_id = data.get('user_id')
    if user_id:
        online_users[user_id] = request.sid
        print(f"🔔 User {user_id} is now ONLINE with socket {request.sid}")
        emit('server_message', {'data': f'Hello user {user_id}, server đã ghi nhận bạn online!'}, to=request.sid)


# 2. HỌC VIÊN TÌM NGƯỜI GIÚP (Client gửi: "Tôi cần tìm người dạy skill X")
@socketio.on('find_tutor')
def handle_find_tutor(data):
    """
    Data client gửi lên: { 'student_id': '...', 'skill_id': 1, 'topic': '...', 'budget': 10 }
    """
    student_id = data.get('student_id')
    skill_id = data.get('skill_id')
    budget = data.get('budget', 0)

    print(f"🔍 Student {student_id} đang tìm Mentor skill {skill_id}...")

    # Bước 1: Check tiền (Có thực mới vực được đạo)
    current_balance = get_user_balance(student_id)
    if current_balance < budget:
        emit('error', {'message': 'Số dư không đủ!'}, to=request.sid)
        return

    # Bước 2: Lưu yêu cầu vào DB (MatchRequest)
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
        emit('error', {'message': 'Lỗi DB: ' + str(e)}, to=request.sid)
        return

    # Bước 3: Tìm các Mentor có skill này VÀ đang Online
    # Query: Tìm user_id trong bảng SkillUser có skill_id = X
    mentors_with_skill = db.session.query(SkillUser.user_id).filter_by(skill_id=skill_id).all()
    # mentors_with_skill trả về list các tuple: [('id_mentor_1',), ('id_mentor_2',)]

    found_anyone = False
    for (mentor_id,) in mentors_with_skill:
        # Nếu mentor này KHÔNG phải là chính mình VÀ đang Online
        if mentor_id != student_id and mentor_id in online_users:
            mentor_socket_id = online_users[mentor_id]

            # Gửi thông báo RIÊNG cho Mentor đó
            emit('new_request_available', {
                'request_id': new_req.id,
                'topic': new_req.topic,
                'budget': new_req.budget_credits,
                'student_id': student_id
            }, to=mentor_socket_id)
            found_anyone = True
            print(f"🚀 Đã bắn tin tới Mentor {mentor_id}")

    if found_anyone:
        emit('server_message', {'data': 'Đã gửi yêu cầu tới các Mentor đang online!'}, to=request.sid)
    else:
        emit('server_message', {'data': 'Tiếc quá, hiện không có Mentor nào online skill này.'}, to=request.sid)


# 3. MENTOR NHẬN KÈO
@socketio.on('accept_request')
def handle_accept(data):
    """
    Data gửi lên: { 'tutor_id': '...', 'request_id': '...' }
    """
    tutor_id = data.get('tutor_id')
    request_id = data.get('request_id')

    # Bước 1: Check xem Request còn đó không hay bị ai nhận rồi
    req = MatchRequest.query.get(request_id)
    if not req or req.status != 'pending':
        emit('error', {'message': 'Kèo này đã bị người khác nhận hoặc đã hủy!'}, to=request.sid)
        return

    # Bước 2: Tạo Session và cập nhật trạng thái
    try:
        # Update Request
        req.status = 'matched'

        # Tạo Session
        # Room ID tạm thời dùng chính ID của request
        new_session = MatchSession(
            request_id=request_id,
            tutor_id=tutor_id,
            room_id=f"room_{request_id}"
        )
        db.session.add(new_session)

        # Ở đây lẽ ra phải TRỪ TIỀN tạm giữ của Student (Logic Escrow mà ta đã bàn)
        # Nhưng để code gọn, tôi sẽ để phần trừ tiền vào bước sau.

        db.session.commit()

        # Bước 3: Thông báo cho cả 2 vào phòng
        # Lấy socket của Student
        student_socket = online_users.get(req.student_id)

        match_data = {
            'message': 'Ghép đôi thành công!',
            'room_id': new_session.room_id,
            'partner_id': tutor_id
        }

        # Báo cho Tutor (Người vừa bấm nhận)
        emit('match_success', match_data, to=request.sid)

        # Báo cho Student (Nếu còn online)
        if student_socket:
            match_data['partner_id'] = req.student_id  # Đổi lại partner là student
            emit('match_success', match_data, to=student_socket)

        print(f"🎉 MATCH SUCCESS: Room {new_session.room_id}")

    except Exception as e:
        db.session.rollback()
        print(e)
        emit('error', {'message': 'Lỗi server khi tạo session'}, to=request.sid)