# Vedic Astrology Intelligence Platform: Technical & Capability Documentation

The Horoscope application is a full-stack intelligence platform built to merge the rigorous, traditional rules of Vedic Astrology (Brihad Parashara Hora Shastra - BPHS) with modern conversational AI. 

Unlike typical "AI Astrology" tools that ask the LLM to calculate planetary math (which LLMs are notoriously bad at), this platform splits the architecture into three strict layers:
1. **Deterministic Calculation Engine**: Exact mathematical positioning powered by the Swiss Ephemeris.
2. **Astrological Logic Engine**: BPHS rules for Dasha timelines, Yogas, Divisional Charts, and Temporal Scoring.
3. **Conversational AI Agent**: An LLM strictly confined to reading the pre-calculated structured JSON to deliver human-like compassion and synthesis, without ever performing math.

---

## 1. Capabilities & Output

The application accepts user birth details (Date, Time, Location) and generates:
- **Natal Charts:** The primary Lagna chart (D1) and key divisional charts like Navamsa (D9) and Dashamsa (D10).
- **Vimshottari Dasha Timeline:** Life-long planetary periods.
- **Yoga Detection:** Detection of classical planetary combinations (e.g., Gajakesari Yoga, Ruchaka Yoga).
- **Temporal Forecast:** A month-by-month predictive breakdown evaluating Opportunity, Risk, and Intensity. 
- **Conversational Agent:** An AI chatbot where users can ask temporal questions ("How does my career look next year?") and receive personalized text interpretations.

---

## 2. Core Astrological Calculations

All foundational math is handled by the backend's `engine/` module, ensuring scientific precision.

