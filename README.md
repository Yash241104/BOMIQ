# 🚀 BOMIQ

**Intelligent BOM Automation Platform for Electronics Engineers**

BOMIQ automates electronic component sourcing by converting an engineering BOM into a procurement-ready BOM using the DigiKey API. It reduces manual component lookup, validates matches, and provides cost analysis through a simple web interface.

## Features

- 📂 Upload BOM (.xlsx)
- ⚙️ Generate Engineering BOM
- ✏️ Edit component parameters before search
- 🔍 Search components using DigiKey API
- ✅ Automatic validation & scoring
- 💰 BOM cost estimation
- 🎯 Optional target cost comparison
- 📊 Search summary dashboard
- ⚡ Engineering time saved estimation

## Tech Stack

- Python
- Streamlit
- Pandas
- DigiKey Product API

## Workflow

```text
Upload BOM
      ↓
Engineering BOM
      ↓
Review & Edit
      ↓
DigiKey Search
      ↓
Validation
      ↓
Final BOM
```

## Run Locally

```bash
git clone https://github.com/Yash241104/BOMIQ.git
cd BOMIQ

python -m venv .venv

# Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py
```

## Roadmap

- Multiple distributor support
- Alternative component suggestions
- Export to Excel & PDF
- Datasheet integration
- BOMIQ Cloud

---

**Status:** 🚧 Active Development
