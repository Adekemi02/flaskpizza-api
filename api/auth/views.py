import redis
from flask import request, abort
from flask_restx import Namespace, Resource, fields
from ..models.users import User, TokenBlocklist
from ..utils import db
from werkzeug.security import generate_password_hash, check_password_hash
from http import HTTPStatus
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity, create_access_token, create_refresh_token, unset_jwt_cookies, JWTManager
from datetime import timedelta, datetime, timezone

auth_namespace = Namespace("Auth", description = "Name space for Authentication")

# signup schema
signup_model = auth_namespace.model(
    'Signup', {
        'id': fields.Integer(),
        'username': fields.String(required=True, description="A username"),
        'email': fields.String(required=True, description="An email"),
        'password': fields.String(required=True, description="A password")
    }
)

# login schema
login_model = auth_namespace.model(
    'Login', {
        'email': fields.String(required=True, description="An email"),
        'password': fields.String(required=True, description="A password")
    }
)

# user schema
user_model = auth_namespace.model(
    'User', {
        'id': fields.Integer(),
        'username': fields.String(required=True, description="A username"),
        'email': fields.String(required=True, description="An email"),
        'password_hash': fields.String(required=True, description="A password"),
        'is_active': fields.Boolean(description="This shows if a User is active or not"),
        'is_staff': fields.Boolean(description="This shows if a User is a member of staff")
    }
)

jwt = JWTManager()

# jwt_redis_blocklist = redis.StrictRedis(
#     host='localhost', port=6379, db=0, decode_responses=True
# )

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None

# @jwt.token_in_blocklist_loader
# def check_if_token_is_revoked(jwt_header, jwt_payload):
#     jti = jwt_payload['jti']
#     token_in_redis = jwt_redis_blocklist.get(jti)
#     return token_in_redis is not None


@auth_namespace.route("/signup")
class SignUp(Resource):
    @auth_namespace.expect(signup_model)
    @auth_namespace.marshal_with(user_model)
    def post(self):
        """
            Sign up a user
        """
        data = request.get_json()

        new_user = User(
            username = data.get('username'),
            email = data.get('email'),
            password_hash = generate_password_hash(data.get('password'))
        )
        new_user.save()

        return new_user, HTTPStatus.CREATED

@auth_namespace.route("/login")
class Login(Resource):
    @auth_namespace.expect(login_model)
    def post(self):
        """
            Generate JWT token for login
        """
        data = request.get_json()

        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()

        if (user is not None) and check_password_hash(user.password_hash, password):
            access_token = create_access_token(identity=user.username)
            refresh_token = create_refresh_token(identity=user.username)

            response = {
                'access_token': access_token,
                'refresh_token': refresh_token
            }

            return response, HTTPStatus.CREATED
        # abort(message="Login credentials does not exist")

@auth_namespace.route('/refresh')
class Refresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """
            Refresh a token
        """
        username = get_jwt_identity()

        access_token = create_access_token(identity=username)
        
        return {"access_token": access_token}, HTTPStatus.OK
    
@auth_namespace.route('/logout')
class Logout(Resource):
    @jwt_required()
    def delete(self):
        """
            Logout a user
        """

        jti = get_jwt()['jti']
        now = datetime.now(timezone.utc)
        db.session.add(TokenBlocklist(jti=jti, created_at=now))
        db.session.commit()

        # jwt_redis_blocklist.set(jti, '', ex=300)

        response = {
            'message': 'Successfully logged out'
        }

        # unset_jwt_cookies
        # db.session.commit()
        return response, HTTPStatus.OK

