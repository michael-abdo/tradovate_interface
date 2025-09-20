import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import websocket
import threading
import queue
from dataclasses import dataclass, asdict
import logging

@dataclass
class OptionsContract:
    symbol: str
    strike: float
    expiration: str
    option_type: str  # 'call' or 'put'
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    delta: float
    gamma: float
    theta: float
    vega: float
    implied_volatility: float
    timestamp: datetime

@dataclass
class OptionsChain:
    underlying_symbol: str
    underlying_price: float
    expiration_date: str
    calls: List[OptionsContract]
    puts: List[OptionsContract]
    timestamp: datetime

class RealTimeOptionsDataFeed:
    """
    EXPERIMENTAL FRAMEWORK: Real-time options chain data ingestion
    with <100ms latency requirements for expiration pressure detection
    """
    
    def __init__(self, symbols: List[str], latency_tracker=None):
        self.symbols = symbols
        self.latency_tracker = latency_tracker or LatencyTracker()
        self.data_queue = queue.Queue(maxsize=1000)
        self.subscribers = []
        self.connection_status = "disconnected"
        self.last_update_time = None
        self.performance_metrics = {
            'messages_received': 0,
            'processing_times': [],
            'data_gaps': 0,
            'reconnections': 0
        }
        
        # Data validation and quality tracking
        self.data_validator = OptionsDataValidator()
        self.quality_tracker = DataQualityTracker()
        
    def connect(self, api_key: str, feed_url: str) -> bool:
        """
        PERFORMANCE REQUIREMENT: Establish connection with <100ms initial latency
        """
        try:
            connection_start = time.time()
            
            # Primary connection setup
            self.ws = websocket.WebSocketApp(
                feed_url,
                header={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Start connection in separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Wait for connection with timeout
            timeout = 5.0  # seconds
            start_wait = time.time()
            while self.connection_status != "connected" and (time.time() - start_wait) < timeout:
                time.sleep(0.01)
            
            connection_time = time.time() - connection_start
            self.latency_tracker.record_connection_latency(connection_time)
            
            if self.connection_status == "connected":
                self._subscribe_to_symbols()
                logging.info(f"Connected to options feed in {connection_time:.3f}s")
                return True
            else:
                logging.error(f"Failed to connect within {timeout}s timeout")
                return False
                
        except Exception as e:
            logging.error(f"Connection failed: {e}")
            return False
    
    def _subscribe_to_symbols(self):
        """
        Subscribe to real-time options chain updates for target symbols
        """
        for symbol in self.symbols:
            subscription_message = {
                'action': 'subscribe',
                'type': 'options_chain',
                'symbol': symbol,
                'fields': [
                    'bid', 'ask', 'last', 'volume', 'open_interest',
                    'delta', 'gamma', 'theta', 'vega', 'implied_volatility'
                ]
            }
            self.ws.send(json.dumps(subscription_message))
            logging.info(f"Subscribed to options chain for {symbol}")
    
    def _on_message(self, ws, message):
        """
        CRITICAL PERFORMANCE PATH: Process incoming data with <100ms latency
        """
        receive_timestamp = time.time()
        
        try:
            # Parse message
            data = json.loads(message)
            
            # Validate message structure
            if not self.data_validator.validate_message(data):
                self.quality_tracker.record_invalid_message(data)
                return
            
            # Extract timestamp from message
            message_timestamp = data.get('timestamp')
            if message_timestamp:
                # Calculate network latency
                network_latency = receive_timestamp - (message_timestamp / 1000)
                self.latency_tracker.record_network_latency(network_latency)
            
            # Process options chain data
            if data.get('type') == 'options_chain':
                options_chain = self._parse_options_chain(data, receive_timestamp)
                
                if options_chain:
                    # Quality validation
                    quality_score = self.quality_tracker.assess_data_quality(options_chain)
                    
                    if quality_score > 0.95:  # High quality threshold
                        # Add to processing queue
                        self.data_queue.put(options_chain, block=False)
                        
                        # Notify subscribers
                        for callback in self.subscribers:
                            try:
                                callback(options_chain)
                            except Exception as e:
                                logging.error(f"Subscriber callback failed: {e}")
                    
                    # Track processing performance
                    processing_time = time.time() - receive_timestamp
                    self.performance_metrics['processing_times'].append(processing_time)
                    self.performance_metrics['messages_received'] += 1
                    
                    # Alert if processing too slow
                    if processing_time > 0.05:  # 50ms threshold
                        logging.warning(f"Slow processing: {processing_time:.3f}s")
            
            self.last_update_time = datetime.now()
            
        except json.JSONDecodeError:
            logging.error("Invalid JSON in message")
            self.quality_tracker.record_parsing_error(message)
        except queue.Full:
            logging.warning("Data queue full - dropping message")
            self.performance_metrics['data_gaps'] += 1
        except Exception as e:
            logging.error(f"Message processing error: {e}")
    
    def _parse_options_chain(self, data: Dict, timestamp: float) -> Optional[OptionsChain]:
        """
        Parse raw options chain data into structured format
        """
        try:
            symbol = data['symbol']
            underlying_price = data.get('underlying_price', 0.0)
            expiration = data.get('expiration')
            
            calls = []
            puts = []
            
            for contract_data in data.get('contracts', []):
                contract = OptionsContract(
                    symbol=contract_data['symbol'],
                    strike=contract_data['strike'],
                    expiration=contract_data['expiration'],
                    option_type=contract_data['type'],
                    bid=contract_data.get('bid', 0.0),
                    ask=contract_data.get('ask', 0.0),
                    last=contract_data.get('last', 0.0),
                    volume=contract_data.get('volume', 0),
                    open_interest=contract_data.get('open_interest', 0),
                    delta=contract_data.get('delta', 0.0),
                    gamma=contract_data.get('gamma', 0.0),
                    theta=contract_data.get('theta', 0.0),
                    vega=contract_data.get('vega', 0.0),
                    implied_volatility=contract_data.get('implied_volatility', 0.0),
                    timestamp=datetime.fromtimestamp(timestamp)
                )
                
                if contract.option_type == 'call':
                    calls.append(contract)
                else:
                    puts.append(contract)
            
            return OptionsChain(
                underlying_symbol=symbol,
                underlying_price=underlying_price,
                expiration_date=expiration,
                calls=calls,
                puts=puts,
                timestamp=datetime.fromtimestamp(timestamp)
            )
            
        except KeyError as e:
            logging.error(f"Missing required field in options data: {e}")
            return None
        except Exception as e:
            logging.error(f"Error parsing options chain: {e}")
            return None
    
    def _on_error(self, ws, error):
        logging.error(f"WebSocket error: {error}")
        self.connection_status = "error"
        
    def _on_close(self, ws, close_status_code, close_msg):
        logging.warning(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.connection_status = "disconnected"
        
    def _on_open(self, ws):
        logging.info("WebSocket connection opened")
        self.connection_status = "connected"
    
    def subscribe(self, callback: Callable[[OptionsChain], None]):
        """
        Register callback for real-time options chain updates
        """
        self.subscribers.append(callback)
    
    def get_latest_data(self) -> Optional[OptionsChain]:
        """
        Get most recent options chain data (non-blocking)
        """
        try:
            return self.data_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_performance_metrics(self) -> Dict:
        """
        Return performance and quality metrics
        """
        if self.performance_metrics['processing_times']:
            avg_processing_time = sum(self.performance_metrics['processing_times']) / len(self.performance_metrics['processing_times'])
            max_processing_time = max(self.performance_metrics['processing_times'])
        else:
            avg_processing_time = 0
            max_processing_time = 0
            
        return {
            'connection_status': self.connection_status,
            'messages_received': self.performance_metrics['messages_received'],
            'average_processing_time': avg_processing_time,
            'max_processing_time': max_processing_time,
            'data_gaps': self.performance_metrics['data_gaps'],
            'reconnections': self.performance_metrics['reconnections'],
            'last_update': self.last_update_time,
            'latency_metrics': self.latency_tracker.get_metrics(),
            'data_quality_score': self.quality_tracker.get_overall_quality_score()
        }
    
    def disconnect(self):
        """
        Clean disconnect from data feed
        """
        self.connection_status = "disconnecting"
        if hasattr(self, 'ws'):
            self.ws.close()
        logging.info("Disconnected from options data feed")

class LatencyTracker:
    """
    Track and measure data feed latency performance
    """
    
    def __init__(self):
        self.network_latencies = []
        self.processing_latencies = []
        self.connection_latencies = []
        
    def record_network_latency(self, latency: float):
        self.network_latencies.append(latency)
        # Keep only recent 1000 measurements
        if len(self.network_latencies) > 1000:
            self.network_latencies.pop(0)
            
    def record_processing_latency(self, latency: float):
        self.processing_latencies.append(latency)
        if len(self.processing_latencies) > 1000:
            self.processing_latencies.pop(0)
            
    def record_connection_latency(self, latency: float):
        self.connection_latencies.append(latency)
        
    def get_metrics(self) -> Dict:
        def calculate_stats(latencies):
            if not latencies:
                return {'avg': 0, 'max': 0, 'min': 0, 'p95': 0}
            
            sorted_latencies = sorted(latencies)
            return {
                'avg': sum(latencies) / len(latencies),
                'max': max(latencies),
                'min': min(latencies),
                'p95': sorted_latencies[int(len(sorted_latencies) * 0.95)] if len(sorted_latencies) > 0 else 0
            }
        
        return {
            'network_latency': calculate_stats(self.network_latencies),
            'processing_latency': calculate_stats(self.processing_latencies),
            'connection_latency': calculate_stats(self.connection_latencies)
        }

class OptionsDataValidator:
    """
    Validate incoming options data for completeness and accuracy
    """
    
    def validate_message(self, data: Dict) -> bool:
        """
        Validate message structure and required fields
        """
        required_fields = ['symbol', 'type', 'timestamp']
        
        for field in required_fields:
            if field not in data:
                return False
                
        if data['type'] == 'options_chain':
            return self._validate_options_chain(data)
            
        return True
    
    def _validate_options_chain(self, data: Dict) -> bool:
        """
        Validate options chain specific data
        """
        required_chain_fields = ['symbol', 'underlying_price', 'contracts']
        
        for field in required_chain_fields:
            if field not in data:
                return False
                
        # Validate contracts
        contracts = data.get('contracts', [])
        if not contracts:
            return False
            
        for contract in contracts:
            if not self._validate_contract(contract):
                return False
                
        return True
    
    def _validate_contract(self, contract: Dict) -> bool:
        """
        Validate individual options contract data
        """
        required_contract_fields = ['symbol', 'strike', 'expiration', 'type']
        
        for field in required_contract_fields:
            if field not in contract:
                return False
                
        # Validate numeric fields
        numeric_fields = ['strike', 'bid', 'ask', 'last', 'delta', 'gamma']
        for field in numeric_fields:
            if field in contract:
                try:
                    float(contract[field])
                except (ValueError, TypeError):
                    return False
                    
        return True

class DataQualityTracker:
    """
    Track data quality metrics for performance monitoring
    """
    
    def __init__(self):
        self.total_messages = 0
        self.invalid_messages = 0
        self.parsing_errors = 0
        self.quality_scores = []
        
    def record_invalid_message(self, data: Dict):
        self.invalid_messages += 1
        
    def record_parsing_error(self, message: str):
        self.parsing_errors += 1
        
    def assess_data_quality(self, options_chain: OptionsChain) -> float:
        """
        Assess quality of options chain data (0.0 to 1.0)
        """
        score = 1.0
        total_contracts = len(options_chain.calls + options_chain.puts)
        
        if total_contracts == 0:
            score = 0.0
        else:
            # Check for missing prices
            for contract in options_chain.calls + options_chain.puts:
                if contract.bid <= 0 or contract.ask <= 0:
                    score -= 0.2  # More severe penalty for missing prices
                if contract.delta == 0 and contract.option_type == 'call':
                    score -= 0.15  # Penalty for missing greeks
                    
            # Check for reasonable bid-ask spreads
            for contract in options_chain.calls + options_chain.puts:
                if contract.bid > 0 and contract.ask > 0:
                    spread_ratio = (contract.ask - contract.bid) / contract.bid
                    if spread_ratio > 0.5:  # 50% spread is suspicious
                        score -= 0.1
                        
        score = max(0.0, score)
        self.quality_scores.append(score)
        self.total_messages += 1
        
        return score
    
    def get_overall_quality_score(self) -> float:
        """
        Return overall data quality score
        """
        if not self.quality_scores:
            return 0.0
            
        return sum(self.quality_scores) / len(self.quality_scores)

# Example usage and testing
if __name__ == "__main__":
    # Initialize feed for NQ options
    symbols = ['NQ']
    feed = RealTimeOptionsDataFeed(symbols)
    
    # Example callback for processing updates
    def handle_options_update(options_chain: OptionsChain):
        print(f"Received options chain for {options_chain.underlying_symbol}")
        print(f"  Underlying price: {options_chain.underlying_price}")
        print(f"  Calls: {len(options_chain.calls)}")
        print(f"  Puts: {len(options_chain.puts)}")
        print(f"  Timestamp: {options_chain.timestamp}")
    
    # Subscribe to updates
    feed.subscribe(handle_options_update)
    
    # Connect (replace with actual API credentials)
    api_key = "your_api_key_here"
    feed_url = "wss://api.tradovate.com/v1/websocket"
    
    if feed.connect(api_key, feed_url):
        print("Connected successfully")
        
        # Monitor performance
        while True:
            time.sleep(10)
            metrics = feed.get_performance_metrics()
            print(f"Performance: {metrics}")
    else:
        print("Failed to connect")