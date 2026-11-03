# BharatVoice (भारतवॉइस)

**Indian-Language Voice Intelligence Assistant for Small Grocery Shops (Kirana Stores)**

BharatVoice enables kirana storekeepers and grocery shop owners to capture spoken customer orders in Hindi and Hinglish, transcribe them with high accuracy via **Gnani AI Prisma**, parse them deterministically into structured grocery items, review and edit line items, enforce human confirmation, and generate spoken confirmations back in Hindi using **Gnani AI Timbre**.

---

## 1. System Architecture

BharatVoice is built as a clean, decoupled full-stack application:

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (SPA)                        │
│   React 18 + Vite + TypeScript + Tailwind CSS + Lucide      │
│                                                             │
│   - Voice Recorder (Web Audio API / MediaRecorder)          │
│   - Audio File Upload & Validation                          │
│   - Live Transcript Editor                                  │
│   - Structured Order Review & Line-Item Editing             │
│   - Explicit Human Confirmation Modal & Button              │
│   - Audio Player for Spoken Confirmation                    │
│   - Metrics & Order History Dashboard                       │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON / REST / Multipart Audio
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                      │
│   Python 3 + FastAPI + Pydantic + SQLAlchemy + SQLite       │
│                                                             │
│   - Audio Validation & Upload Handler                       │
│   - STT Client: Gnani Prisma (v3.0 / indic-auto)            │
│   - TTS Client: Gnani Timbre (v2.5 / Nalini)                │
│   - Catalogue-Based Deterministic Order Parser              │
│   - Human Confirmation State Machine Guard                  │
│   - SQLite Persistence via SQLAlchemy Models                │
│   - Development Mock Mode (with explicit headers & flags)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│  Gnani AI STT (Prisma v3)   │ │  Gnani AI TTS (Timbre v2.5) │
│  https://api.vachana.ai/    │ │  https://api.vachana.ai/    │
│  stt/v3                     │ │  api/v1/tts/inference       │
└─────────────────────────────┘ └─────────────────────────────┘
```

---

## 2. Core Workflow & Human Confirmation Policy

1. **Audio Capture**: The shopkeeper speaks an order or uploads an audio clip (up to 30 seconds, max 10MB; WAV, MP3, OGG, FLAC, M4A, WebM).
2. **Transcription**: The backend invokes Gnani Prisma STT (`POST https://api.vachana.ai/stt/v3`) using header `X-API-Key-ID: <API_KEY>`, `model=prisma-v3.0`, and `language_code=indic-auto`.
3. **Deterministic Parsing**:
   - Matches against an extensible Indian grocery catalogue (pulses, grains, dairy, spices, snacks, oils, vegetables).
   - Resolves Hindi & Hinglish numerals ("do", "dhai", "aadha", "ek", "tin", "paanch", etc.) and digits.
   - Normalizes metric units (`kg`, `g`, `litre`, `ml`, `packet`, `dozen`, `piece`).
   - Detects ambiguous quantities (e.g., "thoda namak" -> requests clarification).
   - Detects unrecognized items and flags them without guessing.
4. **Order Staging (Pending)**: The parsed order is persisted with `status: "pending"`.
   > **Critical Rule**: An order is **NEVER** automatically marked confirmed as a side effect of transcription or parsing.
5. **Review & Human Confirmation**: The shopkeeper inspects the transcription and line items, makes manual corrections if required, and clicks **Confirm Order**.
6. **Spoken Confirmation**: Upon confirmation, Gnani Timbre TTS (`POST https://api.vachana.ai/api/v1/tts/inference`) synthesizes a polite, Hindi audio receipt (e.g., *"Aapka order confirm ho gaya hai: 2 kilo atta aur 1 litre doodh. Dhanyawad!"*).
7. **Audio Playback**: The shopkeeper listens to the synthesized audio directly in the browser.

---

## 3. Technology Stack

- **Frontend**:
  - React 18, Vite, TypeScript
  - Tailwind CSS for responsive typography and layout
  - React Router for multi-page navigation
  - Lucide React icons
  - Native HTML5 Audio & MediaRecorder APIs
