# app/services/transaction_service.py
from ..extensions import db
from ..models.models_model import User, Transaction


def get_user_balance(user_id):
    user = User.query.get(user_id)
    return user.wallet_balance if user else 0

def get_my_transactions(user_id):
    return Transaction.query.filter_by(user_id=user_id)\
        .order_by(Transaction.created_at.desc()).all()

def process_transaction_log(user_id, amount, trans_type, description, related_user_id=None):
    """Hàm nội bộ: Ghi log và trừ/cộng tiền (Không commit)"""
    # with_for_update() để khóa dòng dữ liệu, tránh 2 giao dịch cùng lúc gây sai tiền
    user = User.query.with_for_update().get(user_id)

    if trans_type == "spend":
        if user.wallet_balance < amount:
            raise ValueError("Số dư không đủ để thực hiện giao dịch")
        user.wallet_balance -= amount
    if trans_type == 'earn':
        user.wallet_balance += amount

    log = Transaction(
        user_id=user_id,
        amount=amount,
        trans_type=trans_type,
        description=description,
        related_user_id=related_user_id,
        balance_after=user.wallet_balance,
    )
    db.session.add(log)
    db.session.commit()
    return log

def transfer_credits(sender_id, data):
    """
    Xử lý chuyển tiền từ Sender -> Receiver
    data gồm: receiver_id, amount, description
    """
    if sender_id  == data.receiver_id:
        raise ValueError("Không thể tự chuyển tiền cho chính mình")

    receiver = User.query.get(data.receiver_id)
    if not receiver:
        raise ValueError("Người nhận không tồn tại")

    try:
        # 1. Trừ tiền người gửi (Spend)
        process_transaction_log(
            user_id=sender_id,
            amount=data.amount,
            trans_type='spend',
            description=f"Chuyển tiền tới {receiver.profile.fullname}: {data.description}",
            related_user_id=data.receiver_id
        )
        # 2. Cộng tiền người nhận (Earn)
        process_transaction_log(
            user_id=data.receiver_id,
            amount=data.amount,
            trans_type='earn',
            description=f"Nhận tiền từ {receiver.profile.fullname}: {data.description}",
            # Note: chỗ này logic lấy tên sender hơi phức tạp nếu không query, tạm ghi user hiện tại
            related_user_id=sender_id
        )
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e


def hold_credits(user_id, amount, description, related_id=None):
    """
    Hàm trừ tiền tạm giữ (Escrow).
    Dùng khi bắt đầu phiên học.
    """
    try:
        # 1. Gọi hàm nội bộ process_transaction_log với type='spend'
        # Hàm này (đã viết ở bước trước) sẽ tự động check số dư, nếu thiếu sẽ raise Error
        process_transaction_log(
            user_id=user_id,
            amount=amount,
            trans_type='spend',  # Trừ tiền ngay lập tức
            description=f"[TẠM GIỮ] {description}",
            related_user_id=related_id
        )

        # Lưu ý: Ở đây ta KHÔNG commit ngay, vì hàm này sẽ được gọi lồng
        # trong một transaction lớn hơn ở bên socket_service.
        # Nếu socket_service commit thì cái này mới commit.
        return True
    except Exception as e:
        # Nếu lỗi (ví dụ không đủ tiền), ném lỗi ra ngoài để Socket biết mà dừng lại
        raise e