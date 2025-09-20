#!/usr/bin/env python3
import threading
import time
import json
import sys
import os
import queue
import uuid
import hashlib
from flask import Flask, render_template, jsonify, Response, request
from collections import deque

# Import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import TradovateController

# Create Flask app
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, 
            static_folder=os.path.join(project_root, 'web/static'),
            template_folder=os.path.join(project_root, 'web/templates'))

# Initialize controller
controller = TradovateController()

# SSE Infrastructure
sse_clients = {}  # {client_id: queue.Queue()}
sse_client_metadata = {}  # {client_id: connection_info}
sse_lock = threading.Lock()
last_account_data = None
last_data_hash = None

# Data Change Detection with Bounded Memory
data_history = deque(maxlen=10)  # Keep last 10 data snapshots for comparison
data_change_timestamps = deque(maxlen=50)  # Track change frequency for monitoring
memory_cleanup_counter = 0
MAX_MEMORY_CYCLES = 100  # Force cleanup every 100 data collections

def format_sse_message(event_type, data):
    """Format data as SSE message"""
    message = f"event: {event_type}\n"
    message += f"data: {json.dumps(data)}\n\n"
    return message

def add_sse_client(user_agent=None, remote_addr=None):
    """Add new SSE client with health monitoring and return client ID and queue"""
    client_id = str(uuid.uuid4())
    client_queue = queue.Queue(maxsize=10)  # Bounded queue to prevent memory issues
    
    # Track detailed connection metadata
    connection_info = {
        'connect_time': time.time(),
        'user_agent': user_agent or 'Unknown',
        'remote_addr': remote_addr or 'Unknown',
        'messages_sent': 0,
        'messages_failed': 0,
        'last_activity': time.time(),
        'connection_errors': 0,
        'queue_full_count': 0
    }
    
    with sse_lock:
        sse_clients[client_id] = client_queue
        sse_client_metadata[client_id] = connection_info
        print(f"[SSE Health] Client {client_id[:8]} connected from {remote_addr}. Total clients: {len(sse_clients)}")
    
    return client_id, client_queue

def remove_sse_client(client_id):
    """Remove SSE client by ID with connection duration logging"""
    with sse_lock:
        if client_id in sse_clients:
            # Log connection duration
            if client_id in sse_client_metadata:
                metadata = sse_client_metadata[client_id]
                duration = time.time() - metadata['connect_time']
                print(f"[SSE Health] Client {client_id[:8]} disconnected after {duration:.1f}s. "
                      f"Messages: {metadata['messages_sent']}, Errors: {metadata['connection_errors']}")
                del sse_client_metadata[client_id]
            
            del sse_clients[client_id]
            print(f"[SSE Health] Total clients now: {len(sse_clients)}")

def update_client_activity(client_id, success=True):
    """Update client activity metrics"""
    with sse_lock:
        if client_id in sse_client_metadata:
            metadata = sse_client_metadata[client_id]
            metadata['last_activity'] = time.time()
            if success:
                metadata['messages_sent'] += 1
            else:
                metadata['messages_failed'] += 1
                metadata['connection_errors'] += 1

def get_client_health_status():
    """Get detailed health status of all SSE clients"""
    now = time.time()
    health_data = {
        'total_clients': len(sse_clients),
        'healthy_clients': 0,
        'stale_clients': 0,
        'clients': []
    }
    
    with sse_lock:
        for client_id, metadata in sse_client_metadata.items():
            duration = now - metadata['connect_time']
            inactive_time = now - metadata['last_activity']
            
            client_health = {
                'client_id': client_id[:8],
                'duration_seconds': duration,
                'inactive_seconds': inactive_time,
                'messages_sent': metadata['messages_sent'],
                'connection_errors': metadata['connection_errors'],
                'queue_full_count': metadata['queue_full_count'],
                'remote_addr': metadata['remote_addr'],
                'user_agent': metadata['user_agent'][:50] + '...' if len(metadata['user_agent']) > 50 else metadata['user_agent'],
                'status': 'healthy' if inactive_time < 60 else 'stale'
            }
            
            health_data['clients'].append(client_health)
            
            if client_health['status'] == 'healthy':
                health_data['healthy_clients'] += 1
            else:
                health_data['stale_clients'] += 1
    
    return health_data

def broadcast_to_clients(event_type, data):
    """Broadcast event to all connected SSE clients with health tracking"""
    message = format_sse_message(event_type, data)
    dead_clients = []
    successful_sends = 0
    
    with sse_lock:
        for client_id, client_queue in sse_clients.items():
            try:
                client_queue.put_nowait(message)
                update_client_activity(client_id, success=True)
                successful_sends += 1
            except queue.Full:
                print(f"[SSE Health] Client {client_id[:8]} queue full, dropping message")
                if client_id in sse_client_metadata:
                    sse_client_metadata[client_id]['queue_full_count'] += 1
                update_client_activity(client_id, success=False)
                dead_clients.append(client_id)
            except Exception as e:
                print(f"[SSE Health] Error broadcasting to client {client_id[:8]}: {e}")
                update_client_activity(client_id, success=False)
                dead_clients.append(client_id)
    
    # Enhanced SSE monitoring log
    broadcast_metrics = {
        'event_type': event_type,
        'successful_sends': successful_sends,
        'failed_clients': len(dead_clients),
        'total_clients': len(sse_clients),
        'timestamp': time.strftime('%H:%M:%S')
    }
    print(f"[SSE Broadcast] {broadcast_metrics}")
    
    # Clean up dead clients
    for client_id in dead_clients:
        remove_sse_client(client_id)

def compute_data_hash(data):
    """Compute hash of account data for change detection"""
    try:
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    except Exception as e:
        print(f"[SSE] Error computing data hash: {e}")
        return None

def detect_data_changes(new_data):
    """Enhanced change detection with memory management"""
    global last_account_data, last_data_hash, memory_cleanup_counter
    
    # Force memory cleanup periodically
    memory_cleanup_counter += 1
    if memory_cleanup_counter >= MAX_MEMORY_CYCLES:
        force_memory_cleanup()
        memory_cleanup_counter = 0
    
    # Compute hash for change detection
    new_data_hash = compute_data_hash(new_data)
    
    # Track data history for trend analysis
    timestamp = time.time()
    data_snapshot = {
        'hash': new_data_hash,
        'timestamp': timestamp,
        'record_count': len(new_data) if new_data else 0,
        'accounts': list(set(item.get('account_name', 'unknown') for item in new_data)) if new_data else []
    }
    data_history.append(data_snapshot)
    
    # Determine if significant change occurred
    data_changed = (new_data_hash != last_data_hash)
    
    if data_changed:
        data_change_timestamps.append(timestamp)
        print(f"[Change Detection] Data changed - Hash: {new_data_hash[:8]}, Records: {len(new_data) if new_data else 0}")
        
        # Update global state
        last_account_data = new_data
        last_data_hash = new_data_hash
        
        return True, data_snapshot
    else:
        print(f"[Change Detection] No changes detected - Hash: {new_data_hash[:8] if new_data_hash else 'None'}")
        return False, data_snapshot

def force_memory_cleanup():
    """Force cleanup of memory structures and dead references"""
    global sse_clients
    
    print(f"[Memory Cleanup] Starting cleanup cycle")
    
    # Clean up dead SSE clients
    dead_clients = []
    with sse_lock:
        for client_id, client_queue in list(sse_clients.items()):
            try:
                # Test if queue is responsive
                client_queue.put_nowait("test")
                client_queue.get_nowait()  # Remove test message
            except (queue.Full, queue.Empty):
                pass  # Queue is fine
            except Exception:
                dead_clients.append(client_id)
    
    for client_id in dead_clients:
        remove_sse_client(client_id)
    
    # Log memory status
    change_frequency = len(data_change_timestamps) / max(1, (time.time() - data_change_timestamps[0]) / 60) if data_change_timestamps else 0
    print(f"[Memory Cleanup] Active clients: {len(sse_clients)}, "
          f"Data history: {len(data_history)}, "
          f"Change frequency: {change_frequency:.2f}/min")

