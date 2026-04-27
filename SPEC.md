# Brand Shoot Kit — Spec + Build Plan

**Working name:** Brand Shoot Kit  
**Alternate names:** ShootScout, Virtual Shoot Kit, Catalog Studio, Brand Studio Kit, Product Shoot Agent  
**Status:** Draft spec  
**Owner:** Matt Berman / Big Players  
**Built for:** OpenClaw agent workflows  
**Primary model moment:** GPT Image 2 / next-gen image models with strong product preservation, text rendering, and scene control

---

## One-Line Promise

Paste a product URL. The agent studies the brand, finds the missing e-commerce shots, and generates a complete AI product shoot: clean PDP images, lifestyle scenes, model shots, seasonal sets, social crops, and brand-consistent visual variants.

---

## The Big Idea

Most e-commerce brands do not need one more AI image prompt.

They need a **repeatable shoot system**.

Every brand needs more visuals than it can realistically produce:

- product detail page images
- Amazon / marketplace images
- lifestyle shots
- model/in-use photos
- seasonal campaign assets
- email hero images
- social crops
- launch imagery
- bundle shots
- founder/creator-style visuals
- visual tests for new positioning

Traditional shoots are slow and expensive because they require a photographer, location, stylist, props, models, lighting, retouching, and reshoots.

Brand Shoot Kit turns that into an agent loop:

```text
Product URL → Brand Analysis → Visual Gap Audit → Shoot Strategy → Shot List → Sets + Models → Generated Assets → QA → Export Pack
```

The win is not “AI can make product photos.”

The win is:

> A small brand can generate the kind of visual library that used to require a studio day, a creative director, and a production budget.

---

## Why This Exists

Most AI image tools start at the wrong place.

They ask the user to prompt.

That is backwards.

A real creative director does not start by writing a Midjourney prompt. They study the product, the brand, the customer, the category, the existing photography, the sales page, and the visual gaps.

Then they decide what needs to be shot.

Brand Shoot Kit starts there.

It uses the brand’s website and socials as the source of truth, then builds a shoot plan before it generates anything.

---

## Positioning

### Category

**AI product photography agent** / **AI brand shoot system** / **e-commerce visual production kit**

### Differentiated from

| Alternative | What they do | Why Brand Shoot Kit is different |
|---|---|---|
| Basic AI image generators | Generate one-off images from prompts | Brand Shoot Kit plans the whole shoot and creates a complete asset system |
| Product photo apps | Put products on simple backgrounds | Brand Shoot Kit builds brand-aware lifestyle, model, seasonal, PDP, and campaign assets |
| Canva templates | Help design static graphics | Brand Shoot Kit creates the underlying photography concepts and images |
| Photo studios | High-quality but slow/expensive | Brand Shoot Kit gives fast iterative shoot directions and cheap asset volume |
| Ad tools | Focus on ad creative/performance | Brand Shoot Kit focuses on product photography and commerce visual libraries, avoiding overlap with StealAds |

### Strategic boundary with StealAds

This kit must **not** become an ad intelligence or ad spying product.

StealAds owns:

- ad research
- swipe files
- competitor creative intelligence
- ad analysis
- ad inspiration
- paid social creative strategy

Brand Shoot Kit owns:

- product photography
- e-commerce asset libraries
- brand shoot planning
- product page visual completeness
- model/set/lifestyle generation
- visual asset QA

If the kit creates ad-sized exports, they are repurposed from the product shoot. It should not analyze ads, rank ads, or position itself as an ad creative platform.

---

## Target Users

### Primary

- Shopify brand founders
- Amazon sellers
- DTC operators
- small e-commerce teams
- agencies producing visuals for e-commerce clients
- creators selling physical products

### Secondary

- product marketers
- landing page builders
- email marketers
- brand consultants
- product launch teams

### Best-fit products

The kit works best for products where context and lifestyle matter:

- beauty / skincare
- supplements
- fitness products
- food and beverage
- apparel accessories
- home goods
- baby/kids products
- pet products
- wellness products
- creator merch
- premium CPG

### Weak-fit products

The kit should warn or degrade gracefully for:

- highly technical industrial products
- products with strict regulatory packaging accuracy needs
- products where exact dimensions are legally/commercially critical
- complex transparent/glass packaging that image models distort
- jewelry or luxury goods where tiny details must be perfect
- any product with trademarks/claims that cannot be changed

---

## Input Contract

The kit should feel simple to start.

### Minimum input

```text
Product URL
```

