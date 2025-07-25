# STABILITY IMPLEMENTATION PLAN
## Atomic Task Breakdown for Critical Trading System Fixes

---

## TASK 1: Chrome Process Watchdog - Restart on Crash Detection

### Phase 1: Process Monitoring Infrastructure

#### 1.1 Create Process Monitor Class
- [ ] **1.1.1** Create `src/utils/process_monitor.py` file
- [ ] **1.1.2** Define `ChromeProcessMonitor` class with initialization
- [ ] **1.1.3** Add process ID tracking dictionary: `{account_name: {'pid': int, 'port': int, 'last_seen': datetime}}`
- [ ] **1.1.4** Add process state enum: `STARTING`, `RUNNING`, `CRASHED`, `RESTARTING`
- [ ] **1.1.5** Initialize threading locks for thread-safe process tracking
- [ ] **1.1.6** Add configuration parameters: check interval, restart attempts, timeout values

#### 1.2 Process Health Check Mechanism
- [ ] **1.2.1** Implement `is_process_alive(pid)` using `psutil.pid_exists()`
- [ ] **1.2.2** Implement `is_chrome_responsive(port)` - test HTTP connection to debugging port
- [ ] **1.2.3** Implement `is_tradovate_accessible(port)` - verify Tradovate tab exists and responds
- [ ] **1.2.4** Create composite health check: `check_chrome_health(account_name)`
- [ ] **1.2.5** Add health check logging with timestamps and status codes
- [ ] **1.2.6** Implement exponential backoff for failed health checks

#### 1.3 Continuous Monitoring Loop
- [ ] **1.3.1** Create background monitoring thread in `ChromeProcessMonitor`
- [ ] **1.3.2** Implement monitoring loop with configurable interval (default: 10 seconds)
- [ ] **1.3.3** Add graceful shutdown mechanism for monitoring thread
- [ ] **1.3.4** Implement health check scheduling to avoid overwhelming system
- [ ] **1.3.5** Add monitoring state persistence to survive Python process restarts
- [ ] **1.3.6** Create monitoring metrics collection (uptime, restart count, failure rate)

### Phase 2: Crash Detection

#### 2.1 Process Crash Detection
- [ ] **2.1.1** Detect when Chrome process PID no longer exists
- [ ] **2.1.2** Detect when Chrome debugging port becomes unresponsive
- [ ] **2.1.3** Detect when Chrome responds but Tradovate tab is missing/crashed
- [ ] **2.1.4** Implement crash type classification: `PROCESS_DIED`, `PORT_UNRESPONSIVE`, `TAB_CRASHED`
- [ ] **2.1.5** Add crash timestamp logging with detailed context
- [ ] **2.1.6** Implement crash pattern detection to identify systemic issues

#### 2.2 Crash Validation
- [ ] **2.2.1** Implement multi-check validation before declaring crash (3 failed checks over 30 seconds)
- [ ] **2.2.2** Add distinction between temporary unresponsiveness vs actual crash
- [ ] **2.2.3** Implement crash confirmation through multiple detection methods
- [ ] **2.2.4** Add crash false-positive prevention during system startup/login
- [ ] **2.2.5** Create crash severity assessment (partial vs complete failure)
- [ ] **2.2.6** Log crash validation results with confidence levels

### Phase 3: State Preservation Before Restart

#### 3.1 Account State Capture
- [ ] **3.1.1** Extract current account credentials from `config/credentials.json`
- [ ] **3.1.2** Capture current trading symbol from localStorage/DOM state
- [ ] **3.1.3** Capture current position information via JavaScript injection
- [ ] **3.1.4** Capture current order book state and pending orders
- [ ] **3.1.5** Capture UI state: TP/SL values, quantity settings, risk parameters
- [ ] **3.1.6** Save state to crash recovery file: `recovery/{account_name}_state.json`

#### 3.2 Connection State Backup
- [ ] **3.2.1** Record active pychrome connection objects and their state
- [ ] **3.2.2** Backup current tab IDs and their URLs
- [ ] **3.2.3** Capture JavaScript injection status (which scripts are loaded)
- [ ] **3.2.4** Record authentication status and session cookies
- [ ] **3.2.5** Save network connection parameters and proxy settings
- [ ] **3.2.6** Create connection state snapshot with timestamp

#### 3.3 Trading Context Preservation
- [ ] **3.3.1** Capture any in-flight trading operations and their status
- [ ] **3.3.2** Record recent trade history to avoid duplicate operations
- [ ] **3.3.3** Backup risk management settings and current exposure
- [ ] **3.3.4** Save market data context (last prices, volatility state)
- [ ] **3.3.5** Preserve webhook registration state and active subscriptions
- [ ] **3.3.6** Create trading context checkpoint file

### Phase 4: Restart Procedures

