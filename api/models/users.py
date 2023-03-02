from ..utils import db
import uuid

class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(45), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.Text, nullable=False)
    is_staff = db.Column(db.Boolean(), default=False)
    is_active = db.Column(db.Boolean(), default=False)
    orders = db.relationship("Order", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

    def save(self):
        db.session.add(self)
        db.session.commit()


    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)
    
class TokenBlocklist(db.Model):
    __tablename__="token_blocklist"
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(120), nullable=False, index=True, default=uuid.uuid4)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())