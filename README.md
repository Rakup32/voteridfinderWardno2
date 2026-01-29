# मतदाता सूची खोज प्रणाली (Voter List Search System)

A Streamlit-based application for quickly searching through Nepali voter list data.

## Features

- **सबै डाटा हेर्नुहोस्** - View all voter data
- **मतदाताको नामबाट खोज्नुहोस्** - Search by voter name
- **मतदाता नंबरबाट खोज्नुहोस्** - Search by voter number
- **लिङ्गबाट फिल्टर गर्नुहोस्** - Filter by gender
- **उमेर दायराबाट खोज्नुहोस्** - Search by age range
- Statistics dashboard showing total voters, gender distribution, and average age

## Installation

1. Install required Python packages:
```bash
pip install streamlit pandas openpyxl
```

## File Structure

Make sure you have these files in the same directory:
- `voter_search_app.py` - Main application file
- `voterlist.xlsx` - Your Excel file with voter data

## How to Run

1. Open terminal/command prompt
2. Navigate to the directory containing the files
3. Run the command:
```bash
streamlit run voter_search_app.py
```

4. The application will open in your default web browser automatically
5. If it doesn't open automatically, go to: http://localhost:8501

## Usage

1. **Select Search Type**: Use the sidebar to choose your search method
2. **Enter Search Criteria**: Depending on your selection, enter name, number, or other criteria
3. **View Results**: Results will be displayed in a table format
4. **Statistics**: Check the sidebar for overall statistics

## Data Columns

The application preserves the original Excel data format:
- सि.नं. (Serial Number)
- मतदाता नं (Voter Number)
- मतदाताको नाम (Voter Name)
- उमेर(वर्ष) (Age in Years)
- लिङ्ग (Gender)
- पति/पत्नीको नाम (Spouse Name)
- पिता/माताको नाम (Father/Mother Name)

## Requirements

- Python 3.7+
- streamlit
- pandas
- openpyxl

## Notes

- All data is loaded from the Excel file without any modifications
- The original data format and Nepali text are preserved
- Search is case-insensitive for name searches