def get_data_statistics():
    """Get statistics about data collection and changes"""
    now = time.time()
    recent_changes = [ts for ts in data_change_timestamps if now - ts < 300]  # Last 5 minutes
    
    stats = {
        'active_sse_clients': len(sse_clients),
        'data_history_size': len(data_history),
        'total_changes': len(data_change_timestamps),
        'recent_changes_5min': len(recent_changes),
        'last_update_timestamp': data_history[-1]['timestamp'] if data_history else None,
        'memory_cleanup_counter': memory_cleanup_counter
    }
    
    if data_history:
        stats['current_record_count'] = data_history[-1]['record_count']
        stats['tracked_accounts'] = data_history[-1]['accounts']
    
    return stats

# Chrome Data Collection Service
chrome_access_lock = threading.Lock()
chrome_timeout_lock = threading.Lock()
data_collection_active = False

# Chrome connection health tracking
chrome_health_stats = {
    'total_operations': 0,
    'successful_operations': 0,
    'timeout_operations': 0,
    'failed_operations': 0,
    'last_operation_time': None,
    'connection_health': {}  # {account_name: health_info}
}

# Chrome operation timeouts
CHROME_INJECTION_TIMEOUT = 15  # seconds for script injection
CHROME_EVALUATION_TIMEOUT = 20  # seconds for data evaluation
CHROME_CONNECTION_TIMEOUT = 10  # seconds for connection check

# Background Refresh Scheduler
scheduler_thread = None
scheduler_active = False
scheduler_lock = threading.Lock()
scheduler_stats = {
    'started_at': None,
    'total_cycles': 0,
    'successful_cycles': 0,
    'failed_cycles': 0,
    'last_run': None,
    'last_error': None,
    'consecutive_failures': 0,
    'max_consecutive_failures': 5
}

def log_system_health_summary():
    """Log comprehensive system health summary for monitoring"""
    try:
        client_health = get_client_health_status()
        chrome_health = get_chrome_health_status()
        data_stats = get_data_statistics()
        
        # Create structured health summary
        health_summary = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'sse_clients': client_health['total_clients'],
            'healthy_clients': client_health['healthy_clients'],
            'chrome_success_rate': f"{chrome_health['success_rate']:.1f}%",
            'chrome_connections': chrome_health['connection_count'],
            'data_changes_5min': data_stats['recent_changes_5min'],
            'total_operations': chrome_health['total_operations'],
            'scheduler_cycles': scheduler_stats['total_cycles'],
            'scheduler_success_rate': f"{(scheduler_stats['successful_cycles'] / max(1, scheduler_stats['total_cycles'])) * 100:.1f}%"
        }
        
        print(f"[Health Summary] {health_summary}")
        
    except Exception as e:
        print(f"[Health Summary] Error generating summary: {e}")

def background_refresh_scheduler():
    """Background thread that performs data collection every 30 seconds"""
    global scheduler_active, scheduler_stats
    
    print("[Scheduler] Background refresh scheduler started")
    scheduler_stats['started_at'] = time.time()
    health_log_counter = 0
    
    while scheduler_active:
        try:
            cycle_start = time.time()
            scheduler_stats['total_cycles'] += 1
            scheduler_stats['last_run'] = cycle_start
            
            print(f"[Scheduler] Starting refresh cycle #{scheduler_stats['total_cycles']}")
            
            # Log system health summary every 10 cycles (5 minutes)
            health_log_counter += 1
            if health_log_counter >= 10:
                log_system_health_summary()
                health_log_counter = 0
            
            # Perform Chrome data collection
            try:
                data = collect_chrome_data_safe()
                
                # Check if we got valid data
                if data is not None:
                    scheduler_stats['successful_cycles'] += 1
                    scheduler_stats['consecutive_failures'] = 0
                    print(f"[Scheduler] Cycle #{scheduler_stats['total_cycles']} completed successfully")
                else:
                    raise Exception("collect_chrome_data_safe returned None")
                    
            except Exception as collection_error:
                scheduler_stats['failed_cycles'] += 1
                scheduler_stats['consecutive_failures'] += 1
                scheduler_stats['last_error'] = str(collection_error)
                
                print(f"[Scheduler] Cycle #{scheduler_stats['total_cycles']} failed: {collection_error}")
                
                # Check if we've exceeded max consecutive failures
                if scheduler_stats['consecutive_failures'] >= scheduler_stats['max_consecutive_failures']:
                    print(f"[Scheduler] CRITICAL: {scheduler_stats['consecutive_failures']} consecutive failures. "
                          f"Broadcasting error to clients.")
                    
                    # Broadcast critical error to all clients
                    broadcast_to_clients('scheduler_error', {
                        'message': f'Data collection failing repeatedly: {collection_error}',
                        'consecutive_failures': scheduler_stats['consecutive_failures'],
                        'timestamp': time.time()
                    })
                    
                    # Reset counter to avoid spam
                    scheduler_stats['consecutive_failures'] = 0
                
                # Add exponential backoff for repeated failures
                if scheduler_stats['consecutive_failures'] > 1:
                    backoff_delay = min(60, 2 ** scheduler_stats['consecutive_failures'])
                    print(f"[Scheduler] Applying backoff delay: {backoff_delay}s")
                    time.sleep(backoff_delay)
            
            # Calculate time taken and sleep for remainder of 30 seconds
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, 30 - cycle_duration)
            
            # Enhanced performance logging
            performance_metrics = {
                'cycle': scheduler_stats['total_cycles'],
                'duration_seconds': f"{cycle_duration:.2f}",
                'sleep_time': f"{sleep_time:.2f}",
                'success_rate': f"{(scheduler_stats['successful_cycles'] / scheduler_stats['total_cycles']) * 100:.1f}%",
                'consecutive_failures': scheduler_stats['consecutive_failures']
            }
            
            print(f"[Scheduler Performance] {performance_metrics}")
            
            # Sleep in small increments to allow for quick shutdown
            sleep_elapsed = 0
            while scheduler_active and sleep_elapsed < sleep_time:
                time.sleep(min(1, sleep_time - sleep_elapsed))
                sleep_elapsed += 1
                
        except Exception as scheduler_error:
            print(f"[Scheduler] Critical scheduler error: {scheduler_error}")
            scheduler_stats['failed_cycles'] += 1
            scheduler_stats['last_error'] = str(scheduler_error)
            
            # Emergency broadcast to clients
            try:
                broadcast_to_clients('scheduler_critical', {
                    'message': f'Scheduler critical error: {scheduler_error}',
                    'timestamp': time.time()
                })
            except Exception as broadcast_error:
                print(f"[Scheduler] Failed to broadcast critical error: {broadcast_error}")
            
            # Emergency sleep before retry
            time.sleep(5)
    
    print("[Scheduler] Background refresh scheduler stopped")

def start_background_scheduler():
    """Start the background refresh scheduler"""
    global scheduler_thread, scheduler_active
    
    with scheduler_lock:
        if not scheduler_active:
            scheduler_active = True
            scheduler_thread = threading.Thread(
                target=background_refresh_scheduler,
                daemon=True,
                name="BackgroundRefreshScheduler"
            )
            scheduler_thread.start()
            print("[Scheduler] Background scheduler started")
            return True
        else:
            print("[Scheduler] Background scheduler already running")
            return False

def stop_background_scheduler():
    """Stop the background refresh scheduler gracefully"""
    global scheduler_active, scheduler_thread
    
    with scheduler_lock:
        if scheduler_active:
            print("[Scheduler] Stopping background scheduler...")
            scheduler_active = False
            
            if scheduler_thread and scheduler_thread.is_alive():
                scheduler_thread.join(timeout=5)
                if scheduler_thread.is_alive():
                    print("[Scheduler] Warning: Scheduler thread did not stop gracefully")
                else:
                    print("[Scheduler] Scheduler stopped successfully")
            
            scheduler_thread = None
            return True
        else:
            print("[Scheduler] Scheduler was not running")
            return False

