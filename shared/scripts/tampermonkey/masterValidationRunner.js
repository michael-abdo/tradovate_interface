// ==UserScript==
// @name         Master Validation Runner
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Master coordinator for all DOM validation system tests
// @match        https://trader.tradovate.com/*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('🎯 Master Validation Runner - Coordinating comprehensive validation tests');
    
    // ============================================================================
    // MASTER VALIDATION COORDINATOR
    // ============================================================================
    
    class MasterValidationRunner {
        constructor() {
            this.testSuites = new Map();
            this.overallResults = {
                startTime: Date.now(),
                endTime: null,
                totalDuration: 0,
                suiteResults: new Map(),
                overallScore: 0,
                criticalIssues: [],
                recommendations: []
            };
            this.isRunning = false;
        }
        
        async loadTestSuite(suiteName, scriptSrc) {
            console.log(`📥 Loading test suite: ${suiteName}`);
            
            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = scriptSrc;
                script.onload = () => {
                    console.log(`✅ Loaded test suite: ${suiteName}`);
                    resolve();
                };
                script.onerror = () => {
                    console.error(`❌ Failed to load test suite: ${suiteName}`);
                    reject(new Error(`Failed to load ${suiteName}`));
                };
                document.head.appendChild(script);
            });
        }
        
        async runAllValidationTests() {
            if (this.isRunning) {
                console.warn('⚠️ Validation tests already running');
                return;
            }
            
            this.isRunning = true;
            console.log('🚀 Starting comprehensive DOM validation system tests...\n');
            
            try {
                // Phase 1: Load all test suites
                console.log('📥 Phase 1: Loading Test Suites');
                await this.loadTestSuites();
                
                // Phase 2: Run core functionality tests
                console.log('\n🧪 Phase 2: Core Functionality Tests');
                await this.runCoreFunctionalityTests();
                
                // Phase 3: Run standardization tests
                console.log('\n📏 Phase 3: Standardization Validation Tests');
                await this.runStandardizationTests();
                
                // Phase 4: Run integration tests
                console.log('\n🔗 Phase 4: Integration Tests');
                await this.runIntegrationTests();
                
                // Phase 5: Generate comprehensive report
                console.log('\n📊 Phase 5: Generating Comprehensive Report');
                const finalReport = await this.generateMasterReport();
                
                // Phase 6: Store results and provide recommendations
                console.log('\n✅ Phase 6: Validation Complete');
                this.storeResults(finalReport);
                
                return finalReport;
                
            } catch (error) {
                console.error('❌ Master validation failed:', error.message);
                this.overallResults.criticalIssues.push({
                    level: 'CRITICAL',
                    message: `Master validation failed: ${error.message}`,
                    recommendation: 'Check console for detailed error information'
                });
                return this.generateMasterReport();
            } finally {
                this.isRunning = false;
                this.overallResults.endTime = Date.now();
                this.overallResults.totalDuration = this.overallResults.endTime - this.overallResults.startTime;
            }
        }
        
        async loadTestSuites() {
            const testSuites = [
                {
                    name: 'DOM Validation Test Suite',
                    src: '/scripts/tampermonkey/domValidationTestSuite.js',
                    required: true
                },
                {
                    name: 'Standardized Patterns Validator',
                    src: '/scripts/tampermonkey/standardizedPatternsValidator.js',
                    required: true
                },
                {
                    name: 'Integration Validation Test',
                    src: '/scripts/tampermonkey/integrationValidationTest.js',
                    required: true
                }
            ];
            
            for (const suite of testSuites) {
                try {
                    await this.loadTestSuite(suite.name, suite.src);
                    this.testSuites.set(suite.name, { loaded: true, required: suite.required });
                } catch (error) {
                    console.error(`❌ Failed to load ${suite.name}:`, error.message);
                    this.testSuites.set(suite.name, { loaded: false, required: suite.required, error: error.message });
                    
                    if (suite.required) {
                        this.overallResults.criticalIssues.push({
                            level: 'HIGH',
                            message: `Required test suite failed to load: ${suite.name}`,
                            recommendation: 'Ensure all test suite files are available and accessible'
                        });
                    }
                }
            }
            
            // Wait for test suites to initialize
            await this.delay(2000);
            
            console.log(`📦 Loaded ${Array.from(this.testSuites.values()).filter(s => s.loaded).length}/${testSuites.length} test suites`);
        }
        
        async runCoreFunctionalityTests() {
            try {
                console.log('🧪 Running DOM validation core functionality tests...');
                
                // Check if DOM validation test suite is available
                if (typeof window.runDOMValidationTests === 'function') {
                    const domTestResults = await window.runDOMValidationTests();
                    this.overallResults.suiteResults.set('DOM Core Tests', domTestResults);
                    
                    if (!domTestResults.success) {
                        this.overallResults.criticalIssues.push({
                            level: 'HIGH',
                            message: `DOM core functionality tests failed: ${domTestResults.failed} failures`,
                            recommendation: 'Review DOM helper implementations and fix failing core functions'
                        });
                    }
                } else {
                    this.overallResults.criticalIssues.push({
                        level: 'CRITICAL',
                        message: 'DOM validation test suite not available',
                        recommendation: 'Ensure domValidationTestSuite.js is loaded and functional'
                    });
                }
                
            } catch (error) {
                console.error('❌ Core functionality tests failed:', error.message);
                this.overallResults.criticalIssues.push({
                    level: 'HIGH',
                    message: `Core functionality test execution failed: ${error.message}`,
                    recommendation: 'Check DOM helpers library for critical errors'
                });
            }
        }
        
        async runStandardizationTests() {
            try {
                console.log('📏 Running standardization validation tests...');
                
                // Check if standardization validator is available
                if (typeof window.validateStandardizedPatterns === 'function') {
                    const standardizationResults = await window.validateStandardizedPatterns();
                    this.overallResults.suiteResults.set('Standardization Tests', standardizationResults);
                    
                    if (standardizationResults.overallScore < 80) {
                        this.overallResults.criticalIssues.push({
                            level: 'MEDIUM',
                            message: `Standardization compliance below 80%: ${standardizationResults.overallScore}%`,
                            recommendation: 'Review script implementations and apply standardized patterns'
                        });
                    }
                } else {
                    this.overallResults.criticalIssues.push({
                        level: 'HIGH',
                        message: 'Standardization validator not available',
                        recommendation: 'Ensure standardizedPatternsValidator.js is loaded and functional'
                    });
                }
                
            } catch (error) {
                console.error('❌ Standardization tests failed:', error.message);
                this.overallResults.criticalIssues.push({
                    level: 'MEDIUM',
                    message: `Standardization test execution failed: ${error.message}`,
                    recommendation: 'Check individual script implementations for standardization issues'
                });
            }
        }
        
        async runIntegrationTests() {
            try {
                console.log('🔗 Running integration validation tests...');
                
                // Check if integration tests are available
                if (typeof window.runIntegrationValidation === 'function') {
                    const integrationResults = await window.runIntegrationValidation();
                    this.overallResults.suiteResults.set('Integration Tests', integrationResults);
                    
                    if (!integrationResults.success) {
                        this.overallResults.criticalIssues.push({
                            level: 'HIGH',
                            message: `Integration tests failed: ${integrationResults.passedTests}/${integrationResults.totalTests} passed`,
                            recommendation: 'Review component integration and fix cross-component communication issues'
                        });
                    }
                } else {
                    this.overallResults.criticalIssues.push({
                        level: 'HIGH',
                        message: 'Integration test suite not available',
                        recommendation: 'Ensure integrationValidationTest.js is loaded and functional'
                    });
                }
                
            } catch (error) {
                console.error('❌ Integration tests failed:', error.message);
                this.overallResults.criticalIssues.push({
                    level: 'HIGH',
                    message: `Integration test execution failed: ${error.message}`,
                    recommendation: 'Check DOM helpers and error recovery framework integration'
                });
            }
        }
        
        async generateMasterReport() {
            console.log('\n' + '='.repeat(90));
            console.log('🎯 MASTER DOM VALIDATION SYSTEM REPORT');
            console.log('='.repeat(90));
            
            // Calculate overall scores
            const suiteScores = [];
            let totalTests = 0;
            let totalPassed = 0;
            
            for (const [suiteName, results] of this.overallResults.suiteResults) {
                let suiteScore = 0;
                let suitePassed = 0;
                let suiteTotal = 0;
                
                if (results.success !== undefined) {
                    suiteScore = results.success ? 100 : 0;
                    suitePassed = results.passed || (results.success ? 1 : 0);
                    suiteTotal = results.total || 1;
                } else if (results.overallScore !== undefined) {
                    suiteScore = parseFloat(results.overallScore);
                    suitePassed = results.passedChecks || 0;
                    suiteTotal = results.totalChecks || 1;
                } else if (results.successRate !== undefined) {
                    suiteScore = parseFloat(results.successRate);
                    suitePassed = results.passedTests || 0;
                    suiteTotal = results.totalTests || 1;
                }
                
                suiteScores.push(suiteScore);
                totalTests += suiteTotal;
                totalPassed += suitePassed;
                
                console.log(`📊 ${suiteName}: ${suiteScore}% (${suitePassed}/${suiteTotal})`);
            }
            
            this.overallResults.overallScore = suiteScores.length > 0 
                ? (suiteScores.reduce((a, b) => a + b, 0) / suiteScores.length).toFixed(1)
                : 0;
            
            const totalSuccessRate = totalTests > 0 ? (totalPassed / totalTests * 100).toFixed(1) : 0;
            
            console.log(`\n🎯 OVERALL SYSTEM SCORE: ${this.overallResults.overallScore}%`);
            console.log(`📈 TOTAL SUCCESS RATE: ${totalSuccessRate}% (${totalPassed}/${totalTests})`);
            console.log(`⏱️ TOTAL VALIDATION TIME: ${this.overallResults.totalDuration}ms`);
            
            // System status determination
            const systemStatus = this.determineSystemStatus();
            console.log(`🏆 SYSTEM STATUS: ${systemStatus.status}`);
            console.log(`💡 READINESS: ${systemStatus.readiness}`);
            
            // Critical issues summary
            if (this.overallResults.criticalIssues.length > 0) {
                console.log(`\n⚠️ CRITICAL ISSUES DETECTED: ${this.overallResults.criticalIssues.length}`);
                this.overallResults.criticalIssues.forEach((issue, index) => {
                    console.log(`  ${index + 1}. [${issue.level}] ${issue.message}`);
                    console.log(`     💡 ${issue.recommendation}`);
                });
            } else {
                console.log('\n✅ NO CRITICAL ISSUES DETECTED');
            }
            
            // Recommendations
            this.generateRecommendations();
            if (this.overallResults.recommendations.length > 0) {
                console.log('\n💡 RECOMMENDATIONS:');
                this.overallResults.recommendations.forEach((rec, index) => {
                    console.log(`  ${index + 1}. ${rec}`);
                });
            }
            
            // Component status summary
            console.log('\n📦 COMPONENT STATUS SUMMARY:');
            console.log(`  ✅ DOM Helpers Library: ${this.getComponentStatus('DOM Core Tests')}`);
            console.log(`  ✅ Error Recovery Framework: ${this.getComponentStatus('Integration Tests')}`);
            console.log(`  ✅ Standardization Compliance: ${this.getComponentStatus('Standardization Tests')}`);
            console.log(`  ✅ Cross-Component Integration: ${this.getComponentStatus('Integration Tests')}`);
            
            return {
                overallScore: this.overallResults.overallScore,
                totalSuccessRate,
                totalDuration: this.overallResults.totalDuration,
                systemStatus,
                suiteResults: Object.fromEntries(this.overallResults.suiteResults),
                criticalIssues: this.overallResults.criticalIssues,
                recommendations: this.overallResults.recommendations,
                componentStatus: this.getComponentStatusSummary()
            };
        }
        
        determineSystemStatus() {
            const score = parseFloat(this.overallResults.overallScore);
            const criticalCount = this.overallResults.criticalIssues.filter(i => i.level === 'CRITICAL').length;
            const highCount = this.overallResults.criticalIssues.filter(i => i.level === 'HIGH').length;
            
            if (criticalCount > 0) {
                return {
                    status: '🚨 CRITICAL ISSUES',
                    readiness: 'NOT READY FOR PRODUCTION',
                    priority: 'IMMEDIATE ATTENTION REQUIRED'
                };
            } else if (score >= 95 && highCount === 0) {
                return {
                    status: '🌟 EXCELLENT',
                    readiness: 'PRODUCTION READY',
                    priority: 'DEPLOY WITH CONFIDENCE'
                };
            } else if (score >= 85 && highCount <= 1) {
                return {
                    status: '✅ GOOD',
                    readiness: 'PRODUCTION READY WITH MONITORING',
                    priority: 'DEPLOY WITH STANDARD MONITORING'
                };
            } else if (score >= 70) {
                return {
                    status: '⚠️ NEEDS IMPROVEMENT',
                    readiness: 'PRE-PRODUCTION TESTING REQUIRED',
                    priority: 'ADDRESS ISSUES BEFORE DEPLOYMENT'
                };
            } else {
                return {
                    status: '❌ SIGNIFICANT ISSUES',
                    readiness: 'NOT READY FOR PRODUCTION',
                    priority: 'MAJOR FIXES REQUIRED'
                };
            }
        }
        
        generateRecommendations() {
            const score = parseFloat(this.overallResults.overallScore);
            
            if (score < 80) {
                this.overallResults.recommendations.push(
                    'Focus on improving core DOM validation functionality to reach 80%+ compliance'
                );
            }
            
            if (this.overallResults.criticalIssues.some(i => i.message.includes('not available'))) {
                this.overallResults.recommendations.push(
                    'Ensure all required validation frameworks are properly loaded and accessible'
                );
            }
            
            if (this.overallResults.criticalIssues.some(i => i.message.includes('Integration'))) {
                this.overallResults.recommendations.push(
                    'Review cross-component integration and fix communication issues between frameworks'
                );
            }
            
            const domResults = this.overallResults.suiteResults.get('DOM Core Tests');
            if (domResults && domResults.failed > 0) {
                this.overallResults.recommendations.push(
                    'Fix failing DOM helper functions before deploying to production environment'
                );
            }
            
            if (score >= 95) {
                this.overallResults.recommendations.push(
                    'System is performing excellently - consider setting up continuous monitoring'
                );
            }
        }
        
        getComponentStatus(testSuiteName) {
            const results = this.overallResults.suiteResults.get(testSuiteName);
            if (!results) return 'Unknown';
            
            let score = 0;
            if (results.success !== undefined) {
                score = results.success ? 100 : 0;
            } else if (results.overallScore !== undefined) {
                score = parseFloat(results.overallScore);
            } else if (results.successRate !== undefined) {
                score = parseFloat(results.successRate);
            }
            
            if (score >= 95) return 'Excellent';
            if (score >= 85) return 'Good';
            if (score >= 70) return 'Needs Improvement';
            return 'Requires Attention';
        }
        
        getComponentStatusSummary() {
            return {
                domHelpers: this.getComponentStatus('DOM Core Tests'),
                errorRecovery: this.getComponentStatus('Integration Tests'),
                standardization: this.getComponentStatus('Standardization Tests'),
                integration: this.getComponentStatus('Integration Tests')
            };
        }
        
        storeResults(finalReport) {
            window.masterValidationResults = finalReport;
            window.domValidationSystemStatus = {
                validated: true,
                timestamp: new Date().toISOString(),
                overallScore: finalReport.overallScore,
                readiness: finalReport.systemStatus.readiness,
                criticalIssues: finalReport.criticalIssues.length
            };
            
            console.log('\n💾 Results stored in window.masterValidationResults');
            console.log('📊 System status stored in window.domValidationSystemStatus');
        }
        
        delay(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
    }
    
    // ============================================================================
    // EXECUTION
    // ============================================================================
    
    async function runMasterValidation() {
        const masterRunner = new MasterValidationRunner();
        return await masterRunner.runAllValidationTests();
    }
    
    // Make available globally
    window.runMasterValidation = runMasterValidation;
    window.MasterValidationRunner = MasterValidationRunner;
    
    // Auto-run master validation after page load
    setTimeout(() => {
        console.log('🎯 Auto-starting master validation in 3 seconds...');
        setTimeout(runMasterValidation, 3000);
    }, 1000);
    
})();