### Optional inputs

- product image upload
- Shopify product URL
- Amazon product URL
- brand website URL
- Instagram/TikTok/Pinterest URLs
- target use case: PDP, launch, seasonal, email, Amazon, social
- desired visual direction
- restricted claims or compliance notes
- must-avoid visual styles
- model demographic requirements
- output aspect ratios

### Ideal user command

```text
Run Brand Shoot Kit for https://brand.com/products/product-name
```

or:

```text
Create a full AI product shoot for this Shopify product.
```

---

## Core Output

A complete shoot pack:

```text
/brand-shoot-output/{brand}/{product}/{date}/
  00-brand-analysis.md
  01-visual-gap-audit.md
  02-shoot-strategy.md
  03-shot-list.md
  04-generation-prompts.md
  05-qa-report.md
  06-export-map.md
  assets/
    pdp/
    lifestyle/
    model/
    seasonal/
    social/
    email/
    marketplace/
```

### Deliverables

1. **Brand analysis**  
   What the brand sells, who it is for, price tier, style, tone, colors, visual motifs, existing photography patterns.

2. **Visual gap audit**  
   What images are missing from the current product page and sales ecosystem.

3. **Shoot strategy**  
   The creative direction for the generated shoot.

4. **Shot list**  
   A structured asset plan across PDP, lifestyle, model, seasonal, social, and email.

5. **Generation prompts**  
   GPT Image 2-ready prompts for each asset, with product preservation instructions and negative constraints.

6. **Generated image set**  
   Actual images when model/API access is configured.

7. **QA report**  
   Pass/fail scoring for product accuracy, brand fit, realism, usefulness, and AI artifact risk.

8. **Export map**  
   Which assets go where: product page, email, social, marketplace, homepage, launch campaign.

---

## The Core Loop

```text
Scout → Diagnose → Plan → Generate → Judge → Reroll → Export → Remember
```

### 1. Scout

The agent pulls the website/product page/socials and extracts context.

### 2. Diagnose

The agent identifies what the current visual system already has and what it lacks.

### 3. Plan

The agent creates a shoot strategy and shot list.

### 4. Generate

The agent builds prompts and sends them to GPT Image 2 or the configured image model.

### 5. Judge

The agent reviews outputs against a commerce-specific rubric.

### 6. Reroll

Failed assets get rewritten prompts and regenerated.

### 7. Export

The agent organizes final assets by channel and use case.

### 8. Remember

The agent writes brand/product learnings so future shoots improve.

---

## Agent Architecture

### 1. Brand Scout

**Job:** Understand the brand before any image generation happens.

**Inputs:** Product URL, brand URL, optional social links  
**Outputs:** `00-brand-analysis.md`

Extracts:

- product name
- category
- price point
- audience
- use cases
- ingredients/materials/features
- brand tone
- color palette
- current image style
- trust signals
- claims and benefits
- visual motifs
- social proof patterns
- packaging constraints

Should answer:

- What does this brand want to feel like?
- What kind of buyer is it trying to attract?
- Is it premium, playful, clinical, founder-led, earthy, bold, minimalist, etc.?
- What visual world already exists?

**Anti-patterns:**

- Do not hallucinate brand values from nothing.
- Do not overfit to a single page section.
- Do not treat generic Shopify copy as deep brand truth.
- Do not scrape private or gated content.

---

### 2. Product Analyst

**Job:** Understand the product as a physical object.

**Inputs:** Product images from page or uploaded image  
**Outputs:** Product constraints section in `00-brand-analysis.md`

Extracts:

- object type
- material
- shape
- color
- packaging
- logo placement
- label constraints
- visible text
- size/scale clues
- must-preserve details
- likely distortion risks

Must produce a **Product Preservation Brief**:

```markdown
## Product Preservation Brief
- Product type:
- Must preserve:
- Can vary:
- Never change:
- Distortion risks:
- Accuracy confidence:
```

**Anti-patterns:**

- Do not generate new packaging claims.
- Do not alter label text unless explicitly requested.
- Do not invent product variants.
- Do not make the product look materially more premium than reality unless labeled as concept-only.

---

### 3. Visual Gap Finder

**Job:** Identify what visual assets the brand needs.

**Inputs:** Existing product page images + brand analysis  
**Outputs:** `01-visual-gap-audit.md`

Checks for:

- clean hero product shot
- white / neutral background image
- product scale/context shot
- in-use lifestyle shot
- model holding/using product
- detail / texture / ingredient shot
- benefit visualization
- bundle/group shot
- before/after or comparison visual
- social crop
- email hero
- seasonal/campaign visual
- marketplace-compliant image

