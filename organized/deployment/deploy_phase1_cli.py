#!/usr/bin/env python3
"""
CLI deployment runner for Phase 1 - Executes without user prompts
"""

import sys
from deploy_phase1 import Phase1Deployer

def main():
    """Execute Phase 1 deployment directly"""
    print("\n🚀 Starting Phase 1 Deployment (CLI mode)...")
    print("=" * 60)
    
    deployer = Phase1Deployer()
    
    # Run deployment directly without prompts
    success = deployer.deploy()
    
    if success:
        print("\n✅ Phase 1 deployment completed successfully!")
        print("\nNext steps:")
        print("1. Test the enhanced startup: python3 start_all.py")
        print("2. Monitor logs in: logs/startup/")
        print("3. Check deployment report in the current directory")
        sys.exit(0)
    else:
        print("\n❌ Phase 1 deployment failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()