- **Backend**:
  - Python 3.11+
  - FastAPI (REST API framework)
  - Pydantic v2 (DTO validation & schemas)
  - SQLAlchemy 2.0 (ORM) with SQLite persistence
  - HTTPX / Requests for outbound API communication
  - Pytest for automated test suites
- **AI Services**:
  - **Speech-to-Text**: Gnani Prisma v3.0 (`https://api.vachana.ai/stt/v3`)
  - **Text-to-Speech**: Gnani Timbre v2.5 (`https://api.vachana.ai/api/v1/tts/inference`)
  - **Order Intelligence**: Deterministic rule- and catalogue-based multilingual parser

---

## 4. API Specification

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health status, version, and Gnani API connection mode (Real vs Mock) |
| `/api/stt/transcribe` | POST | Transcribe uploaded or recorded audio (multipart/form-data) |
| `/api/orders/parse` | POST | Parse transcript into structured grocery items with clarification flags |
| `/api/orders` | POST | Create a new pending order |
| `/api/orders` | GET | List orders with filtering (status, pagination, search) |
| `/api/orders/{order_id}` | GET | Retrieve a specific order by ID |
| `/api/orders/{order_id}` | PUT | Update order items or notes |
| `/api/orders/{order_id}/confirm` | POST | Explicitly confirm an order (triggers TTS audio generation) |
| `/api/tts/synthesize` | POST | Synthesize custom text into Hindi speech |
| `/api/dashboard/stats` | GET | Aggregated metrics: total orders, pending, confirmed, revenue estimate |

---

## 5. Development Phases

- **Phase 0**: Project Setup, Architecture Baseline, Documentation & Environment Specification *(Completed)*
- **Phase 1**: Backend Foundation (FastAPI, SQLite, SQLAlchemy models, Pydantic schemas, Health Check, Configuration) *(Completed)*
- **Phase 2**: Deterministic Hindi/Hinglish Catalogue & Order Parser with Clarification Logic & Automated Tests *(Completed)*
- **Phase 3**: Gnani AI Speech Integration (STT Prisma v3.0, TTS Timbre v2.5, Resilient HTTP Clients & Mock Fallbacks) *(Next)*
- **Phase 4**: Order Lifecycle & Confirmation API (CRUD, Strict Confirmation Guards, Spoken Receipt generation)
- **Phase 5**: Frontend Foundation (Vite + React + TypeScript + Tailwind CSS, App Layout, Routing, Theme)
- **Phase 6**: Audio Recording & Transcription UI (Browser Mic Recording, File Upload, Transcript Editing)
- **Phase 7**: Structured Order Review, Clarification, & Confirmation Flow (Editable Table, Explicit Confirmation Modal, Spoken Audio Player)
- **Phase 8**: Dashboard Analytics, Order History, Settings & Integration Testing
- **Phase 9**: Final Verification, Polishing, Automated Test Suite Execution, & Technical Demonstration Readiness

---

## 6. Catalogue & Deterministic Order Parser

BharatVoice incorporates a zero-hallucination, catalogue-driven NLP extraction engine designed specifically for everyday Kirana grocery interactions.

### 6.1 Supported Product Catalogue
Categories defined in `app/services/catalogue.py`:
- **Staples**: Atta (गेहूं का आटा), Rice (चावल, बासमती), Maida (मैदा), Suji (सूजी), Besan (बेसन), Eggs (अंडे)
- **Dairy**: Milk (दूध), Dahi (दही), Paneer (पनीर), Butter (मक्खन), Ghee (देसी घी)
- **Pulses**: Arhar / Toor Dal (अरहर दाल), Moong Dal (मूंग), Masoor Dal (मसूर), Chana Dal (चना), Rajma (राजमा), Chole (छोले)
- **Spices**: Salt (नमक), Haldi (हल्दी), Red Chilli Powder (लाल मिर्च), Coriander (धनिया पाउडर), Jeera (जीरा)
- **Oils**: Mustard Oil (सरसों का तेल), Refined Oil (रिफाइंड तेल), Sunflower Oil (सनफ्लावर तेल)
- **Household**: Soap (साबुन), Detergent (सर्फ, वाशिंग पाउडर), Dishwash (विम बार, बर्तन का साबुन)
- **Packaged Goods**: Biscuits (बिस्कुट), Bread (ब्रेड, डबल रोटी), Tea (चाय पत्ती), Sugar (चीनी, शक्कर), Noodles (मैगी)

