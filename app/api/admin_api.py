from flask import Blueprint, jsonify, request
from app.services.init_all_service import InitAllService

admin_bp = Blueprint('admin_api', __name__)

@admin_bp.route('/init-all', methods=['GET'])
def init_all():
    """触发全量数据初始化"""
    start_date = request.args.get('start_date', '2025-01-01')
    success = InitAllService.run_async(start_date)
    if success:
        return jsonify({"code": 200, "message": "初始化任务已在后台启动，请访问 /api/admin/status 查看进度"})
    else:
        return jsonify({"code": 400, "message": "任务已在运行中，请勿重复启动"})

@admin_bp.route('/status', methods=['GET'])
def get_status():
    """查看初始化进度"""
    return jsonify({"code": 200, "data": InitAllService.get_status()})
