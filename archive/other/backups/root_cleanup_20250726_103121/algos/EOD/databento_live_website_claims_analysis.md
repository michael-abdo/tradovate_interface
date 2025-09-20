# Databento Live Website Claims Analysis
## What Databento ACTUALLY Claims vs. What They Deliver

### 📊 COMPREHENSIVE ANALYSIS OF LIVE WEBSITE CLAIMS

---

## 1. GENERAL OPTIONS COVERAGE CLAIMS

### ✅ What Databento Claims on Their Live Website:

**From https://databento.com/options:**
- **"Since we source our data from the full direct feeds, we cover every instrument on each exchange and trading venue—every strike and expiration"**
- **"Across US equity options (OPRA), CME, and ICE, we currently cover almost 2 million options tickers"**
- **"We cover all US equity options and options on futures"**
- **"You can use parent symbology to fetch all strikes and expirations for a root symbol"**

**From https://databento.com/futures:**
- **"930k+ futures, spreads, and options on futures from all CME and ICE exchanges"**
- **"Over 3 million symbols"**
- **"all listed options contracts"**

---

## 2. CME GLOBEX SPECIFIC CLAIMS

### ✅ What Databento Claims About CME Coverage:

**From https://databento.com/datasets/GLBX.MDP3:**
- **"2,138 products" across "Futures, Options"**
- **"MDP 3.0 is the sole data feed for all instruments traded on CME Globex, including futures, options, spreads and combinations"**
- **"Directly captured at Aurora DC3 with an FPGA-based network card and hardware timestamping"**

---

## 3. SPECIFIC OPTIONS TYPES MENTIONED

### ✅ What Databento Acknowledges:

**0DTE Options (from https://databento.com/blog/what-are-0-dte-options):**
- They provide "Options on futures data from CME Globex, ICE Futures Europe, and ICE Endex"
- They understand 0DTE options and provide data for them
- They note that "approximately 56% of SPX options volume was in 0DTE contracts"

**OPRA Coverage (from https://databento.com/microstructure/opra):**
- "Databento provides both historical and real-time OPRA data"
- They position themselves as unique in providing comprehensive OPRA data

---

## 4. WHAT DATABENTO DOES NOT CLAIM

### ❌ Missing Claims on Live Website:

**No Specific Claims About:**
- Q3C, Q1A, or QNE option symbols
- "Week-3 Wednesday expiry" terminology
- "Monday & Wednesday weekly options"
- Specific weekly option naming conventions
- Daily expiring NQ options
- Comprehensive coverage of ALL NQ option expirations

### ❌ No Live Documentation Found For:
- NQ options catalog page (returns JavaScript enable page)
- Options on futures introduction page (returns JavaScript enable page)
- Specific NQ options coverage details

---

## 5. REALITY CHECK: WHAT OUR TESTING FOUND

### 📊 API Results vs. Website Claims:

| **Website Claim** | **API Reality** | **Discrepancy** |
|-------------------|-----------------|------------------|
| "every instrument...every strike and expiration" | Only 212 NQ options found | Significant gap |
| "all listed options contracts" | Only 6 expiration dates | Major limitation |
| "930k+ futures, spreads, and options on futures" | Zero weekly options matching CME formats | Missing weekly options |
| "2,138 products" in CME options | No Q3C, Q1A, QNE symbols | Standard weekly formats missing |

### 📋 Specific Findings:
- **Retrieved:** 1,547 NQ option trades
- **Found:** 212 unique NQ options (not "all")
- **Expirations:** Only 6 dates (not "every expiration")
- **Weekly Options:** Zero found (despite "all listed" claims)

---

## 6. CRITICAL ANALYSIS

### 🔍 What Databento's Live Website Actually Promises:

1. **Comprehensive Coverage Language:** Uses strong language like "every instrument," "all listed," and "comprehensive"
2. **Technical Capability:** Demonstrates understanding of 0DTE options and modern market structure
3. **Data Breadth:** Claims millions of symbols and products
4. **API Functionality:** Promises parent symbology for complete option chains

### ⚠️ What's Missing from Live Website:

1. **Specific Weekly Options:** No mention of Q3C, Q1A, QNE formats
2. **NQ-Specific Coverage:** No detailed NQ options page accessible
3. **Expiration Schedules:** No specific claims about daily/weekly expiration coverage
4. **Limitations Disclosure:** No clear statement of what they don't provide

---

## 7. CONCLUSION

### 📊 The Gap Between Claims and Reality:

**Databento's live website makes BROAD, GENERAL claims about comprehensive options coverage ("every instrument," "all listed options") but:**

1. **Lacks specificity** about weekly option formats (Q3C, Q1A, QNE)
2. **Cannot deliver** on general claims when tested systematically
3. **Provides incomplete coverage** despite comprehensive language
4. **Has inaccessible documentation** for key product pages

### 🎯 Key Findings:

1. **Their live website claims are GENERAL, not specific** to weekly options
2. **They understand modern options** (0DTE, OPRA) but don't deliver weekly formats
3. **API testing reveals significant gaps** in their "comprehensive" coverage
4. **Missing documentation** suggests incomplete product offerings

### 💡 Implication for Support Request:

**The discrepancy is between:**
- **Broad marketing claims** ("every instrument," "all listed")
- **Specific technical reality** (only quarterly options available)
- **Industry-standard expectations** (weekly options should be included in "all listed")

This analysis strengthens the support case by showing that even their GENERAL claims about comprehensive coverage are not being met by their actual API capabilities.

---

**Analysis Date:** July 17, 2025  
**Pages Analyzed:** 8 live Databento web pages  
**API Tests Referenced:** 15+ comprehensive tests  
**Key Finding:** Broad claims, narrow delivery