#### 4.1 Clean Shutdown Process
- [ ] **4.1.1** Send graceful termination signal to Chrome process (SIGTERM)
- [ ] **4.1.2** Wait for graceful shutdown (max 10 seconds)
- [ ] **4.1.3** Force kill Chrome process if graceful shutdown fails (SIGKILL)
- [ ] **4.1.4** Clean up temporary Chrome profile directories
- [ ] **4.1.5** Release debugging port resources
- [ ] **4.1.6** Clear any zombie pychrome connection objects

#### 4.2 Chrome Process Restart
- [ ] **4.2.1** Generate new Chrome profile directory path
- [ ] **4.2.2** Verify debugging port is available before restart
- [ ] **4.2.3** Launch new Chrome process with identical parameters to original
- [ ] **4.2.4** Implement startup verification - wait for debugging port activation
- [ ] **4.2.5** Verify Chrome process health before proceeding
- [ ] **4.2.6** Update process tracking with new PID and startup time

#### 4.3 Restart Failure Handling
- [ ] **4.3.1** Implement retry logic: max 3 restart attempts with exponential backoff
- [ ] **4.3.2** Try alternative Chrome profiles/configurations on repeated failures
- [ ] **4.3.3** Escalate to system administrator on multiple restart failures
- [ ] **4.3.4** Implement circuit breaker pattern - temporary disable on excessive failures
- [ ] **4.3.5** Log all restart attempts and their outcomes
- [ ] **4.3.6** Create restart failure alerts and notifications

### Phase 5: State Restoration After Restart

#### 5.1 Authentication Recovery
- [ ] **5.1.1** Navigate to Tradovate login page in new Chrome instance
- [ ] **5.1.2** Inject credentials from preserved state
- [ ] **5.1.3** Execute login sequence with validation at each step
- [ ] **5.1.4** Verify successful authentication and access to trading interface
- [ ] **5.1.5** Handle multi-factor authentication if required
- [ ] **5.1.6** Restore session cookies and authentication tokens

#### 5.2 Trading Interface Restoration
- [ ] **5.2.1** Wait for Tradovate interface to fully load
- [ ] **5.2.2** Re-inject all required Tampermonkey scripts
- [ ] **5.2.3** Restore trading symbol from preserved state
- [ ] **5.2.4** Restore UI settings: TP/SL values, quantities, risk parameters
- [ ] **5.2.5** Verify all trading controls are functional
- [ ] **5.2.6** Re-establish market data connections

#### 5.3 Connection State Recovery
- [ ] **5.3.1** Re-create pychrome connection objects
- [ ] **5.3.2** Re-establish all required browser tabs
- [ ] **5.3.3** Verify JavaScript injection capabilities
- [ ] **5.3.4** Restore event listeners and monitoring hooks
- [ ] **5.3.5** Re-register with main application connection pool
- [ ] **5.3.6** Validate full system connectivity end-to-end

### Phase 6: Integration with Existing Code

#### 6.1 Auto-Login Integration
- [ ] **6.1.1** Modify `src/auto_login.py` to register processes with watchdog
- [ ] **6.1.2** Add watchdog initialization to `launch_chrome_instances()` function
- [ ] **6.1.3** Update process tracking to include watchdog PIDs
- [ ] **6.1.4** Modify shutdown procedures to stop watchdog cleanly
- [ ] **6.1.5** Add watchdog status to login monitor reporting
- [ ] **6.1.6** Update configuration loading to include watchdog settings

#### 6.2 Main Application Integration
- [ ] **6.2.1** Modify `src/app.py` to handle connection restoration events
- [ ] **6.2.2** Add connection recovery callbacks for trade resumption
- [ ] **6.2.3** Update trading functions to verify connection health before execution
- [ ] **6.2.4** Add watchdog status to application health checks
- [ ] **6.2.5** Implement trading pause/resume during restart operations
- [ ] **6.2.6** Update error handling to trigger watchdog recovery

---

## TASK 2: Connection Health Monitoring - Detect/recover from network issues

### Phase 1: Connection Monitoring Infrastructure

#### 1.1 Connection Health Monitor Class
- [ ] **1.1.1** Create `src/utils/connection_monitor.py` file
- [ ] **1.1.2** Define `ConnectionHealthMonitor` class with connection tracking
- [ ] **1.1.3** Add connection registry: `{account_name: {'primary': conn, 'backup': conn, 'status': enum}}`
- [ ] **1.1.4** Define connection states: `HEALTHY`, `DEGRADED`, `FAILED`, `RECOVERING`
- [ ] **1.1.5** Initialize connection pool with primary and backup connections
- [ ] **1.1.6** Add configuration: health check intervals, retry attempts, failover thresholds

