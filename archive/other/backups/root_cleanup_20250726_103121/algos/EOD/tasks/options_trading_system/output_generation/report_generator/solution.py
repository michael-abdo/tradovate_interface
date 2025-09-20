#!/usr/bin/env python3
"""
TASK: report_generator
TYPE: Leaf Task
PURPOSE: Generate human-readable trading reports from analysis results
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add tasks directory to path for common utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from common_utils import PathManager

# Add parent task to path for analysis access
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, parent_dir)
from analysis_engine.integration import run_analysis_engine


class TradingReportGenerator:
    """Generate comprehensive trading reports from analysis engine results"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the report generator
        
        Args:
            config: Configuration for report formatting and content
        """
        self.config = config
        self.report_style = config.get("style", "professional")
        self.include_details = config.get("include_details", True)
        self.include_market_context = config.get("include_market_context", True)
        
    def generate_header(self, analysis_results: Dict[str, Any]) -> str:
        """Generate report header"""
        lines = []
        lines.append("=" * 80)
        lines.append("NQ OPTIONS TRADING SYSTEM - ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Primary Algorithm: {analysis_results.get('primary_algorithm', 'nq_ev_analysis').upper()}")
        lines.append(f"Execution Time: {analysis_results.get('execution_time_seconds', 0):.2f}s")
        lines.append(f"Successful Analyses: {analysis_results.get('summary', {}).get('successful_analyses', 0)}/2")
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def generate_executive_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Generate executive summary section"""
        lines = []
        lines.append("\n📊 EXECUTIVE SUMMARY")
        lines.append("-" * 50)
        
        synthesis = analysis_results.get("synthesis", {})
        trading_recs = synthesis.get("trading_recommendations", [])
        
        if trading_recs:
            primary_rec = trading_recs[0]
            try:
                lines.append(f"🎯 PRIMARY RECOMMENDATION: {primary_rec.get('trade_direction', 'UNKNOWN')}")
                lines.append(f"   Entry: {primary_rec.get('entry_price', 0):,.2f}")
                lines.append(f"   Target: {primary_rec.get('target', 0):,.0f} ({primary_rec.get('expected_value', 0):+.1f} EV)")
                lines.append(f"   Stop: {primary_rec.get('stop', 0):,.0f}")
                lines.append(f"   Position Size: {primary_rec.get('position_size', 'N/A')}")
                lines.append(f"   Confidence: {primary_rec.get('confidence', 'N/A')}")
                lines.append(f"   Probability: {primary_rec.get('probability', 0):.1%}")
            except Exception as e:
                lines.append(f"⚠️  ERROR IN PRIMARY RECOMMENDATION: {str(e)}")
                lines.append(f"   Available fields: {list(primary_rec.keys())}")
        else:
            lines.append("⚠️  NO PRIMARY RECOMMENDATIONS")
            lines.append("   No setups met quality criteria")
        
        # Market context
        market_context = synthesis.get("market_context", {})
        if market_context:
            lines.append(f"\n📈 MARKET CONTEXT:")
            lines.append(f"   NQ Price: ${market_context.get('nq_price', 0):,.2f}")
            lines.append(f"   Quality Setups: {market_context.get('quality_setups', 0)}")
            lines.append(f"   Risk Bias: {market_context.get('risk_bias', 'unknown').title()}")
            lines.append(f"   Battle Zones: {market_context.get('critical_zones', 0)} critical")
        
        return "\n".join(lines)
    
    def generate_nq_ev_section(self, analysis_results: Dict[str, Any]) -> str:
        """Generate detailed NQ EV analysis section"""
        lines = []
        lines.append("\n🧮 NQ OPTIONS EV ANALYSIS (PRIMARY)")
        lines.append("-" * 50)
        
        ev_results = analysis_results.get("individual_results", {}).get("expected_value", {})
        if ev_results.get("status") == "success":
            result = ev_results["result"]
            trading_report = result.get("trading_report", {})
            
            lines.append(f"Underlying Price: ${result['underlying_price']:,.2f}")
            lines.append(f"Strikes Analyzed: {result['strikes_analyzed']}")
            lines.append(f"Total Setups Generated: {result['setups_generated']:,}")
            lines.append(f"Quality Setups Found: {result['quality_setups']:,}")
            lines.append(f"Quality Ratio: {result['metrics']['quality_ratio']:.1%}")
            lines.append(f"Best EV: {result['metrics']['best_ev']:+.1f} points")
            lines.append(f"Average Probability: {result['metrics']['avg_probability']:.1%}")
            
            # Top opportunities
            top_opps = trading_report.get("top_opportunities", [])
            if top_opps:
                lines.append(f"\n🏆 TOP {min(5, len(top_opps))} OPPORTUNITIES:")
                lines.append(f"{'Rank':<5} {'Dir':<6} {'TP':<8} {'SL':<8} {'Prob':<7} {'RR':<6} {'EV':<10}")
                lines.append("-" * 50)
                
                for opp in top_opps[:5]:
                    lines.append(
                        f"{opp['rank']:<5} "
                        f"{opp['direction'][:4].upper():<6} "
                        f"{opp['tp']:<8.0f} "
                        f"{opp['sl']:<8.0f} "
                        f"{opp['probability']:<7.1%} "
                        f"{opp['risk_reward']:<6.1f} "
                        f"{opp['expected_value']:+10.1f}"
                    )
            
            # Execution recommendation
            exec_rec = trading_report.get("execution_recommendation")
            if exec_rec:
                try:
                    lines.append(f"\n💡 EXECUTION RECOMMENDATION:")
                    lines.append(f"   Direction: {exec_rec.get('trade_direction', 'N/A')}")
                    lines.append(f"   Entry: {exec_rec.get('entry_price', 0):,.2f}")
                    lines.append(f"   Target: {exec_rec.get('target', 0):,.0f} ({exec_rec.get('reward_points', 0):+.0f} points)")
                    lines.append(f"   Stop: {exec_rec.get('stop', 0):,.0f} ({exec_rec.get('risk_points', 0):+.0f} points)")
                    lines.append(f"   Expected Value: {exec_rec.get('expected_value', 0):+.1f} points")
                    lines.append(f"   Position Size: {exec_rec.get('position_size', 'N/A')}")
                    lines.append(f"   Win Probability: {exec_rec.get('probability', 0):.1%}")
                except Exception as e:
                    lines.append(f"\n💡 EXECUTION RECOMMENDATION ERROR: {str(e)}")
                    lines.append(f"   Available fields: {list(exec_rec.keys())}")
        else:
            lines.append("❌ NQ EV Analysis Failed")
            lines.append(f"   Error: {ev_results.get('error', 'Unknown')}")
        
        return "\n".join(lines)
    
    def generate_supplementary_analyses(self, analysis_results: Dict[str, Any]) -> str:
        """Generate supplementary analyses section"""
        lines = []
        lines.append("\n📋 SUPPLEMENTARY ANALYSES")
        lines.append("-" * 50)
        
        # Risk Analysis
        risk_results = analysis_results.get("individual_results", {}).get("risk", {})
        if risk_results.get("status") == "success":
            result = risk_results["result"]
            summary = result["summary"]
            
            lines.append(f"🎯 RISK ANALYSIS (Institutional Positioning):")
            lines.append(f"   Market Bias: {summary['bias']}")
            lines.append(f"   Total Call Risk: ${summary['total_call_risk']:,.0f}")
            lines.append(f"   Total Put Risk: ${summary['total_put_risk']:,.0f}")
            lines.append(f"   Risk Ratio: {summary['risk_ratio']:.2f}")
            lines.append(f"   Verdict: {summary['verdict']}")
            
            # Battle zones
            battle_zones = result.get("battle_zones", [])[:3]
            if battle_zones:
                lines.append(f"   Critical Battle Zones:")
                for i, zone in enumerate(battle_zones, 1):
                    lines.append(f"     {i}. {zone['strike']} ({zone['type']}) - "
                               f"${zone['risk_amount']:,.0f} ({zone['urgency']})")
            
            # Key signals
            signals = result.get("signals", [])[:3]
            if signals:
                lines.append(f"   Key Risk Signals:")
                for i, signal in enumerate(signals, 1):
                    lines.append(f"     {i}. {signal}")
        else:
            lines.append("🎯 RISK ANALYSIS: Failed")
        
        return "\n".join(lines)
    
    def generate_execution_priorities(self, analysis_results: Dict[str, Any]) -> str:
        """Generate execution priorities section"""
        lines = []
        lines.append("\n⚡ EXECUTION PRIORITIES")
        lines.append("-" * 50)
        
        priorities = analysis_results.get("synthesis", {}).get("execution_priorities", [])
        
        if priorities:
            for i, priority in enumerate(priorities[:5], 1):
                rec = priority.get("recommendation", {})
                try:
                    lines.append(f"{i}. {priority.get('priority', 'N/A')} - {rec.get('trade_direction', 'N/A')}")
                    lines.append(f"   Entry: {rec.get('entry_price', 0):,.2f} → Target: {rec.get('target', 0):,.0f}")
                    lines.append(f"   EV: {rec.get('expected_value', 0):+.1f} | {priority.get('reasoning', 'N/A')}")
                    if i < len(priorities):
                        lines.append("")
                except Exception as e:
                    lines.append(f"{i}. ERROR: {str(e)}")
                    lines.append(f"   Available fields: {list(rec.keys())}")
                    lines.append("")
        else:
            lines.append("No execution priorities available")
        
        return "\n".join(lines)
    
    def generate_footer(self, analysis_results: Dict[str, Any]) -> str:
        """Generate report footer"""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("RISK DISCLAIMER")
        lines.append("-" * 50)
        lines.append("• This analysis is for informational purposes only")
        lines.append("• Past performance does not guarantee future results")
        lines.append("• Trading involves substantial risk of loss")
        lines.append("• Only trade with risk capital you can afford to lose")
        lines.append("• Consider your risk tolerance and trading experience")
        lines.append("=" * 80)
        lines.append(f"Report generated by NQ Options Trading System v1.0")
        lines.append(f"Timestamp: {analysis_results.get('timestamp', get_utc_timestamp())}")
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def generate_report(self, data_config: Dict[str, Any], analysis_config: Dict[str, Any] = None) -> str:
        """Generate complete trading report"""
        
        # Check for cached analysis results first
        if "_cached_analysis_results" in data_config:
            analysis_results = data_config["_cached_analysis_results"]
        else:
            # Run analysis engine to get results
            analysis_results = run_analysis_engine(data_config, analysis_config)
        
        # Generate report sections
        sections = []
        sections.append(self.generate_header(analysis_results))
        sections.append(self.generate_executive_summary(analysis_results))
        sections.append(self.generate_nq_ev_section(analysis_results))
        
        if self.include_market_context:
            sections.append(self.generate_supplementary_analyses(analysis_results))
        
        sections.append(self.generate_execution_priorities(analysis_results))
        sections.append(self.generate_footer(analysis_results))
        
        # Combine all sections
        full_report = "\n".join(sections)
        
        return {
            "report_text": full_report,
            "analysis_results": analysis_results,
            "metadata": {
                "generated_at": get_utc_timestamp(),
                "report_style": self.report_style,
                "sections_included": len(sections),
                "total_length": len(full_report)
            }
        }


# Module-level function for easy integration
def generate_trading_report(data_config: Dict[str, Any], 
                          report_config: Dict[str, Any] = None,
                          analysis_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate comprehensive trading report
    
    Args:
        data_config: Configuration for data sources
        report_config: Configuration for report formatting (optional)
        analysis_config: Configuration for analysis engine (optional)
        
    Returns:
        Dict with report text and metadata
    """
    if report_config is None:
        report_config = {
            "style": "professional",
            "include_details": True,
            "include_market_context": True
        }
    
    generator = TradingReportGenerator(report_config)
    return generator.generate_report(data_config, analysis_config)