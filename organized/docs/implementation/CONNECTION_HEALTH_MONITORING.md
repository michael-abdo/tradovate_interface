# Connection Health Monitoring Implementation Guide
## Automated Network Recovery and Failover for Trading Reliability

---

## 🚨 CRITICAL TRADING REQUIREMENT
**Network failures = missed trades and unmanaged positions**  
**Target**: <30 second recovery time with zero missed trades

---

## OVERVIEW

The Connection Health Monitoring system provides real-time network health assessment, automatic failure detection, and seamless failover to backup connections to ensure uninterrupted trading operations.

### Key Features
- **Real-time connection monitoring** - Continuous health checks every 5 seconds
- **Multi-level failure detection** - TCP, HTTP, WebSocket, and application-level checks
- **Connection pooling** - Primary and backup connections per account
- **Automatic failover** - Seamless switching without losing trading state
- **Network quality assessment** - Latency, bandwidth, and stability monitoring

---

## IMPLEMENTATION PHASES

## Phase 1: Connection Monitoring Infrastructure

### 1.1 Connection Health Monitor Class

**File**: `src/utils/connection_monitor.py`

```python
import asyncio
import threading
import time
import json
import requests
import websocket
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import logging
import statistics

class ConnectionState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"

@dataclass
class ConnectionMetrics:
    response_time: float
    success_rate: float
    error_count: int
    last_success: datetime
    last_failure: Optional[datetime]
    consecutive_failures: int
    consecutive_successes: int

@dataclass
class ConnectionInfo:
    account_name: str
    port: int
    browser_instance: object
    tab_id: str
    state: ConnectionState
    metrics: ConnectionMetrics
    backup_available: bool

class ConnectionHealthMonitor:
    def __init__(self, config_path: str = "config/connection_monitor.json"):
        self.connections: Dict[str, Dict[str, ConnectionInfo]] = {}
        self.config = self._load_config(config_path)
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        self.connection_lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        self.metrics_history: Dict[str, List[Dict]] = {}
        self.failure_callbacks: List[Callable] = []
        self.recovery_callbacks: List[Callable] = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load connection monitoring configuration"""
        default_config = {
            "check_interval": 5,  # seconds
            "health_check_timeout": 10,  # seconds
            "failure_threshold": 3,  # consecutive failures
            "recovery_threshold": 2,  # consecutive successes
            "degraded_response_time": 2.0,  # seconds
            "failed_response_time": 5.0,  # seconds
            "connection_pool_size": 2,  # primary + backup
            "retry_attempts": 3,
            "retry_delay": 1.0,  # seconds
            "metrics_retention_hours": 24
        }
        
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            self.logger.warning(f"Config file {config_path} not found, using defaults")
            
        return default_config
```

**Implementation Steps**:
- [ ] **1.1.1** Create `src/utils/connection_monitor.py` file
- [ ] **1.1.2** Define connection tracking with primary/backup pools
- [ ] **1.1.3** Add connection registry with state management
- [ ] **1.1.4** Define connection states and metrics structures
- [ ] **1.1.5** Initialize connection pool with load balancing
- [ ] **1.1.6** Add configuration loading with monitoring parameters

### 1.2 Connection Metrics Collection

```python
def _collect_connection_metrics(self, account_name: str, connection_type: str) -> ConnectionMetrics:
    """Collect comprehensive connection metrics"""
    connection_info = self.connections[account_name][connection_type]
    
    # Initialize metrics if not exists
    if not hasattr(connection_info, 'metrics') or not connection_info.metrics:
        connection_info.metrics = ConnectionMetrics(
            response_time=0.0,
            success_rate=1.0,
            error_count=0,
            last_success=datetime.now(),
            last_failure=None,
            consecutive_failures=0,
            consecutive_successes=0
        )
    
    # Perform health check and measure response time
    start_time = time.time()
    health_result = self._perform_health_check(account_name, connection_type)
    response_time = time.time() - start_time
    
    # Update metrics
    metrics = connection_info.metrics
    metrics.response_time = response_time
    
    if health_result["healthy"]:
        metrics.consecutive_successes += 1
        metrics.consecutive_failures = 0
        metrics.last_success = datetime.now()
    else:
        metrics.consecutive_failures += 1
        metrics.consecutive_successes = 0
        metrics.error_count += 1
        metrics.last_failure = datetime.now()
    
    # Calculate rolling success rate
    metrics.success_rate = self._calculate_success_rate(account_name, connection_type)
    
    # Store metrics in history
    self._store_metrics_history(account_name, connection_type, metrics)
    
    return metrics

def _calculate_success_rate(self, account_name: str, connection_type: str) -> float:
    """Calculate rolling success rate over time window"""
    history_key = f"{account_name}_{connection_type}"
    
    if history_key not in self.metrics_history:
        return 1.0
    
    # Get metrics from last hour
    cutoff_time = datetime.now() - timedelta(hours=1)
    recent_metrics = [
        m for m in self.metrics_history[history_key]
        if datetime.fromisoformat(m["timestamp"]) > cutoff_time
    ]
    
    if not recent_metrics:
        return 1.0
    
    successful_checks = sum(1 for m in recent_metrics if m["healthy"])
    total_checks = len(recent_metrics)
    
    return successful_checks / total_checks

def _store_metrics_history(self, account_name: str, connection_type: str, metrics: ConnectionMetrics):
    """Store metrics history for analysis"""
    history_key = f"{account_name}_{connection_type}"
    
    if history_key not in self.metrics_history:
        self.metrics_history[history_key] = []
    
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "response_time": metrics.response_time,
        "healthy": metrics.consecutive_failures == 0,
        "error_count": metrics.error_count,
        "success_rate": metrics.success_rate
    }
    
    self.metrics_history[history_key].append(history_entry)
    
    # Cleanup old entries
    cutoff_time = datetime.now() - timedelta(hours=self.config["metrics_retention_hours"])
    self.metrics_history[history_key] = [
        entry for entry in self.metrics_history[history_key]
        if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
    ]
```

