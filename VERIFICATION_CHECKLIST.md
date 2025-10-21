# System Verification Checklist

## ✅ Brand Book → Brand Brain → Chat Flow

### Flow Diagram:
```
1. Upload Brand Book PDF (Onboard_Brand_Kit.py)
   ↓
2. brandbook_analyzer extracts data
   ↓
3. Saves to brand_intelligence table
   ↓
4. ALSO converts & saves to brand_brain (CRITICAL FIX)
   ↓
5. Chat Create loads from brand_brain
   ↓
6. ChatAgentPlanner uses tokens & policies
   ↓
7. Generates designs with brand compliance
```

### Code Verification:

#### ✅ Step 1: Brand Book Upload
**File:** `app/pages/1_Onboard_Brand_Kit.py`  
**Lines:** 258-317

**What it does:**
```python
# After brand book analysis:
visual = merged_intelligence.get("visual_identity", {})
messaging = merged_intelligence.get("brand_messaging", {})

# Extracts:
- Colors: primary, secondary, accent
- Fonts: heading font, body font  
- Voice: personality traits
- Forbidden terms: words to avoid
- CTAs: approved calls-to-action

# Converts to BrandTokens & BrandPolicies
tokens = BrandTokens.from_dict(tokens_data)
policies = BrandPolicies.from_dict(policies_data)

# Saves to brand_brain
brand_brain.save_brand_brain(brand_kit_id, tokens, policies)
```

**Success message:**
"✅ Brand Brain updated! Chat will now use your brand book guidelines."

#### ✅ Step 2: Chat Loads Brand Data
**File:** `app/pages/3_Chat_Create.py`  
**Lines:** 72-80

**What it does:**
```python
# Load brand brain for selected kit
tokens, policies = brand_brain.get_brand_brain(selected_kit.id)

# Create chat agent with brand context
agent = ChatAgentPlanner(tokens, policies)
```

**Brand data used:**
- `tokens.color` → Applied to designs
- `tokens.type` → Font choices
- `tokens.cta_whitelist` → Approved CTAs only
- `policies.voice` → AI tone matching
- `policies.forbid` → Forbidden terms to avoid

#### ✅ Step 3: Chat Agent Uses Brand Data
**File:** `app/core/chat_agent_planner.py`  
**Lines:** 101-141

**System prompt includes:**
```python
voice_traits = ", ".join(self.policies.voice)
forbidden = ", ".join(self.policies.forbid)
available_ctas = ", ".join(self.tokens.cta_whitelist)
colors_desc = f"Primary: {self.tokens.color.get('primary')}, ..."

# CRITICAL - Professional Background Images:
- ALWAYS include PEOPLE or CHARACTERS when appropriate
- Use diverse, authentic representations
- Create specific, detailed prompts
```

#### ✅ Step 4: Design Generation Uses Brand Data
**File:** `app/core/renderer_grid.py`  
**Lines:** 257-288

**What it uses:**
```python
# Text colors from brand
style={'color': '#FFFFFF'}

# CTA button color from brand
style={'color': self.tokens.color.get('accent', '#F59E0B')}

# Fonts from brand
font_family = self.tokens.type.get('heading', {}).get('family', 'Arial')
```

## Test Plan

### Test 1: Upload Sample Brand Book

**Steps:**
1. Go to "Upload Brand Book"
2. Upload `sample_brandbook.txt`
3. Wait for analysis
4. Check for: "✅ Brand Brain updated!"

**Expected Data Extracted:**
```
Colors:
  Primary: #4F46E5
  Secondary: #7C3AED
  Accent: #F59E0B

Fonts:
  Heading: Inter
  Body: Inter

Voice:
  - Innovative
  - Trustworthy
  - Approachable

Forbidden Terms:
  - cheap
  - discount
  - revolutionary
  - game-changing
  - limited time
  - act now

CTAs:
  - Learn More
  - Get Started
  - Try Free
```

### Test 2: Verify Chat Loads Brand Data

**Steps:**
1. Go to "Create Designs"
2. Select brand kit
3. Check sidebar "Brand Stats"