def get_scheduler_status():
    """Get current scheduler status and statistics"""
    uptime = time.time() - scheduler_stats['started_at'] if scheduler_stats['started_at'] else 0
    
    status = {
        'active': scheduler_active,
        'uptime_seconds': uptime,
        'total_cycles': scheduler_stats['total_cycles'],
        'successful_cycles': scheduler_stats['successful_cycles'],
        'failed_cycles': scheduler_stats['failed_cycles'],
        'success_rate': (scheduler_stats['successful_cycles'] / max(1, scheduler_stats['total_cycles'])) * 100,
        'last_run': scheduler_stats['last_run'],
        'last_error': scheduler_stats['last_error'],
        'consecutive_failures': scheduler_stats['consecutive_failures'],
        'health_status': 'healthy' if scheduler_stats['consecutive_failures'] < 3 else 'degraded'
    }
    
    return status

def execute_chrome_operation_with_timeout(operation_func, timeout, operation_name, account_name):
    """Execute Chrome operation with timeout protection and health tracking"""
    import threading
    import queue
    
    # Update operation statistics
    chrome_health_stats['total_operations'] += 1
    chrome_health_stats['last_operation_time'] = time.time()
    
    # Initialize account health if not exists
    if account_name not in chrome_health_stats['connection_health']:
        chrome_health_stats['connection_health'][account_name] = {
            'total_ops': 0,
            'successful_ops': 0,
            'timeout_ops': 0,
            'failed_ops': 0,
            'last_success': None,
            'last_failure': None,
            'consecutive_failures': 0
        }
    
    account_health = chrome_health_stats['connection_health'][account_name]
    account_health['total_ops'] += 1
    
    start_time = time.time()
    result_queue = queue.Queue()
    
    def worker():
        try:
            result = operation_func()
            result_queue.put(('success', result))
        except Exception as e:
            result_queue.put(('error', e))
    
    # Start the operation in a separate thread
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()
    
    try:
        # Wait for result with timeout
        result_type, result_value = result_queue.get(timeout=timeout)
        
        if result_type == 'success':
            # Success tracking
            duration = time.time() - start_time
            chrome_health_stats['successful_operations'] += 1
            account_health['successful_ops'] += 1
            account_health['last_success'] = time.time()
            account_health['consecutive_failures'] = 0
            
            print(f"[Chrome Timeout] {operation_name} for {account_name} completed in {duration:.2f}s")
            return result_value
        else:
            # Operation failed
            raise result_value
            
    except queue.Empty:
        # Timeout occurred
        chrome_health_stats['timeout_operations'] += 1
        account_health['timeout_ops'] += 1
        account_health['consecutive_failures'] += 1
        account_health['last_failure'] = time.time()
        
        print(f"[Chrome Timeout] {operation_name} for {account_name} timed out after {timeout}s")
        raise TimeoutError(f"Chrome operation '{operation_name}' timed out after {timeout}s")
        
    except Exception as e:
        # Failure tracking
        chrome_health_stats['failed_operations'] += 1
        account_health['failed_ops'] += 1
        account_health['consecutive_failures'] += 1
        account_health['last_failure'] = time.time()
        
        print(f"[Chrome Timeout] {operation_name} for {account_name} failed: {e}")
        raise e

def check_chrome_connection_health(conn):
    """Check if Chrome connection is healthy with simple check"""
    try:
        # Simple connectivity check without complex timeout handling
        if conn.tab:
            result = conn.tab.Runtime.evaluate(expression="'ping'")
            return result is not None
        return False
    except Exception as e:
        print(f"[Chrome Health] Connection check failed for {conn.account_name}: {e}")
        return False

def get_chrome_health_status():
    """Get comprehensive Chrome connection health status"""
    now = time.time()
    total_ops = chrome_health_stats['total_operations']
    
    health_summary = {
        'total_operations': total_ops,
        'success_rate': (chrome_health_stats['successful_operations'] / max(1, total_ops)) * 100,
        'timeout_rate': (chrome_health_stats['timeout_operations'] / max(1, total_ops)) * 100,
        'failure_rate': (chrome_health_stats['failed_operations'] / max(1, total_ops)) * 100,
        'last_operation': chrome_health_stats['last_operation_time'],
        'connection_count': len(chrome_health_stats['connection_health']),
        'connections': []
    }
    
    # Per-connection health
    for account_name, health in chrome_health_stats['connection_health'].items():
        conn_health = {
            'account_name': account_name,
            'total_operations': health['total_ops'],
            'success_rate': (health['successful_ops'] / max(1, health['total_ops'])) * 100,
            'consecutive_failures': health['consecutive_failures'],
            'last_success': health['last_success'],
            'last_failure': health['last_failure'],
            'status': 'healthy' if health['consecutive_failures'] < 3 else 'degraded'
        }
        
        # Calculate time since last operation
        if health['last_success']:
            conn_health['seconds_since_success'] = now - health['last_success']
        if health['last_failure']:
            conn_health['seconds_since_failure'] = now - health['last_failure']
            
        health_summary['connections'].append(conn_health)
    
    return health_summary