**Implementation Steps**:
- [ ] **1.2.1** Implement response time tracking for each connection
- [ ] **1.2.2** Track success/failure rates over time windows
- [ ] **1.2.3** Monitor connection establishment time and stability
- [ ] **1.2.4** Collect network error types and frequencies
- [ ] **1.2.5** Track connection recovery time after failures
- [ ] **1.2.6** Store metrics in time-series format

### 1.3 Health Check Scheduling

```python
def start_monitoring(self):
    """Start background connection monitoring"""
    if self.monitoring_thread and self.monitoring_thread.is_alive():
        self.logger.warning("Connection monitoring already running")
        return
    
    self.shutdown_event.clear()
    self.monitoring_thread = threading.Thread(
        target=self._monitoring_loop,
        name="ConnectionHealthMonitor",
        daemon=True
    )
    self.monitoring_thread.start()
    self.logger.info("Connection health monitoring started")

def _monitoring_loop(self):
    """Main monitoring loop with staggered checks"""
    check_cycle = 0
    
    while not self.shutdown_event.is_set():
        try:
            # Get list of connections to check
            with self.connection_lock:
                connections_to_check = self._get_connections_for_check(check_cycle)
            
            # Perform health checks in parallel for efficiency
            self._perform_parallel_health_checks(connections_to_check)
            
            # Process results and trigger actions
            self._process_health_check_results()
            
            check_cycle += 1
            
            # Wait for next check interval
            self.shutdown_event.wait(self.config["check_interval"])
            
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
            self.shutdown_event.wait(5)  # Brief pause before retry

def _get_connections_for_check(self, check_cycle: int) -> List[tuple]:
    """Get connections to check this cycle (staggered checking)"""
    all_connections = []
    
    for account_name, connection_types in self.connections.items():
        for connection_type, connection_info in connection_types.items():
            # Prioritize active trading connections
            priority = 0 if connection_type == "primary" else 1
            all_connections.append((account_name, connection_type, priority))
    
    # Sort by priority and distribute across check cycles
    all_connections.sort(key=lambda x: x[2])
    
    # Return subset for this cycle to avoid overwhelming system
    connections_per_cycle = max(1, len(all_connections) // 3)
    start_idx = (check_cycle * connections_per_cycle) % len(all_connections)
    end_idx = start_idx + connections_per_cycle
    
    return all_connections[start_idx:end_idx]

def _perform_parallel_health_checks(self, connections_to_check: List[tuple]):
    """Perform health checks in parallel"""
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        
        for account_name, connection_type, _ in connections_to_check:
            future = executor.submit(
                self._collect_connection_metrics,
                account_name,
                connection_type
            )
            futures.append((future, account_name, connection_type))
        
        # Process completed checks
        for future, account_name, connection_type in futures:
            try:
                metrics = future.result(timeout=self.config["health_check_timeout"])
                self._update_connection_state(account_name, connection_type, metrics)
            except Exception as e:
                self.logger.error(f"Health check failed for {account_name}/{connection_type}: {e}")
```

**Implementation Steps**:
- [ ] **1.3.1** Create background thread for continuous monitoring
- [ ] **1.3.2** Implement staggered health checks to avoid overload
- [ ] **1.3.3** Add adaptive check intervals based on health history
- [ ] **1.3.4** Create priority-based checking (active connections first)
- [ ] **1.3.5** Implement parallel health check execution
- [ ] **1.3.6** Add configurable monitoring intensity levels

---

## Phase 2: Health Check Mechanisms

### 2.1 Connection Liveness Tests

