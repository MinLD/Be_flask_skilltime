# app/controller/transaction_controller.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..utils.response import success_response, error_response
from ..services.transaction_service import get_user_balance, get_my_transactions, transfer_credits
from ..schemas.transaction_schema import TransferRequest, TransactionResponse

transaction_bp = Blueprint('api/transactions', __name__)

@transaction_bp.route('/balance', methods=['GET'])
@jwt_required()
def get_balance():
    user_id = get_jwt_identity()
    balance = get_user_balance(user_id)
    return success_response(data={"balance": balance}, message="Get balance successfully")


@transaction_bp.route('/', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    trans_list = get_my_transactions(user_id)

    # Format dữ liệu trả về
    results = []
    for t in trans_list:
        item = TransactionResponse.model_validate(t).model_dump()
        # Lấy tên người liên quan (nếu có)
        if t.related_user and t.related_user.profile:
            item['related_user_name'] = t.related_user.profile.fullname
        else:
            item['related_user_name'] = "Unknown"
        results.append(item)

    return success_response(data=results, message="Get transaction history successfully")


@transaction_bp.route('/transfer', methods=['POST'])
@jwt_required()
def transfer():
    user_id = get_jwt_identity()
    req_data = TransferRequest(**request.get_json())
    transfer_credits(sender_id=user_id, data=req_data)
    return success_response(data=None, message="Transfer successful")