#### 1.2 Connection Metrics Collection
- [ ] **1.2.1** Implement response time tracking for each connection
- [ ] **1.2.2** Track connection success/failure rates over time windows
- [ ] **1.2.3** Monitor connection establishment time and stability
- [ ] **1.2.4** Collect network error types and frequencies
- [ ] **1.2.5** Track connection recovery time after failures
- [ ] **1.2.6** Store metrics in time-series format for analysis

#### 1.3 Health Check Scheduling
- [ ] **1.3.1** Create background thread for continuous health monitoring
- [ ] **1.3.2** Implement staggered health checks to avoid system overload
- [ ] **1.3.3** Add adaptive check intervals based on connection health history
- [ ] **1.3.4** Create priority-based checking (active trading connections first)
- [ ] **1.3.5** Implement health check batching for efficiency
- [ ] **1.3.6** Add configurable monitoring intensity levels

### Phase 2: Health Check Mechanisms

#### 2.1 Connection Liveness Tests
- [ ] **2.1.1** Implement basic TCP connection test to Chrome debugging port
- [ ] **2.1.2** Test HTTP response time to `/json` endpoint
- [ ] **2.1.3** Verify WebSocket connection establishment capability
- [ ] **2.1.4** Test JavaScript execution response time via pychrome
- [ ] **2.1.5** Validate DOM accessibility and responsiveness
- [ ] **2.1.6** Check memory usage and resource consumption

#### 2.2 Application-Level Health Checks
- [ ] **2.2.1** Test Tradovate page accessibility and rendering
- [ ] **2.2.2** Verify authentication status and session validity
- [ ] **2.2.3** Test trading interface element accessibility
- [ ] **2.2.4** Validate market data feed connectivity
- [ ] **2.2.5** Check order placement capability (test mode)
- [ ] **2.2.6** Verify JavaScript injection and execution success

#### 2.3 Network Quality Assessment
- [ ] **2.3.1** Measure network latency to Tradovate servers
- [ ] **2.3.2** Test bandwidth available for trading operations
- [ ] **2.3.3** Detect packet loss and connection instability
- [ ] **2.3.4** Monitor DNS resolution times for trading domains
- [ ] **2.3.5** Test proxy/VPN connection stability if applicable
- [ ] **2.3.6** Assess network congestion impact on trading

### Phase 3: Failure Detection

#### 3.1 Connection Failure Classification
- [ ] **3.1.1** Detect complete connection loss (TCP connection closed)
- [ ] **3.1.2** Identify partial failures (slow responses, timeouts)
- [ ] **3.1.3** Recognize authentication failures and session expiry
- [ ] **3.1.4** Detect DOM manipulation failures (elements not found)
- [ ] **3.1.5** Identify JavaScript execution failures and errors
- [ ] **3.1.6** Classify network-level vs application-level failures

#### 3.2 Failure Severity Assessment
- [ ] **3.2.1** Determine if failure affects trading capability immediately
- [ ] **3.2.2** Assess impact on position monitoring and risk management
- [ ] **3.2.3** Evaluate effect on order execution and modification
- [ ] **3.2.4** Determine if failure is temporary or requires intervention
- [ ] **3.2.5** Assess whether backup connections can handle the load
- [ ] **3.2.6** Create failure severity scoring system (1-10 scale)

#### 3.3 Failure Pattern Recognition
- [ ] **3.3.1** Identify recurring failure patterns and root causes
- [ ] **3.3.2** Detect system-wide issues vs isolated account problems
- [ ] **3.3.3** Recognize market hours vs off-hours failure patterns
- [ ] **3.3.4** Identify correlation between network conditions and failures
- [ ] **3.3.5** Track failure clustering and cascade effects
- [ ] **3.3.6** Create predictive failure detection based on patterns

### Phase 4: Recovery Procedures

#### 4.1 Immediate Recovery Actions
- [ ] **4.1.1** Implement automatic failover to backup connections
- [ ] **4.1.2** Execute connection reset and re-establishment procedures
- [ ] **4.1.3** Clear connection state and reinitialize pychrome objects
- [ ] **4.1.4** Refresh browser tabs and re-inject required scripts
- [ ] **4.1.5** Re-authenticate and restore session state
- [ ] **4.1.6** Validate recovery success before resuming operations

#### 4.2 Progressive Recovery Strategy
- [ ] **4.2.1** Start with least disruptive recovery methods first
- [ ] **4.2.2** Escalate to more aggressive recovery if simple methods fail
- [ ] **4.2.3** Implement recovery timeout limits to prevent infinite loops
- [ ] **4.2.4** Add recovery attempt counters with circuit breaker logic
- [ ] **4.2.5** Create recovery success validation at each escalation level
- [ ] **4.2.6** Log all recovery attempts and their effectiveness