```python
def _perform_health_check(self, account_name: str, connection_type: str) -> Dict:
    """Comprehensive connection health check"""
    connection_info = self.connections[account_name][connection_type]
    port = connection_info.port
    
    health_result = {
        "account": account_name,
        "connection_type": connection_type,
        "timestamp": datetime.now().isoformat(),
        "healthy": True,
        "checks": {},
        "errors": []
    }
    
    try:
        # Level 1: TCP Connection Test
        tcp_healthy = self._test_tcp_connection(port)
        health_result["checks"]["tcp_connection"] = tcp_healthy
        
        if not tcp_healthy:
            health_result["healthy"] = False
            health_result["errors"].append("TCP connection failed")
            return health_result
        
        # Level 2: HTTP Response Test
        http_healthy, http_response_time = self._test_http_response(port)
        health_result["checks"]["http_response"] = http_healthy
        health_result["checks"]["http_response_time"] = http_response_time
        
        if not http_healthy:
            health_result["healthy"] = False
            health_result["errors"].append("HTTP response failed")
            return health_result
        
        # Level 3: WebSocket Connection Test
        ws_healthy = self._test_websocket_connection(port)
        health_result["checks"]["websocket"] = ws_healthy
        
        # Level 4: JavaScript Execution Test
        js_healthy, js_response_time = self._test_javascript_execution(port)
        health_result["checks"]["javascript_execution"] = js_healthy
        health_result["checks"]["js_response_time"] = js_response_time
        
        if not js_healthy:
            health_result["healthy"] = False
            health_result["errors"].append("JavaScript execution failed")
        
        # Level 5: DOM Accessibility Test
        dom_healthy = self._test_dom_accessibility(port)
        health_result["checks"]["dom_accessibility"] = dom_healthy
        
        if not dom_healthy:
            health_result["healthy"] = False
            health_result["errors"].append("DOM accessibility failed")
        
        # Overall health assessment
        critical_checks = ["tcp_connection", "http_response", "javascript_execution"]
        health_result["healthy"] = all(
            health_result["checks"].get(check, False) for check in critical_checks
        )
        
    except Exception as e:
        health_result["healthy"] = False
        health_result["errors"].append(f"Health check exception: {str(e)}")
    
    return health_result

def _test_tcp_connection(self, port: int) -> bool:
    """Test basic TCP connection to Chrome debugging port"""
    import socket
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except Exception:
        return False

def _test_http_response(self, port: int) -> tuple[bool, float]:
    """Test HTTP response time to Chrome debugging endpoint"""
    try:
        start_time = time.time()
        response = requests.get(
            f"http://localhost:{port}/json",
            timeout=self.config["health_check_timeout"]
        )
        response_time = time.time() - start_time
        
        return response.status_code == 200, response_time
    except requests.RequestException:
        return False, float('inf')

def _test_websocket_connection(self, port: int) -> bool:
    """Test WebSocket connection capability"""
    try:
        # Get available tab for WebSocket test
        response = requests.get(f"http://localhost:{port}/json", timeout=5)
        tabs = response.json()
        
        if not tabs:
            return False
        
        # Test WebSocket connection to first available tab
        tab = tabs[0]
        ws_url = tab["webSocketDebuggerUrl"]
        
        # Quick WebSocket connection test
        def on_error(ws, error):
            pass
        
        def on_close(ws, close_status_code, close_msg):
            pass
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_error=on_error,
            on_close=on_close
        )
        
        # Test connection with timeout
        connection_thread = threading.Thread(target=ws.run_forever)
        connection_thread.daemon = True
        connection_thread.start()
        
        time.sleep(1)  # Brief connection test
        ws.close()
        
        return True
        
    except Exception:
        return False

def _test_javascript_execution(self, port: int) -> tuple[bool, float]:
    """Test JavaScript execution via pychrome"""
    try:
        import pychrome
        
        start_time = time.time()
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        if not tabs:
            return False, float('inf')
        
        # Test JavaScript execution on first available tab
        tab = tabs[0]
        tab.start()
        
        # Simple JavaScript execution test
        result = tab.Runtime.evaluate(expression="1 + 1")
        execution_time = time.time() - start_time
        
        tab.stop()
        
        # Check if execution was successful
        success = (
            result.get("result", {}).get("value") == 2 and
            execution_time < self.config["health_check_timeout"]
        )
        
        return success, execution_time
        
    except Exception:
        return False, float('inf')

def _test_dom_accessibility(self, port: int) -> bool:
    """Test DOM accessibility and responsiveness"""
    try:
        import pychrome
        
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        # Find Tradovate tab
        tradovate_tab = None
        for tab in tabs:
            if "tradovate.com" in tab.url.lower():
                tradovate_tab = tab
                break
        
        if not tradovate_tab:
            return False
        
        tradovate_tab.start()
        
        # Test DOM accessibility
        dom_test_js = """
        ({
            documentReady: document.readyState === 'complete',
            bodyExists: document.body !== null,
            tradovateElements: document.querySelectorAll('[class*="trading"], [class*="chart"]').length > 0,
            responsive: Date.now()
        })
        """
        
        result = tradovate_tab.Runtime.evaluate(expression=dom_test_js)
        tradovate_tab.stop()
        
        dom_state = result.get("result", {}).get("value", {})
        
        return (
            dom_state.get("documentReady", False) and
            dom_state.get("bodyExists", False) and
            isinstance(dom_state.get("responsive"), (int, float))
        )
        
    except Exception:
        return False
```

**Implementation Steps**:
- [ ] **2.1.1** Implement basic TCP connection test to debugging port
- [ ] **2.1.2** Test HTTP response time to `/json` endpoint  
- [ ] **2.1.3** Verify WebSocket connection establishment capability
- [ ] **2.1.4** Test JavaScript execution response time via pychrome
- [ ] **2.1.5** Validate DOM accessibility and responsiveness
- [ ] **2.1.6** Check memory usage and resource consumption

### 2.2 Application-Level Health Checks

