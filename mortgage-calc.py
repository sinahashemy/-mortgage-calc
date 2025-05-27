import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def calculate_monthly_payment(principal, annual_rate, months):
    # Convert annual rate to monthly rate
    monthly_rate = annual_rate / 12 / 100
    
    # Calculate monthly payment using the mortgage payment formula
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    return monthly_payment

def calculate_annuity_loan(loan_amount, property_value, initial_repayment_rate, annual_rate, years):
    # Convert annual rate to monthly rate
    monthly_rate = annual_rate / 12 / 100
    
    # Calculate initial monthly repayment amount
    initial_monthly_repayment = loan_amount * (initial_repayment_rate / 12 / 100)
    
    # Calculate initial monthly interest
    initial_monthly_interest = loan_amount * monthly_rate
    
    # Calculate initial monthly payment (repayment + interest)
    monthly_payment = initial_monthly_repayment + initial_monthly_interest
    
    # Calculate number of months
    months = years * 12
    
    # Initialize arrays
    balance = np.zeros(months + 1)
    monthly_interest = np.zeros(months + 1)
    monthly_principal = np.zeros(months + 1)
    
    balance[0] = loan_amount
    
    # Calculate amortization schedule
    for month in range(1, months + 1):
        interest = balance[month-1] * monthly_rate
        principal_payment = monthly_payment - interest
        
        balance[month] = balance[month-1] - principal_payment
        monthly_interest[month] = interest
        monthly_principal[month] = principal_payment
    
    return balance, monthly_interest, monthly_principal, monthly_payment

def calculate_full_payoff_period(remaining_balance, monthly_payment, annual_rate):
    # Calculate how many more months needed to pay off the remaining balance
    if remaining_balance <= 0:
        return 0
        
    monthly_rate = annual_rate / 12 / 100
    
    # Calculate months remaining until fully paid
    # Using formula: n = -log(1 - r*P/M) / log(1+r)
    # Where: n = number of payments, r = monthly rate, P = principal, M = monthly payment
    numerator = -np.log(1 - (monthly_rate * remaining_balance / monthly_payment))
    denominator = np.log(1 + monthly_rate)
    
    # Handle potential division by zero or numerical issues
    if denominator == 0 or np.isnan(numerator) or np.isnan(denominator):
        return float('inf')  # Cannot be paid off with current payment
        
    months_remaining = numerator / denominator
    
    # Round up to next month
    return int(np.ceil(months_remaining))

def calculate_amortization_schedule(principal, annual_rate, months):
    monthly_rate = annual_rate / 12 / 100
    monthly_payment = calculate_monthly_payment(principal, annual_rate, months)
    
    # Initialize arrays to store data
    balance = np.zeros(months + 1)
    monthly_interest = np.zeros(months + 1)
    monthly_principal = np.zeros(months + 1)
    
    balance[0] = principal
    
    # Calculate amortization schedule
    for month in range(1, months + 1):
        interest = balance[month-1] * monthly_rate
        principal_payment = monthly_payment - interest
        
        balance[month] = balance[month-1] - principal_payment
        monthly_interest[month] = interest
        monthly_principal[month] = principal_payment
    
    return balance, monthly_interest, monthly_principal, monthly_payment

def create_amortization_table(balance, monthly_interest, monthly_principal, months):
    data = {
        'Month': range(1, months + 1),
        'Remaining Balance (€)': balance[1:],
        'Principal Payment (€)': monthly_principal[1:],
        'Interest Payment (€)': monthly_interest[1:],
        'Total Payment (€)': monthly_principal[1:] + monthly_interest[1:]
    }
    return pd.DataFrame(data)