Classifies each as:

- present and strong
- present but weak
- missing
- not relevant

Example output:

```markdown
## Visual Gap Audit

| Asset Type | Status | Notes | Priority |
|---|---|---|---|
| PDP hero | Present but weak | Product visible but lighting feels flat | High |
| Model/in-use | Missing | No human context for scale or usage | High |
| Detail shot | Missing | Texture/material not shown | Medium |
| Seasonal set | Missing | Good opportunity for Q4/email | Low |
```

**Anti-patterns:**

- Do not recommend every possible asset for every product.
- Do not bloat the shot list.
- Prioritize what would actually improve the commerce experience.

---

### 4. Shoot Director

**Job:** Create the creative direction for the shoot.

**Inputs:** Brand analysis + visual gap audit  
**Outputs:** `02-shoot-strategy.md`

Produces:

- shoot concept
- visual world
- lighting style
- background/set direction
- prop language
- model usage guidance
- moodboard words
- photography references in plain language
- color system
- channel priorities

Should create 2-3 possible directions, then recommend one.

Example directions:

1. **Clean Commerce** — crisp, bright, PDP-first, marketplace-safe
2. **Editorial Lifestyle** — premium, magazine-like, emotional context
3. **Social Native** — phone-shot, creator-style, real-life use

Then choose:

```markdown
## Recommended Direction
Use Editorial Lifestyle as the primary shoot world, with Clean Commerce exports for PDP and marketplace use.
```

**Anti-patterns:**

- Do not produce vague style words like “modern and clean” without specifics.
- Do not choose a visual world that conflicts with the brand’s price point.
- Do not make every brand look like Apple, Glossier, or Aesop.

---

### 5. Shot List Builder

**Job:** Convert strategy into a production-ready shot list.

**Inputs:** Shoot strategy  
**Outputs:** `03-shot-list.md`

Each shot includes:

- shot name
- asset category
- goal
- scene description
- product treatment
- model/hand requirements
- props/set
- aspect ratios
- channel use
- priority
- generation difficulty

Shot categories:

#### PDP / Commerce

- hero product shot
- clean background shot
- alternate angle
- scale/context shot
- texture/detail shot
- bundle/group shot
- benefit visual

#### Lifestyle

- product in environment
- product being used
- morning/evening routine
- travel/work/gym/kitchen/bathroom scene
- social proof visual

#### Model / Human

- hand holding product
- model applying/using product
- body crop/no-face option
- founder/creator-style usage
- demographic-specific variants

#### Campaign / Seasonal

- holiday set
- summer set
- launch hero
- gifting scene
- limited-time theme

#### Channel Outputs

- email hero
- homepage banner
- social square
- social vertical
- marketplace-safe image

**Default shot pack:**

```text
12 core shots
- 3 PDP images
- 3 lifestyle images
- 2 model/in-use images
- 2 social crops
- 1 email/homepage hero
- 1 seasonal/campaign image
```

**Anti-patterns:**

- Do not generate a 50-shot monster plan by default.
- Do not include model shots when product/category makes them unnecessary.
- Do not force seasonal shots if the brand has no seasonal use case.

---

### 6. Casting Agent

**Job:** Define model/human presence without drifting into fake influencer sludge.

**Inputs:** Brand analysis + shot list  
**Outputs:** Casting notes embedded in `03-shot-list.md`

Guides:

- demographic range
- wardrobe
- body/hand framing
- pose
- expression
- usage moment
- environment fit
- whether face should be visible

Default bias:

- Prefer hands/body crops over full synthetic faces unless the use case requires a face.
- Use believable, understated model direction.
- Keep product primary.

**Anti-patterns:**

- No uncanny perfect models.
- No fake influencer glamour unless the brand explicitly calls for it.
- No demographic stereotyping.
- No unrealistic body/skin/age assumptions.

---

### 7. Set Designer

**Job:** Build believable environments around the product.

**Inputs:** Brand world + shot list  
**Outputs:** Set details in prompts

Set types:

- bathroom counter
- kitchen island
- gym bag / locker
- bedside table
- office desk
- beach towel
- backpack/travel pouch
- fridge/pantry
- nursery
- pet/home environment
- clean studio sweep
- premium editorial set
- holiday/gifting table

Set design includes:

- surface material
- background depth
- props
- lighting
- color relationships
- clutter level
- camera distance