```python
def _test_tradovate_application_health(self, port: int) -> Dict:
    """Test Tradovate-specific application health"""
    try:
        import pychrome
        
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        # Find Tradovate tab
        tradovate_tab = None
        for tab in tabs:
            if "tradovate.com" in tab.url.lower():
                tradovate_tab = tab
                break
        
        if not tradovate_tab:
            return {"healthy": False, "error": "No Tradovate tab found"}
        
        tradovate_tab.start()
        
        # Comprehensive Tradovate application health check
        app_health_js = """
        ({
            // Authentication check
            authenticated: !document.querySelector('#name-input') && 
                          !document.querySelector('.login-form'),
            
            // Trading interface check
            tradingInterface: document.querySelector('.trading-interface') !== null ||
                            document.querySelector('[data-testid="trading-view"]') !== null,
            
            // Market data check
            marketDataActive: !!document.querySelector('.market-data') ||
                            !!document.querySelector('[class*="price"]'),
            
            // Order controls check
            orderControlsAvailable: !!document.querySelector('button[class*="buy"]') ||
                                  !!document.querySelector('button[class*="sell"]'),
            
            // WebSocket connection status
            websocketConnected: window.WebSocket && 
                              window.navigator.onLine,
            
            // JavaScript injection status
            scriptsLoaded: typeof window.autoTrade === 'function' ||
                          typeof window.clickExitForSymbol === 'function',
            
            // Performance metrics
            pageLoadComplete: document.readyState === 'complete',
            responseTime: performance.now(),
            
            // Error detection
            jsErrors: window.jsErrorCount || 0,
            networkErrors: window.networkErrorCount || 0,
            
            // Trading readiness
            tradingReady: typeof window.autoTrade === 'function' &&
                         !document.querySelector('.loading') &&
                         !document.querySelector('.error-message')
        })
        """
        
        result = tradovate_tab.Runtime.evaluate(expression=app_health_js)
        tradovate_tab.stop()
        
        app_state = result.get("result", {}).get("value", {})
        
        # Assess overall application health
        critical_components = [
            "authenticated",
            "tradingInterface", 
            "tradingReady"
        ]
        
        app_healthy = all(app_state.get(component, False) for component in critical_components)
        
        return {
            "healthy": app_healthy,
            "details": app_state,
            "critical_failures": [
                comp for comp in critical_components 
                if not app_state.get(comp, False)
            ]
        }
        
    except Exception as e:
        return {"healthy": False, "error": str(e)}

def _test_market_data_connectivity(self, port: int) -> bool:
    """Test market data feed connectivity"""
    try:
        import pychrome
        
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        tradovate_tab = None
        for tab in tabs:
            if "tradovate.com" in tab.url.lower():
                tradovate_tab = tab
                break
        
        if not tradovate_tab:
            return False
        
        tradovate_tab.start()
        
        # Check market data freshness
        market_data_js = """
        (() => {
            // Look for price elements and check if they're updating
            const priceElements = document.querySelectorAll('[class*="price"], [class*="bid"], [class*="ask"]');
            
            if (priceElements.length === 0) return false;
            
            // Check if prices contain valid numbers
            let validPrices = 0;
            priceElements.forEach(element => {
                const text = element.textContent || element.innerText || '';
                if (/\\d+\\.\\d+/.test(text)) {
                    validPrices++;
                }
            });
            
            // At least some price elements should contain valid price data
            return validPrices > 0;
        })()
        """
        
        result = tradovate_tab.Runtime.evaluate(expression=market_data_js)
        tradovate_tab.stop()
        
        return result.get("result", {}).get("value", False)
        
    except Exception:
        return False

def _test_order_placement_capability(self, port: int, test_mode: bool = True) -> bool:
    """Test order placement capability (safe test mode)"""
    if not test_mode:
        # Only perform in test mode to avoid accidental orders
        return True
    
    try:
        import pychrome
        
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        tradovate_tab = None
        for tab in tabs:
            if "tradovate.com" in tab.url.lower():
                tradovate_tab = tab
                break
        
        if not tradovate_tab:
            return False
        
        tradovate_tab.start()
        
        # Test order interface accessibility (without placing actual orders)
        order_test_js = """
        (() => {
            // Check if trading interface elements are accessible
            const buyButton = document.querySelector('button[class*="buy"], #buyBtn');
            const sellButton = document.querySelector('button[class*="sell"], #sellBtn');
            const qtyInput = document.querySelector('input[class*="quantity"], #qtyInput');
            const symbolInput = document.querySelector('input[class*="symbol"], #symbolInput');
            
            return {
                buyButtonAvailable: buyButton !== null && !buyButton.disabled,
                sellButtonAvailable: sellButton !== null && !sellButton.disabled,
                quantityInputAvailable: qtyInput !== null,
                symbolInputAvailable: symbolInput !== null,
                tradingInterfaceReady: typeof window.autoTrade === 'function'
            };
        })()
        """
        
        result = tradovate_tab.Runtime.evaluate(expression=order_test_js)
        tradovate_tab.stop()
        
        order_capability = result.get("result", {}).get("value", {})
        
        # All trading interface elements should be available
        return all(order_capability.values())
        
    except Exception:
        return False
```

**Implementation Steps**:
- [ ] **2.2.1** Test Tradovate page accessibility and rendering
- [ ] **2.2.2** Verify authentication status and session validity
- [ ] **2.2.3** Test trading interface element accessibility
- [ ] **2.2.4** Validate market data feed connectivity
- [ ] **2.2.5** Check order placement capability (test mode)
- [ ] **2.2.6** Verify JavaScript injection and execution success

---

## Phase 3: Failure Detection

### 3.1 Connection Failure Classification

