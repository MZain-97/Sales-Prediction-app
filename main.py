import streamlit as st
import pandas as pd
from scipy.optimize import linprog
from pulp import *
from pyomo.environ import *
from io import BytesIO


# Custom CSS for the title and download button
st.markdown("""
    <style>
    .red-title {
        border: 2px solid red;
        padding: 10px;
        color: red;
        text-align: center;
    }
    .title {
        
        padding: 10px;
        color: red;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Title of the app with red outline
st.markdown('<h1 class="title"> Upscaling Engine App</h1>', unsafe_allow_html=True)



# Title of the app
st.sidebar.title('Excel File Uploader')

# File uploader widget
uploaded_file = st.sidebar.file_uploader("Choose an Excel file", type="xlsx")



if uploaded_file is not None:

    # Forecast years selection
    forecast_years = st.sidebar.multiselect(
    "Select forecast years",
    options=['2024', '2025', '2026', '2027', '2028', '2029', '2030'],
    default=['2024']
    )
    # Read the Excel file
    excel_file = pd.ExcelFile(uploaded_file)

    data = pd.read_excel(excel_file, 'Dataset')
    product_group_totals = pd.read_excel(excel_file, 'By Product Group')
    end_usage_totals = pd.read_excel(excel_file, 'By Segment')
    minimum_values = pd.read_excel(excel_file, 'Pipeline')
    test_data = pd.read_excel(excel_file, 'Test')
    st.markdown('<h2 class="title">Before Predictions</h2>', unsafe_allow_html=True)
    st.dataframe(data)

    # Selecting the columns for existing years
    existing_years = ['2020', '2021', '2022', '2023']

    # Filter out rows where any data in existing years is missing
    try:
        # Filter out rows where any data in existing years is missing
        df = data.dropna(subset=existing_years)
    except KeyError as e:
        st.error(f"The following columns are missing: {e}")
        st.stop()

    # Set the growth percentage
    growth_percentage = 5

    # Calculate the growth factor from the percentage
    growth_factor = 1 + growth_percentage / 100

    # Apply the growth factor to generate forecasts
    last_year = existing_years[-1]
    for year in forecast_years:
        df[year] = df[last_year] * growth_factor
        last_year = year

    unpivoted_baseline = pd.melt(df, id_vars=['Product Group', 'Product Line', 'End Usage Level 1', 'End Usage Level 2'],
                                 var_name='Year', value_name='Value')

    # Convert the Year column to numeric
    unpivoted_baseline['Year'] = unpivoted_baseline['Year'].astype(int)

    end_usage_totals = pd.melt(end_usage_totals, id_vars=['End Usage Level 1', 'End Usage Level 2'],
                               var_name='Year', value_name='Value')

    # Convert the Year column to numeric
    end_usage_totals['Year'] = end_usage_totals['Year'].astype(int)

    product_group_totals = pd.melt(product_group_totals, id_vars=['Product Group'],
                                   var_name='Year', value_name='Value')
    # Convert the Year column to numeric
    product_group_totals['Year'] = product_group_totals['Year'].astype(int)

    minimum_values = pd.melt(minimum_values, id_vars=['Product Group', 'End Usage Level 1'],
                             var_name='Year', value_name='Value')
    # Convert the Year column to numeric
    minimum_values['Year'] = minimum_values['Year'].astype(int)

    # Ensure the optimize_data function works with the provided dataframes
    # unpivoted_baseline = optimize_data(unpivoted_baseline, product_group_totals, end_usage_totals)
    Final_df = pd.pivot_table(unpivoted_baseline, values='Value', index=['Product Group', 'Product Line', 'End Usage Level 1', 'End Usage Level 2'], columns='Year').reset_index()

    st.markdown('<h2 class="title">After Predictions</h2>', unsafe_allow_html=True)
    st.dataframe(Final_df)

    # Convert the DataFrames to an Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write DataFrames to different sheets
        Final_df.to_excel(writer, sheet_name='Dataset')
        product_group_totals.to_excel(writer, sheet_name='By Product Group')
        end_usage_totals.to_excel(writer, sheet_name='By Segment')
        minimum_values.to_excel(writer, sheet_name='Pipeline')
        test_data.to_excel(writer, sheet_name='Test')
    output.seek(0)
    
    st.sidebar.download_button(
        label="Download Excel file",
        data=output,
        file_name='combined_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key='button2'
    )