#### 4.3 Recovery Verification
- [ ] **4.3.1** Test connection stability after recovery
- [ ] **4.3.2** Verify all trading functions are operational
- [ ] **4.3.3** Confirm market data feeds are working
- [ ] **4.3.4** Validate position monitoring and risk controls
- [ ] **4.3.5** Test order placement capability (if safe to do so)
- [ ] **4.3.6** Create post-recovery health assessment report

### Phase 5: Connection Pooling and Failover

#### 5.1 Connection Pool Management
- [ ] **5.1.1** Create primary/secondary connection pools per account
- [ ] **5.1.2** Implement connection load balancing for optimal performance
- [ ] **5.1.3** Add connection pool sizing based on trading requirements
- [ ] **5.1.4** Create connection lifecycle management (create, use, retire)
- [ ] **5.1.5** Implement connection warming to maintain readiness
- [ ] **5.1.6** Add pool health monitoring and automatic pool adjustment

#### 5.2 Failover Logic
- [ ] **5.2.1** Define failover triggers and thresholds
- [ ] **5.2.2** Implement seamless failover without losing trading state
- [ ] **5.2.3** Create failover decision tree based on failure type
- [ ] **5.2.4** Add automatic failback to primary connections when recovered
- [ ] **5.2.5** Implement graceful degradation for partial failures
- [ ] **5.2.6** Create failover notification and logging system

#### 5.3 State Synchronization
- [ ] **5.3.1** Synchronize authentication state across all connections
- [ ] **5.3.2** Maintain consistent trading parameters across failover
- [ ] **5.3.3** Sync JavaScript injection state and script versions
- [ ] **5.3.4** Keep position and order state consistent across connections
- [ ] **5.3.5** Synchronize risk management settings and limits
- [ ] **5.3.6** Create state verification after each failover event

### Phase 6: Integration Points

#### 6.1 Main Application Integration
- [ ] **6.1.1** Modify `TradovateConnection` class to use health monitoring
- [ ] **6.1.2** Add connection health checks before each trading operation
- [ ] **6.1.3** Implement connection retry logic in `autoTrade()` function
- [ ] **6.1.4** Add health monitoring to connection establishment in `find_tradovate_tab()`
- [ ] **6.1.5** Update error handling to trigger connection recovery
- [ ] **6.1.6** Create health status reporting for dashboard integration

#### 6.2 Auto-Login Integration
- [ ] **6.2.1** Add connection monitoring to login process verification
- [ ] **6.2.2** Implement connection pool initialization during startup
- [ ] **6.2.3** Create backup connection establishment during login
- [ ] **6.2.4** Add login success verification through connection health
- [ ] **6.2.5** Update login monitoring to include connection health status
- [ ] **6.2.6** Create login failure recovery through connection monitoring

#### 6.3 Dashboard and Monitoring Integration
- [ ] **6.3.1** Add connection health metrics to dashboard displays
- [ ] **6.3.2** Create real-time connection status indicators
- [ ] **6.3.3** Add connection health alerts and notifications
- [ ] **6.3.4** Create connection health historical charts and analysis
- [ ] **6.3.5** Add manual connection recovery triggers in dashboard
- [ ] **6.3.6** Create connection health API endpoints for external monitoring

---

## IMPLEMENTATION PRIORITY ORDER

### Week 1: Critical Process Monitoring
1. Complete Task 1, Phases 1-2 (Process monitoring and crash detection)
2. Complete Task 2, Phases 1-2 (Connection monitoring and health checks)

### Week 2: Recovery Implementation  
3. Complete Task 1, Phases 3-4 (State preservation and restart procedures)
4. Complete Task 2, Phases 3-4 (Failure detection and recovery)

### Week 3: Advanced Features
5. Complete Task 1, Phases 5-6 (State restoration and integration)
6. Complete Task 2, Phases 5-6 (Connection pooling and integration)

### Week 4: Testing and Validation
7. End-to-end testing of all watchdog and health monitoring features
8. Load testing and failure simulation
9. Documentation and operational procedures

## SUCCESS METRICS

- **Chrome Uptime**: >99.9% process availability
- **Connection Recovery**: <30 seconds average recovery time
- **Trading Continuity**: Zero missed trades due to connection issues  
- **False Positive Rate**: <1% for crash detection
- **Recovery Success Rate**: >95% automated recovery success

## CONFIGURATION FILES NEEDED

- `config/process_monitor.json` - Watchdog configuration
- `config/connection_monitor.json` - Health monitoring settings
- `recovery/` - Directory for state preservation files
- `logs/stability/` - Dedicated logging for stability features

## TESTING REQUIREMENTS

- Simulate Chrome process crashes during active trading
- Test network disconnection and reconnection scenarios
- Validate state preservation across restart cycles
- Test failover under various failure conditions
- Load test with multiple simultaneous account failures