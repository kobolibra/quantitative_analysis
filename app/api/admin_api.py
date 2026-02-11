from flask import Blueprint, jsonify, request
import threading

admin_bp = Blueprint('admin_api', __name__)

@admin_bp.route('/init-all', methods=['GET'])
def init_all():
    from app.services.init_all_service import InitAllService
    start_date = request.args.get('start_date', '2025-01-01')
    success = InitAllService.run_async(start_date)
    return jsonify({"code": 200, "message": "Task started", "start_date": start_date}) if success else jsonify({"code": 400, "message": "Already running"})

@admin_bp.route('/status', methods=['GET'])
def get_status():
    from app.services.init_all_service import InitAllService
    return jsonify({"code": 200, "data": InitAllService.get_status()})