def calculate_combined_loan(property_value, liquidity, kfw_loan_amount, kfw_initial_repayment, kfw_interest_rate, kfw_years,
                          bank_loan_amount, bank_initial_repayment, bank_interest_rate, bank_years):
    # Calculate KFW loan details
    kfw_balance, kfw_monthly_interest, kfw_monthly_principal, kfw_monthly_payment = calculate_annuity_loan(
        kfw_loan_amount, property_value, kfw_initial_repayment, kfw_interest_rate, kfw_years
    )
    
    # Calculate Bank loan details
    bank_balance, bank_monthly_interest, bank_monthly_principal, bank_monthly_payment = calculate_annuity_loan(
        bank_loan_amount, property_value, bank_initial_repayment, bank_interest_rate, bank_years
    )
    
    # Calculate combined monthly payment
    total_monthly_payment = kfw_monthly_payment + bank_monthly_payment
    
    return {
        'kfw': {
            'balance': kfw_balance,
            'monthly_interest': kfw_monthly_interest,
            'monthly_principal': kfw_monthly_principal,
            'monthly_payment': kfw_monthly_payment,
            'years': kfw_years
        },
        'bank': {
            'balance': bank_balance,
            'monthly_interest': bank_monthly_interest,
            'monthly_principal': bank_monthly_principal,
            'monthly_payment': bank_monthly_payment,
            'years': bank_years
        },
        'total_monthly_payment': total_monthly_payment
    }

def calculate_payoff_date(balance, monthly_payment, annual_rate, start_date, loan_term_years):
    if balance[0] <= 0:
        return start_date
        
    # Calculate the expected end date based on loan term
    expected_end_date = start_date + timedelta(days=365 * loan_term_years)
    
    # Calculate how many months of payments are needed to pay off the remaining balance
    monthly_rate = annual_rate / 12 / 100
    remaining_balance = balance[-1]  # Get the remaining balance at the end of loan term
    
    if remaining_balance <= 0:
        return expected_end_date
        
    # Calculate additional months needed to pay off remaining balance
    numerator = -np.log(1 - (monthly_rate * remaining_balance / monthly_payment))
    denominator = np.log(1 + monthly_rate)
    
    if denominator == 0 or np.isnan(numerator) or np.isnan(denominator):
        return None
        
    additional_months = int(np.ceil(numerator / denominator))
    return expected_end_date + timedelta(days=30 * additional_months)