```python
class FailureType(Enum):
    NETWORK_DISCONNECTION = "network_disconnection"
    SLOW_RESPONSE = "slow_response"
    AUTHENTICATION_EXPIRED = "authentication_expired"
    DOM_UNRESPONSIVE = "dom_unresponsive"
    JAVASCRIPT_FAILURE = "javascript_failure"
    WEBSOCKET_FAILURE = "websocket_failure"
    MARKET_DATA_STALE = "market_data_stale"

def _classify_failure_type(self, health_result: Dict) -> FailureType:
    """Classify failure type based on health check results"""
    checks = health_result.get("checks", {})
    errors = health_result.get("errors", [])
    
    # Network-level failures
    if not checks.get("tcp_connection", True):
        return FailureType.NETWORK_DISCONNECTION
    
    # Response time failures
    http_time = checks.get("http_response_time", 0)
    js_time = checks.get("js_response_time", 0)
    
    if (http_time > self.config["failed_response_time"] or 
        js_time > self.config["failed_response_time"]):
        return FailureType.SLOW_RESPONSE
    
    # Application-level failures
    if not checks.get("javascript_execution", True):
        return FailureType.JAVASCRIPT_FAILURE
    
    if not checks.get("dom_accessibility", True):
        return FailureType.DOM_UNRESPONSIVE
    
    if not checks.get("websocket", True):
        return FailureType.WEBSOCKET_FAILURE
    
    # Authentication failures (derived from app health check)
    app_details = health_result.get("app_health", {}).get("details", {})
    if not app_details.get("authenticated", True):
        return FailureType.AUTHENTICATION_EXPIRED
    
    # Market data failures
    if not app_details.get("marketDataActive", True):
        return FailureType.MARKET_DATA_STALE
    
    # Default to slow response if unclear
    return FailureType.SLOW_RESPONSE

def _assess_failure_severity(self, failure_type: FailureType, metrics: ConnectionMetrics) -> int:
    """Assess failure severity on scale of 1-10"""
    base_severity = {
        FailureType.NETWORK_DISCONNECTION: 10,  # Critical
        FailureType.AUTHENTICATION_EXPIRED: 9,   # Critical
        FailureType.JAVASCRIPT_FAILURE: 8,       # High
        FailureType.DOM_UNRESPONSIVE: 7,        # High
        FailureType.WEBSOCKET_FAILURE: 6,       # Medium-High
        FailureType.MARKET_DATA_STALE: 5,       # Medium
        FailureType.SLOW_RESPONSE: 3            # Low-Medium
    }.get(failure_type, 5)
    
    # Adjust based on failure frequency
    if metrics.consecutive_failures > 5:
        base_severity = min(10, base_severity + 2)
    elif metrics.consecutive_failures > 2:
        base_severity = min(10, base_severity + 1)
    
    # Adjust based on success rate
    if metrics.success_rate < 0.5:
        base_severity = min(10, base_severity + 2)
    elif metrics.success_rate < 0.8:
        base_severity = min(10, base_severity + 1)
    
    return base_severity

def _update_connection_state(self, account_name: str, connection_type: str, metrics: ConnectionMetrics):
    """Update connection state based on health metrics"""
    with self.connection_lock:
        if account_name not in self.connections:
            return
        
        connection_info = self.connections[account_name][connection_type]
        previous_state = connection_info.state
        
        # Determine new state
        if metrics.consecutive_failures == 0:
            # Healthy connection
            new_state = ConnectionState.HEALTHY
        elif metrics.consecutive_failures < self.config["failure_threshold"]:
            # Degraded but not failed
            if metrics.response_time > self.config["degraded_response_time"]:
                new_state = ConnectionState.DEGRADED
            else:
                new_state = ConnectionState.HEALTHY
        else:
            # Failed connection
            new_state = ConnectionState.FAILED
        
        # Update connection state
        connection_info.state = new_state
        connection_info.metrics = metrics
        
        # Log state changes
        if new_state != previous_state:
            self.logger.info(
                f"Connection state changed for {account_name}/{connection_type}: "
                f"{previous_state.value} -> {new_state.value}"
            )
            
            # Trigger appropriate callbacks
            if new_state == ConnectionState.FAILED and previous_state != ConnectionState.FAILED:
                self._trigger_failure_callbacks(account_name, connection_type, metrics)
            elif new_state == ConnectionState.HEALTHY and previous_state == ConnectionState.FAILED:
                self._trigger_recovery_callbacks(account_name, connection_type, metrics)

def _trigger_failure_callbacks(self, account_name: str, connection_type: str, metrics: ConnectionMetrics):
    """Trigger registered failure callbacks"""
    for callback in self.failure_callbacks:
        try:
            callback(account_name, connection_type, metrics)
        except Exception as e:
            self.logger.error(f"Failure callback error: {e}")

def _trigger_recovery_callbacks(self, account_name: str, connection_type: str, metrics: ConnectionMetrics):
    """Trigger registered recovery callbacks"""
    for callback in self.recovery_callbacks:
        try:
            callback(account_name, connection_type, metrics)
        except Exception as e:
            self.logger.error(f"Recovery callback error: {e}")
```

**Implementation Steps**:
- [ ] **3.1.1** Detect complete connection loss (TCP closed)
- [ ] **3.1.2** Identify partial failures (slow responses, timeouts)
- [ ] **3.1.3** Recognize authentication failures and session expiry
- [ ] **3.1.4** Detect DOM manipulation failures
- [ ] **3.1.5** Identify JavaScript execution failures
- [ ] **3.1.6** Classify network-level vs application-level failures

---

## Phase 4: Recovery Procedures

### 4.1 Immediate Recovery Actions