**Anti-patterns:**

- Do not add random props.
- Do not make scenes look like stock-photo sets.
- Do not let props compete with the product.
- Do not use impossible product scale.

---

### 8. Prompt Producer

**Job:** Convert each shot into a generation-ready prompt.

**Inputs:** Shot list + product preservation brief  
**Outputs:** `04-generation-prompts.md`

Each prompt includes:

```markdown
## Shot 01 — {Name}

**Use case:** PDP / Lifestyle / Social / Email
**Aspect ratio:** 1:1, 4:5, 16:9, etc.
**Reference image:** {source product image}

**Prompt:**
[Full GPT Image 2 prompt]

**Product preservation rules:**
- Keep exact product shape, color, label placement, and visible logo.
- Do not change packaging text.
- Do not invent new claims.

**Negative constraints:**
- no distorted label
- no extra logos
- no unreadable text
- no extra product variants
- no fake badges
- no malformed hands

**Reroll instruction if failed:**
[Specific correction]
```

Prompt design must be operational, not pretty.

The prompt should specify:

- composition
- subject placement
- product treatment
- camera angle
- lens/lighting only when useful
- set/background
- model/hand position
- typography/text rules if any
- brand consistency rules
- negative constraints

**Anti-patterns:**

- Do not overstuff prompts with cinematic nonsense.
- Do not use famous artist names as a crutch.
- Do not rely on vibes when product accuracy matters.
- Do not include unsupported claims in generated image text.

---

### 9. Image Generator

**Job:** Generate assets through configured provider.

**Primary:** GPT Image 2 / OpenAI image generation  
**Fallbacks:** Gemini image, Replicate/Nano Banana, other configured providers

Generation modes:

1. **Prompt-only concepting** — no API keys required; produces prompts and plans.
2. **Reference-guided generation** — product image supplied; attempts product preservation.
3. **Edit mode** — modifies or places product image into new scenes where supported.
4. **Batch mode** — generates a full shot pack.

The system should degrade gracefully:

- If no image API key exists, produce the shoot plan and prompts.
- If social scraping fails, use website-only brand analysis.
- If product images cannot be downloaded, ask for upload or provide manual fallback.

---

### 10. Photo Editor QA

**Job:** Reject bad images before the user sees a polished-looking failure.

**Outputs:** `05-qa-report.md`

Rubric:

| Criterion | Weight | What it checks |
|---|---:|---|
| Product accuracy | 30 | Shape, label, color, scale, packaging fidelity |
| Commerce usefulness | 20 | Does this help sell or explain the product? |
| Brand fit | 15 | Matches extracted brand world |
| Scene realism | 15 | Believable lighting, setting, model, hands |
| Visual clarity | 10 | Product is visible and not visually buried |
| AI artifact risk | 10 | Distortions, fake text, uncanny details |

Pass thresholds:

- **85+**: approve
- **70-84**: usable with caution / optional reroll
- **50-69**: reroll
- **<50**: reject and rewrite prompt

Automatic rejection triggers:

- product label changed
- product shape materially changed
- wrong number of products
- fake certification/claim added
- unreadable key text
- deformed hand touching product
- product not visible enough
- category mismatch

**Anti-patterns:**

- Do not praise every output.
- Do not let “pretty” override product accuracy.
- Do not pass images that would create customer confusion.

---

### 11. Export Mapper

**Job:** Organize final images by practical use.

**Outputs:** `06-export-map.md`

Maps assets to:

- Shopify PDP gallery
- Amazon / marketplace listing
- homepage hero
- collection page tile
- email hero
- abandoned cart email
- launch announcement
- Instagram feed
- Instagram story
- TikTok cover
- Pinterest pin
- paid creative export folder — optional, not core positioning

Example:

```markdown
## Recommended Placement

| Asset | Best Use | Why |
|---|---|---|
| 01-clean-hero.png | PDP image 1 | Clear product visibility |
| 04-model-hand.png | PDP image 3 / social | Adds scale and human context |
| 08-seasonal-gift.png | Email hero | Strong campaign context |
```

---

### 12. Creative Memory

**Job:** Store brand/product learnings for future shoots.

Writes:

```text
workspace/brand/visual-profile.md
workspace/brand/product-shot-memory.md
workspace/brand/assets.md
```

Stores:

- approved visual worlds
- rejected visual worlds
- product preservation rules
- preferred model direction
- prompt fragments that worked
- prompt fragments that failed
- QA notes
- output performance if later supplied

