# 🚀 BOMIQ

> Intelligent BOM Automation Platform for Electronics Engineers

BOMIQ is a Python-based platform that automates the process of converting an engineering Bill of Materials (BOM) into a procurement-ready BOM by intelligently identifying electronic components, validating matches, estimating costs, and generating sourcing insights using the DigiKey API.

The goal of BOMIQ is to significantly reduce the manual engineering effort involved in component sourcing while improving accuracy and procurement efficiency.

---

## ✨ Features

### 📂 BOM Processing
- Upload Excel BOMs (.xlsx)
- Automatic column mapping
- Engineering BOM generation
- Editable intermediate BOM before sourcing
- Add/Delete component rows directly from the interface

---

### 🔍 Intelligent Component Search
- Live DigiKey API integration
- Automatic search query generation
- Multi-threaded component lookup
- Manufacturer & part number retrieval
- Real-time search progress

---

### ✅ Validation Engine
Each sourced component is validated against engineering requirements.

Validation includes:

- Component Value
- Package
- Tolerance
- Voltage Rating
- Current Rating
- Power Rating
- Dielectric
- Part Type

Every component receives:

- Validation Score (%)
- Match Status
- Matched Parameters
- Mismatched Parameters

---

### 💰 Cost Analysis

Two operating modes are available:

#### Option 1
Calculate Final BOM Cost

#### Option 2
Compare Against Target BOM Cost

Includes:

- Actual BOM Cost
- Target Cost
- Cost Difference
- Percentage Difference

---

### ⚡ Engineering Productivity

BOMIQ estimates engineering effort saved by comparing:

- Manual sourcing time
- Automated sourcing time

and displays:

- Search Time
- Manual Estimate
- Speed Improvement

---

### 📊 Dashboard

Interactive dashboard showing:

- Total Components
- Components Found
- Partial Matches
- Few Parameter Matches
- Components Not Found
- Automation Percentage

---

### 🔌 DigiKey API Monitor

Displays:

- Connection Status
- Daily API Requests Remaining
- API Calls During Current Session

---

## 🛠 Technology Stack

- Python
- Streamlit
- Pandas
- DigiKey Product API
- Concurrent Futures (Multi-threading)

---

## 📁 Project Structure

```
BOMIQ
│
├── app.py
├── search_engine.py
├── digikey_api.py
├── validators.py
├── parser.py
├── mapping.py
├── normalizers.py
├── config.py
├── requirements.txt
└── assets/
```

---

## ⚙ Installation

Clone the repository

```bash
git clone https://github.com/Yash241104/BOMIQ.git
```

Move into the project

```bash
cd BOMIQ
```

Create virtual environment

```bash
python -m venv .venv
```

Activate

Linux

```bash
source .venv/bin/activate
```

Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run

```bash
streamlit run app.py
```

---

## 📌 Current Workflow

```
Upload BOM
      │
      ▼
Column Mapping
      │
      ▼
Engineering BOM Generation
      │
      ▼
User Review / Edit
      │
      ▼
DigiKey Component Search
      │
      ▼
Validation Engine
      │
      ▼
Cost Analysis
      │
      ▼
Final Procurement BOM
```

---

## 🚧 Planned Features

- Mouser API Integration
- Multi-distributor Comparison
- Alternative Component Suggestions
- Datasheet Links
- Export to Professional Excel
- Export to PDF Report
- Project Save / Load
- Web Deployment
- Desktop Application
- AI-assisted Parameter Extraction

---

## 📷 Screenshots

> Screenshots will be added in future releases.

---

## 🤝 Contributing

This project is currently under active development.

Suggestions, ideas, and improvements are always welcome.

---

## 👨‍💻 Author

**Yashwant N. Jirankali**

Electronics & Communication Engineering

Power Electronics | Automation | Embedded Systems | Python

---

## ⭐ Support

If you found this project interesting, consider giving it a ⭐ on GitHub.