### A. Ephemeris Engine (`engine/ephemeris.py`)
- **Library:** `swisseph` (Swiss Ephemeris), the industry standard for astronomical accuracy.
- **Ayanamsa:** Fixed to Lahiri (Chitra Paksha) for traditional Vedic sidereal calculations (`swe.SIDM_LAHIRI`).
- **Positions:** Calculates exact longitudinal positions for the Ascendant (Lagna) and 9 planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, and Ketu). Rahu and Ketu are computed as "True Nodes".
- **House System:** Uses the Whole Sign House (Bhav) system starting relative to the Ascendant sign.
- **Zodiac & Nakshatra Mapping:** Maps the 360° celestial span into 12 Zodiac signs (30° each) and 27 Nakshatras (13° 20' each) with 4 padas per Nakshatra. Calculates the reigning Nakshatra Lord for all 27 stars.

### B. Divisional Charts (Varga) (`engine/divisional.py`)
Mathematical extensions of the D1 chart:
- **Navamsa (D9):** Critical for marriage and inner strength. Calculated by dividing each 30° sign into 9 parts of 3°20'.
- **Dashamsa (D10):** Analyzes career and profession. Calculated by dividing each sign into 10 parts of 3° each. Odd/Even sign logic directs the starting point.

### C. Vimshottari Dasha Timeline (`engine/dasha.py`)
- **Concept:** A 120-year progressing timeline of planetary rulerships triggered by the exact degree of the Moon at birth.
- **Calculation:** Computes the fractional elapsed time of the Moon's birth Nakshatra to determine the starting point of the current Mahadasha (major ruler).
- **Sub-periods:** Mathematically computes Antardashas (sub-rulers) by proportionally applying the 120-year ratios to the Mahadasha span.

### D. Yoga Detection (`engine/yoga.py`)
- Programmatically scans the calculated chart for classic Parashari Yogas (e.g., "Mutual Reception", "Pancha Mahapurusha Yogas" like Ruchaka, Bhadra, Hamsa, Malavya, and Shasha).
- Determines if conditions are met across houses, sign rulerships, exaltations, and Kendra positions (houses 1, 4, 7, 10).
- **Nakshatra Yogas:** Detects subtle but highly powerful Nakshatra-level alignments, including Nakshatra Parivartana (mutual exchange of Nakshatra Lords) and Nakshatra Raj Yogas.

---

## 3. Temporal Scoring & Period Analysis

The system generates month-by-month forward mathematical predictions using `temporal/period_analysis.py` and `scoring/scorer.py`.

- **Transit Overlays:** Uses the Swiss Ephemeris to calculate where planets transit during a future month and overlays them against the Natal Chart (from Ascendant and Natal Moon). Returns both the transiting Sign and the exact transiting Nakshatra.
- **Dasha Activations:** Looks up which Mahadasha and Antardasha are actively ruling during that month.
- **Event Scoring:** Computes quantitative values (0 to 10) for Opportunity, Risk, and Overall Intensity:
  - It weights transits of major slow-moving planets (Jupiter, Saturn, Nodes) heavier than fast-moving inner planets.
  - Benefic transits through favorable houses (e.g., Jupiter in 11th) increase the Opportunity Score.
  - Malefic transits through unfavorable houses (e.g., Saturn in 8th) increase the Risk Score.
  - **Tara Bala (Navatara) Scoring:** Dynamically overlays the 9-star cycle counting from the birth Moon's Nakshatra. Transit scores are boosted for favorable stars (*Sampat*, *Sadhaka*, *Mitra*) and penalized for unfavorable stars (*Vipat*, *Pratyari*, *Naidhana*).
- **Domain Focus:** Scores are isolated based on domains (e.g., Career looks at 10th house, Marriage looks at 7th house).
- **High Significance Windows:** Flags specific months where `intensity_index` passes a predefined threshold. 

---

## 4. LLM AI Agent Implementation

The "Conversational Ask Agent" (`temporal/agent.py`) provides human-readable context to the mathematical scores.

### Critical Safety & Architecture Rules
The system explicitly prevents "hallucinations" common when prompting LLMs with raw birth data.
1. The LLM gets **No Math Duties**: It does not see birth coordinates and is explicitly forbidden from calculating transits, dashas, or chart positions.
2. **Context Passing:** The LLM prompt is injected with the strictly calculated JSON output from the deterministic Engine. It only sees a "pre-solved" state. Example of data parsed to LLM:
   * "User has Ascendant Leo with Mars in 10th House."
   * "In March 2027, User is in Jupiter Mahadasha. The Intensity Index is 8/10. Opportunity is High."
3. **Intent Detection:** Before reaching the LLM, the backend uses RegEx to parse the user's string (e.g., "Will I get married next year?") to extract the Domain ("marriage") and Timeframe ("next 12 months"). The backend computes the scoring for that exact timeframe and feeds ONLY the results to the LLM.

### LLM Prompt Structure
The System Prompt enforces a wise, compassionate persona while instilling strict safety guidelines:
> "Never claim inevitability. Use language like 'tendency', 'theme', 'window of heightened activity'... Never make definitive health or legal predictions."

The User Prompt builds a highly structured context document tracking exact placements over time:
```text
=== NATAL CHART SUMMARY ===
Ascendant: Taurus (Rohini 2)
Planets: Sun in Aries (House 12, Nakshatra: Ashwini)...

=== ACTIVE DASHAS BY MONTH ===
  Jan 2026: Saturn-Moon | Intensity 7.2/10 | Houses: [1, 5, 9] | Transits: Jupiter in Gemini (Punarvasu)...
...
```

The LLM integrates this data to craft comforting, analytical paragraphs—connecting the numeric `opportunity_index` with narrative astrological meaning drawn from House, Sign, and Nakshatra themes.

---

## 5. Karmic Cycles Engine (`engine/karmic_cycles.py`, `temporal/karmic_timeline.py`)

A deterministic engine built to track multi-year, long-term astrological cycles that represent major life maturity milestones. These calculations give the dashboard and LLM context regarding long-duration pressures or expansion.

- **Sade Sati:** Detects the 7.5-year transit of Saturn traversing the 12th, 1st, and 2nd houses from the Natal Moon sign. Divides the tracking into Rising, Peak, and Setting phases.
- **Saturn Return:** Deterministically calculates when transiting Saturn returns to the exact longitude of Natal Saturn (~29.5 year interval), marking periods of structural maturity and karmic reckoning.
- **Jupiter Return:** Computes ~12 year intervals of Jupiter returning to its natal position, indicative of expansion and ideological growth.
- **Timeline Merging:** Aggregates these distinct cycles into a structured chronological timeline array and tracking metrics to be ingested by the `/karmic-cycles` API and optionally injected into the Conversational LLM context prompt (`=== KARMIC CYCLES ===`).

### Technology Stack
- **AI Backend API:** OpenAI GPT-4o (or configurable via `OPENAI_MODEL`).
- **Framework:** FastAPI Backend / Next.js Server Components.
- **Execution:** Cloud Run (Serverless Container).
