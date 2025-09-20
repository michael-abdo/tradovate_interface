#!/usr/bin/env python3
"""
Post-test cleanup and rollback decision maker
Analyzes test results and provides deployment recommendations
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from structured_logger import get_logger
from chrome_cleanup import ChromeCleanup
from backup_manager import BackupManager


class PostTestDecision:
    """Handles post-test cleanup and deployment decisions"""
    
    def __init__(self, test_id: str):
        self.logger = get_logger("post_test", log_file="test/post_test_decision.log")
        self.test_id = test_id
        self.test_report_path = f"logs/test/startup_test_report_{test_id}.json"
        self.decision = {
            'rollback_needed': False,
            'reason': '',
            'recommendations': [],
            'cleanup_performed': []
        }
    
    def load_test_report(self) -> dict:
        """Load the test report"""
        try:
            with open(self.test_report_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error("Test report not found", path=self.test_report_path)
            return None
        except Exception as e:
            self.logger.error("Error loading test report", error=str(e))
            return None
    
    def analyze_test_results(self, report: dict) -> bool:
        """Analyze test results and determine if rollback is needed"""
        self.logger.info("Analyzing test results", test_id=self.test_id)
        
        # Define rollback criteria
        rollback_criteria = {
            'critical_startup_failure': False,
            'excessive_retries': False,
            'performance_degradation': False,
            'phase1_enhancement_failure': False
        }
        
        # Check if Phase 1 enhancements caused the failure
        if not report['success']:
            # Analyze the failure reason
            metrics = report.get('metrics', {})
            log_summary = report.get('log_summary', {})
            
            # Check if Chrome instances started
            if metrics.get('chrome_instances_started', 0) >= 2:
                self.logger.info("Chrome instances started successfully")
                # If Chrome started, the Phase 1 enhancements worked
                rollback_criteria['phase1_enhancement_failure'] = False
            else:
                self.logger.warning("Chrome instances failed to start")
                rollback_criteria['critical_startup_failure'] = True
            
            # Check retry attempts
            if metrics.get('retry_attempts', 0) >= 3:
                rollback_criteria['excessive_retries'] = True
            
            # Check performance
            if metrics.get('startup_time', 0) > 60:
                rollback_criteria['performance_degradation'] = True
        
        # Make rollback decision
        needs_rollback = any(rollback_criteria.values())
        
        if needs_rollback:
            reasons = [k for k, v in rollback_criteria.items() if v]
            self.decision['rollback_needed'] = True
            self.decision['reason'] = f"Rollback needed due to: {', '.join(reasons)}"
        else:
            self.decision['rollback_needed'] = False
            self.decision['reason'] = "Phase 1 enhancements working correctly"
        
        return needs_rollback
    
    def cleanup_test_artifacts(self):
        """Clean up test-related Chrome processes and files"""
        self.logger.info("Starting post-test cleanup")
        
        cleanup_tasks = []
        
        # 1. Clean up any test Chrome processes
        try:
            cleanup = ChromeCleanup()
            processes = cleanup.find_chrome_processes()
            
            if processes:
                self.logger.info(f"Found {len(processes)} Chrome processes to clean")
                results = cleanup.perform_cleanup(
                    kill_processes=True,
                    clean_profiles=False,
                    clean_locks=True
                )
                cleanup_tasks.append(f"Cleaned {results['processes_killed']} Chrome processes")
        except Exception as e:
            self.logger.error("Error during Chrome cleanup", error=str(e))
        
        # 2. Archive test logs
        try:
            test_archive_dir = f"logs/test_archives/{self.test_id}"
            os.makedirs(test_archive_dir, exist_ok=True)
            
            # Move test-specific logs
            log_files = [
                f"logs/test/startup_test_report_{self.test_id}.json",
                f"test_summary_{self.test_id}.txt",
                f"logs/test/validation_report_{self.test_id}.json"
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    dest = os.path.join(test_archive_dir, os.path.basename(log_file))
                    shutil.move(log_file, dest)
                    cleanup_tasks.append(f"Archived {os.path.basename(log_file)}")
            
        except Exception as e:
            self.logger.error("Error archiving logs", error=str(e))
        
        self.decision['cleanup_performed'] = cleanup_tasks
        return cleanup_tasks
    
    def generate_recommendations(self, report: dict):
        """Generate deployment recommendations"""
        recommendations = []
        
        if self.decision['rollback_needed']:
            recommendations.append("⚠️  ROLLBACK RECOMMENDED - Phase 1 caused critical issues")
            recommendations.append("Run: python3 backup_manager.py rollback backup_20250725_211135")
        else:
            recommendations.append("✅ DEPLOYMENT RECOMMENDED - Phase 1 enhancements working correctly")
            
            # Check for known issues
            if report and not report['success']:
                if "'ChromeStabilityMonitor' object has no attribute" in str(report):
                    recommendations.append("Fix dashboard.py bug before production deployment:")
                    recommendations.append("  Add hasattr check for register_connection method")
            
            recommendations.append("Monitor production deployment closely for first 24 hours")
            recommendations.append("Keep rollback command ready: python3 backup_manager.py rollback backup_20250725_211135")
        
        self.decision['recommendations'] = recommendations
        return recommendations
    
    def make_decision(self):
        """Make the final deployment decision"""
        print("\n" + "="*60)
        print("🎯 POST-TEST ANALYSIS & DECISION")
        print("="*60)
        
        # Load test report
        report = self.load_test_report()
        if not report:
            print("\n❌ Cannot load test report - manual review required")
            return False
        
        # Analyze results
        print("\n📊 Analyzing test results...")
        needs_rollback = self.analyze_test_results(report)
        
        # Perform cleanup
        print("\n🧹 Performing cleanup...")
        cleanup_tasks = self.cleanup_test_artifacts()
        for task in cleanup_tasks:
            print(f"  ✓ {task}")
        
        # Generate recommendations
        print("\n📋 Generating recommendations...")
        recommendations = self.generate_recommendations(report)
        
        # Display decision
        print("\n" + "="*60)
        print("🏁 FINAL DECISION")
        print("="*60)
        
        if needs_rollback:
            print(f"\n❌ ROLLBACK REQUIRED")
            print(f"Reason: {self.decision['reason']}")
        else:
            print(f"\n✅ DEPLOYMENT APPROVED")
            print(f"Reason: {self.decision['reason']}")
        
        print("\n📌 Recommendations:")
        for rec in recommendations:
            print(f"  {rec}")
        
        # Save decision report
        decision_file = f"deployment_decision_{self.test_id}.json"
        with open(decision_file, 'w') as f:
            json.dump({
                'test_id': self.test_id,
                'timestamp': datetime.now().isoformat(),
                'decision': self.decision,
                'test_success': report.get('success', False),
                'test_metrics': report.get('metrics', {})
            }, f, indent=2)
        
        print(f"\n📄 Decision report saved to: {decision_file}")
        
        return not needs_rollback


def main():
    """Run post-test decision maker"""
    # Get test ID from argument or use latest
    if len(sys.argv) > 1:
        test_id = sys.argv[1]
    else:
        # Find latest test report
        test_reports = list(Path("logs/test").glob("startup_test_report_*.json"))
        if test_reports:
            latest = max(test_reports, key=lambda p: p.stat().st_mtime)
            test_id = latest.stem.replace("startup_test_report_", "")
        else:
            print("❌ No test reports found")
            return 1
    
    print(f"Using test ID: {test_id}")
    
    decision_maker = PostTestDecision(test_id)
    deployment_approved = decision_maker.make_decision()
    
    return 0 if deployment_approved else 1


if __name__ == "__main__":
    sys.exit(main())