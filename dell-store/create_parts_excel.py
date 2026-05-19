"""Run this once to create the service_parts.xlsx file in data/ folder.
Usage: python create_parts_excel.py
"""

import pandas as pd
import os

# Sample service parts data for Dell models
parts_data = [
    # Inspiron 15 3520
    {"model": "Dell Inspiron 15 3520", "part": "Screen/Display", "part_code": "LCD-3520", "price": 4500, "labour_charge": 800},
    {"model": "Dell Inspiron 15 3520", "part": "Keyboard", "part_code": "KB-3520", "price": 1800, "labour_charge": 500},
    {"model": "Dell Inspiron 15 3520", "part": "Battery", "part_code": "BAT-3520", "price": 3200, "labour_charge": 400},
    {"model": "Dell Inspiron 15 3520", "part": "Motherboard", "part_code": "MB-3520", "price": 12500, "labour_charge": 1500},
    {"model": "Dell Inspiron 15 3520", "part": "RAM (8GB DDR4)", "part_code": "RAM8-3520", "price": 2200, "labour_charge": 300},
    {"model": "Dell Inspiron 15 3520", "part": "SSD (512GB)", "part_code": "SSD512-3520", "price": 3500, "labour_charge": 400},
    {"model": "Dell Inspiron 15 3520", "part": "Charger/Adapter", "part_code": "CHG-3520", "price": 1500, "labour_charge": 0},
    {"model": "Dell Inspiron 15 3520", "part": "Touchpad", "part_code": "TP-3520", "price": 1200, "labour_charge": 600},
    {"model": "Dell Inspiron 15 3520", "part": "Fan/Cooling", "part_code": "FAN-3520", "price": 900, "labour_charge": 500},
    {"model": "Dell Inspiron 15 3520", "part": "Hinge", "part_code": "HNG-3520", "price": 1100, "labour_charge": 700},
    # Inspiron 14 5430
    {"model": "Dell Inspiron 14 5430", "part": "Screen/Display", "part_code": "LCD-5430", "price": 6500, "labour_charge": 800},
    {"model": "Dell Inspiron 14 5430", "part": "Keyboard", "part_code": "KB-5430", "price": 2200, "labour_charge": 500},
    {"model": "Dell Inspiron 14 5430", "part": "Battery", "part_code": "BAT-5430", "price": 4000, "labour_charge": 400},
    {"model": "Dell Inspiron 14 5430", "part": "Motherboard", "part_code": "MB-5430", "price": 16000, "labour_charge": 1500},
    {"model": "Dell Inspiron 14 5430", "part": "RAM (16GB LPDDR5)", "part_code": "RAM16-5430", "price": 4500, "labour_charge": 300},
    {"model": "Dell Inspiron 14 5430", "part": "SSD (512GB)", "part_code": "SSD512-5430", "price": 3500, "labour_charge": 400},
    {"model": "Dell Inspiron 14 5430", "part": "Charger/Adapter", "part_code": "CHG-5430", "price": 1800, "labour_charge": 0},
    {"model": "Dell Inspiron 14 5430", "part": "Touchpad", "part_code": "TP-5430", "price": 1500, "labour_charge": 600},
    {"model": "Dell Inspiron 14 5430", "part": "Fan/Cooling", "part_code": "FAN-5430", "price": 1100, "labour_charge": 500},
    {"model": "Dell Inspiron 14 5430", "part": "Hinge", "part_code": "HNG-5430", "price": 1300, "labour_charge": 700},
    # XPS 13 9340
    {"model": "Dell XPS 13 9340", "part": "Screen/Display", "part_code": "LCD-9340", "price": 12000, "labour_charge": 1000},
    {"model": "Dell XPS 13 9340", "part": "Keyboard", "part_code": "KB-9340", "price": 3500, "labour_charge": 600},
    {"model": "Dell XPS 13 9340", "part": "Battery", "part_code": "BAT-9340", "price": 5500, "labour_charge": 500},
    {"model": "Dell XPS 13 9340", "part": "Motherboard", "part_code": "MB-9340", "price": 28000, "labour_charge": 2000},
    {"model": "Dell XPS 13 9340", "part": "RAM (16GB LPDDR5x)", "part_code": "RAM16-9340", "price": 5500, "labour_charge": 300},
    {"model": "Dell XPS 13 9340", "part": "SSD (512GB NVMe)", "part_code": "SSD512-9340", "price": 4500, "labour_charge": 400},
    {"model": "Dell XPS 13 9340", "part": "Charger/Adapter (USB-C)", "part_code": "CHG-9340", "price": 2500, "labour_charge": 0},
    {"model": "Dell XPS 13 9340", "part": "Touchpad", "part_code": "TP-9340", "price": 2000, "labour_charge": 700},
    {"model": "Dell XPS 13 9340", "part": "Fan/Cooling", "part_code": "FAN-9340", "price": 1500, "labour_charge": 600},
    {"model": "Dell XPS 13 9340", "part": "Speaker", "part_code": "SPK-9340", "price": 1200, "labour_charge": 500},
    # XPS 15 9530
    {"model": "Dell XPS 15 9530", "part": "Screen/Display (OLED)", "part_code": "LCD-9530", "price": 18000, "labour_charge": 1200},
    {"model": "Dell XPS 15 9530", "part": "Keyboard", "part_code": "KB-9530", "price": 3800, "labour_charge": 600},
    {"model": "Dell XPS 15 9530", "part": "Battery", "part_code": "BAT-9530", "price": 6500, "labour_charge": 500},
    {"model": "Dell XPS 15 9530", "part": "Motherboard", "part_code": "MB-9530", "price": 35000, "labour_charge": 2500},
    {"model": "Dell XPS 15 9530", "part": "RAM (32GB DDR5)", "part_code": "RAM32-9530", "price": 8000, "labour_charge": 300},
    {"model": "Dell XPS 15 9530", "part": "SSD (1TB NVMe)", "part_code": "SSD1T-9530", "price": 7500, "labour_charge": 400},
    {"model": "Dell XPS 15 9530", "part": "Charger/Adapter", "part_code": "CHG-9530", "price": 2800, "labour_charge": 0},
    {"model": "Dell XPS 15 9530", "part": "GPU (RTX 4060)", "part_code": "GPU-9530", "price": 22000, "labour_charge": 2000},
    {"model": "Dell XPS 15 9530", "part": "Fan/Cooling", "part_code": "FAN-9530", "price": 1800, "labour_charge": 600},
    {"model": "Dell XPS 15 9530", "part": "Hinge", "part_code": "HNG-9530", "price": 1500, "labour_charge": 800},
    # Latitude 5540
    {"model": "Dell Latitude 5540", "part": "Screen/Display", "part_code": "LCD-5540", "price": 5500, "labour_charge": 800},
    {"model": "Dell Latitude 5540", "part": "Keyboard", "part_code": "KB-5540", "price": 2000, "labour_charge": 500},
    {"model": "Dell Latitude 5540", "part": "Battery", "part_code": "BAT-5540", "price": 3800, "labour_charge": 400},
    {"model": "Dell Latitude 5540", "part": "Motherboard", "part_code": "MB-5540", "price": 18000, "labour_charge": 1500},
    {"model": "Dell Latitude 5540", "part": "RAM (16GB DDR4)", "part_code": "RAM16-5540", "price": 3500, "labour_charge": 300},
    {"model": "Dell Latitude 5540", "part": "SSD (256GB)", "part_code": "SSD256-5540", "price": 2500, "labour_charge": 400},
    {"model": "Dell Latitude 5540", "part": "Charger/Adapter", "part_code": "CHG-5540", "price": 1600, "labour_charge": 0},
    {"model": "Dell Latitude 5540", "part": "Touchpad", "part_code": "TP-5540", "price": 1400, "labour_charge": 600},
    {"model": "Dell Latitude 5540", "part": "Fan/Cooling", "part_code": "FAN-5540", "price": 1000, "labour_charge": 500},
    {"model": "Dell Latitude 5540", "part": "Webcam Module", "part_code": "CAM-5540", "price": 800, "labour_charge": 400},
    # Vostro 3520
    {"model": "Dell Vostro 3520", "part": "Screen/Display", "part_code": "LCD-V3520", "price": 4000, "labour_charge": 800},
    {"model": "Dell Vostro 3520", "part": "Keyboard", "part_code": "KB-V3520", "price": 1500, "labour_charge": 500},
    {"model": "Dell Vostro 3520", "part": "Battery", "part_code": "BAT-V3520", "price": 2800, "labour_charge": 400},
    {"model": "Dell Vostro 3520", "part": "Motherboard", "part_code": "MB-V3520", "price": 10000, "labour_charge": 1500},
    {"model": "Dell Vostro 3520", "part": "RAM (8GB DDR4)", "part_code": "RAM8-V3520", "price": 2000, "labour_charge": 300},
    {"model": "Dell Vostro 3520", "part": "SSD (256GB)", "part_code": "SSD256-V3520", "price": 2200, "labour_charge": 400},
    {"model": "Dell Vostro 3520", "part": "Charger/Adapter", "part_code": "CHG-V3520", "price": 1200, "labour_charge": 0},
    {"model": "Dell Vostro 3520", "part": "Touchpad", "part_code": "TP-V3520", "price": 1000, "labour_charge": 600},
    {"model": "Dell Vostro 3520", "part": "Fan/Cooling", "part_code": "FAN-V3520", "price": 800, "labour_charge": 500},
    {"model": "Dell Vostro 3520", "part": "Hinge", "part_code": "HNG-V3520", "price": 900, "labour_charge": 700},
]

# Create DataFrame and save
df = pd.DataFrame(parts_data)

os.makedirs("data", exist_ok=True)
df.to_excel("data/service_parts.xlsx", index=False, engine="openpyxl")

print(f"Created data/service_parts.xlsx with {len(df)} parts across {df['model'].nunique()} models")
print(f"\nModels included:")
for model in df["model"].unique():
    part_count = len(df[df["model"] == model])
    print(f"  - {model} ({part_count} parts)")
