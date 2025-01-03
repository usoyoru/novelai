from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_app import app
from flask_app.models import Vote

db = SQLAlchemy()

@app.route('/vote/<int:chapter_id>', methods=['POST'])
def vote(chapter_id):
    wallet_address = request.form.get('wallet_address')
    signature = request.form.get('signature')

    if not wallet_address or not signature:
        return jsonify({'detail': '缺少必要的参数'}), 400

    # 检查是否已经投票
    existing_vote = Vote.query.filter_by(
        wallet_address=wallet_address,
        chapter_id=chapter_id
    ).first()

    if existing_vote:
        return jsonify({'detail': '您已经为这个章节投过票了'}), 400

    try:
        # 验证签名
        message = f'Vote for chapter {chapter_id}'
        encoded_message = message.encode('utf8')
        # TODO: 在这里添加签名验证逻辑

        # 创建新的投票记录
        new_vote = Vote(
            wallet_address=wallet_address,
            chapter_id=chapter_id,
            signature=signature
        )
        db.session.add(new_vote)
        db.session.commit()

        return jsonify({'detail': '投票成功'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'detail': f'投票失败: {str(e)}'}), 500 