This is what makes the kit compound.

---

## File Architecture

Recommended repo:

```text
brand-shoot-kit/
  README.md
  SPEC.md
  PLAN.md
  VERSION
  .env.example
  openclaw.example.json
  install.sh
  uninstall.sh
  doctor.sh
  skills/
    brand-shoot/
      SKILL.md
      references/
        visual-gap-rubric.md
        product-preservation.md
        ecommerce-shot-taxonomy.md
        set-design-patterns.md
        model-casting-guide.md
        qa-rubric.md
        prompt-patterns.md
      scripts/
        scout-url.sh
        extract-product-images.sh
        analyze-brand.mjs
        generate-shot-list.mjs
        qa-images.mjs
        export-pack.mjs
      assets/
        shot-list-template.md
        brand-analysis-template.md
        qa-report-template.md
        export-map-template.md
  evals/
    trigger-evals.md
    execution-evals.md
    output-quality-rubric.md
  examples/
    skincare-brand/
    supplement-brand/
    coffee-brand/
    home-goods-brand/
```

---

## Skill Trigger Description

```yaml
name: brand-shoot
description: "Create a brand-aware AI product shoot from a product URL, product page, or uploaded product image. Use for e-commerce photography, PDP image planning, lifestyle/model/product scene generation, visual gap audits, and AI photoshoot packs. Do not use for ad spy research, competitor ad analysis, or paid creative intelligence; route those to StealAds-style workflows."
metadata:
  openclaw:
    emoji: "📸"
    user-invocable: true
    requires:
      bins: ["node"]
      env: []
```

Optional env:

```text
OPENAI_API_KEY            # GPT Image 2 / image generation
GOOGLE_AI_API_KEY         # fallback image generation / vision analysis
FIRECRAWL_API_KEY         # better website extraction
APIFY_API_TOKEN           # optional social scraping
REPLICATE_API_TOKEN       # fallback/reference image workflows
```

No env should be strictly required for the planning-only mode.

---

## Core SKILL.md Behavior

The skill should not act like a generic prompt writer.

It should act like an e-commerce creative director.

### Required sequence

1. Intake product URL/image
2. Analyze brand and product
3. Identify visual gaps
4. Recommend shoot direction
5. Build shot list
6. Generate prompts
7. Generate images if configured
8. QA outputs
9. Export organized pack
10. Write visual memory

### Default output if image generation is unavailable

A complete planning pack:

- brand analysis
- visual gap audit
- recommended shoot strategy
- 12-shot list
- generation prompts
- QA checklist
- export map

This still has value and makes the skill usable without API setup.

---

## MVP Scope

The MVP should ship as a useful planning + prompt-generation kit before full automation.

### MVP must do

- accept product URL
- fetch/extract page text and image URLs
- create brand analysis
- create product preservation brief
- create visual gap audit
- create 12-shot list
- create GPT Image 2-ready prompts
- create QA rubric/report template
- create export map
- save outputs to workspace folder
- include examples and evals
- include install/doctor scripts

### MVP should optionally do

- download product images
- call image generation API
- run vision QA on outputs
- package final assets into folders

### MVP should not do yet

- fully automate Shopify upload
- edit live product pages
- create paid ad campaigns
- analyze competitor ads
- promise exact product fidelity for all categories
- run external social scraping without clear user-provided URLs/config

---

## V1 Scope

V1 should become an actual production workflow.

### V1 adds

- product image extraction and reference selection
- GPT Image 2 generation integration
- batch generation for shot lists
- automatic reroll instructions
- QA scoring using vision model
- output folder organization
- brand visual memory
- social URL analysis where available
- multiple shot pack presets

### Shot pack presets

```text
starter-pack        8 images
standard-shoot      12 images
launch-pack         20 images
seasonal-pack       12 images
marketplace-pack    8 images
social-pack         10 images
```

---

## V2 Scope

V2 can become the serious commerce visual system.

### V2 adds

- Shopify product page integration
- marketplace compliance checks
- A/B asset variants
- performance feedback memory
- competitor category photography analysis — not ad analysis
- automatic product page gallery recommendations
- background removal / compositing workflows
- image editing pipeline for real product cutouts
- human approval queue
- team/client-ready PDF or HTML shoot deck

---

## Example Run

User:

```text
Run Brand Shoot Kit for https://example.com/products/hydrating-face-serum
```

Agent:

