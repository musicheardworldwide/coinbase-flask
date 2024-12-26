from flask import Flask, jsonify, request
from coinbase.rest import RESTClient
from coinbase.websocket import WSClient  # For websocket integration
import os
import logging

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Coinbase REST client
api_key = "organizations/0ac8929c-c6f1-407d-ba07-32388c139228/apiKeys/af3a949f-7f32-4531-8681-7db675164749"
api_secret = os.getenv("COINBASE_API_SECRET", "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIGxRMBNUct0ZuxqAvsS0SXEPawccpyQOrsFOR5ldo206oAoGCCqGSM49\nAwEHoUQDQgAEdRH67aqLQBIsJ285M6q9xDr6LhC8ooPIK/B++acPedhlgpoPiaaF\nqNFseBQCYf1B7gPXbhjzCJ9JrVJmyFbDCQ==\n-----END EC PRIVATE KEY-----\n")  # Ensure the API secret is set as an environment variable
client = RESTClient(api_key=api_key, api_secret=api_secret, verbose=True, rate_limit_headers=True)

# Helper function for error handling
def handle_error(e, context="An error occurred"):
    logger.error(f"{context}: {str(e)}")
    return jsonify({'error': str(e)}), 500

# Routes
@app.route('/')
def index():
    return "Coinbase API Flask App"

# Get account information
@app.route('/accounts', methods=['GET'])
def get_accounts():
    try:
        accounts = client.get_accounts()
        return jsonify([account.to_dict() for account in accounts.accounts])
    except Exception as e:
        return handle_error(e, "Failed to fetch accounts")

# Get a single account by ID
@app.route('/accounts/<account_id>', methods=['GET'])
def get_account(account_id):
    try:
        account = client.get_account(account_id)
        return jsonify(account.to_dict())
    except Exception as e:
        return handle_error(e, f"Failed to fetch account {account_id}")

# Place a market order (buy/sell)
@app.route('/order', methods=['POST'])
def place_order():
    data = request.json
    try:
        if data['side'] == 'buy':
            order = client.market_order_buy(
                client_order_id=data['client_order_id'],
                product_id=data['product_id'],
                base_size=data['base_size']
            )
        elif data['side'] == 'sell':
            order = client.market_order_sell(
                client_order_id=data['client_order_id'],
                product_id=data['product_id'],
                base_size=data['base_size']
            )
        else:
            return jsonify({'error': 'Invalid order side'}), 400
        return jsonify(order.to_dict())
    except Exception as e:
        return handle_error(e, "Failed to place order")

# List all orders
@app.route('/orders', methods=['GET'])
def list_orders():
    try:
        orders = client.get_orders()
        return jsonify([order.to_dict() for order in orders.orders])
    except Exception as e:
        return handle_error(e, "Failed to fetch orders")

# Get details of a specific order
@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    try:
        order = client.get_order(order_id)
        return jsonify(order.to_dict())
    except Exception as e:
        return handle_error(e, f"Failed to fetch order {order_id}")

# Cancel an order
@app.route('/orders/<order_id>/cancel', methods=['DELETE'])
def cancel_order(order_id):
    try:
        result = client.cancel_order(order_id)
        return jsonify(result)
    except Exception as e:
        return handle_error(e, f"Failed to cancel order {order_id}")

# Get transaction history for an account
@app.route('/transactions/<account_id>', methods=['GET'])
def get_transactions(account_id):
    try:
        transactions = client.get_transactions(account_id)
        return jsonify([txn.to_dict() for txn in transactions.transactions])
    except Exception as e:
        return handle_error(e, f"Failed to fetch transactions for account {account_id}")

# Get detailed transaction by ID
@app.route('/transactions/<account_id>/<transaction_id>', methods=['GET'])
def get_transaction(account_id, transaction_id):
    try:
        transaction = client.get_transaction(account_id, transaction_id)
        return jsonify(transaction.to_dict())
    except Exception as e:
        return handle_error(e, f"Failed to fetch transaction {transaction_id}")