```python
def _initiate_connection_recovery(self, account_name: str, connection_type: str, failure_type: FailureType):
    """Initiate appropriate recovery procedure based on failure type"""
    self.logger.info(f"Starting recovery for {account_name}/{connection_type} - {failure_type.value}")
    
    recovery_strategy = {
        FailureType.NETWORK_DISCONNECTION: self._recover_network_connection,
        FailureType.SLOW_RESPONSE: self._recover_slow_connection,
        FailureType.AUTHENTICATION_EXPIRED: self._recover_authentication,
        FailureType.DOM_UNRESPONSIVE: self._recover_dom_interface,
        FailureType.JAVASCRIPT_FAILURE: self._recover_javascript_injection,
        FailureType.WEBSOCKET_FAILURE: self._recover_websocket_connection,
        FailureType.MARKET_DATA_STALE: self._recover_market_data
    }
    
    recovery_function = recovery_strategy.get(failure_type, self._recover_generic)
    
    # Mark connection as recovering
    with self.connection_lock:
        self.connections[account_name][connection_type].state = ConnectionState.RECOVERING
    
    # Execute recovery in separate thread to avoid blocking monitoring
    recovery_thread = threading.Thread(
        target=self._execute_recovery_with_timeout,
        args=(recovery_function, account_name, connection_type, failure_type),
        name=f"Recovery-{account_name}-{connection_type}",
        daemon=True
    )
    recovery_thread.start()

def _execute_recovery_with_timeout(self, recovery_function, account_name: str, 
                                 connection_type: str, failure_type: FailureType):
    """Execute recovery function with timeout and retry logic"""
    max_attempts = self.config["retry_attempts"]
    retry_delay = self.config["retry_delay"]
    
    for attempt in range(max_attempts):
        try:
            self.logger.info(f"Recovery attempt {attempt + 1}/{max_attempts} for {account_name}")
            
            # Execute recovery function
            success = recovery_function(account_name, connection_type)
            
            if success:
                self.logger.info(f"Recovery successful for {account_name}/{connection_type}")
                
                # Verify recovery with health check
                time.sleep(2)  # Brief pause for stabilization
                if self._verify_recovery(account_name, connection_type):
                    with self.connection_lock:
                        self.connections[account_name][connection_type].state = ConnectionState.HEALTHY
                    return
                else:
                    self.logger.warning(f"Recovery verification failed for {account_name}")
            
        except Exception as e:
            self.logger.error(f"Recovery attempt {attempt + 1} failed: {e}")
        
        # Wait before retry (exponential backoff)
        if attempt < max_attempts - 1:
            delay = retry_delay * (2 ** attempt)
            time.sleep(delay)
    
    # All recovery attempts failed
    self.logger.error(f"Recovery failed for {account_name}/{connection_type} after {max_attempts} attempts")
    
    # Try failover to backup connection
    if connection_type == "primary":
        self._attempt_failover_to_backup(account_name)

def _recover_network_connection(self, account_name: str, connection_type: str) -> bool:
    """Recover from network disconnection"""
    try:
        connection_info = self.connections[account_name][connection_type]
        port = connection_info.port
        
        # Reset pychrome connection
        import pychrome
        new_browser = pychrome.Browser(url=f"http://localhost:{port}")
        
        # Test basic connectivity
        tabs = new_browser.list_tab()
        if not tabs:
            return False
        
        # Update connection object
        connection_info.browser_instance = new_browser
        
        # Re-establish tab connection
        tradovate_tab = None
        for tab in tabs:
            if "tradovate.com" in tab.url.lower():
                tradovate_tab = tab
                break
        
        if tradovate_tab:
            connection_info.tab_id = tradovate_tab.id
            return True
        
        return False
        
    except Exception as e:
        self.logger.error(f"Network connection recovery failed: {e}")
        return False

def _recover_authentication(self, account_name: str, connection_type: str) -> bool:
    """Recover from authentication expiry"""
    try:
        connection_info = self.connections[account_name][connection_type]
        browser = connection_info.browser_instance
        
        # Get Tradovate tab
        tabs = browser.list_tab()
        tradovate_tab = None
        for tab in tabs:
            if "tradovate.com" in tab.url.lower():
                tradovate_tab = tab
                break
        
        if not tradovate_tab:
            return False
        
        tradovate_tab.start()
        
        # Check if login page is showing
        login_check_js = """
        document.querySelector('#name-input') !== null ||
        document.querySelector('.login-form') !== null
        """
        
        result = tradovate_tab.Runtime.evaluate(expression=login_check_js)
        login_needed = result.get("result", {}).get("value", False)
        
        if login_needed:
            # Get credentials and re-authenticate
            credentials = self._get_account_credentials(account_name)
            if credentials:
                success = self._execute_login_sequence(tradovate_tab, credentials)
                tradovate_tab.stop()
                return success
        else:
            # Session might have recovered on its own
            tradovate_tab.stop()
            return True
        
        tradovate_tab.stop()
        return False
        
    except Exception as e:
        self.logger.error(f"Authentication recovery failed: {e}")
        return False

def _recover_javascript_injection(self, account_name: str, connection_type: str) -> bool:
    """Recover from JavaScript injection failure"""
    try:
        connection_info = self.connections[account_name][connection_type]
        browser = connection_info.browser_instance
        
        # Get Tradovate tab
        tabs = browser.list_tab()
        tradovate_tab = None
        for tab in tabs:
            if "tradovate.com" in tab.url.lower():
                tradovate_tab = tab
                break
        
        if not tradovate_tab:
            return False
        
        tradovate_tab.start()
        
        # Re-inject required scripts
        script_paths = [
            "scripts/tampermonkey/autoOrder.user.js",
            "scripts/tampermonkey/autoriskManagement.js"
        ]
        
        for script_path in script_paths:
            if os.path.exists(script_path):
                with open(script_path, 'r') as f:
                    script_content = f.read()
                
                # Extract and inject script content
                script_core = self._extract_script_core(script_content)
                tradovate_tab.Runtime.evaluate(expression=script_core)
        
        # Verify injection success
        verification_js = """
        typeof window.autoTrade === 'function' &&
        typeof window.clickExitForSymbol === 'function'
        """
        
        result = tradovate_tab.Runtime.evaluate(expression=verification_js)
        success = result.get("result", {}).get("value", False)
        
        tradovate_tab.stop()
        return success
        
    except Exception as e:
        self.logger.error(f"JavaScript injection recovery failed: {e}")
        return False

def _verify_recovery(self, account_name: str, connection_type: str) -> bool:
    """Verify that recovery was successful"""
    try:
        # Perform comprehensive health check
        health_result = self._perform_health_check(account_name, connection_type)
        
        # Recovery is successful if all critical checks pass
        critical_checks = ["tcp_connection", "http_response", "javascript_execution"]
        return all(health_result["checks"].get(check, False) for check in critical_checks)
        
    except Exception:
        return False
```

**Implementation Steps**:
- [ ] **4.1.1** Implement automatic failover to backup connections
- [ ] **4.1.2** Execute connection reset and re-establishment
- [ ] **4.1.3** Clear connection state and reinitialize pychrome
- [ ] **4.1.4** Refresh browser tabs and re-inject scripts
- [ ] **4.1.5** Re-authenticate and restore session state
- [ ] **4.1.6** Validate recovery success before resuming

