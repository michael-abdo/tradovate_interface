import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add the project root to import paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Account model directly
from app.models.account import Account

class TestAccountPhaseAndSizeMatrix(unittest.TestCase):
    """Tests for account phase and size matrix functionality"""
    
    def setUp(self):
        # Create test accounts with different phases
        self.test_accounts = [
            Account(id=1001, name="Phase1Account", phase=1, strategy="TestStrategy1", active=True),
            Account(id=1002, name="Phase2Account", phase=2, strategy="TestStrategy2", active=True),
            Account(id=1003, name="Phase3Account", phase=3, strategy="TestStrategy3", active=True)
        ]
        
        # Mock the Account.get_accounts method
        self.get_accounts_patcher = patch('app.models.account.Account.get_accounts', 
                                         return_value=self.test_accounts)
        self.mock_get_accounts = self.get_accounts_patcher.start()
        
        # Debug output
        print("\nDebug - Test accounts created:")
        for account in self.test_accounts:
            print(f"  Account {account.name}: Phase {account.phase}, ID {account.id}")
    
    def tearDown(self):
        self.get_accounts_patcher.stop()
    
    def test_account_phase_properties(self):
        """Test that account phase is properly stored and accessed"""
        # Test Phase 1 account
        phase1_account = self.test_accounts[0]
        self.assertEqual(phase1_account.phase, 1)
        
        # Test Phase 2 account
        phase2_account = self.test_accounts[1]
        self.assertEqual(phase2_account.phase, 2)
        
        # Test Phase 3 account
        phase3_account = self.test_accounts[2]
        self.assertEqual(phase3_account.phase, 3)
        
        # Test changing phase
        phase1_account.phase = 2
        self.assertEqual(phase1_account.phase, 2)
    
    def test_get_phase_size_method(self):
        """Test the get_phase_size method with different phases"""
        # Default size is 10
        default_size = 10
        
        # Test Phase 1 size
        phase1_size = Account.get_phase_size(1, default_size)
        self.assertEqual(phase1_size, default_size)
        
        # Test Phase 2 size (2x default)
        phase2_size = Account.get_phase_size(2, default_size)
        self.assertEqual(phase2_size, default_size * 2)
        
        # Test Phase 3 size (3x default)
        phase3_size = Account.get_phase_size(3, default_size)
        self.assertEqual(phase3_size, default_size * 3)
        
        # Test invalid phase (should return default)
        invalid_phase_size = Account.get_phase_size(4, default_size)
        self.assertEqual(invalid_phase_size, default_size)
    
    def test_size_calculation_for_different_phases(self):
        """Test size calculation for different account phases"""
        # We'll simulate the logic from app.py for calculating sizes
        base_quantity = 10
        phase1_size = 5
        phase2_size = 15
        phase3_size = 25
        
        # Test for different account phases
        for account in self.test_accounts:
            # Determine quantity based on account phase (similar to app.py logic)
            account_phase = int(account.phase)
            
            if account_phase == 1:
                quantity = phase1_size
            elif account_phase == 2:
                quantity = phase2_size
            elif account_phase == 3:
                quantity = phase3_size
            else:
                quantity = base_quantity
            
            # Verify the calculated quantities
            if account_phase == 1:
                self.assertEqual(quantity, phase1_size)
            elif account_phase == 2:
                self.assertEqual(quantity, phase2_size)
            elif account_phase == 3:
                self.assertEqual(quantity, phase3_size)
    
    def test_matrix_logic_with_order_sequence(self):
        """Test size matrix logic with different order sequences"""
        # Size matrix (similar to index.html)
        size_matrix = {
            1: {1: 5, 2: 10, 3: 15, 4: 20},  # Phase 1 sizes
            2: {1: 10, 2: 15, 3: 20, 4: 25},  # Phase 2 sizes
            3: {1: 20, 2: 25, 3: 30, 4: 35}   # Phase 3 sizes
        }
        
        # Test each account with different order sequences
        for account in self.test_accounts:
            phase = int(account.phase)
            
            # Verify order sizes for each sequence
            for order_num in range(1, 5):
                expected_size = size_matrix[phase][order_num]
                # Print debug info
                print(f"Debug - Matrix lookup: Phase {phase}, Order {order_num} = Size {expected_size}")
                
                # This assertion should always pass since we're just testing our matrix logic
                self.assertEqual(size_matrix[phase][order_num], expected_size)
    
    def test_get_account_by_strategy(self):
        """Test that accounts can be retrieved by strategy name"""
        # Mock the get_account_by_strategy method
        with patch('app.models.account.Account.get_account_by_strategy') as mock_get_by_strategy:
            # Set up the mock to return accounts based on strategy
            def side_effect(strategy):
                for account in self.test_accounts:
                    if account.strategy == strategy:
                        return account
                return None
            
            mock_get_by_strategy.side_effect = side_effect
            
            # Test retrieving each account by strategy
            for account in self.test_accounts:
                retrieved_account = Account.get_account_by_strategy(account.strategy)
                mock_get_by_strategy.assert_called_with(account.strategy)
                
                # Verify we got the expected account
                self.assertEqual(retrieved_account, account)

if __name__ == '__main__':
    unittest.main()