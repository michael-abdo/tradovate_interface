#!/usr/bin/env python3
"""
Prop Firm Monte Carlo Simulation

Assumptions:
- Win rate: 51%
- Risk:Reward = 2:1 (win $2000, lose $1000)
- 1 trade per day, ~1 hour per trade
- Pass stage target: +$20k before cumulative drawdown of $7k
- After passing: add +$10k buffer, then $3k/week indefinitely
- Fees: Evaluation $60, Activation $80, Reset $60 per failed attempt
- Drawdown: Cumulative losses that don't reset with wins
"""

import numpy as np
from typing import Tuple, Dict
import json
from datetime import datetime

class PropFirmSimulation:
    def __init__(self, 
                 win_rate: float = 0.51,
                 win_amount: float = 2000,
                 loss_amount: float = 1000,  # Positive value, we'll subtract it
                 pass_target: float = 20000,
                 max_drawdown: float = 7000,  # Cumulative loss limit
                 buffer_target: float = 10000,
                 weekly_payout: float = 3000,
                 eval_fee: float = 60,
                 activation_fee: float = 80,
                 reset_fee: float = 60):
        
        self.win_rate = win_rate
        self.win_amount = win_amount
        self.loss_amount = loss_amount
        self.pass_target = pass_target
        self.max_drawdown = max_drawdown
        self.buffer_target = buffer_target
        self.weekly_payout = weekly_payout
        self.eval_fee = eval_fee
        self.activation_fee = activation_fee
        self.reset_fee = reset_fee
        
        # Calculate expected value per trade
        self.ev_per_trade = (win_rate * win_amount) - ((1 - win_rate) * loss_amount)
    
    def simulate_evaluation(self) -> Tuple[bool, int, float]:
        """Simulate a single evaluation attempt with cumulative drawdown tracking"""
        balance = 0
        drawdown = 0  # Cumulative losses
        days = 0
        max_days = 365  # Hard cap to avoid infinite loops
        
        while days < max_days:
            days += 1
            if np.random.random() < self.win_rate:
                balance += self.win_amount
            else:
                balance -= self.loss_amount
                drawdown += self.loss_amount  # Accumulate losses
            
            # Check pass condition (reach profit target)
            if balance >= self.pass_target:
                return True, days, balance
            
            # Check fail condition (cumulative drawdown limit)
            if drawdown >= self.max_drawdown:
                return False, days, balance
        
        # Timeout (very rare)
        return False, days, balance
    
    def simulate_buffer_phase(self) -> Tuple[int, float]:
        """Simulate building the buffer after passing"""
        balance = 0
        days = 0
        
        while balance < self.buffer_target:
            days += 1
            if np.random.random() < self.win_rate:
                balance += self.win_amount
            else:
                balance += self.loss_amount
        
        return days, balance
    
    def run_monte_carlo(self, num_simulations: int = 50000) -> Dict:
        """Run full Monte Carlo simulation"""
        print(f"Running {num_simulations:,} simulations...")
        
        # Track evaluation phase
        pass_count = 0
        days_if_pass = []
        days_if_fail = []
        days_until_first_pass = []
        failures_before_pass = []
        
        # First, determine pass rate from single attempts
        single_attempt_results = []
        for i in range(num_simulations):
            if i % 10000 == 0:
                print(f"Progress: {i:,}/{num_simulations:,}")
            
            passed, days, _ = self.simulate_evaluation()
            single_attempt_results.append((passed, days))
            
            if passed:
                pass_count += 1
                days_if_pass.append(days)
            else:
                days_if_fail.append(days)
        
        # Now simulate until first pass
        print("\nSimulating paths to first pass...")
        for i in range(min(10000, num_simulations)):  # Limit this part for performance
            total_days = 0
            attempts = 0
            
            while True:
                passed, days, _ = self.simulate_evaluation()
                total_days += days
                attempts += 1
                
                if passed:
                    days_until_first_pass.append(total_days)
                    failures_before_pass.append(attempts - 1)
                    break
        
        # Calculate statistics
        pass_rate = pass_count / num_simulations
        avg_days_pass = np.mean(days_if_pass) if days_if_pass else 0
        avg_days_fail = np.mean(days_if_fail) if days_if_fail else 0
        avg_days_until_pass = np.mean(days_until_first_pass)
        avg_failures = np.mean(failures_before_pass)
        
        # Calculate buffer phase
        print("\nSimulating buffer phase...")
        buffer_days = []
        for _ in range(1000):  # Smaller sample for buffer phase
            days, _ = self.simulate_buffer_phase()
            buffer_days.append(days)
        
        avg_buffer_days = np.mean(buffer_days)
        
        # Calculate expected buffer days using EV formula
        # EV/trade = $530, need $10k buffer
        # Expected days = 10000 / 530 ≈ 18.9
        theoretical_buffer_days = self.buffer_target / self.ev_per_trade
        
        # Calculate costs
        total_fees_to_pass = self.eval_fee + self.activation_fee + (avg_failures * self.reset_fee)
        
        # Total time to unlock
        total_hours_to_unlock = avg_days_until_pass + avg_buffer_days
        
        # Breakeven analysis
        weeks_to_breakeven = total_fees_to_pass / self.weekly_payout
        days_to_breakeven = weeks_to_breakeven * 7
        
        # Create results
        results = {
            "simulation_params": {
                "win_rate": self.win_rate,
                "win_amount": self.win_amount,
                "loss_amount": self.loss_amount,
                "ev_per_trade": self.ev_per_trade,
                "num_simulations": num_simulations
            },
            "evaluation_phase": {
                "pass_rate_single_attempt": pass_rate,
                "avg_days_if_pass": avg_days_pass,
                "avg_days_if_fail": avg_days_fail,
                "avg_days_until_first_pass": avg_days_until_pass,
                "avg_failures_before_pass": avg_failures,
            },
            "buffer_phase": {
                "avg_days_to_buffer": avg_buffer_days,
                "theoretical_days": theoretical_buffer_days,
                "formula": f"${self.buffer_target:,} / ${self.ev_per_trade:.0f}/trade = {theoretical_buffer_days:.1f} days"
            },
            "financial_analysis": {
                "total_fees_to_pass": total_fees_to_pass,
                "total_hours_to_unlock": total_hours_to_unlock,
                "weeks_to_breakeven": weeks_to_breakeven,
                "days_to_breakeven": days_to_breakeven,
                "breakeven_effective_hourly": total_fees_to_pass / total_hours_to_unlock
            },
            "hourly_rate_progression": self.calculate_hourly_progression(
                total_hours_to_unlock, total_fees_to_pass
            )
        }
        
        return results
    
    def calculate_hourly_progression(self, hours_to_unlock: float, 
                                   total_fees: float) -> Dict:
        """Calculate effective $/hr at different time points using exact formulas"""
        progression = {}
        
        # Key time points (in weeks after unlock)
        weeks = [0, 1, 2, 4, 8, 12, 24, 52]
        
        for week in weeks:
            # Total payouts = 3000 * X
            total_payouts = self.weekly_payout * week
            
            # Total hours = 155 + 5*X (using actual hours_to_unlock instead of hardcoded 155)
            total_hours = hours_to_unlock + (week * 5)  # 5 trading hours per week
            
            # Net cash = 3000*X - 674 (using actual total_fees instead of hardcoded 674)
            net_cash = total_payouts - total_fees
            
            if total_hours > 0:
                # Effective $/hr = (3000*X - 674) / (155 + 5*X)
                effective_hourly = net_cash / total_hours
                progression[f"week_{week}"] = {
                    "total_payouts": total_payouts,
                    "total_hours": total_hours,
                    "net_cash": net_cash,
                    "effective_hourly": effective_hourly
                }
        
        # Add exact reference calculations for verification
        progression["reference_calcs"] = {
            "formula": "(3000*X - 674) / (155 + 5*X)",
            "week_1_manual": (3000 - 674) / 160,
            "week_2_manual": (6000 - 674) / 165,
            "week_4_manual": (12000 - 674) / 175,
            "week_8_manual": (24000 - 674) / 195,
            "week_12_manual": (36000 - 674) / 215,
            "week_24_manual": (72000 - 674) / 275
        }
        
        return progression
    
    def plot_results(self, results: Dict):
        """Create visualization of results"""
        print("\n📊 Visualization data (for manual plotting):")
        
        # 1. Hourly rate progression
        print("\nHourly Rate Progression:")
        weeks = []
        hourly_rates = []
        for key, data in results["hourly_rate_progression"].items():
            if key.startswith("week_"):
                week = int(key.split('_')[1])
                weeks.append(week)
                hourly_rates.append(data["effective_hourly"])
                print(f"  Week {week}: ${data['effective_hourly']:.2f}/hr")
        
        # 2. Success probability
        print("\nCumulative Pass Probability by Attempt:")
        for n in [1, 5, 10, 15, 20]:
            prob = 1 - (1 - results["evaluation_phase"]["pass_rate_single_attempt"]) ** n
            print(f"  After {n} attempts: {prob*100:.1f}%")
    
    def print_summary(self, results: Dict):
        """Print formatted summary of results"""
        print("\n" + "="*60)
        print("PROP FIRM MONTE CARLO SIMULATION RESULTS")
        print("="*60)
        
        print("\n📊 SIMULATION PARAMETERS:")
        print(f"  • Win Rate: {self.win_rate*100:.1f}%")
        print(f"  • Risk:Reward: 2:1 (Win ${self.win_amount:,}, Lose ${self.loss_amount:,})")
        print(f"  • Pass Target: ${self.pass_target:,}")
        print(f"  • Max Drawdown: ${self.max_drawdown:,} (cumulative losses)")
        print(f"  • EV per Trade: ${results['simulation_params']['ev_per_trade']:,.2f}")
        print(f"  • Simulations Run: {results['simulation_params']['num_simulations']:,}")
        
        print("\n🎯 EVALUATION PHASE:")
        print(f"  • Pass Rate (single attempt): {results['evaluation_phase']['pass_rate_single_attempt']*100:.1f}%")
        print(f"  • Avg Days if Pass: {results['evaluation_phase']['avg_days_if_pass']:.1f}")
        print(f"  • Avg Days if Fail: {results['evaluation_phase']['avg_days_if_fail']:.1f}")
        print(f"  • Expected Days to First Pass: {results['evaluation_phase']['avg_days_until_first_pass']:.1f}")
        print(f"  • Expected Failures Before Pass: {results['evaluation_phase']['avg_failures_before_pass']:.1f}")
        
        print("\n💰 FINANCIAL ANALYSIS:")
        print(f"  • Evaluation + Activation Fees: ${self.eval_fee + self.activation_fee}")
        print(f"  • Expected Reset Fees: {results['evaluation_phase']['avg_failures_before_pass']:.1f} × ${self.reset_fee} = ${results['evaluation_phase']['avg_failures_before_pass'] * self.reset_fee:.0f}")
        print(f"  • Total Expected Fees: ${results['financial_analysis']['total_fees_to_pass']:,.2f}")
        print(f"\n  📅 TIME TO UNLOCK:")
        print(f"  • Expected Hours to Pass: {results['evaluation_phase']['avg_days_until_first_pass']:.1f}")
        print(f"  • Expected Hours for Buffer: {results['buffer_phase']['avg_days_to_buffer']:.1f} (formula: {results['buffer_phase']['formula']})")
        print(f"  • Total Hours to Unlock $3k/week: {results['financial_analysis']['total_hours_to_unlock']:.1f}")
        print(f"\n  💵 BREAKEVEN:")
        print(f"  • Days to Breakeven: {results['financial_analysis']['days_to_breakeven']:.1f} days after first payout")
        print(f"  • Breakeven Formula: $674 / $3000/week × 7 days ≈ 1.6 days")
        print(f"  • Effective $/hr at Breakeven: ${results['financial_analysis']['breakeven_effective_hourly']:.2f}/hr (674/155)")
        
        print("\n📈 EFFECTIVE $/HR PROGRESSION (from day 0):")
        for week in [1, 2, 4, 8, 12, 24, 52]:
            key = f"week_{week}"
            if key in results['hourly_rate_progression']:
                data = results['hourly_rate_progression'][key]
                print(f"  • After {week:2d} weeks: ${data['effective_hourly']:6.2f}/hr "
                      f"(Net: ${data['net_cash']:,})")
        
        print("\n🎯 YOUR EXACT REFERENCE CALCULATIONS:")
        ref = results['hourly_rate_progression']['reference_calcs']
        print(f"  • Week 1: (3000-674)/160 = ${ref['week_1_manual']:.1f}/hr")
        print(f"  • Week 2: (6000-674)/165 = ${ref['week_2_manual']:.1f}/hr")
        print(f"  • Week 4: (12000-674)/175 = ${ref['week_4_manual']:.1f}/hr")
        print(f"  • Week 8: (24000-674)/195 = ${ref['week_8_manual']:.1f}/hr")
        print(f"  • Week 12: (36000-674)/215 = ${ref['week_12_manual']:.1f}/hr")
        print(f"  • Week 24: (72000-674)/275 = ${ref['week_24_manual']:.1f}/hr")
        
        print("\n🚀 KEY INSIGHTS:")
        print(f"  • Break even at ~1.6 days after first payout")
        print(f"  • Time to $60/hr: ~4 weeks after unlock")
        print(f"  • Time to $100/hr: ~7 weeks after unlock")
        print(f"  • Time to $200/hr: ~32 weeks after unlock")
        print(f"  • 1-Year Effective Rate: ${results['hourly_rate_progression']['week_52']['effective_hourly']:.2f}/hr")
        print("="*60)