---

## Phase 5: Connection Pooling and Failover

### 5.1 Connection Pool Management

```python
def initialize_connection_pool(self, account_name: str, primary_port: int, backup_port: int):
    """Initialize connection pool with primary and backup connections"""
    
    with self.connection_lock:
        self.connections[account_name] = {}
        
        # Initialize primary connection
        primary_connection = self._create_connection(account_name, primary_port, "primary")
        self.connections[account_name]["primary"] = primary_connection
        
        # Initialize backup connection
        backup_connection = self._create_connection(account_name, backup_port, "backup")
        self.connections[account_name]["backup"] = backup_connection
        
        self.logger.info(f"Connection pool initialized for {account_name}")

def _create_connection(self, account_name: str, port: int, connection_type: str) -> ConnectionInfo:
    """Create a new connection info object"""
    import pychrome
    
    try:
        browser = pychrome.Browser(url=f"http://localhost:{port}")
        tabs = browser.list_tab()
        
        # Find Tradovate tab
        tab_id = None
        for tab in tabs:
            if "tradovate.com" in tab.url.lower():
                tab_id = tab.id
                break
        
        metrics = ConnectionMetrics(
            response_time=0.0,
            success_rate=1.0,
            error_count=0,
            last_success=datetime.now(),
            last_failure=None,
            consecutive_failures=0,
            consecutive_successes=0
        )
        
        return ConnectionInfo(
            account_name=account_name,
            port=port,
            browser_instance=browser,
            tab_id=tab_id or "",
            state=ConnectionState.UNKNOWN,
            metrics=metrics,
            backup_available=connection_type == "primary"
        )
        
    except Exception as e:
        self.logger.error(f"Failed to create connection for {account_name}:{port} - {e}")
        
        # Return failed connection info
        return ConnectionInfo(
            account_name=account_name,
            port=port,
            browser_instance=None,
            tab_id="",
            state=ConnectionState.FAILED,
            metrics=ConnectionMetrics(
                response_time=float('inf'),
                success_rate=0.0,
                error_count=1,
                last_success=datetime.now() - timedelta(hours=1),
                last_failure=datetime.now(),
                consecutive_failures=1,
                consecutive_successes=0
            ),
            backup_available=connection_type == "primary"
        )

def get_healthy_connection(self, account_name: str) -> Optional[ConnectionInfo]:
    """Get the healthiest available connection for an account"""
    
    with self.connection_lock:
        if account_name not in self.connections:
            return None
        
        connections = self.connections[account_name]
        
        # Prefer primary if healthy
        primary = connections.get("primary")
        if primary and primary.state == ConnectionState.HEALTHY:
            return primary
        
        # Fall back to backup if available and healthy
        backup = connections.get("backup")
        if backup and backup.state == ConnectionState.HEALTHY:
            return backup
        
        # If neither is healthy, return the least broken one
        available_connections = [conn for conn in connections.values() if conn.browser_instance]
        
        if not available_connections:
            return None
        
        # Sort by health metrics (fewer failures, better response time)
        available_connections.sort(
            key=lambda c: (c.metrics.consecutive_failures, c.metrics.response_time)
        )
        
        return available_connections[0]

def _attempt_failover_to_backup(self, account_name: str) -> bool:
    """Attempt failover from primary to backup connection"""
    
    try:
        with self.connection_lock:
            connections = self.connections.get(account_name, {})
            primary = connections.get("primary")
            backup = connections.get("backup")
            
            if not backup:
                self.logger.error(f"No backup connection available for {account_name}")
                return False
            
            # Check backup connection health
            backup_health = self._perform_health_check(account_name, "backup")
            
            if not backup_health["healthy"]:
                self.logger.error(f"Backup connection unhealthy for {account_name}")
                return False
            
            # Sync state from primary to backup if possible
            if primary and primary.browser_instance:
                self._sync_connection_state(primary, backup)
            
            # Mark backup as primary temporarily
            backup.backup_available = False
            
            self.logger.info(f"Failover successful for {account_name} - using backup connection")
            return True
            
    except Exception as e:
        self.logger.error(f"Failover failed for {account_name}: {e}")
        return False

def _sync_connection_state(self, source_conn: ConnectionInfo, target_conn: ConnectionInfo):
    """Synchronize state between connections"""
    try:
        if not source_conn.browser_instance or not target_conn.browser_instance:
            return
        
        # Get state from source connection
        source_tabs = source_conn.browser_instance.list_tab()
        source_tradovate_tab = None
        
        for tab in source_tabs:
            if "tradovate.com" in tab.url.lower():
                source_tradovate_tab = tab
                break
        
        if not source_tradovate_tab:
            return
        
        # Get state from target connection
        target_tabs = target_conn.browser_instance.list_tab()
        target_tradovate_tab = None
        
        for tab in target_tabs:
            if "tradovate.com" in tab.url.lower():
                target_tradovate_tab = tab
                break
        
        if not target_tradovate_tab:
            return
        
        # Sync trading parameters
        source_tradovate_tab.start()
        target_tradovate_tab.start()
        
        # Extract state from source
        state_extraction_js = """
        ({
            symbol: document.getElementById('symbolInput')?.value || '',
            quantity: document.getElementById('qtyInput')?.value || '',
            takeProfitTicks: document.getElementById('tpInput')?.value || '',
            stopLossTicks: document.getElementById('slInput')?.value || '',
            tickSize: document.getElementById('tickInput')?.value || ''
        })
        """
        
        source_result = source_tradovate_tab.Runtime.evaluate(expression=state_extraction_js)
        source_state = source_result.get("result", {}).get("value", {})
        
        # Apply state to target
        if source_state:
            state_application_js = f"""
            if (document.getElementById('symbolInput')) {{
                document.getElementById('symbolInput').value = '{source_state.get("symbol", "")}';
            }}
            if (document.getElementById('qtyInput')) {{
                document.getElementById('qtyInput').value = '{source_state.get("quantity", "")}';
            }}
            if (document.getElementById('tpInput')) {{
                document.getElementById('tpInput').value = '{source_state.get("takeProfitTicks", "")}';
            }}
            if (document.getElementById('slInput')) {{
                document.getElementById('slInput').value = '{source_state.get("stopLossTicks", "")}';
            }}
            if (document.getElementById('tickInput')) {{
                document.getElementById('tickInput').value = '{source_state.get("tickSize", "")}';
            }}
            """
            
            target_tradovate_tab.Runtime.evaluate(expression=state_application_js)
        
        source_tradovate_tab.stop()
        target_tradovate_tab.stop()
        
        self.logger.info(f"State synchronized between connections for {source_conn.account_name}")
        
    except Exception as e:
        self.logger.error(f"State synchronization failed: {e}")
```

