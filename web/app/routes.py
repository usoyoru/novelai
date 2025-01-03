from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import Vote

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///novel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/vote/<int:novel_id>/<int:chapter_number>/<int:option_id>', methods=['POST'])
def vote(novel_id, chapter_number, option_id):
    wallet_address = request.form.get('wallet_address')
    signature = request.form.get('signature')

    if not wallet_address or not signature:
        return jsonify({'detail': 'Missing required parameters'}), 400

    # Check if already voted
    existing_vote = Vote.query.filter_by(
        wallet_address=wallet_address,
        novel_id=novel_id,
        chapter_number=chapter_number
    ).first()

    if existing_vote:
        return jsonify({'detail': 'You have already voted for this chapter'}), 400

    try:
        # Verify signature
        message = f'Vote for chapter {chapter_number}'
        encoded_message = message.encode('utf8')
        # TODO: Add signature verification logic here

        # Create new vote record
        new_vote = Vote(
            wallet_address=wallet_address,
            novel_id=novel_id,
            chapter_number=chapter_number,
            option_id=option_id,
            signature=signature
        )
        db.session.add(new_vote)
        db.session.commit()

        return jsonify({'detail': 'Vote successful'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'detail': f'Vote failed: {str(e)}'}), 500 