```text
BRAND SHOOT KIT
Product: Hydrating Face Serum
Brand: Example Skin
Mode: Planning + Generation

Brand read:
- Premium but approachable skincare
- Minimal cream/green palette
- Audience: women 28-45, ingredient-aware, sensitive-skin concerns
- Current PDP has clean pack shots but weak lifestyle context

Visual gaps:
1. No model/in-use application shot
2. No texture detail shot
3. No bathroom counter lifestyle scene
4. No scale/context shot
5. No seasonal/gifting image

Recommended shoot direction:
"Quiet Clinical Luxury" — warm bathroom light, clean stone surfaces, soft towels, subtle botanicals, human hands only, no fake dermatologist claims.

Shot pack:
12 images generated / planned
- 3 PDP
- 3 lifestyle
- 2 model/in-use
- 2 social
- 1 email hero
- 1 seasonal

QA:
8 approved
3 reroll recommended
1 rejected due to label distortion
```

---

## Newsletter Story

### Strong framing

> I’m building an AI product shoot agent.

Not an image prompt pack.
Not another AI art demo.

A real agent that can study a product page, understand the brand, find the missing shots, and build a complete product photography library.

### Hook draft

Every e-commerce brand has the same problem:

They need more product visuals than they can afford to shoot.

Product page images. Lifestyle shots. Model shots. Seasonal assets. Email headers. Social crops. Marketplace images.

The product might not change, but the context has to change constantly.

So this week I’m building an agent that starts where a real creative director starts: by studying the brand.

You give it a product URL. It pulls the site, analyzes the visual identity, finds what the product page is missing, creates a shoot plan, generates the assets, and QA-checks the results.

That is the part people miss about GPT Image 2.

The breakthrough is not prettier images.

The breakthrough is that image generation is finally good enough to become part of a production loop.

### Subject lines

- I’m building an AI product shoot agent
- Paste a product URL. Get a full brand shoot.
- GPT Image 2 just made product shoots weird
- The AI photoshoot agent I wanted to exist
- I’m replacing the product shoot planning process

---

## Naming Directions

The current name is not final. The name needs to feel sharper than “Product Photo Kit.”

### Best current candidates

#### 1. ShootScout

Pros:
- active, agentic, memorable
- captures the scrape/analyze/planning step
- not limited to image generation

Cons:
- less immediately obvious than Product Photo Kit

Tagline:

> ShootScout studies your brand and builds the product shoot you should have run.

#### 2. Brand Shoot Kit

Pros:
- clear
- aligned with kit naming
- broad enough for product, lifestyle, model, seasonal

Cons:
- less distinctive

Tagline:

> Paste a product URL. Get a full brand shoot.

#### 3. Virtual Shoot Kit

Pros:
- intuitive
- easy newsletter headline
- explains the core promise fast

Cons:
- sounds slightly generic

Tagline:

> Your AI creative director for product shoots.

#### 4. Catalog Studio

Pros:
- commerce-specific
- sounds polished

Cons:
- may feel too static/PDP-focused

Tagline:

> Turn one product page into a complete commerce image library.

#### 5. Ghost Studio

Pros:
- cool, memorable
- implies invisible production studio

Cons:
- less clear; may need explanation

Tagline:

> A product studio without the studio.

### Recommendation

For the newsletter, use the plain-English promise:

> I’m building an AI product shoot agent.

For the repo, use a practical name until a better brand emerges:

> `brand-shoot-kit`

If we want a more branded public name later, `ShootScout` is the strongest candidate.

---

## Quality Bar

This kit is good only if it feels like a real operator system.

It must not feel like:

- a list of prompts
- a generic AI image wrapper
- a moodboard generator
- a Canva substitute
- a toy demo

It must feel like:

- a creative director
- an e-commerce merchandiser
- a product photographer
- a set designer
- a QA editor
- an asset production workflow

### Success criteria

A user should be able to paste one product URL and receive:

1. a brand-aware visual read
2. a useful diagnosis of missing commerce images
3. a specific shoot direction
4. a practical shot list
5. prompts that produce better images than generic prompting
6. QA that catches bad product distortions
7. a folder of assets organized by use case
8. memory that makes the next shoot better

---

## Build Plan

### Phase 0 — Naming + Positioning Lock

**Goal:** Decide public framing before building too much around the wrong name.

Tasks:

- Choose working repo name: `brand-shoot-kit`
- Keep public headline: “AI product shoot agent”
- Decide whether `ShootScout` is the branded name
- Write README opening in Matt’s style
- Define explicit StealAds boundary

Exit criteria:

- One-line promise is locked
- README hero section is strong
- No confusion with ad creative tooling

---

### Phase 1 — Repo Scaffold

**Goal:** Create a shippable kit structure that passes BigSkills standards.

Tasks:

- Create repo/folder structure
- Add README.md
- Add SPEC.md
- Add VERSION
- Add `.env.example`
- Add `openclaw.example.json`
- Add `install.sh`
- Add `uninstall.sh`
- Add `doctor.sh`
- Add eval files
- Add examples folder

Exit criteria:

- `doctor.sh` runs
- install path works
- required files exist
- skill can be loaded by OpenClaw

---

### Phase 2 — Core Skill

**Goal:** Make the skill behavior strong before writing too many scripts.

Tasks:

- Write `skills/brand-shoot/SKILL.md`
- Include core workflow
- Include anti-patterns
- Include product preservation rules
- Include visual gap rubric
- Include output contract
- Include planning-only fallback
- Add before/after example showing weak prompt vs Brand Shoot Kit prompt

Exit criteria:

- Skill materially improves output vs vanilla model
- It behaves like a commerce creative director, not a prompt generator
- It produces a full planning pack from a product URL

---

### Phase 3 — References + Rubrics

**Goal:** Move depth out of SKILL.md into reusable references.

Files:

- `references/visual-gap-rubric.md`
- `references/product-preservation.md`
- `references/ecommerce-shot-taxonomy.md`
- `references/set-design-patterns.md`
- `references/model-casting-guide.md`
- `references/qa-rubric.md`
- `references/prompt-patterns.md`

Exit criteria:

- Core stays lean
- References carry domain depth
- Agent has enough taste calibration to avoid generic outputs

---

### Phase 4 — URL Scout MVP

**Goal:** Pull enough website context to make the kit feel magic.

Script:

```text
scripts/scout-url.sh
```

Responsibilities:

- fetch product page
- extract title, meta description, headings, product copy
- extract image URLs
- identify likely product images
- save raw extraction JSON/markdown

Implementation options:

- simple `curl`/Node fetch first
- optional Firecrawl when configured
- optional social extraction later

Exit criteria:

- Given a normal Shopify product URL, returns usable text + image candidates
- Fails gracefully with clear manual fallback

---

### Phase 5 — Planning Pack Generator

**Goal:** Generate the full non-image output reliably.

Scripts:

- `analyze-brand.mjs`
- `generate-shot-list.mjs`

Outputs:

- `00-brand-analysis.md`
- `01-visual-gap-audit.md`
- `02-shoot-strategy.md`
- `03-shot-list.md`
- `04-generation-prompts.md`
- `06-export-map.md`

Exit criteria:

- One product URL creates a complete shoot plan
- Output is useful even without image API access
- Shot list is not bloated

---

### Phase 6 — Image Generation Integration

**Goal:** Generate first actual assets.

Tasks:

- integrate GPT Image 2 via OpenAI image API/tooling
- support reference image input where possible
- generate batch from selected shots
- save assets by category
- capture prompt + settings metadata

Exit criteria:

- Generate at least 8 images from one product URL/upload
- Save prompt metadata with every image
- Preserve product acceptably on simple product categories

---

### Phase 7 — QA + Reroll Loop

**Goal:** Make outputs trustworthy.

Script:

```text
scripts/qa-images.mjs
```

Tasks:

- score generated images with vision model or manual checklist
- identify rejection triggers
- create reroll instructions
- optionally regenerate failed shots
- produce `05-qa-report.md`

Exit criteria:

- QA catches label distortion/product mismatch
- Bad images are not presented as final wins
- Reroll prompts are specific, not generic

---

### Phase 8 — Example Packs

**Goal:** Make the repo feel real and demo-ready.

Create examples for:

1. skincare serum
2. supplement bottle
3. coffee bag
4. home goods product

Each example includes:

- source URL or mock page
- brand analysis
- visual gap audit
- shot list
- prompts
- generated assets if available
- QA report

Exit criteria:

- README can show concrete examples
- Newsletter can use one compelling demo
- The examples prove the kit is not theoretical

---

### Phase 9 — Public README + Launch Polish

**Goal:** Make it as strong as prior kits.

README structure:

1. Hero promise
2. What it does
3. Why this exists
4. What a real run looks like
5. Quick start
6. The agent loop
7. Skills/modules
8. Output examples
9. Requirements
10. Setup
11. Roadmap
12. Boundaries / limitations
13. License

Exit criteria:

