# Address Solving V2

Vietnamese address comparison tool with province extraction and matching capabilities.

## 📁 Project Structure

```
address_solving_v2/
├── src/                          # Source code
│   ├── __init__.py
│   └── province_comparator.py   # Province extraction & comparison logic
├── data/                         # Data files
│   └── tinh_thanh.json          # Province variants database (5,297 variants)
├── tests/                        # Test files
│   ├── __init__.py
│   ├── test_address_app.py      # Gradio web interface for testing
│   └── test_data/
│       ├── address_comparison_output.json
│       └── address_match.csv
├── scripts/                      # Utility scripts
│   └── compare_address_pairs.py # Batch comparison script
├── .gitignore
├── README.md
└── requirements.txt
```

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## 💻 Usage

### Web Interface (Gradio)

```bash
cd address_solving_v2
python tests/test_address_app.py
```

Giao diện sẽ mở tại: `http://localhost:7861`

### Batch Processing Script

```bash
python scripts/compare_address_pairs.py
```

### Python API

```python
from src.province_comparator import ProvinceComparator

# Initialize comparator
comparator = ProvinceComparator('data/tinh_thanh.json')

# Extract province from address
province = comparator.extract_province("123 Nguyễn Huệ, TP Đà Nẵng")
print(province)  # "Thành phố Đà Nẵng"

# Compare two addresses
is_match, reason = comparator.compare_provinces("Đà Nẵng", "Da Nang")
print(is_match)  # True
```

## ✨ Features

- 📍 Extract provinces from Vietnamese addresses
- 🏛️ Support for 5,297 province name variants
- ✅ Smart matching with word boundary detection
- 🔄 Handle merged provinces (e.g., Hà Tây → Hà Nội)
- 🎯 93.6% accuracy on test dataset
- 🌐 Gradio web interface for easy testing
- 📊 Batch processing for CSV files

## 📝 License

MIT
