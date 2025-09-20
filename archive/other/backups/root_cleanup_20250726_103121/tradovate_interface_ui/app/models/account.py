class Account:
    """
    Represents a trading account with related information.
    """
    # Class-level storage for accounts to persist between requests
    _accounts = []
    _initialized = False
    
    def __init__(self, name, id, strategy="", symbol="NQM5", phase=1, platform="Tradovate", active=True, account_type="Futures"):
        self.name = name
        self.id = id
        self.strategy = strategy
        self.symbol = symbol
        self.phase = phase
        self.platform = platform
        self.active = active
        self.account_type = account_type
    
    @classmethod
    def get_accounts(cls):
        """
        Returns a list of all available accounts.
        """
        # Initialize accounts only once
        if not cls._initialized:
            cls._accounts = [
                # Execute platform accounts (Tradovate)
                cls('DEMO3655059', 20653801, 'multiple', 'NQM5', 1, 'Tradovate', True, 'Futures'),
                cls('DEMO3655059-1', 20658313, '', 'NQM5', 1, 'Tradovate', True, 'Futures'),
                cls('DEMO3655059-2', 20658317, '', 'NQM5', 1, 'Tradovate', True, 'Futures'),
                
                # Elite Trader Funding accounts
                cls('ETF-100K-01', 30001, 'nq', 'NQM5', 1, 'Elite Trader Funding', True, 'Futures'),
                cls('ETF-150K-01', 30002, 'es', 'ESM5', 2, 'Elite Trader Funding', True, 'Futures'),
                
                # MyFundedFutures accounts
                cls('MFF-200K-01', 40001, 'multi', 'NQM5', 2, 'MyFundedFutures', True, 'Futures'),
                cls('MFF-100K-01', 40002, 'rty', 'RTYM5', 1, 'MyFundedFutures', True, 'Futures'),
                
                # TradeDay accounts
                cls('TD-50K-01', 50001, 'nq', 'NQM5', 1, 'TradeDay', True, 'Futures'),
                cls('TD-100K-01', 50002, 'es', 'ESM5', 2, 'TradeDay', True, 'Futures'),
                
                # The Trading Pit accounts
                cls('TTP-25K-01', 60001, 'multi', 'NQM5', 1, 'The Trading Pit', True, 'Futures'),
                cls('TTP-150K-01', 60002, 'cl', 'CLM5', 3, 'The Trading Pit', True, 'Futures'),
                
                # Funded Elite accounts
                cls('FE-75K-01', 70001, 'nq', 'NQM5', 1, 'Funded Elite', True, 'Futures'),
                cls('FE-150K-01', 70002, 'gc', 'GCM5', 2, 'Funded Elite', True, 'Futures'),
                
                # Topstep accounts
                cls('TS-50K-01', 80001, 'es', 'ESM5', 1, 'Topstep', True, 'Futures'),
                cls('TS-100K-01', 80002, 'nq', 'NQM5', 2, 'Topstep', True, 'Futures'),
                
                # Apex Trader Funding accounts
                cls('ATF-25K-01', 90001, 'rty', 'RTYM5', 1, 'Apex Trader Funding', True, 'Futures'),
                cls('ATF-100K-01', 90002, 'nq', 'NQM5', 3, 'Apex Trader Funding', True, 'Futures')
            ]
            cls._initialized = True
            
        return cls._accounts
    
    @classmethod
    def get_platforms(cls):
        """
        Returns a list of all available platforms.
        """
        # Get unique platforms from all accounts
        platforms = set()
        for account in cls.get_accounts():
            platforms.add(account.platform)
        return sorted(list(platforms))
    
    @classmethod
    def get_account_types(cls):
        """
        Returns a list of all available account types.
        """
        # Get unique account types from all accounts
        types = set()
        for account in cls.get_accounts():
            types.add(account.account_type)
        return sorted(list(types))
    
    @classmethod
    def get_account_by_strategy(cls, strategy_text):
        """
        Find an account by its strategy text.
        
        Args:
            strategy_text (str): The strategy text to match
            
        Returns:
            Account or None: The matching account or None if not found
        """
        for account in cls.get_accounts():
            if account.strategy == strategy_text:
                return account
        return None
        
    @classmethod
    def get_phase_size(cls, phase, default_size=10):
        """
        Get the lot size for a specific phase.
        
        Args:
            phase (int): The phase number (1, 2, or 3)
            default_size (int): Default size to return if phase is invalid
            
        Returns:
            int: The lot size for the specified phase
        """
        # Phase sizes should be determined by the UI inputs
        # This is a fallback in case they aren't provided
        if phase == 1:
            return default_size  # Default size for Phase 1
        elif phase == 2:
            return default_size * 2  # Default size for Phase 2
        elif phase == 3:
            return default_size * 3  # Default size for Phase 3
        else:
            return default_size  # Default fallback