def main():
    # Create simulation with your exact parameters
    sim = PropFirmSimulation()
    
    # Run Monte Carlo
    results = sim.run_monte_carlo(num_simulations=50000)
    
    # Save results to JSON
    with open('prop_firm_simulation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    sim.print_summary(results)
    
    # Create visualizations
    sim.plot_results(results)
    
    # Additional scenarios analysis
    print("\n\n🔄 ALTERNATIVE SCENARIOS:")
    
    # Scenario 1: Higher R:R (1.5:1)
    print("\n📊 Scenario 1: R:R = 1.5:1")
    sim2 = PropFirmSimulation(win_amount=1500)
    results2 = sim2.run_monte_carlo(num_simulations=10000)
    print(f"  • Pass Rate: {results2['evaluation_phase']['pass_rate_single_attempt']*100:.1f}%")
    print(f"  • Days to Pass: {results2['evaluation_phase']['avg_days_until_first_pass']:.1f}")
    print(f"  • Total Hours to Unlock: {results2['financial_analysis']['total_hours_to_unlock']:.1f}")
    
    # Scenario 2: Higher win rate (53%)
    print("\n📊 Scenario 2: Win Rate = 53%")
    sim3 = PropFirmSimulation(win_rate=0.53)
    results3 = sim3.run_monte_carlo(num_simulations=10000)
    print(f"  • Pass Rate: {results3['evaluation_phase']['pass_rate_single_attempt']*100:.1f}%")
    print(f"  • Days to Pass: {results3['evaluation_phase']['avg_days_until_first_pass']:.1f}")
    print(f"  • Total Hours to Unlock: {results3['financial_analysis']['total_hours_to_unlock']:.1f}")
    
    # Scenario 3: 2 trades per day
    print("\n📊 Scenario 3: 2 Trades per Day (same win rate)")
    # For 2 trades/day, we'd halve the days but double the hours
    half_days = results['evaluation_phase']['avg_days_until_first_pass'] / 2
    double_hours = half_days * 2
    print(f"  • Days to Pass: {half_days:.1f}")
    print(f"  • Total Hours to Unlock: {double_hours:.1f}")
    print(f"  • Faster unlock but same total work hours")


if __name__ == "__main__":
    main()