# Market Data - Get Product Candles
@app.route('/candles/<product_id>', methods=['GET'])
def get_candles(product_id):
    try:
        candles = client.get_candles(product_id=product_id, start="2024-12-01", end="2024-12-26", granularity="ONE_DAY")
        return jsonify(candles.to_dict())
    except Exception as e:
        return handle_error(e, f"Failed to fetch candles for {product_id}")

# Market Data - Get Market Trades
@app.route('/trades/<product_id>', methods=['GET'])
def get_market_trades(product_id):
    try:
        trades = client.get_market_trades(product_id=product_id, limit=5)
        return jsonify(trades.to_dict())
    except Exception as e:
        return handle_error(e, f"Failed to fetch trades for {product_id}")

# Order Management - Place a Limit Order
@app.route('/limit_order', methods=['POST'])
def place_limit_order():
    data = request.json
    try:
        order = client.limit_order_gtc(
            client_order_id=data['client_order_id'],
            product_id=data['product_id'],
            side=data['side'],
            base_size=data['base_size'],
            limit_price=data['limit_price']
        )
        return jsonify(order.to_dict())
    except Exception as e:
        return handle_error(e, "Failed to place limit order")

# Portfolio Management - Create Portfolio
@app.route('/portfolio', methods=['POST'])
def create_portfolio():
    data = request.json
    try:
        portfolio = client.create_portfolio(name=data['name'])
        return jsonify(portfolio.to_dict())
    except Exception as e:
        return handle_error(e, "Failed to create portfolio")

# Portfolio Management - Move Funds Between Portfolios
@app.route('/move_funds', methods=['POST'])
def move_funds():
    data = request.json
    try:
        result = client.move_portfolio_funds(
            source_portfolio_id=data['source_portfolio_id'],
            destination_portfolio_id=data['destination_portfolio_id'],
            amount=data['amount'],
            currency=data['currency']
        )
        return jsonify(result)
    except Exception as e:
        return handle_error(e, "Failed to move funds between portfolios")

# WebSocket Integration - Subscribe to Ticker Updates
@app.route('/subscribe_websocket', methods=['POST'])
def subscribe_websocket():
    data = request.json
    try:
        client_ws = WSClient(api_key=api_key, api_secret=api_secret, on_message=lambda msg: print(msg))
        client_ws.open()
        client_ws.subscribe(product_ids=[data['product_id']], channels=["ticker"])
        return jsonify({'status': 'Subscription successful'})
    except Exception as e:
        return handle_error(e, "Failed to subscribe to websocket")

# Advanced Features - Convert Quotes
@app.route('/convert_quote', methods=['POST'])
def create_convert_quote():
    data = request.json
    try:
        quote = client.create_convert_quote(
            from_currency=data['from_currency'],
            to_currency=data['to_currency'],
            amount=data['amount']
        )
        return jsonify(quote.to_dict())
    except Exception as e:
        return handle_error(e, "Failed to create convert quote")

# Advanced Features - Get Best Bid/Ask
@app.route('/best_bid_ask/<product_id>', methods=['GET'])
def get_best_bid_ask(product_id):
    try:
        best_bid_ask = client.get_best_bid_ask(product_ids=[product_id])
        return jsonify(best_bid_ask.to_dict())
    except Exception as e:
        return handle_error(e, f"Failed to fetch best bid/ask for {product_id}")

# Public Endpoints - Get Server Time
@app.route('/server_time', methods=['GET'])
def get_server_time():
    try:
        server_time = client.get_unix_time()
        return jsonify({'server_time': server_time})
    except Exception as e:
        return handle_error(e, "Failed to fetch server time")

# Error Handling - Unit Tests (Example)
@app.route('/test_accounts', methods=['GET'])
def test_accounts():
    try:
        accounts_page = client.list_accounts()
        if accounts_page.size == 0:
            return jsonify({'error': 'No accounts found'}), 404
        return jsonify(accounts_page.to_dict())
    except Exception as e:
        return handle_error(e, "Failed to list accounts in test")
@app.route('/ui')
def serve_ui():
    return send_from_directory('.', 'index.html')

# Run the Flask app
if __name__ == '__main__':
    port = int(os.getenv("FLASK_PORT", 5432))
    app.run(host='0.0.0.0', port=port, debug=True)