- README reads like a product, not documentation
- First 200 words sell the idea
- Quick start works
- No overclaims

---

### Phase 10 — BigSkills Quality Gate

**Goal:** Ensure this meets the standard of the best kits.

Checklist:

- [ ] README has strong narrative and concrete quick start
- [ ] SKILL.md changes behavior vs vanilla model
- [ ] Install/doctor/uninstall exist and run
- [ ] `.env.example` explains optional capabilities
- [ ] `openclaw.example.json` included
- [ ] Trigger evals include should/should-not examples
- [ ] Execution evals include at least 3 benchmark product categories
- [ ] Doctor checks file presence and dependency basics
- [ ] Examples are realistic
- [ ] StealAds boundary is explicit
- [ ] Planning-only mode works without paid APIs
- [ ] Product accuracy warnings are honest

---

## Execution Evals

### Eval 1 — Skincare PDP

Input:

```text
Create a brand shoot for a premium hydrating face serum product page.
```

Expected:

- identifies skincare-specific shot needs
- avoids medical claims
- includes texture/detail shot
- includes bathroom/vanity lifestyle scene
- prefers hands/application over fake model glamour
- product preservation warning for label accuracy

### Eval 2 — Supplement Bottle

Input:

```text
Create a product shoot for a daily greens supplement.
```

Expected:

- includes kitchen/morning routine context
- avoids unsupported health claims
- includes scoop/mixing/use scene
- includes marketplace-safe hero
- warns about label/claim preservation

### Eval 3 — Coffee Bag

Input:

```text
Create a launch shoot for a premium coffee bag.
```

Expected:

- includes bag hero, beans/detail, brewing lifestyle, kitchen counter
- includes gifting/seasonal optional shot
- uses warm editorial visual world
- does not invent origin/certification claims

### Eval 4 — Bad Fit Product

Input:

```text
Create a brand shoot for a precision industrial valve with exact technical labeling.
```

Expected:

- warns about product fidelity risk
- recommends planning/prompt pack over final production assets
- suggests real CAD/product photography if exact dimensions matter

---

## Trigger Evals

### Should trigger

- “Create a full AI product shoot from this Shopify URL”
- “Generate PDP and lifestyle images for this product”
- “Audit this product page’s photography gaps”
- “Turn this product photo into a model/lifestyle shoot”
- “Build an AI photoshoot plan for this e-commerce brand”

### Should not trigger

- “Find winning ads from this competitor” → StealAds
- “Analyze Meta ad performance” → Meta Ads Kit
- “Write product page copy” → CRO/copy skill
- “Generate SEO images for this blog post” → SEO images skill
- “Make a random fantasy image” → generic image generation

---

## Risks + Mitigations

### Risk: Product distortion

Mitigation:

- product preservation brief
- reference image use
- QA rejection triggers
- honest disclaimers
- planning-only fallback for high-accuracy products

### Risk: Generic AI aesthetic

Mitigation:

- brand scout
- visual gap audit
- set-design reference library
- anti-slop QA rubric

### Risk: Too close to StealAds

Mitigation:

- no ad intelligence language
- no competitor ad analysis
- product photography and e-commerce asset positioning
- paid ad exports only as secondary repurposing

### Risk: Social scraping complexity

Mitigation:

- website-first MVP
- social URL optional
- manual paste/upload fallback

### Risk: Overbuilding before demo

Mitigation:

- MVP starts with planning pack and prompts
- one killer example before broad automation
- only add image generation after planning output is strong

---

## The Killer Demo

Use one plain product page with mediocre visuals.

Show:

1. Original product page screenshot
2. Brand analysis
3. Visual gap audit
4. Recommended shoot direction
5. 12-shot list
6. Before: “generic AI product prompt”
7. After: Brand Shoot Kit prompts
8. Generated image grid
9. QA report showing accepted/rejected/rerolled images
10. Export map showing where each asset goes

The visual story:

> One product URL became a complete brand shoot.

That is the headline.

---

## Final Recommendation

Build this as `brand-shoot-kit` with the public story:

> I’m building an AI product shoot agent.

Keep the first version brutally focused:

- one product URL
- brand analysis
- visual gap audit
- 12-shot shoot plan
- GPT Image 2 prompts
- optional generation
- QA report

Do not start with Shopify upload, paid ads, or complex social scraping.

The thing that will make this feel like a Big Players kit is the loop:

```text
Scout → Diagnose → Plan → Generate → Judge → Export → Remember
```

That is the product.
