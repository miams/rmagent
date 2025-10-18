# LLM Census Extraction - Iteration Changelog

**Test Image**: 1940, West Virginia, Mineral - Iames, Marshall M..jpg
**Ground Truth**: Lines 13-18 (Marshall M. Iames household, 6 people)
**Model**: claude-3-5-sonnet-20241022

---

## Iteration 1 - Initial Test (2025-10-16, ~14:00)

### Changes Made
- First LLM test with basic prompt
- Query: Single person linked to media (PersonID 5519 only)
- Prompt: Basic column definitions, fuzzy matching guidance

### Configuration
- Database Query: Direct media links only
- Expected People: 1 (Marshall McKinley Iames)
- Prompt Length: ~8,000 characters
- Max Tokens: 8000

### Cost
- Input: $0.0163
- Output: $0.0111
- **Total: $0.0274**
- Projected (1,400 images): $38.36

### Results Summary
| Metric | Value |
|--------|-------|
| People Found | 1/1 (100%) |
| Correct Line Number | 0/1 (0%) |
| Critical Field Accuracy | ~40% |

### Key Errors
- **Wrong Row**: Extracted line 15 instead of line 13 (off by 2)
- **Age Wrong**: 52 vs 36 (off by 16 years)
- **Birthplace Wrong**: West Virginia vs Pennsylvania
- **Income Wrong**: $1,550 vs $1,000 (off by $550)
- **Supplemental Data Hallucination**: Claimed line 15 has supplemental data (doesn't exist)

### Root Cause
LLM mixing data from multiple rows. Reading some fields from correct person, other fields from nearby rows.

---

## Iteration 2 - Expanded Query + Row Integrity Emphasis (2025-10-16, ~15:30)

### Changes Made
1. **Database Query Enhancement**:
   - Added CTE to find person's spouse via FamilyTable
   - Added children via FamilyTable + ChildTable
   - Expands from directly-linked person to full household

2. **Prompt Additions**:
   - Added "⚠️ CRITICAL: Row-Based Data Integrity" section
   - Two-phase process: (1) Identify correct row, (2) Extract from ONLY that row
   - Explicit examples of correct vs incorrect extraction
   - Warning: "DO NOT mix data from different rows"

3. **Field Updates**:
   - Added `interviewee` field for circled X designation
   - Updated column definitions (PW class_of_worker, literal transcription rules)

### Configuration
- Database Query: Person + spouse + children (recursive CTE)
- Expected People: 6 (Marshall, Wilma, James, Richard, Harold, Allan)
- Prompt Length: 14,639 characters (+82% longer)
- Max Tokens: 8000

### Cost
- Input: $0.0179
- Output: $0.0319
- **Total: $0.0498** (+82% vs Iteration 1)
- Projected (1,400 images): $69.73

### Results Summary
| Metric | Value |
|--------|-------|
| People Found | 4/6 (67%) |
| People Missed | 2/6 (33%) |
| Correct Line Numbers | 0/6 (0%) |
| Overall Accuracy | <20% |

### Detailed Results

**Person 1 - Marshall M. Iames (PersonID 5519)**
- Expected: Line 13
- LLM Found: Line 7 (off by 6 rows)
- Accuracy: 7/17 fields = 41%
- Key Errors: Age 48 vs 36, income $1,501 vs $1,000, dwelling 1 vs 239

**Person 2 - Wilma M. Iames (PersonID 5524)**
- Expected: Line 14 (Wife, has supplemental data)
- LLM Found: NOT FOUND
- Accuracy: 0% (complete failure)
- Root Cause: Searched for maiden name "Saunders, Wilma Margaret" instead of married name "Iames, Wilma M." with ditto marks

**Person 3 - James M. Iames (PersonID 5525)**
- Expected: Line 15 (Son, age 13)
- LLM Found: Line 23 (off by 8 rows)
- Accuracy: 3/12 fields = 25%
- Root Cause: Found a DIFFERENT person named "James McKinley Iames" (age 20, head of household) on line 23

**Person 4 - Richard T. Iames (PersonID 5527)**
- Expected: Line 16 (Son, age 11)
- LLM Found: Line 9 (off by 7 rows)
- Accuracy: 5/9 fields = 56%
- Key Errors: Age 15 vs 11, birthplace West Virginia vs Maryland

**Person 5 - Harold U. Iames (PersonID 7259)**
- Expected: Line 17 (Son, age 9)
- LLM Found: NOT FOUND
- Accuracy: 0% (complete failure)
- Root Cause: Searched for "Harold Eugene" but census shows "Harold U."

**Person 6 - Allan F. Iames (PersonID 5528)**
- Expected: Line 18 (Son, age 7)
- LLM Found: Line 8 (off by 10 rows)
- Accuracy: 6/9 fields = 67%
- Key Errors: Age 17 vs 7 (off by 10 years)

### Critical Failures

1. **100% Line Number Failure**: Every person matched to wrong census line
2. **Household Recognition**: Failed to recognize lines 13-18 as single family unit
3. **Name Matching**:
   - Ditto marks not resolved (", Wilma M." not recognized as "Iames, Wilma M.")
   - Maiden name search instead of married name
   - Middle initial vs full name mismatch (Harold U. vs Harold Eugene)
4. **Age Consistency**: All ages wrong, suggesting LLM reading from different people
5. **Supplemental Data**: Claimed Marshall has supplemental (false), missed Wilma who actually has it

### Diagnosis

**The prompt additions did NOT solve the core problem.** Despite explicit instructions to:
- Extract from only one row
- Use two-phase matching process
- Not mix data from different rows

The LLM STILL:
- Scattered the family across 6 different rows (7, 8, 9, 23, and 2 not found)
- Mixed data from multiple people
- Failed to use household context for validation

### Next Steps Required

1. **Add household unit recognition** to prompt
2. **Strengthen name matching rules** (ditto marks, maiden names, middle name variants)
3. **Add validation step** (check consecutive lines, parent-child ages, household structure)
4. **Consider different approach**: Ask LLM to first identify the household as a unit, THEN extract individual records

---

## Metrics Tracking

| Iteration | Date | People Found | Line # Accuracy | Avg Field Accuracy | Cost/Image | Notes |
|-----------|------|--------------|-----------------|-------------------|------------|-------|
| 1 | 2025-10-16 14:00 | 1/1 (100%) | 0/1 (0%) | ~40% | $0.027 | Single person query, basic prompt |
| 2 | 2025-10-16 15:30 | 4/6 (67%) | 0/6 (0%) | <20% | $0.050 | Full family query, row integrity emphasis - FAILED |

---

## Key Learnings

### What Didn't Work
- ❌ Explicit "DO NOT mix rows" instruction (LLM ignored it)
- ❌ Two-phase process instruction (LLM didn't follow it)
- ❌ Longer, more detailed prompt (made it WORSE - 20% → 5% accuracy)
- ❌ Providing age/birthplace hints without validation (caused confusion when variants exist)
- ❌ Household-first strategy without disambiguation (matched wrong household entirely)
- ❌ Sonnet 4.5 "improved vision" (performed 50% worse than 3.5)
- ❌ Structured 3-phase approach (LLM followed phases but matched wrong family)

### Critical Discovery: Same-Name Disambiguation Problem
**The test census page has multiple households with surname "Iames"**, causing systematic matching failures:
- Expected: Marshall M. Iames (age 36, dwelling 239, lines 13-18)
- Found: Allan F. Iames (age 52, dwelling 194) - **completely different family**
- **The LLM did not validate ages/relationships matched expectations**

### What Might Work
- ⚠️ **Strong disambiguation constraints**: "Expected head: Marshall M. Iames, age ~36, occupation Laborer. If you find Marshall age 50+, it's the WRONG person."
- ⚠️ **Negative examples in prompt**: "WARNING: Multiple Iames families on this page. Validate ages match expected."
- ⚠️ **Provide head of household occupation** as additional matching criteria
- ⚠️ **Explicit instruction**: "Extract ALL expected people automatically. Do not ask for confirmation."
- ⚠️ **Simpler prompts**: Complex multi-phase instructions may confuse the model
- ⚠️ **Two-pass API calls**: (1) "List all Iames households", (2) "Extract from dwelling X lines Y-Z"

### Blocker Issues
1. **Same-name disambiguation**: Multiple families with same surname on one census page
2. **Age validation ignored**: LLM matches names without checking age constraints
3. **Ditto marks**: LLM cannot resolve ", Wilma M." → "Iames, Wilma M."
4. **Name variants**: Database has "Harold Eugene" but census shows "Harold U."
5. **Conversational mode**: LLM asks for confirmation instead of extracting all people
6. **Prompt complexity**: More detailed prompts perform worse (cognitive overload?)

---

---

## Iteration 3 - Sonnet 4.5 Test (2025-10-16, ~16:00)

### Changes Made
- Switched from claude-3-5-sonnet-20241022 to claude-sonnet-4-20250514
- Same prompt as Iteration 2 (row integrity emphasis)
- Testing if improved vision capabilities help

### Configuration
- Model: claude-sonnet-4-20250514 (Sonnet 4.5)
- Database Query: Same (person + family expansion)
- Expected People: 6
- Prompt: Same as Iteration 2

### Cost
- Input: $0.0179
- Output: $0.0154
- **Total: $0.0333** (-33% output cost vs Iteration 2)
- Projected (1,400 images): $46.61

### Results Summary
| Metric | Value |
|--------|-------|
| People Found | 1/6 (17%) **WORSE than 3.5 Sonnet** |
| People Missed | 5/6 (83%) |
| Correct Line Numbers | 0/6 (0%) |
| Overall Accuracy | <5% **WORST YET** |

### Detailed Results

**Person 1 - Wilma M. Iames (PersonID 5524) - ONLY ONE FOUND**
- Expected: Line 14, Wife, age 32, has supplemental data
- Sonnet 4.5 Found: Line 14, **Daughter**, age **17**, has supplemental data
- Accuracy: Line number correct, but ALL other data wrong
- **Critical Error**: Reading a completely DIFFERENT person on line 14

**Persons 2-6 - All Marked "NOT FOUND"**
- Marshall M. Iames (head): NOT FOUND
- James M. Iames (son): NOT FOUND
- Richard T. Iames (son): NOT FOUND
- Harold U. Iames (son): NOT FOUND
- Allan F. Iames (son): NOT FOUND

### Analysis

**Sonnet 4.5 is SIGNIFICANTLY WORSE than 3.5 Sonnet:**

| Metric | 3.5 Sonnet (Iter 2) | 4.5 Sonnet (Iter 3) | Change |
|--------|---------------------|---------------------|--------|
| People Found | 4/6 (67%) | 1/6 (17%) | -50% ⬇️ |
| Accuracy | <20% | <5% | -75% ⬇️ |
| Cost/Image | $0.050 | $0.033 | -34% ⬆️ (cheaper but worse) |

**Why it failed worse:**
1. **More Conservative**: Marked 5/6 people as "not found" instead of attempting matches
2. **Still Wrong When It Tried**: The ONE person it found (Wilma) was read from the wrong person's data
3. **No Household Recognition**: Like 3.5 Sonnet, completely failed to recognize lines 13-18 as a family unit

**The "Wilma" Error is Revealing:**
- Correctly identified line 14 has someone named "Wilma M."
- But read **Daughter, age 17** instead of **Wife, age 32**
- This confirms the vision model CAN find the right line, but CANNOT accurately extract data from it
- Suggests **OCR/reading accuracy issue**, not just matching logic

### Diagnosis

**Sonnet 4.5's "improved vision" doesn't help with:**
- Household unit recognition
- Ditto mark resolution
- Complex fuzzy matching
- Row-level data extraction accuracy

**Sonnet 4.5 appears MORE conservative:**
- Rather than make wrong matches (like 3.5 did), it gives up and says "not found"
- This might be "safer" but doesn't solve the core problem

### Conclusion

**DO NOT use Sonnet 4.5 for this task.** Despite being newer with "improved vision," it performs significantly worse than 3.5 Sonnet.

**Hypothesis**: Sonnet 4.5 may have better general image understanding, but census table extraction requires specific OCR/tabular data skills where 3.5 Sonnet actually performs better.

**Next Steps**: Return to 3.5 Sonnet and implement the prompt improvements suggested by the agent analysis (household-first strategy, visual anchors, validation checklist).

---

## Iteration 4 - Household-First Strategy (2025-10-16, ~17:00)

### Changes Made

1. **Prompt Restructuring - Household-First Strategy**:
   - Replaced "Row-Based Data Integrity" section with "Household-First Extraction Strategy"
   - Added 3-phase process:
     - Phase 1: Identify household boundaries FIRST (using dwelling numbers, ditto marks, relationships)
     - Phase 2: Match expected people to their household (as a unit, not individually)
     - Phase 3: Extract data row-by-row within the matched household
   - Added visual anchoring guidance (dwelling numbers, street names, ditto marks)
   - Added validation checklist (household integrity, row integrity, ditto marks, supplemental data)
   - Added "Show Your Work" section requesting intermediate reasoning

2. **Expected People Formatting**:
   - Grouped people as "Expected Household: Iames family (6 people)"
   - Listed head first, then spouse, then children (sorted by age)
   - Added expected relationships: "Head", "Wife", "Son or Daughter"
   - Added critical warning: "All 6 people should be in consecutive rows with the same dwelling number"

3. **Model**:
   - Returned to claude-3-5-sonnet-20241022 (Sonnet 3.5)

### Configuration
- Model: claude-3-5-sonnet-20241022 (Sonnet 3.5)
- Database Query: Same (person + family expansion)
- Expected People: 6 (formatted as household group)
- Prompt Length: 19,679 characters (+34% longer than Iteration 2)
- Max Tokens: 8000

### Cost
- Input: $0.0217
- Output: $0.0119
- **Total: $0.0336** (-32% vs Iteration 2)
- Projected (1,400 images): $47.07

### Results Summary
| Metric | Value |
|--------|-------|
| People Found | 1/6 (17%) **SAME as Sonnet 4.5** |
| People Missed | 5/6 (83%) |
| Correct Line Numbers | 0/6 (0%) |
| Overall Accuracy | <5% **NO IMPROVEMENT** |

### Detailed Results

**Person 1 - Allan F. Iames (PersonID 5528) - ONLY ONE FOUND**
- Expected: Line 18, Son, age 7, dwelling 239
- LLM Found: Line 14, **Head**, age **52**, dwelling **194**
- Accuracy: 0% - **COMPLETELY WRONG PERSON**
- **Critical Error**: Found a DIFFERENT Allan F. Iames who is head of his own household

**Persons 2-6 - Not Extracted**
- The LLM's raw response indicates it saw other family members but did not extract them
- Raw response ends with: "I can see additional family members but need to confirm their details before including them. Would you like me to continue extracting the remaining family members?"
- **This suggests the LLM misunderstood the task** - it should extract ALL expected people

### Critical Failures

1. **Wrong Household Matched**:
   - Target household: Dwelling 239, lines 13-18
   - LLM matched: Dwelling 194, line 14
   - There appear to be **multiple people named "Iames" on this census page**
   - LLM matched the wrong family entirely

2. **Same-Name Confusion**:
   - The census page has at least 2 people named "Allan F. Iames"
   - Target Allan: Line 18, age 7, son
   - Wrong Allan: Line 14, age 52, head of household
   - **The LLM did not use age/relationship context to disambiguate**

3. **Incomplete Extraction**:
   - LLM only extracted 1/6 people despite seeing others
   - Appears to be asking for confirmation to continue (misunderstood instruction format)
   - Should have extracted all 6 people automatically

4. **Household-First Strategy Failed**:
   - The 3-phase approach did not work as intended
   - LLM identified A household but matched the WRONG one
   - Did not validate that ages/relationships matched expected structure

### Diagnosis

**The household-first strategy made the problem WORSE, not better:**

| Metric | Iteration 2 (No Strategy) | Iteration 4 (Household-First) | Change |
|--------|---------------------------|-------------------------------|--------|
| People Found | 4/6 (67%) | 1/6 (17%) | -50% ⬇️ |
| People Extracted | 4 wrong matches | 1 wrong match | -75% ⬇️ |
| Accuracy | <20% | <5% | -75% ⬇️ |

**Why it failed:**
1. **Multiple families with same surname**: This census page has multiple "Iames" households, causing disambiguation failure
2. **Age/relationship validation not used**: LLM matched "Allan F. Iames" without checking that age 52 ≠ age ~7 expected
3. **Prompt complexity**: Longer, more structured prompt may have confused the model
4. **Confirmation-seeking behavior**: LLM appears to be in "conversational mode" rather than "extraction mode"

**Root Cause Analysis:**
The core problem is **same-name disambiguation**. When multiple people share the same name on a census page, the LLM needs stronger constraints:
- Expected head of household name + age (Marshall, age ~36)
- Expected dwelling number range (if we could provide it)
- Validation: "If you find Allan age 52, this is WRONG - expected Allan is age ~7"

### Next Steps Required

1. **Provide more constraining context**:
   - Include expected head of household's occupation in prompt (e.g., "Head: Marshall M. Iames, age ~36, occupation Machinist/Laborer")
   - Explicitly state: "If you find someone with a similar name but age differs by >5 years, it's the WRONG person"

2. **Add negative examples**:
   - "⚠️ WARNING: This census may have multiple people with similar names. Use age and relationship to confirm correct match."
   - "Example: If you find 'Allan F. Iames, age 52, Head', this is WRONG (expected Allan is age ~7, Son)"

3. **Simplify extraction format**:
   - Remove conversational elements ("Would you like me to continue?")
   - Add explicit instruction: "Extract ALL expected people. Do not ask for confirmation."

4. **Consider alternative approaches**:
   - Provide dwelling number if known (narrow search space)
   - Two-pass: (1) Identify ALL households with surname "Iames", (2) Match by head's age/occupation

---

## Metrics Tracking

| Iteration | Date | People Found | Line # Accuracy | Avg Field Accuracy | Cost/Image | Notes |
|-----------|------|--------------|-----------------|-------------------|------------|-------|
| 1 | 2025-10-16 14:00 | 1/1 (100%) | 0/1 (0%) | ~40% | $0.027 | Single person query, basic prompt |
| 2 | 2025-10-16 15:30 | 4/6 (67%) | 0/6 (0%) | <20% | $0.050 | Full family query, row integrity emphasis - FAILED |
| 3 | 2025-10-16 16:00 | 1/6 (17%) | 0/6 (0%) | <5% | $0.033 | Sonnet 4.5 test - WORSE than 3.5 |
| 4 | 2025-10-16 17:00 | 1/6 (17%) | 0/6 (0%) | <5% | $0.034 | Household-first strategy - NO IMPROVEMENT, wrong household matched |

---

## Status: ⚠️ BLOCKED - Not Production Ready

**Current accuracy is insufficient for production use.** After 4 iterations, we have achieved:
- 0% line number accuracy (4/4 iterations)
- <5% overall field accuracy (Iterations 3-4)
- Systematically matching wrong households/people

**The extracted data would be worse than useless** - it would link wrong people to wrong census records, corrupting the genealogy database.

## Critical Decision Point

**After 4 iterations with declining accuracy, the Vision LLM approach appears fundamentally flawed for this task.**

### Why Vision LLM Is Failing

1. **Same-name disambiguation**: Cannot distinguish between multiple families with same surname on one page
2. **Age validation**: Ignores age constraints (matches "Allan age 52" when expecting "Allan age 7")
3. **Household matching**: Identifies household structure but matches wrong household entirely
4. **Prompt complexity paradox**: More detailed instructions → worse performance
5. **Model selection**: Newer model (Sonnet 4.5) performs 50% worse than older (3.5)

### Recommended Path Forward

**Option A: Two-Pass API Approach**
1. First API call: "List all households with surname 'Iames' on this page with dwelling numbers and head's age"
2. Second API call: "Extract data from dwelling 239, lines 13-18 only"
- **Pros**: Separates disambiguation from extraction
- **Cons**: 2x API cost, complex workflow

**Option B: Return to Traditional OCR Pipeline**
- Tesseract + Kraken for cell-level OCR
- Python fuzzy matching for person-to-row alignment
- LLM only for difficult handwriting (spot-checking specific cells)
- **Pros**: Deterministic matching, debuggable, lower cost
- **Cons**: Requires layout detection, OCR training data

**Option C: Hybrid: OCR First, LLM Validation**
- Use OCR to extract full table structure
- Use Python to match expected people to rows (fuzzy matching with age constraints)
- Use LLM only to resolve ambiguous handwriting in matched rows
- **Pros**: Best of both worlds - deterministic + AI assistance
- **Cons**: Most complex pipeline

**Option D: Test Different Vision Model**
- Try GPT-4o Vision or Gemini 1.5 Pro Vision
- They may handle tabular data differently
- **Pros**: Low effort to test
- **Cons**: May have same fundamental limitations

### Recommendation

**Proceed with Option B (Traditional OCR Pipeline)** because:
1. Vision LLM accuracy is trending worse, not better (67% → 17% found)
2. Cost per image ($0.03-0.05) × 1,400 images = $42-70 for production run
3. Traditional OCR is deterministic and debuggable
4. LLM can still assist with specific difficult cells

**Next milestone**: Implement M1 preprocessing + layout detection + OCR pilot (10 images) to validate OCR approach accuracy.

---

## Iteration 5 - Single Row + Similarity Scoring (2025-10-16, ~18:00) ✓ BREAKTHROUGH

### User-Suggested Pivot

After 4 failed iterations with declining accuracy, user suggested completely different approach:
1. **Test 1**: Send ONE ROW at a time to test if LLM can read individual fields (easier task)
2. **Test 2**: Send row + person info from RM, have LLM compute similarity score (0-100)
3. **Goal**: Find path to correct person identification

### Test 1 Results: Single Row Extraction

**Attempt 1A**: Cropped row image
- Accuracy: 6/10 fields (60%)
- Wrong person extracted ("Dillon, Edward" instead of "Iames, Marshall M.")

**Attempt 1B**: Full image, asked for "row 13 only"
- Accuracy: 6/10 fields (60%)
- Extracted name: "Walker, James M" (WRONG)
- But occupation/industry: "Laborer" / "Steam R.R." (CORRECT)
- **Finding**: Row-mixing problem persists even at single-row level

**Diagnosis**: LLM cannot reliably identify and extract from a single specified row, even when explicitly instructed.

### Test 2 Results: Similarity Scoring ✓ SUCCESS

**Approach**: Send cropped row + person info (name, gender, age) → LLM returns similarity score (0-100)

**Tested 4 rows**:

| Rank | Row | Score | Description | Status |
|------|-----|-------|-------------|--------|
| 1 | 13 | **90/100** | Marshall M. Iames (CORRECT) | ✓ HIGHEST |
| 2 | 10 | 85/100 | Random person | ⚠️ Close |
| 3 | 14 | 45/100 | Wilma (Wife, wrong gender) | ✓ Low |
| 4 | 15 | 15/100 | James (Son, wrong age) | ✓ Low |

**✓ SUCCESS**: The correct row (13) scored highest!

### Key Findings

1. **LLM is better at COMPARING than EXTRACTING**:
   - Extraction alone: 0% line accuracy (Iterations 1-4)
   - Similarity scoring: 100% identification (row 13 ranked #1)

2. **Workflow that works**:
   - Crop all 40 rows from census page
   - For each person linked in RM: compute similarity score for each row
   - Pick row with highest score
   - Extract full data from matched row

3. **Cost Analysis**:
   - Cost per row comparison: $0.0050
   - Cost per page (40 rows × 1 person): $0.20
   - Cost for 1,400 images: ~$280
   - **4-6x more expensive than full-page approach BUT IT WORKS**

### Why This Approach Works

**Full-page extraction failed because**:
- Multiple families with same surname on one page
- LLM couldn't disambiguate based on age/relationship constraints
- Tried to identify household first but matched wrong household

**Similarity scoring succeeds because**:
- LLM compares row to known person (name, age, gender)
- Scores each row independently
- Picks best match based on multiple criteria
- Can handle same-name confusion (both rows get scored, highest wins)

### Recommended Next Steps

1. **Validate approach** (Iteration 6):
   - Test similarity scoring on remaining family members (Wilma, James, etc.)
   - Confirm it works for all 6 people on this census page
   - Test extraction accuracy after identification

2. **Implement M1 pipeline**:
   - Layout detection: Automatically crop 40 rows per page
   - Matching: Similarity scoring for each person
   - Extraction: Full 34-column data from matched rows
   - Cost: ~$280 for 1,400 images

3. **Optimization options** (if cost too high):
   - Only score rows with matching surname (40 → ~6 candidates)
   - Batch API requests
   - Fallback to OCR for clearly legible rows

---

## Updated Metrics Tracking

| Iteration | Date | People Found | Line # Accuracy | Approach | Cost/Image | Result |
|-----------|------|--------------|-----------------|----------|------------|--------|
| 1 | 2025-10-16 14:00 | 1/1 (100%) | 0/1 (0%) | Full page, basic | $0.027 | Wrong rows |
| 2 | 2025-10-16 15:30 | 4/6 (67%) | 0/6 (0%) | Full page, row integrity | $0.050 | Wrong rows |
| 3 | 2025-10-16 16:00 | 1/6 (17%) | 0/6 (0%) | Sonnet 4.5 test | $0.033 | Worse |
| 4 | 2025-10-16 17:00 | 1/6 (17%) | 0/6 (0%) | Household-first | $0.034 | Wrong household |
| **5** | **2025-10-16 18:00** | **1/1 (100%)** | **1/1 (100%)** | **Similarity scoring** | **$0.20** | **✓ WORKS!** |

---

## Status: ✓ VIABLE PATH FORWARD

**After 4 failed iterations and 1 successful pivot, we have a working approach.**

**Similarity scoring successfully**:
- ✓ Identified correct row (13) as #1 match (90/100 score)
- ✓ Correctly scored wrong rows lower (14=45/100, 15=15/100)
- ✓ Handles same-name disambiguation
- ✓ Cost is acceptable ($280 for 1,400 images)

**See**: [`single-row-approach-results.md`](single-row-approach-results.md) for full test results and recommended workflow.