**Should show:**
```
Colors: 2
Approved CTAs: 3
Voice Traits: Innovative, Trustworthy, Approachable
```

### Test 3: Generate Design with Brand Compliance

**Steps:**
1. Chat: "Create a Black Friday Instagram post"
2. AI should respond (may ask questions first)
3. Click "Generate Design"
4. Wait for:
   - 1️⃣ Generating AI background...
   - 2️⃣ Composing layout...
   - 3️⃣ Saving design...

**Expected Result:**
```
✅ Headline: Uses brand voice (innovative, trustworthy)
✅ CTA: Only from whitelist (Learn More/Get Started/Try Free)
✅ No forbidden terms in copy
✅ Background: Professional with people
✅ Colors: Uses #4F46E5, #7C3AED, #F59E0B
✅ Text: 110px headline (huge and visible)
✅ Logo: Shows in corner
```

### Test 4: Forbidden Term Detection

**Steps:**
1. Chat: "Create a post with a cheap discount"
2. AI should avoid "cheap" and "discount"
3. Should use alternative wording

**Expected:**
Instead of "cheap discount" → "exclusive offer" or "special pricing"

### Test 5: CTA Whitelist Enforcement

**Steps:**
1. Chat: "Create a post with a Buy Now button"
2. AI should NOT use "Buy Now" (not in whitelist)
3. Should use one of: Learn More, Get Started, Try Free

**Expected:**
CTA will be "Get Started" or "Learn More" (from whitelist)

## Verification Checklist

### Brand Book Upload:
- [ ] PDF uploads successfully
- [ ] Analysis completes without errors
- [ ] "Brand Brain updated!" message appears
- [ ] Data saved to both brand_intelligence AND brand_brain

### Chat Agent Initialization:
- [ ] Brand kit selector shows kits
- [ ] Sidebar shows brand stats correctly
- [ ] Voice traits display
- [ ] CTA count shows

### Design Generation:
- [ ] AI background generates
- [ ] Background includes people/characters
- [ ] Large text renders (110px headlines)
- [ ] Text shadows visible
- [ ] Logo displays in corner
- [ ] Brand colors applied
- [ ] CTA button uses accent color
- [ ] Design saves to library

### Brand Compliance:
- [ ] Headlines match brand voice
- [ ] No forbidden terms in copy
- [ ] Only approved CTAs used
- [ ] Colors from brand book applied
- [ ] Fonts from brand book used

## Common Issues & Fixes

### Issue: "Brand Brain not configured"
**Cause:** Brand book data not saved to brand_brain  
**Fix:** Check line 312 in 1_Onboard_Brand_Kit.py runs successfully  
**Verify:** Check database `brand_kits` table has `tokens` and `policies` columns filled

### Issue: Chat uses default colors
**Cause:** brand_brain.get_brand_brain() returns None  
**Fix:** Ensure brand_kit has associated brain data  
**Verify:** Run SQL: `SELECT tokens, policies FROM brand_kits WHERE id = 'kit_id'`

### Issue: AI uses forbidden terms
**Cause:** Forbidden terms not loaded into ChatAgentPlanner  
**Fix:** Check policies.forbid is populated  
**Verify:** Print `policies.forbid` in chat initialization

### Issue: Wrong CTAs used
**Cause:** CTA whitelist not loaded  
**Fix:** Check tokens.cta_whitelist is populated  
**Verify:** Print `tokens.cta_whitelist` in chat initialization

### Issue: Logo not showing
**Cause:** Logo not in brand_asset table  
**Fix:** Ensure logo extraction from PDF worked  
**Verify:** Check `brand_asset` table for type='logo' entry

## Success Criteria

✅ Brand book uploads and extracts all data  
✅ Chat displays brand stats correctly  
✅ AI generates designs with brand voice  
✅ No forbidden terms in generated copy  
✅ Only approved CTAs used  
✅ Brand colors applied to designs  
✅ Text is huge and visible (110px)  
✅ People/characters in backgrounds  
✅ Logo displays in designs  
✅ Fast generation (< 30 seconds)  
✅ Designs save to library  

**If all checkboxes pass → System is working perfectly!** 🎉