def main():
    st.title("Mortgage Calculator")
    st.write("Calculate your monthly mortgage payments and view the amortization schedule")
    
    # Initialize session state for loan amounts if not exists
    if 'kfw_amount' not in st.session_state:
        st.session_state.kfw_amount = 100000  # Default to 100K
    if 'bank_amount' not in st.session_state:
        st.session_state.bank_amount = 0
    if 'total_loan_amount' not in st.session_state:
        st.session_state.total_loan_amount = 0

    def update_kfw_amount():
        # Update bank amount to maintain total
        st.session_state.bank_amount = st.session_state.total_loan_amount - st.session_state.kfw_amount

    def update_bank_amount():
        # This function is no longer needed as bank amount is calculated automatically
        pass
    
    # Create tabs for different calculation methods
    tab1, tab2 = st.tabs(["Standard Calculator", "Combined Loan Calculator"])
    
    with tab1:
        st.subheader("Standard Mortgage Calculator")
        # Input fields
        col1, col2 = st.columns(2)
        
        with col1:
            principal = st.number_input("Total Loan Amount (€)", 
                                      min_value=10000, 
                                      max_value=10000000, 
                                      value=300000, 
                                      step=10000)
        
        with col2:
            annual_rate = st.slider("Annual Interest Rate (%)", 
                                  min_value=0.1, 
                                  max_value=15.0, 
                                  value=5.0, 
                                  step=0.01)
        
        months = st.slider("Loan Term (Months)", 
                          min_value=12, 
                          max_value=480, 
                          value=240, 
                          step=12)
        
        # Calculate results
        balance, monthly_interest, monthly_principal, monthly_payment = calculate_amortization_schedule(
            principal, annual_rate, months
        )
        
        # Display results
        st.subheader("Monthly Payment")
        st.write(f"€{monthly_payment:,.2f}")
        
        # Create amortization chart
        fig = go.Figure()
        
        # Add traces for principal and interest
        fig.add_trace(go.Bar(
            x=list(range(1, months + 1)),
            y=monthly_principal,
            name='Principal',
            marker_color='blue'
        ))
        
        fig.add_trace(go.Bar(
            x=list(range(1, months + 1)),
            y=monthly_interest,
            name='Interest',
            marker_color='red'
        ))
        
        # Update layout
        fig.update_layout(
            title='Monthly Payment Breakdown',
            xaxis_title='Months',
            yaxis_title='Amount (€)',
            barmode='stack',
            hovermode='x unified'
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Display summary statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Interest Paid", f"€{np.sum(monthly_interest):,.2f}")
        with col2:
            st.metric("Total Amount Paid", f"€{(np.sum(monthly_principal) + np.sum(monthly_interest)):,.2f}")
            
        col3, col4 = st.columns(2)
        with col3:
            st.metric("Total Principal Paid", f"€{np.sum(monthly_principal):,.2f}")
        with col4:
            st.metric("Remaining Balance", f"€{balance[-1]:,.2f}")
            
        # Display amortization table
        st.subheader("Amortization Schedule")
        df = create_amortization_table(balance, monthly_interest, monthly_principal, months)
        st.dataframe(df.style.format({
            'Remaining Balance (€)': '{:,.2f}',
            'Principal Payment (€)': '{:,.2f}',
            'Interest Payment (€)': '{:,.2f}',
            'Total Payment (€)': '{:,.2f}'
        }))
    
    with tab2:
        st.subheader("Combined Loan Calculator")
        
        # Property Value input
        property_value = st.number_input("Project Value (€)", 
                                       min_value=10000, 
                                       max_value=10000000, 
                                       value=700000, 
                                       step=10000)
        
        # Liquidity input
        liquidity = st.number_input("Available Liquidity (€)", 
                                  min_value=0, 
                                  max_value=property_value, 
                                  value=50000, 
                                  step=1000)
        
        # Start Year input
        current_year = datetime.now().year
        start_year = st.number_input("Start Year of Payment", 
                                   min_value=current_year, 
                                   max_value=current_year + 50, 
                                   value=current_year)
        
        # Calculate total loan amount
        total_loan_amount = property_value - liquidity
        st.session_state.total_loan_amount = total_loan_amount
        
        # Display total loan amount
        st.metric("Total Loan Amount Needed", f"€{total_loan_amount:,.2f}")
        
        st.markdown("---")
        st.subheader("Loan Details")
        
        # Create two columns for loan details with equal width
        col_kfw, col_bank = st.columns(2)
        
        with col_kfw:
            st.markdown("### KFW Loan")
            # KFW Loan Amount dropdown
            kfw_loan_amount = st.selectbox("KFW Loan Amount (€)", 
                                         options=[100000, 220000],
                                         format_func=lambda x: f"€{x:,.0f}",
                                         index=0 if st.session_state.kfw_amount == 100000 else 1,
                                         key="kfw_amount",
                                         on_change=update_kfw_amount)
            
            # KFW Loan Parameters
            kfw_initial_repayment = st.number_input("KFW Initial Repayment Rate (%)", 
                                                  min_value=0.1, 
                                                  max_value=10.0, 
                                                  value=2.0, 
                                                  step=0.01)
            
            kfw_interest_rate = st.number_input("KFW Annual Interest Rate (%)", 
                                              min_value=0.1, 
                                              max_value=15.0, 
                                              value=1.0, 
                                              step=0.01)
            
            # KFW Loan Term
            kfw_years = st.slider("KFW Loan Term (Years)", 
                                min_value=1, 
                                max_value=40, 
                                value=10, 
                                step=1)
        
        with col_bank:
            st.markdown("### Bank Loan")
            # Display Bank Loan Amount (calculated)
            bank_loan_amount = total_loan_amount - kfw_loan_amount
            st.metric("Bank Loan Amount (€)", f"€{bank_loan_amount:,.2f}")
            
            # Bank Loan Parameters
            bank_initial_repayment = st.number_input("Bank Initial Repayment Rate (%)", 
                                                   min_value=0.1, 
                                                   max_value=10.0, 
                                                   value=3.0, 
                                                   step=0.01)
            
            bank_interest_rate = st.number_input("Bank Annual Interest Rate (%)", 
                                               min_value=0.1, 
                                               max_value=15.0, 
                                               value=3.45, 
                                               step=0.01)
            
            # Bank Loan Term
            bank_years = st.slider("Bank Loan Term (Years)", 
                                 min_value=1, 
                                 max_value=40, 
                                 value=10, 
                                 step=1)
        
        # Use the calculated values for calculations
        kfw_loan_amount = st.session_state.kfw_amount
        bank_loan_amount = total_loan_amount - kfw_loan_amount
        
        # Calculate results
        results = calculate_combined_loan(
            property_value, liquidity,
            kfw_loan_amount, kfw_initial_repayment, kfw_interest_rate, kfw_years,
            bank_loan_amount, bank_initial_repayment, bank_interest_rate, bank_years
        )
        
        # Calculate and display mortgage percentage
        mortgage_percentage = (total_loan_amount / property_value) * 100
        st.markdown("---")
        st.subheader("Mortgage Details")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Mortgage Percentage", f"{mortgage_percentage:.1f}%")
        with col2:
            st.metric("Down Payment", f"€{liquidity:,.2f}")
        
        # Display monthly payments
        st.markdown("---")
        st.subheader("Monthly Payments")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("KFW Monthly Payment", f"€{results['kfw']['monthly_payment']:,.2f}")
        with col2:
            st.metric("Bank Monthly Payment", f"€{results['bank']['monthly_payment']:,.2f}")
        with col3:
            st.metric("Total Monthly Payment", f"€{results['total_monthly_payment']:,.2f}")
        
        # Create amortization chart
        fig = go.Figure()
        
        # Add traces from bottom to top
        fig.add_trace(go.Bar(
            x=list(range(1, results['bank']['years'] * 12 + 1)),
            y=results['bank']['monthly_principal'],
            name='Bank Principal',
            marker_color='red'
        ))
        
        fig.add_trace(go.Bar(
            x=list(range(1, results['kfw']['years'] * 12 + 1)),
            y=results['kfw']['monthly_principal'],
            name='KFW Principal',
            marker_color='blue'
        ))
        
        fig.add_trace(go.Bar(
            x=list(range(1, results['bank']['years'] * 12 + 1)),
            y=results['bank']['monthly_interest'],
            name='Bank Interest',
            marker_color='pink'
        ))
        
        fig.add_trace(go.Bar(
            x=list(range(1, results['kfw']['years'] * 12 + 1)),
            y=results['kfw']['monthly_interest'],
            name='KFW Interest',
            marker_color='lightblue'
        ))
        
        # Update layout
        fig.update_layout(
            title='Monthly Payment Breakdown',
            xaxis_title='Months',
            yaxis_title='Amount (€)',
            barmode='stack',
            hovermode='x unified'
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Display summary statistics
        st.markdown("---")
        st.subheader("Summary Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total KFW Interest Paid", f"€{np.sum(results['kfw']['monthly_interest']):,.2f}")
            st.metric("Total Bank Interest Paid", f"€{np.sum(results['bank']['monthly_interest']):,.2f}")
            st.markdown("---")
            total_interest = np.sum(results['kfw']['monthly_interest']) + np.sum(results['bank']['monthly_interest'])
            st.metric("Total Interest Paid", f"€{total_interest:,.2f}")
        
        with col2:
            st.metric("Total KFW Amount Paid", f"€{np.sum(results['kfw']['monthly_principal']) + np.sum(results['kfw']['monthly_interest']):,.2f}")
            st.metric("Total Bank Amount Paid", f"€{np.sum(results['bank']['monthly_principal']) + np.sum(results['bank']['monthly_interest']):,.2f}")
            st.markdown("---")
            total_amount = (np.sum(results['kfw']['monthly_principal']) + np.sum(results['kfw']['monthly_interest']) + 
                          np.sum(results['bank']['monthly_principal']) + np.sum(results['bank']['monthly_interest']))
            st.metric("Total Amount Paid", f"€{total_amount:,.2f}")
        
        with col3:
            st.metric("KFW Remaining Balance", f"€{results['kfw']['balance'][-1]:,.2f}")
            st.metric("Bank Remaining Balance", f"€{results['bank']['balance'][-1]:,.2f}")
            st.markdown("---")
            total_remaining = results['kfw']['balance'][-1] + results['bank']['balance'][-1]
            st.metric("Total Remaining Balance", f"€{total_remaining:,.2f}")
        
        # Add Loan End Date Predictions
        st.markdown("---")
        st.subheader("Loan Payoff Predictions")
        
        # Calculate payoff dates
        start_date = datetime(start_year, 1, 1)  # Use January 1st of the start year
        
        # Calculate actual payoff dates based on remaining balance
        kfw_payoff_date = calculate_payoff_date(
            results['kfw']['balance'],
            results['kfw']['monthly_payment'],
            kfw_interest_rate,
            start_date,
            kfw_years
        )
        
        bank_payoff_date = calculate_payoff_date(
            results['bank']['balance'],
            results['bank']['monthly_payment'],
            bank_interest_rate,
            start_date,
            bank_years
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### KFW Loan")
            if kfw_payoff_date:
                expected_end_date = start_date + timedelta(days=365 * kfw_years)
                additional_months = (kfw_payoff_date - expected_end_date).days // 30
                total_months = (kfw_years * 12) + additional_months
                total_years = total_months / 12
                st.metric("Start Date", start_date.strftime("%B %d, %Y"))
                st.metric("Actual Payoff Date", kfw_payoff_date.strftime("%B %d, %Y"))
                st.metric("Additional Months Needed", f"{additional_months:,}")
                st.metric("Total Years Needed", f"{total_years:.1f}")
            else:
                st.metric("Start Date", start_date.strftime("%B %d, %Y"))
                st.metric("Actual Payoff Date", "Cannot be calculated")
                st.metric("Additional Months Needed", "N/A")
                st.metric("Total Years Needed", "N/A")
        
        with col2:
            st.markdown("### Bank Loan")
            if bank_payoff_date:
                expected_end_date = start_date + timedelta(days=365 * bank_years)
                additional_months = (bank_payoff_date - expected_end_date).days // 30
                total_months = (bank_years * 12) + additional_months
                total_years = total_months / 12
                st.metric("Start Date", start_date.strftime("%B %d, %Y"))
                st.metric("Actual Payoff Date", bank_payoff_date.strftime("%B %d, %Y"))
                st.metric("Additional Months Needed", f"{additional_months:,}")
                st.metric("Total Years Needed", f"{total_years:.1f}")
            else:
                st.metric("Start Date", start_date.strftime("%B %d, %Y"))
                st.metric("Actual Payoff Date", "Cannot be calculated")
                st.metric("Additional Months Needed", "N/A")
                st.metric("Total Years Needed", "N/A")
        
        # Display amortization tables
        st.markdown("---")
        st.subheader("Amortization Schedules")
        
        # KFW Amortization Table
        st.write("KFW Loan Amortization Schedule")
        kfw_df = create_amortization_table(
            results['kfw']['balance'],
            results['kfw']['monthly_interest'],
            results['kfw']['monthly_principal'],
            results['kfw']['years'] * 12
        )
        st.dataframe(kfw_df.style.format({
            'Remaining Balance (€)': '{:,.2f}',
            'Principal Payment (€)': '{:,.2f}',
            'Interest Payment (€)': '{:,.2f}',
            'Total Payment (€)': '{:,.2f}'
        }))
        
        # Bank Amortization Table
        st.write("Bank Loan Amortization Schedule")
        bank_df = create_amortization_table(
            results['bank']['balance'],
            results['bank']['monthly_interest'],
            results['bank']['monthly_principal'],
            results['bank']['years'] * 12
        )
        st.dataframe(bank_df.style.format({
            'Remaining Balance (€)': '{:,.2f}',
            'Principal Payment (€)': '{:,.2f}',
            'Interest Payment (€)': '{:,.2f}',
            'Total Payment (€)': '{:,.2f}'
        }))

if __name__ == "__main__":
    main()
