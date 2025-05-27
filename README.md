# Mortgage Calculator

A Streamlit-based mortgage calculator that helps users calculate and visualize mortgage payments for combined KFW and Bank loans.

## Features

- Calculate mortgage payments for combined KFW and Bank loans
- Visualize payment breakdowns with interactive charts
- View detailed amortization schedules
- Compare different loan scenarios
- Support for:
  - Property value and liquidity inputs
  - KFW loan amounts (€100,000 or €220,000)
  - Customizable interest rates and repayment rates
  - Different loan terms for each loan type

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mortgage-calc.git
cd mortgage-calc
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run mortgage-calc.py
```

## Usage

1. Enter the property value and available liquidity
2. Select the KFW loan amount (€100,000 or €220,000)
3. Adjust the Bank loan amount (automatically calculated)
4. Set the interest rates and repayment rates for both loans
5. Choose the loan terms for each loan type
6. View the results:
   - Monthly payments
   - Payment breakdown charts
   - Amortization schedules
   - Summary statistics

## Requirements

- Python 3.7+
- Streamlit
- Plotly
- NumPy
- Pandas

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 