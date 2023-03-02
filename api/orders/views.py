from flask_restx import Namespace, Resource, fields
from ..models.orders import Order
from ..models.users import User
from ..utils import db
from http import HTTPStatus
from flask_jwt_extended import jwt_required, get_jwt_identity

order_namespace = Namespace("order", description = "Name space for Order")


order_model = order_namespace.model(
    'Order', {
        'id': fields.Integer(),
        'flavour': fields.String(description='Pizza flavour', required=True),
        'size': fields.String(description='Size of order', required=True, 
            enum=['SMALL', 'MEDIUM', 'LARGE', 'EXTRA_LARGE']
        ),
        'quantity': fields.Integer(description='Number of pizza'),
        'order_status': fields.String(descripton='The status of order',
            required=True, enum = ['PENDING','IN_TRANSIT', 'DELIVERED']
        )
    }
)

order_status_model = order_namespace.model(
    'OrderStatus', {
        'order_status': fields.String(required=True, description='Order Status',
        enum = ['PENDING','IN_TRANSIT', 'DELIVERED'])
    }
)

@order_namespace.route("/orders")
class OrderGetCreate(Resource):
    @order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = 'Get all Orders of Users'
    )
    @jwt_required()
    def get(self):
        """
            Get all orders
            auth required
        """
        orders = Order.query.all()

        return orders, HTTPStatus.OK


    @order_namespace.expect(order_model)
    @order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = 'Place an Order'
    )
    @jwt_required()
    def post(self):
        """
            Place an order
        """

        username = get_jwt_identity()

        current_user = User.query.filter_by(username=username).first()

        data = order_namespace.payload

        new_order = Order(
            size = data['size'],
            quantity = data['quantity'],
            flavour = data['flavour']
        )

        new_order.user = current_user
        new_order.save()

        return new_order, HTTPStatus.CREATED


@order_namespace.route("/order/<int:order_id>")
class GetUpdateDelete(Resource):
    @order_namespace.marshal_with(order_model)  # used for get method
    @order_namespace.doc(
        description = 'Get an Order by ID',
        params = {'order_id': 'An ID for an order'}
    )
    @jwt_required()

    def get(self, order_id):
        """
            Retrieve an order by id
        """
        
        order = Order.get_by_id(order_id)
        return order, HTTPStatus.OK


    @order_namespace.expect(order_model)    # used for post method
    @order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = 'Update an Order by ID',
        params = {'order_id': 'An ID for an order'}
    )
    @jwt_required()
    def put(self, order_id):
        """
            Update an order by id
            auth required
        """

        order_to_update = Order.get_by_id(order_id)
        data = order_namespace.payload

        order_to_update.quantity = data['quantity']
        order_to_update.size = data['size']
        order_to_update.flavour = data['flavour']

        db.session.commit()

        return order_to_update, HTTPStatus.OK


    @order_namespace.doc(
        description = 'Delete an Order by ID',
        params = {'order_id': 'An ID for an order'}
    )
    @jwt_required()
    def delete(self, order_id):
        """
            Delete an order by id
            auth required
        """
        order_to_delete = Order.get_by_id(order_id)
        order_to_delete.delete()
        
        return {"message": "Order deleted successfully"}, HTTPStatus.OK


@order_namespace.route("/user/<int:user_id>/order/<int:order_id>")
class GetSpecificOrderByUser(Resource):
    @order_namespace.marshal_list_with(order_model)
    @order_namespace.doc(
        description = 'Get a user specific order by user ID and order ID',
        params = {'order_id': 'An ID for an order',
                  'user_id': 'An ID for user'}
    )
    @jwt_required()

    def get(self, user_id, order_id):
        """
            Get a user specific Order
            auth required
        """
        user = User.get_by_id(user_id)
        order = Order.query.filter_by(id=order_id).filter_by(user=user).first()

        return order, HTTPStatus.OK


@order_namespace.route("/user/<user_id>/orders")
class UserOrders(Resource):
    @order_namespace.marshal_list_with(order_model)
    @order_namespace.doc(
        description = 'Get all user orders by user ID',
        params = {'user_id': 'An ID for a user'}
    )
    @jwt_required()
    def get(self, user_id):

        """
            Get a user Orders
            auth required
        """

        user = User.get_by_id(user_id)
        orders = user.orders

        return orders, HTTPStatus.OK

# Path: api\orders\models.py
# this is for admin to update order status
@order_namespace.route("/order/status/<int:order_id>")
class UpdateOrderStatus(Resource):
    @order_namespace.expect(order_status_model)
    @order_namespace.marshal_with(order_model)
    @order_namespace.doc(
        description = 'Update a user order status',
        params = {'order_id': 'An ID for an order'}
    )
    @jwt_required()

    def patch(self, order_id):
        """
            Update an order's Status
        """
        
        data = order_namespace.payload
        order_to_update = Order.get_by_id(order_id)
        order_to_update.order_status = data['order_status']

        db.session.commit()

        return order_to_update, HTTPStatus.OK