def collect_chrome_data_safe():
    """Thread-safe Chrome data collection with error recovery"""
    global last_account_data, last_data_hash
    
    with chrome_access_lock:
        try:
            print(f"[Chrome Service] Starting data collection at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            account_data = []
            
            # Fetch data from all tabs with timeout and error recovery
            for i, conn in enumerate(controller.connections):
                if conn.tab:
                    try:
                        # Load JavaScript with timeout protection
                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        autorisk_path = os.path.join(project_root, 'scripts/tampermonkey/autoriskManagement.js')
                        
                        with open(autorisk_path, 'r') as file:
                            autorisk_js = file.read()
                        
                        print(f"[Chrome Service] Injecting phase logic for {conn.account_name}")
                        
                        # Set timeout for Chrome operations
                        start_time = time.time()
                        
                        # Check connection health first
                        if not check_chrome_connection_health(conn):
                            print(f"[Chrome Service] Connection health check failed for {conn.account_name}")
                            continue
                        
                        # Inject JavaScript with timeout protection
                        def injection_operation():
                            return conn.tab.Runtime.evaluate(expression=autorisk_js)
                        
                        try:
                            execute_chrome_operation_with_timeout(
                                injection_operation,
                                CHROME_INJECTION_TIMEOUT,
                                "script_injection",
                                conn.account_name
                            )
                        except Exception as inject_error:
                            print(f"[Chrome Service] Script injection failed for {conn.account_name}: {inject_error}")
                            continue
                        
                        # Execute data collection with timeout protection
                        def evaluation_operation():
                            return conn.tab.Runtime.evaluate(
                                expression="JSON.stringify(getTableData())"
                            )
                        
                        try:
                            result = execute_chrome_operation_with_timeout(
                                evaluation_operation,
                                CHROME_EVALUATION_TIMEOUT,
                                "data_evaluation",
                                conn.account_name
                            )
                        except Exception as eval_error:
                            print(f"[Chrome Service] Data evaluation failed for {conn.account_name}: {eval_error}")
                            continue
                        
                        execution_time = time.time() - start_time
                        print(f"[Chrome Service] Collection for {conn.account_name} took {execution_time:.2f}s")
                        
                        # Process results with validation
                        if result and 'result' in result and 'value' in result['result']:
                            try:
                                tab_data = json.loads(result['result']['value'])
                                print(f"[Chrome Service] Collected {len(tab_data) if tab_data else 0} rows from {conn.account_name}")
                                
                                if not tab_data:
                                    continue
                                
                                # Add metadata and standardize format
                                for item in tab_data:
                                    item['account_name'] = conn.account_name
                                    item['account_index'] = i
                                    item['collection_timestamp'] = time.time()
                                    
                                    # Ensure Phase field exists (renamed from User)
                                    if 'User' in item and 'Phase' not in item:
                                        item['Phase'] = item['User']
                                    
                                    # Standardize Account field
                                    if 'Account ▲' in item:
                                        account_value = item['Account ▲']
                                        item.pop('Account ▲', None)
                                        if 'Account' not in item:
                                            item['Account'] = account_value
                                
                                account_data.extend(tab_data)
                                
                            except json.JSONDecodeError as e:
                                print(f"[Chrome Service] JSON parsing failed for {conn.account_name}: {e}")
                                continue
                        else:
                            print(f"[Chrome Service] No valid result structure for {conn.account_name}")
                            
                    except Exception as e:
                        print(f"[Chrome Service] Connection error for {conn.account_name}: {e}")
                        # Continue with other connections
                        continue
            
            # Use enhanced change detection with memory management
            data_changed, data_snapshot = detect_data_changes(account_data)
            
            if data_changed or last_account_data is None:
                print(f"[Chrome Service] Data changed, broadcasting to {len(sse_clients)} clients")
                
                # Broadcast to SSE clients with metadata
                broadcast_data = {
                    'accounts': account_data,
                    'metadata': {
                        'timestamp': data_snapshot['timestamp'],
                        'record_count': data_snapshot['record_count'],
                        'tracked_accounts': data_snapshot['accounts'],
                        'change_detected': True
                    }
                }
                broadcast_to_clients('account_data', broadcast_data)
            else:
                print(f"[Chrome Service] No data changes detected - skipping broadcast")
            
            print(f"[Chrome Service] Collection completed: {len(account_data)} total records")
            return account_data
            
        except Exception as e:
            print(f"[Chrome Service] Critical error during data collection: {e}")
            # Broadcast error to clients
            broadcast_to_clients('error', {'message': str(e), 'timestamp': time.time()})
            return []

def inject_account_data_function():
    """Inject the getAllAccountTableData function into all tabs"""
    for conn in controller.connections:
        if conn.tab:
            try:
                # Read the function from the file
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                account_data_path = os.path.join(project_root, 
                                       'scripts/tampermonkey/getAllAccountTableData.user.js')
                with open(account_data_path, 'r') as file:
                    get_account_data_js = file.read()
                
                # Inject it into the tab
                conn.tab.Runtime.evaluate(expression=get_account_data_js)
                print(f"Injected getAllAccountTableData into {conn.account_name}")
            except Exception as e:
                print(f"Error injecting account data function: {e}")

# Route for dashboard UI
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# API endpoint to get all account data
@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Get account data using the thread-safe Chrome data collection service"""
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referer = request.headers.get('Referer', 'Unknown')
    print(f"[Accounts API] Request from {request.remote_addr} - UA: {user_agent[:100]} - Referer: {referer}")
    
    # Use the thread-safe data collection service
    account_data = collect_chrome_data_safe()
    return jsonify(account_data)

# API endpoint to update phase status in Chrome tabs
@app.route('/api/update-phases', methods=['POST'])
def update_phases():
    print(f"\n[Phase Update API] Called at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[Phase Update API] Total connections: {len(controller.connections)}")
    
    try:
        results = []
        # Execute updateUserColumnPhaseStatus on all tabs
        for i, conn in enumerate(controller.connections):
            print(f"[Phase Update API] Processing connection {i}: {conn.account_name}")
            if conn.tab:
                try:
                    # First inject the risk management script that contains updateUserColumnPhaseStatus
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    risk_script_path = os.path.join(project_root, 
                                          'scripts/tampermonkey/autoriskManagement.js')
                    
                    # Read and extract the core functions from the script
                    with open(risk_script_path, 'r') as file:
                        risk_script = file.read()
                    
                    # Inject the complete autoriskManagement.js functions to run actual phase logic
                    functions_to_inject = """
                    // Inject phase criteria from autoriskManagement.js
                    const phaseCriteria = [
                        // ── DEMO ──
                        {
                            phase: '1',
                            accountNameIncludes: 'DEMO',
                            totalAvailOperator: '<',
                            totalAvailValue: 60000,
                            distDrawOperator: '>',
                            distDrawValue: 2000,
                            maxActive: 0,
                            reduceFactor: 0.5,
                            useOr: false,
                            quantity: 20
                        },
                        {
                            phase: '2',
                            accountNameIncludes: 'DEMO',
                            totalAvailOperator: '>=',
                            totalAvailValue: 60000,
                            distDrawOperator: '<=',
                            distDrawValue: 2000,
                            maxActive: 0,
                            reduceFactor: null,
                            useOr: true,
                            quantity: 10
                        },
                        
                        // ── APEX ──
                        {
                            phase: '1',
                            accountNameIncludes: 'APEX',
                            totalAvailOperator: '<',
                            totalAvailValue: 310000,
                            distDrawOperator: '>',
                            distDrawValue: 2000,
                            maxActive: 0,
                            reduceFactor: 0.5,
                            useOr: false,
                            quantity: 20
                        },
                        {
                            phase: '2',
                            accountNameIncludes: 'APEX',
                            totalAvailOperator: '>=',
                            totalAvailValue: 310000,
                            distDrawOperator: '<=',
                            distDrawValue: 2000,
                            maxActive: 0,
                            reduceFactor: null,
                            useOr: true,
                            quantity: 10
                        },
                        {
                            phase: '3',
                            accountNameIncludes: 'PAAPEX',
                            totalAvailOperator: null,
                            totalAvailValue: 0,
                            distDrawOperator: null,
                            distDrawValue: 0,
                            maxActive: 20,
                            reduceFactor: null,
                            useOr: false,
                            quantity: 2
                        }
                    ];
                    
                    // Phase analysis function
                    function analyzePhase(row, reset = false) {
                        if (reset || typeof analyzePhase.phaseData === 'undefined') {
                            console.log("[analyzePhase] resetting phaseData");
                            analyzePhase.phaseData = {};

                            const phase1Count = phaseCriteria.filter(r => r.phase === '1').length;
                            const rule1 = phaseCriteria.find(r => r.phase === '1');
                            if (rule1) {
                                rule1.maxActive = 1;
                                console.log(`[analyzePhase] set phase 1 maxActive to ${rule1.maxActive}`);
                            }

                            const increment = typeof analyzePhase.maxActiveIncrement === 'number'
                            ? analyzePhase.maxActiveIncrement
                            : 1;
                            const rule2 = phaseCriteria.find(r => r.phase === '2');
                            if (rule2) {
                                rule2.maxActive = 1;
                                console.log(`[analyzePhase] increased phase 2 maxActive to ${rule2.maxActive}`);
                            }
                        }

                        if (row === null) {
                            return;
                        }

                        function parseValue(val) {
                            if (!val || typeof val !== 'string') {
                                console.log(`[parseValue] Invalid value: ${val}, type: ${typeof val}`);
                                return 0;
                            }
                            const num = parseFloat(val.replace(/[$,()]/g, ''));
                            return (val.includes('(') && val.includes(')')) ? -num : num;
                        }
                        const parsed = {
                            totalAvail: parseValue(row["Total Available Margin"] || "$0.00"),
                            distDraw:   parseValue(row["Dist Drawdown Net Liq"] || "$0.00")
                        };

                        const accountName = row["Account ▲"] || row["Account"] || "";
                        function compareNumeric(value, operator, compareValue) {
                            const ops = { '>':(a,b)=>a>b, '<':(a,b)=>a<b, '>=':(a,b)=>a>=b, '<=':(a,b)=>a<=b };
                            return ops[operator]?.(value, compareValue) ?? false;
                        }
                        function matchesRule(rule) {
                            if (rule.accountNameIncludes && !accountName.includes(rule.accountNameIncludes)) return false;
                            const ta = rule.totalAvailOperator
                            ? compareNumeric(parsed.totalAvail, rule.totalAvailOperator, rule.totalAvailValue)
                            : true;
                            const dd = rule.distDrawOperator
                            ? compareNumeric(parsed.distDraw, rule.distDrawOperator, rule.distDrawValue)
                            : true;
                            return rule.useOr && rule.totalAvailOperator && rule.distDrawOperator
                                ? (ta || dd)
                            : (ta && dd);
                        }

                        let rule = accountName.includes('PAAPEX')
                        ? phaseCriteria.find(r => r.accountNameIncludes === 'PAAPEX')
                        : phaseCriteria.find(matchesRule) || { phase:'Unknown', maxActive:0, profitLimit:Infinity };

                        row.phase = rule.phase;
                        row.phaseInfo = { phase:rule.phase, maxActive:rule.maxActive, profitLimit:rule.profitLimit,
                                         accountName, totalAvail:parsed.totalAvail, distDraw:parsed.distDraw,
                                         reduceFactor:rule.reduceFactor||null };

                        if (rule.phase === '2' && parsed.totalAvail > 320000) {
                            row.active = false;
                            return rule.phase;
                        }

                        if (!analyzePhase.phaseData[rule.phase]) {
                            analyzePhase.phaseData[rule.phase] = { activeCount:0, cumulativeProfit:0 };
                        }

                        function parseDollar(val) {
                            const num = parseFloat(val.replace(/[$,()]/g, ''));
                            return (val.includes('(') && val.includes(')')) ? -num : num;
                        }
                        const profit = parseDollar(row["Dollar Total P L"]||"$0.00");
                        analyzePhase.phaseData[rule.phase].cumulativeProfit += profit;

                        // Determine how many can be active
                        let allowedActive = rule.maxActive;
                        if (analyzePhase.phaseData[rule.phase].cumulativeProfit > rule.profitLimit) {
                            allowedActive = rule.reduceFactor
                                ? Math.ceil(rule.maxActive * rule.reduceFactor)
                            : 0;
                        }

                        const currentActive = analyzePhase.phaseData[rule.phase].activeCount;
                        if (currentActive >= allowedActive) {
                            row.active = false;
                            return rule.phase;
                        }

                        // Otherwise activate
                        row.active = true;
                        analyzePhase.phaseData[rule.phase].activeCount++;

                        return rule.phase;
                    }
                    
                    // Enhanced getTableData function with real phase analysis
                    if (typeof getTableData === 'undefined') {
                        window.getTableData = function() {
                            const accountTable = document.querySelector('.module.positions.data-table');
                            if (!accountTable) return [];
                            
                            const rows = accountTable.querySelectorAll('.fixedDataTableRowLayout_rowWrapper');
                            if (!rows.length) return [];

                            // First row as header (skip header in final output)
                            const headerCells = rows[0].querySelectorAll('.public_fixedDataTableCell_cellContent');
                            const headers = Array.from(headerCells).map(cell => cell.textContent.trim());

                            const jsonData = [];
                            // Reset phase tracking before processing rows.
                            analyzePhase(null, true);

                            rows.forEach((row, index) => {
                                if (index === 0) return; // Skip header row
                                const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
                                const values = Array.from(cells).map(cell => cell.textContent.trim());
                                if (values.length) {
                                    const rowObj = {};
                                    headers.forEach((header, i) => {
                                        rowObj[header] = values[i];
                                    });
                                    // Process the row to determine its phase and active state.
                                    rowObj.phase = analyzePhase(rowObj);

                                    // Build a simplified object with the desired keys including "active".
                                    const simpleRow = {
                                        "Account ▲": rowObj["Account ▲"] || rowObj["Account"] || "",
                                        "Dollar Total P L": rowObj["Dollar Total P L"] || "",
                                        "Dollar Open P L": rowObj["Dollar Open P L"] || "",
                                        "Dist Drawdown Net Liq": rowObj["Dist Drawdown Net Liq"] || "",
                                        "Total Available Margin": rowObj["Total Available Margin"] || "",
                                        "phase": rowObj.phase,
                                        "active": rowObj.active || false
                                    };

                                    jsonData.push(simpleRow);
                                }
                            });

                            return jsonData;
                        };
                    }
                    
                    if (typeof updateUserColumnPhaseStatus === 'undefined') {
                        window.updateUserColumnPhaseStatus = function() {
                            console.log("[updateUserColumnPhaseStatus] Starting...");
                            
                            const accountTable = document.querySelector('.module.positions.data-table');
                            if (!accountTable) {
                                console.error("[updateUserColumnPhaseStatus] No accountTable found");
                                return;
                            }
                            
                            const rows = accountTable.querySelectorAll('.fixedDataTableRowLayout_rowWrapper');
                            if (!rows.length) {
                                console.error("[updateUserColumnPhaseStatus] No rows found");
                                return;
                            }
                            console.log(`[updateUserColumnPhaseStatus] Found ${rows.length} rows`);
                            
                            // Determine the index of the "User" column from the header row
                            const headerCells = rows[0].querySelectorAll('.public_fixedDataTableCell_cellContent');
                            console.log(`[updateUserColumnPhaseStatus] Header cells:`, 
                                Array.from(headerCells).map(c => c.textContent.trim()));
                                
                            let userIndex = -1;
                            headerCells.forEach((cell, i) => {
                                if (cell.textContent.trim().startsWith("User")) {
                                    userIndex = i;
                                    console.log(`[updateUserColumnPhaseStatus] Found User column at index ${i}`);
                                }
                            });
                            
                            if (userIndex === -1) {
                                console.error("[updateUserColumnPhaseStatus] User column not found");
                                return;
                            }
                            
                            console.log("[updateUserColumnPhaseStatus] Getting table data...");
                            const tableData = getTableData();
                            console.log(`[updateUserColumnPhaseStatus] Table data: ${tableData.length} rows`);
                            if (tableData.length === 0) {
                                console.error("[updateUserColumnPhaseStatus] No data from getTableData()");
                                return;
                            }
                            
                            // Update the "User" column cells for each data row with phase and status
                            rows.forEach((row, idx) => {
                                if (idx === 0) return; // skip header row
                                const cells = row.querySelectorAll('.public_fixedDataTableCell_cellContent');
                                
                                if (cells.length > userIndex) {
                                    const cell = cells[userIndex];
                                    if (!tableData[idx - 1]) {
                                        console.error(`[updateUserColumnPhaseStatus] No data for row ${idx}`);
                                        return;
                                    }
                                    
                                    const dataRow = tableData[idx - 1];
                                    const accountName = dataRow["Account ▲"] || dataRow["Account"] || "Unknown";
                                    console.log(`[updateUserColumnPhaseStatus] Setting row ${idx} (${accountName}) phase=${dataRow.phase}, active=${dataRow.active}`);
                                    
                                    cell.textContent = `${dataRow.phase} (${dataRow.active ? 'active' : 'inactive'})`;
                                    cell.style.color = dataRow.active ? 'green' : 'red';
                                } else {
                                    console.error(`[updateUserColumnPhaseStatus] Row ${idx} doesn't have enough cells`);
                                }
                            });
                            
                            console.log("[updateUserColumnPhaseStatus] Completed");
                        };
                    }
                    """
                    
                    # Inject the functions
                    print(f"[Phase Update API] Injecting functions for {conn.account_name}")
                    conn.tab.Runtime.evaluate(expression=functions_to_inject)
                    
                    # Now execute updateUserColumnPhaseStatus
                    print(f"[Phase Update API] Executing updateUserColumnPhaseStatus for {conn.account_name}")
                    result = conn.tab.Runtime.evaluate(
                        expression="updateUserColumnPhaseStatus(); 'Phase update completed';")
                    
                    if result and 'result' in result:
                        print(f"[Phase Update API] Success for {conn.account_name}: {result['result'].get('value', 'Completed')}")
                        results.append({
                            "account": conn.account_name,
                            "status": "success",
                            "message": result['result'].get('value', 'Completed')
                        })
                    else:
                        print(f"[Phase Update API] No result for {conn.account_name}")
                        results.append({
                            "account": conn.account_name,
                            "status": "error",
                            "message": "No result returned"
                        })
                        
                except Exception as e:
                    print(f"[Phase Update API] Error for {conn.account_name}: {str(e)}")
                    results.append({
                        "account": conn.account_name,
                        "status": "error",
                        "message": str(e)
                    })
            else:
                print(f"[Phase Update API] No tab for connection {i}: {conn.account_name}")
        
        print(f"[Phase Update API] Completed. Total results: {len(results)}")
        return jsonify({
            "status": "success",
            "message": f"Phase update executed on {len(results)} accounts",
            "details": results
        })
        
    except Exception as e:
        print(f"[Phase Update API] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# API endpoint to get summary data
@app.route('/api/summary', methods=['GET'])
def get_summary():
    # We'll forward this to the accounts endpoint since we're now focusing on account data
    accounts_response = get_accounts()
    accounts_data = json.loads(accounts_response.get_data(as_text=True))
    
    # Calculate summary stats
    total_pnl = 0
    total_margin = 0
    
    for account in accounts_data:
        # Try to extract P&L (check both original and standardized names)
        pnl_fields = ['Total P&L', 'Dollar Total P L']
        for field in pnl_fields:
            if field in account:
                val = account[field]
                if isinstance(val, (int, float)):
                    total_pnl += val
                elif isinstance(val, str):
                    try:
                        total_pnl += float(val.replace('$', '').replace(',', ''))
                    except (ValueError, TypeError):
                        pass
                break
                    
        # Try to extract margin (check both original and standardized names)
        margin_fields = ['Available Margin', 'Total Available Margin']
        for field in margin_fields:
            if field in account:
                val = account[field]
                if isinstance(val, (int, float)):
                    total_margin += val
                elif isinstance(val, str):
                    try:
                        total_margin += float(val.replace('$', '').replace(',', ''))
                    except (ValueError, TypeError):
                        pass
                break
    
    return jsonify({
        'total_pnl': total_pnl,
        'total_margin': total_margin,
        'account_count': len(accounts_data)
    })

# API endpoint to execute trades
@app.route('/api/trade', methods=['POST'])
def execute_trade():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        quantity = data.get('quantity', 1)
        action = data.get('action', 'Buy')
        tick_size = data.get('tick_size', 0.25)
        account_index = data.get('account', 'all')
        
        # Check TP/SL enable flags
        enable_tp = data.get('enable_tp', True)
        enable_sl = data.get('enable_sl', True)
        
        # Only get TP/SL values if they are enabled
        tp_ticks = data.get('tp_ticks', 100) if enable_tp else 0
        sl_ticks = data.get('sl_ticks', 40) if enable_sl else 0
        
        # Ensure tp_ticks and sl_ticks are integers
        tp_ticks = int(tp_ticks) if tp_ticks else 0
        sl_ticks = int(sl_ticks) if sl_ticks else 0
        
        print(f"Trade request: {symbol} {action} {quantity} TP:{tp_ticks if enable_tp else 'disabled'} SL:{sl_ticks if enable_sl else 'disabled'}")
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            # We need to update auto_trade.js to respect tp_ticks=0 and sl_ticks=0 as disabled
            result = controller.execute_on_all(
                'auto_trade', 
                symbol, 
                quantity, 
                action, 
                tp_ticks if enable_tp else 0,  # Pass 0 to disable TP
                sl_ticks if enable_sl else 0,  # Pass 0 to disable SL
                tick_size
            )
            
            # Count successful trades
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            
            return jsonify({
                'status': 'success',
                'message': f'{action} trade executed on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': result
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'auto_trade', 
                symbol, 
                quantity, 
                action, 
                tp_ticks if enable_tp else 0,  # Pass 0 to disable TP
                sl_ticks if enable_sl else 0,  # Pass 0 to disable SL
                tick_size
            )
            
            return jsonify({
                'status': 'success',
                'message': f'{action} trade executed on account {account_index}',
                'accounts_affected': 1,
                'details': result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to exit positions or cancel orders
@app.route('/api/exit', methods=['POST'])
def exit_positions():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        option = data.get('option', 'cancel-option-Exit-at-Mkt-Cxl')
        account_index = data.get('account', 'all')
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            result = controller.execute_on_all('exit_positions', symbol, option)
            
            # Count successful operations
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            
            # After exit positions, run risk management on all accounts
            print(f"Running auto risk management after exit positions on all accounts")
            risk_results = controller.execute_on_all('run_risk_management')
            risk_accounts_affected = sum(1 for r in risk_results if r.get('result', {}).get('status') == 'success')
            print(f"Auto risk management completed on {risk_accounts_affected} accounts")
            
            return jsonify({
                'status': 'success',
                'message': f'Exit/cancel operation executed on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': result,
                'risk_management': {
                    'accounts_affected': risk_accounts_affected,
                    'details': risk_results
                }
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'exit_positions', 
                symbol, 
                option
            )
            
            # After exit positions, run risk management
            print(f"Running auto risk management after exit positions on account {account_index}")
            risk_result = controller.execute_on_one(
                account_index,
                'run_risk_management'
            )
            print(f"Auto risk management completed: {risk_result}")
            
            return jsonify({
                'status': 'success',
                'message': f'Exit/cancel operation executed on account {account_index}',
                'accounts_affected': 1,
                'details': result,
                'risk_management': risk_result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
        
# API endpoint to update symbol on accounts
@app.route('/api/update-symbol', methods=['POST'])
def update_symbol():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol', 'NQ')
        account_index = data.get('account', 'all')
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            result = controller.execute_on_all('update_symbol', symbol)
            
            # Count successful operations
            accounts_affected = sum(1 for r in result if 'error' not in r['result'])
            
            return jsonify({
                'status': 'success',
                'message': f'Symbol updated to {symbol} on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': result
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'update_symbol', 
                symbol
            )
            
            return jsonify({
                'status': 'success',
                'message': f'Symbol updated to {symbol} on account {account_index}',
                'accounts_affected': 1,
                'details': result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to update quantity on accounts
@app.route('/api/update-quantity', methods=['POST'])
def update_quantity():
    try:
        data = request.json
        
        # Extract parameters from request
        quantity = data.get('quantity', 1)
        account_index = data.get('account', 'all')
        
        # Update quantity in Chrome UI
        js_code = f"""
        (function() {{
            try {{
                // Update quantity input field
                const qtyInput = document.getElementById('quantityInput');
                if (qtyInput) {{
                    qtyInput.value = {quantity};
                    qtyInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    qtyInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    console.log("Quantity updated to {quantity} in Tradovate UI");
                    return "Quantity updated in UI";
                }} else {{
                    console.error("Quantity input field not found");
                    return "Quantity input field not found";
                }}
            }} catch (err) {{
                console.error("Error updating quantity:", err);
                return "Error: " + err.toString();
            }}
        }})();
        """
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            results = []
            for i, conn in enumerate(controller.connections):
                if conn.tab:
                    try:
                        ui_result = conn.tab.Runtime.evaluate(expression=js_code)
                        result_value = ui_result.get('result', {}).get('value', 'Unknown')
                        results.append({"account": i, "result": result_value})
                    except Exception as e:
                        results.append({"account": i, "error": str(e)})
            
            # Count successful operations
            accounts_affected = sum(1 for r in results if "error" not in r)
            
            return jsonify({
                'status': 'success',
                'message': f'Quantity updated to {quantity} on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': results
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            if account_index < len(controller.connections) and controller.connections[account_index].tab:
                try:
                    ui_result = controller.connections[account_index].tab.Runtime.evaluate(expression=js_code)
                    result_value = ui_result.get('result', {}).get('value', 'Unknown')
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Quantity updated to {quantity} on account {account_index}',
                        'accounts_affected': 1,
                        'details': result_value
                    })
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': str(e)
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Account {account_index} not found or not available'
                }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to run auto risk management
@app.route('/api/risk-management', methods=['POST'])
def run_risk_management():
    try:
        data = request.json
        account_index = data.get('account', 'all')
        
        if account_index == 'all':
            # Run on all accounts
            results = controller.execute_on_all('run_risk_management')
            
            # Count successful operations
            accounts_affected = sum(1 for r in results if r.get('result', {}).get('status') == 'success')
            
            return jsonify({
                'status': 'success',
                'message': f'Auto risk management executed on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': results
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            result = controller.execute_on_one(
                account_index,
                'run_risk_management'
            )
            
            return jsonify({
                'status': 'success',
                'message': f'Auto risk management executed on account {account_index}',
                'accounts_affected': 1,
                'details': result
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# API endpoint to get strategy mappings
@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        strategy_file = os.path.join(project_root, 'config/strategy_mappings.json')
        if not os.path.exists(strategy_file):
            # Create default file if it doesn't exist
            default_mappings = {
                "strategy_mappings": {
                    "DEFAULT": []
                }
            }
            with open(strategy_file, 'w') as f:
                json.dump(default_mappings, f, indent=2)
                
        with open(strategy_file, 'r') as f:
            mappings = json.load(f)
        return jsonify(mappings), 200
    except Exception as e:
        print(f"Error loading strategy mappings: {e}")
        return jsonify({"error": f"Failed to load strategy mappings: {str(e)}"}), 500

# API endpoint to update strategy mappings
@app.route('/api/strategies', methods=['POST'])
def update_strategies():
    try:
        data = request.json
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        strategy_file = os.path.join(project_root, 'config/strategy_mappings.json')
        
        with open(strategy_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Strategy mappings updated: {json.dumps(data, indent=2)}")
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error saving strategy mappings: {e}")
        return jsonify({"error": f"Failed to update strategy mappings: {str(e)}"}), 500

# API endpoint to update all trade control settings
@app.route('/api/update-trade-controls', methods=['POST'])
def update_trade_controls():
    try:
        data = request.json
        
        # Extract parameters from request
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        tp_ticks = data.get('tp_ticks')
        sl_ticks = data.get('sl_ticks')
        tick_size = data.get('tick_size')
        
        # Additional parameters
        enable_tp = data.get('enable_tp')
        enable_sl = data.get('enable_sl')
        tp_price = data.get('tp_price')
        sl_price = data.get('sl_price')
        entry_price = data.get('entry_price')
        source_field = data.get('source_field', None)  # Which field triggered the update
        account_index = data.get('account', 'all')
        
        # Create JavaScript to update all the trade controls in the UI
        js_code = """
        (function() {
            try {
                const updates = {
                    success: true,
                    updates: {}
                };
        """
        
        # Only update symbol if it was explicitly changed in the dashboard (not when other fields change)
        if symbol and source_field == 'symbolInput':
            js_code += f"""
                // Update symbol in Tradovate UI
                try {{
                    const symbolInput = document.getElementById('symbolInput');
                    if (symbolInput) {{
                        symbolInput.value = "{symbol}";
                        symbolInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        symbolInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.symbol = "{symbol}";
                        console.log("Updated symbol to {symbol} in Tradovate UI");
                    }}
                }} catch (err) {{
                    updates.updates.symbol = "error: " + err.toString();
                    console.error("Error updating symbol:", err);
                }}
            """
            
        if quantity:
            js_code += f"""
                // Update quantity - matching ID 'qtyInput' from autoOrder.user.js
                try {{
                    const qtyInput = document.getElementById('qtyInput');
                    if (qtyInput) {{
                        qtyInput.value = {quantity};
                        qtyInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        qtyInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.quantity = {quantity};
                    }}
                }} catch (err) {{
                    updates.updates.quantity = "error: " + err.toString();
                }}
            """
            
        if tp_ticks:
            js_code += f"""
                // Update TP ticks - matching ID 'tpInput' from autoOrder.user.js
                try {{
                    const tpInput = document.getElementById('tpInput');
                    if (tpInput) {{
                        tpInput.value = {tp_ticks};
                        tpInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        tpInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.tp_ticks = {tp_ticks};
                    }}
                }} catch (err) {{
                    updates.updates.tp_ticks = "error: " + err.toString();
                }}
            """
            
        if sl_ticks:
            js_code += f"""
                // Update SL ticks - matching ID 'slInput' from autoOrder.user.js
                try {{
                    const slInput = document.getElementById('slInput');
                    if (slInput) {{
                        slInput.value = {sl_ticks};
                        slInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        slInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.sl_ticks = {sl_ticks};
                    }}
                }} catch (err) {{
                    updates.updates.sl_ticks = "error: " + err.toString();
                }}
            """
            
        if tick_size:
            js_code += f"""
                // Update tick size - matching ID 'tickInput' from autoOrder.user.js
                try {{
                    const tickInput = document.getElementById('tickInput');
                    if (tickInput) {{
                        tickInput.value = {tick_size};
                        tickInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        tickInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.tick_size = {tick_size};
                    }}
                }} catch (err) {{
                    updates.updates.tick_size = "error: " + err.toString();
                }}
            """
        
        # Add additional fields
        if enable_tp is not None:
            js_code += f"""
                // Update TP checkbox - matching ID 'tpCheckbox' from autoOrder.user.js
                try {{
                    const tpCheckbox = document.getElementById('tpCheckbox');
                    if (tpCheckbox) {{
                        tpCheckbox.checked = {'true' if enable_tp else 'false'};
                        tpCheckbox.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.enable_tp = {'true' if enable_tp else 'false'};
                    }}
                }} catch (err) {{
                    updates.updates.enable_tp = "error: " + err.toString();
                }}
            """
            
        if enable_sl is not None:
            js_code += f"""
                // Update SL checkbox - matching ID 'slCheckbox' from autoOrder.user.js
                try {{
                    const slCheckbox = document.getElementById('slCheckbox');
                    if (slCheckbox) {{
                        slCheckbox.checked = {'true' if enable_sl else 'false'};
                        slCheckbox.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.enable_sl = {'true' if enable_sl else 'false'};
                    }}
                }} catch (err) {{
                    updates.updates.enable_sl = "error: " + err.toString();
                }}
            """
            
        if tp_price:
            js_code += f"""
                // Update TP price input - matching ID 'tpPriceInput' from autoOrder.user.js
                try {{
                    const tpPriceInput = document.getElementById('tpPriceInput');
                    if (tpPriceInput) {{
                        tpPriceInput.value = {tp_price};
                        tpPriceInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        tpPriceInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.tp_price = {tp_price};
                    }}
                }} catch (err) {{
                    updates.updates.tp_price = "error: " + err.toString();
                }}
            """
            
        if sl_price:
            js_code += f"""
                // Update SL price input - matching ID 'slPriceInput' from autoOrder.user.js
                try {{
                    const slPriceInput = document.getElementById('slPriceInput');
                    if (slPriceInput) {{
                        slPriceInput.value = {sl_price};
                        slPriceInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        slPriceInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.sl_price = {sl_price};
                    }}
                }} catch (err) {{
                    updates.updates.sl_price = "error: " + err.toString();
                }}
            """
            
        if entry_price:
            js_code += f"""
                // Update entry price input - matching ID 'entryPriceInput' from autoOrder.user.js
                try {{
                    const entryPriceInput = document.getElementById('entryPriceInput');
                    if (entryPriceInput) {{
                        entryPriceInput.value = {entry_price};
                        entryPriceInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        entryPriceInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        updates.updates.entry_price = {entry_price};
                    }}
                }} catch (err) {{
                    updates.updates.entry_price = "error: " + err.toString();
                }}
            """
        
        # Close the JavaScript function
        js_code += """
                console.log("Trade control updates complete:", updates);
                return JSON.stringify(updates);
            } catch (err) {
                console.error("Error updating trade controls:", err);
                return JSON.stringify({success: false, error: err.toString()});
            }
        })();
        """
        
        # Check if we should execute on all accounts or just one
        if account_index == 'all':
            results = []
            for i, conn in enumerate(controller.connections):
                if conn.tab:
                    try:
                        ui_result = conn.tab.Runtime.evaluate(expression=js_code)
                        result_value = ui_result.get('result', {}).get('value', '{}')
                        # Parse the JSON result
                        try:
                            parsed_result = json.loads(result_value)
                            results.append({"account": i, "result": parsed_result})
                        except:
                            results.append({"account": i, "result": result_value})
                    except Exception as e:
                        results.append({"account": i, "error": str(e)})
            
            # Count successful operations
            accounts_affected = sum(1 for r in results if "error" not in r)
            
            return jsonify({
                'status': 'success',
                'message': f'Trade controls updated on {accounts_affected} accounts',
                'accounts_affected': accounts_affected,
                'details': results
            })
        else:
            # Execute on specific account
            account_index = int(account_index)
            if account_index < len(controller.connections) and controller.connections[account_index].tab:
                try:
                    ui_result = controller.connections[account_index].tab.Runtime.evaluate(expression=js_code)
                    result_value = ui_result.get('result', {}).get('value', '{}')
                    # Parse the JSON result
                    try:
                        parsed_result = json.loads(result_value)
                        result = parsed_result
                    except:
                        result = result_value
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Trade controls updated on account {account_index}',
                        'accounts_affected': 1,
                        'details': result
                    })
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': str(e)
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Account {account_index} not found or not available'
                }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# SSE Endpoint for real-time updates
@app.route('/api/events', methods=['GET'])
def sse_stream():
    """Server-Sent Events endpoint for real-time account data updates with health monitoring"""
    # Collect client information for health tracking outside the generator
    user_agent = request.headers.get('User-Agent', 'Unknown')
    remote_addr = request.remote_addr
    
    def event_stream():
        client_id, client_queue = add_sse_client(user_agent, remote_addr)
        
        try:
            # Send initial connection confirmation with client info
            yield format_sse_message('connected', {
                'client_id': client_id[:8], 
                'timestamp': time.time(),
                'server_info': 'Trading Dashboard SSE v1.0'
            })
            
            # Send current data immediately if available
            print(f"[SSE] Client {client_id[:8]} connecting. last_account_data: {len(last_account_data) if last_account_data else 'None'} records")
            
            if last_account_data is not None and len(last_account_data) > 0:
                broadcast_data = {
                    'accounts': last_account_data,
                    'metadata': {
                        'timestamp': time.time(),
                        'initial_load': True,
                        'record_count': len(last_account_data)
                    }
                }
                print(f"[SSE] Sending initial data to client {client_id[:8]}: {len(last_account_data)} records")
                yield format_sse_message('account_data', broadcast_data)
            else:
                print(f"[SSE] No initial data available for client {client_id[:8]}, triggering immediate collection")
                # Send loading indicator
                yield format_sse_message('no_data', {'message': 'Collecting initial data...', 'timestamp': time.time()})
                
                # Trigger immediate data collection in a separate thread to avoid blocking SSE
                def trigger_immediate_collection():
                    try:
                        print(f"[SSE] Starting immediate collection for client {client_id[:8]}")
                        account_data = collect_chrome_data(chrome_service)
                        if account_data and len(account_data) > 0:
                            print(f"[SSE] Immediate collection successful: {len(account_data)} records")
                    except Exception as e:
                        print(f"[SSE] Immediate collection failed: {e}")
                
                threading.Thread(target=trigger_immediate_collection, daemon=True).start()
            
            # Stream events from the queue (non-blocking)
            last_heartbeat = time.time()
            while True:
                try:
                    # Non-blocking check for messages
                    try:
                        message = client_queue.get_nowait()
                        yield message
                        update_client_activity(client_id, success=True)
                    except queue.Empty:
                        # No messages available, send heartbeat if needed
                        now = time.time()
                        if now - last_heartbeat >= 30:
                            health_stats = get_data_statistics()
                            yield format_sse_message('heartbeat', {
                                'timestamp': now,
                                'client_id': client_id[:8],
                                'server_stats': health_stats
                            })
                            update_client_activity(client_id, success=True)
                            last_heartbeat = now
                        
                        # Brief sleep to prevent excessive CPU usage
                        time.sleep(0.1)
                        
                except Exception as e:
                    print(f"[SSE Health] Error streaming to client {client_id[:8]}: {e}")
                    update_client_activity(client_id, success=False)
                    break
        
        except GeneratorExit:
            print(f"[SSE Health] Client {client_id[:8]} disconnected (GeneratorExit)")
        except Exception as e:
            print(f"[SSE Health] Unexpected error for client {client_id[:8]}: {e}")
        finally:
            remove_sse_client(client_id)
    
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

# Health monitoring endpoint
@app.route('/api/health', methods=['GET'])
def health_status():
    """Get detailed health status of all system components"""
    client_health = get_client_health_status()
    data_stats = get_data_statistics()
    scheduler_status = get_scheduler_status()
    chrome_health = get_chrome_health_status()
    
    # Determine overall system health
    system_health = 'healthy'
    if not scheduler_status['active']:
        system_health = 'scheduler_down'
    elif scheduler_status['health_status'] == 'degraded':
        system_health = 'degraded'
    elif chrome_health['success_rate'] < 70:
        system_health = 'chrome_degraded'
    elif client_health['total_clients'] == 0:
        system_health = 'no_clients'
    
    health_info = {
        'timestamp': time.time(),
        'sse_clients': client_health,
        'data_collection': data_stats,
        'scheduler': scheduler_status,
        'chrome_health': chrome_health,
        'chrome_connections': len(controller.connections),
        'system_status': system_health
    }
    
    return jsonify(health_info)

# Chrome health monitoring endpoint
@app.route('/api/chrome/health', methods=['GET'])
def chrome_health_status():
    """Get detailed Chrome connection health status"""
    return jsonify(get_chrome_health_status())

# Scheduler control endpoints
@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the background refresh scheduler"""
    success = start_background_scheduler()
    return jsonify({
        'success': success,
        'message': 'Scheduler started' if success else 'Scheduler already running',
        'status': get_scheduler_status()
    })

@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the background refresh scheduler"""
    success = stop_background_scheduler()
    return jsonify({
        'success': success,
        'message': 'Scheduler stopped' if success else 'Scheduler was not running',
        'status': get_scheduler_status()
    })

@app.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    """Get current scheduler status"""
    return jsonify(get_scheduler_status())

# Run the app
def run_flask_dashboard():
    """Start the Flask dashboard with all services"""
    inject_account_data_function()
    
    # Start the background refresh scheduler
    print("[Dashboard] Starting background refresh scheduler...")
    start_background_scheduler()
    
    try:
        app.run(host='0.0.0.0', port=6001)
    finally:
        # Cleanup on shutdown
        print("[Dashboard] Shutting down background scheduler...")
        stop_background_scheduler()

if __name__ == '__main__':
    # Start the Flask server with all services
    inject_account_data_function()
    
    # Start the background refresh scheduler
    print("[Dashboard] Starting background refresh scheduler...")
    start_background_scheduler()
    
    try:
        app.run(host='0.0.0.0', port=6001, debug=True)
        print("Dashboard running at http://localhost:6001")
    except KeyboardInterrupt:
        print("\n[Dashboard] Received shutdown signal")
    finally:
        # Cleanup on shutdown
        print("[Dashboard] Shutting down background scheduler...")
        stop_background_scheduler()
        print("[Dashboard] Shutdown complete")