import pandas as pd
import numpy as np
import os
import time
import re

def diagnostic_plot():
    # 1. Peek at the file to see the actual separator and columns
    with open('wildfire_results.csv', 'r') as f:
        first_line = f.readline()
        print(f"File Header detected: {first_line.strip()}")

    # 2. Load the data
    # We'll try to be flexible with separators
    try:
        df = pd.read_csv('wildfire_results.csv', sep=None, engine='python')
    except Exception as e:
        print(f"Could not read CSV: {e}")
        return

    # 3. Clean column names (remove whitespace)
    df.columns = [c.strip() for c in df.columns]
    
    # 4. Filter for numeric time and valid model names
    df['time'] = pd.to_numeric(df['time'], errors='coerce')
    df = df.dropna(subset=['time'])
    
    unique_times = sorted(df['time'].unique())
    print(f"Found {len(unique_times)} valid time steps.")

    grid = np.zeros((101, 101))
    
    for t in unique_times:
        current_data = df[df['time'] == t]
        for _, row in current_data.iterrows():
            # Extract coordinates from strings like "(50,50)" or "50,50"
            m_name = str(row['model_name'])
            coords = re.findall(r'\d+', m_name)
            
            if len(coords) >= 2:
                r, c = int(coords[0]), int(coords[1])
                
                # Extract burned value - it might be a single float or a "0.5;15;0" string
                data_val = str(row['data']).split(';')[0]
                try:
                    grid[r, c] = float(data_val)
                except:
                    continue

        # Only display if fire has spread beyond the first cell
        if np.sum(grid > 0) > 0:
            os.system('clear')
            print(f"--- FIRE MATRIX | Time: {t}h ---")
            # Display center of the forest
            for r in range(40, 61):
                line = ""
                for c in range(40, 61):
                    val = grid[r, c]
                    if val >= 0.9: line += "# "
                    elif val > 0:  line += "* "
                    else:           line += ". "
                print(line)
            time.sleep(0.1)

diagnostic_plot()