**Implementation Steps**:
- [ ] **5.1.1** Create primary/secondary connection pools per account
- [ ] **5.1.2** Implement connection load balancing for performance
- [ ] **5.1.3** Add connection pool sizing based on requirements
- [ ] **5.1.4** Create connection lifecycle management
- [ ] **5.1.5** Implement connection warming to maintain readiness
- [ ] **5.1.6** Add pool health monitoring and adjustment

---

## Phase 6: Integration Points

### 6.1 Main Application Integration

**File Modifications**: `src/app.py`

```python
# Add to imports
from utils.connection_monitor import ConnectionHealthMonitor

class TradovateConnection:
    def __init__(self, port, account_name=None):
        # ... existing code ...
        
        # Initialize connection health monitoring
        if not hasattr(TradovateConnection, '_health_monitor'):
            TradovateConnection._health_monitor = ConnectionHealthMonitor()
            TradovateConnection._health_monitor.start_monitoring()
        
        # Register this connection with health monitor
        self._health_monitor.initialize_connection_pool(
            account_name or f"Account_{port}",
            port,
            port + 1000  # Backup port
        )
        
    def execute_trade_with_health_check(self, symbol, quantity=1, action="Buy", **kwargs):
        """Execute trade with connection health verification"""
        
        # Get healthy connection
        healthy_conn = self._health_monitor.get_healthy_connection(self.account_name)
        
        if not healthy_conn:
            return {"success": False, "error": "No healthy connection available"}
        
        # Use healthy connection for trading
        if healthy_conn.port != self.port:
            self.logger.info(f"Using failover connection on port {healthy_conn.port}")
            # Switch to backup connection
            self.port = healthy_conn.port
            self.browser = healthy_conn.browser_instance
        
        # Execute trade with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self._execute_trade_internal(symbol, quantity, action, **kwargs)
                
                if result.get("success"):
                    return result
                else:
                    self.logger.warning(f"Trade attempt {attempt + 1} failed: {result.get('error')}")
                    
            except Exception as e:
                self.logger.error(f"Trade execution error on attempt {attempt + 1}: {e}")
            
            # Brief pause before retry
            time.sleep(1)
        
        return {"success": False, "error": "Trade execution failed after retries"}
```

**Implementation Steps**:
- [ ] **6.1.1** Modify `TradovateConnection` class to use health monitoring
- [ ] **6.1.2** Add connection health checks before trading operations
- [ ] **6.1.3** Implement connection retry logic in trade functions
- [ ] **6.1.4** Add health monitoring to connection establishment
- [ ] **6.1.5** Update error handling to trigger recovery
- [ ] **6.1.6** Create health status reporting for dashboard

---

## TESTING REQUIREMENTS

### Unit Tests
```python
# test_connection_monitor.py
def test_connection_health_checks():
    """Test various health check mechanisms"""
    
def test_failure_detection_and_classification():
    """Test failure detection logic"""
    
def test_connection_pool_management():
    """Test connection pooling and failover"""
    
def test_recovery_procedures():
    """Test connection recovery mechanisms"""
```

### Integration Tests
- Simulate network disconnection scenarios
- Test failover under various failure conditions
- Validate state synchronization across connections
- Test recovery under load

### Performance Tests
- Connection pool efficiency under high load
- Health check overhead measurement
- Failover speed testing
- Memory usage optimization

---

## CONFIGURATION

**File**: `config/connection_monitor.json`
```json
{
    "check_interval": 5,
    "health_check_timeout": 10,
    "failure_threshold": 3,
    "recovery_threshold": 2,
    "degraded_response_time": 2.0,
    "failed_response_time": 5.0,
    "connection_pool_size": 2,
    "retry_attempts": 3,
    "retry_delay": 1.0,
    "metrics_retention_hours": 24,
    "enable_parallel_checks": true,
    "max_parallel_workers": 5,
    "log_level": "INFO"
}
```

---

## SUCCESS METRICS

- **Connection Availability**: >99.5% healthy connections
- **Recovery Time**: <30 seconds average failover time
- **False Positive Rate**: <2% incorrect failure detection
- **Failover Success**: >98% successful automatic failovers
- **Trading Continuity**: Zero missed trades due to connection issues

---

## OPERATIONAL PROCEDURES

### Monitoring Dashboard
- Real-time connection health matrix
- Response time trends and alerts
- Failover frequency and success rates
- Network quality metrics

### Alerting
- Connection degradation warnings
- Failover execution notifications
- Recovery failure escalations
- Performance threshold breaches

### Maintenance
- Connection pool optimization
- Health check threshold tuning
- Performance metric analysis
- Network quality assessment