### 6.2 Supported Quantities & Units
- **Spoken Numerals**: `ek` (1), `do` (2), `teen` (3), `chaar` (4), `paanch` (5), `chhah` (6), `saat` (7), `aath` (8), `nau` (9), `das` (10), `gyarah` (11), `barah` (12) and their Devanagari equivalents.
- **Fractions**: `aadha` / `aadhi` (0.5), `sawa` (1.25), `dedh` (1.5), `dhai` (2.5), `paune` (0.75).
- **Decimals & Integers**: Standard digits (`1`, `2`, `1.5`, `2.5`, `500`).
- **Units**: Weight (`kg`, `g`), Volume (`litre`, `ml`), Packaging / Count (`packet`, `piece`, `dozen`, `bottle`, `tin`, `tray`).

### 6.3 Ambiguity & Clarification Policies
The parser enforces strict Kirana safety rules:
1. **Missing Quantities**: Phrases like `"atta le aana"` prompt clarification rather than guessing a default.
2. **Vague Quantities**: Words like `"thoda namak"` or `"kuch biscuit"` trigger explicit clarification.
3. **Unsupported Products**: Terms absent from the catalogue (e.g., `"seb"`, `"amrood"`) are flagged in `unsupported_products` and hold the order in `needs_clarification`.
4. **Unit Safety**: Incompatible units (e.g., `"2 litre atta"`) or ambiguous bulk units are flagged for human clarification.
5. **Purity**: Parsing is a strictly stateless query that **NEVER** modifies the database or confirms an order.

### 6.4 API Usage: `POST /api/orders/parse`

**Request**:
```json
{
  "transcript": "Bhaiya, do kilo atta aur ek litre doodh bhej dena."
}
```

**Response (Ready for Review)**:
```json
{
  "items": [
    {
      "product_id": "atta",
      "name": "Atta",
      "quantity": 2.0,
      "unit": "kg",
      "unit_price": 45.0
    },
    {
      "product_id": "milk",
      "name": "Milk",
      "quantity": 1.0,
      "unit": "litre",
      "unit_price": 33.0
    }
  ],
  "status": "ready_for_review",
  "clarification_required": false,
  "clarification_message": null,
  "unsupported_products": []
}
```

**Response (Needs Clarification)**:
```json
{
  "items": [
    {
      "product_id": "atta",
      "name": "Atta",
      "quantity": 2.0,
      "unit": "kg",
      "unit_price": 45.0
    }
  ],
  "status": "needs_clarification",
  "clarification_required": true,
  "clarification_message": "Vague quantity 'thoda' for 'Salt'. Please specify an exact quantity (e.g. 1 kg or 1 packet).",
  "unsupported_products": []
}
```

### 6.5 Known Language Limitations
- Regional colloquial product aliases not listed in `_PRODUCTS` will be flagged as unsupported rather than guessed.
- Mathematical operations (e.g., "do kilo atta minus aadha kilo") are outside the grammar; customer must state net quantities.

---

## 7. Quick Start & Execution Guide (Windows / PowerShell)

### Prerequisites
- Python 3.11+
- Node.js 18+ (for upcoming frontend phases)

### Backend Setup

1. **Navigate to the backend directory**:
   ```powershell
   cd c:\Users\Asus\OneDrive\Desktop\Gen-AI\bharatvoice\backend
   ```

2. **Create and activate the virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional)**:
   By default, the backend loads settings from `.env.example` placeholders with mock mode enabled (`USE_MOCK_GNANI=true`). To customize, copy `.env.example`:
   ```powershell
   cp ..\.env.example .env
   ```

5. **Run automated test suite**:
   ```powershell
   pytest -v
   ```

6. **Start the FastAPI backend server**:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

7. **Verify health endpoint**:
   Open browser or run in PowerShell:
   ```powershell
   curl http://localhost:8000/api/health
   ```

