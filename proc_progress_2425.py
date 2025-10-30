# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from sklearn.preprocessing import MinMaxScaler
import matplotlib.ticker as mticker

# Title
st.title("Procurement Progress Dashboard (FY 24/25)")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=['xlsx'])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # --- Data Preview ---
    st.write("### Data Preview")
    st.dataframe(df.head())

    # --- Calculate summaries ---
    total_firms = df['Contractor/ Firm'].nunique()
    total_amount_allocated = df['PO Amount (PKR)'].sum()
    total_items_demanded = df['Items Demanded'].sum()
    total_quantity_demanded = df['Quantity Demanded'].sum()
    total_items_delivered = df['Items Delivered'].sum()
    total_quantities_delivered = df['Quantity Delivered'].sum()
    total_bal_items = total_items_demanded - total_items_delivered
    total_bal_quantities = total_quantity_demanded - total_quantities_delivered

    summary_data = {
        'Metric': [
            'Total Firms Participated',
            'Total Amount Allocated (PKR)',
            'Total Items Demanded',
            'Total Quantity Demanded',
            'Total Items Delivered',
            'Total Quantities Delivered',
            'Total Bal Items',
            'Total Bal Quantities'
        ],
        'Value': [
            total_firms,
            total_amount_allocated,
            total_items_demanded,
            total_quantity_demanded,
            total_items_delivered,
            total_quantities_delivered,
            total_bal_items,
            total_bal_quantities
        ]
    }
    summary_df = pd.DataFrame(summary_data)

    st.write("### Summary Table")
    st.dataframe(summary_df)

    # --- Firm Performance & Ranking ---
    df['Balance Quantity'] = df['Quantity Demanded'] - df['Quantity Delivered']
    firm_performance = df.groupby('Contractor/ Firm').agg(
        Total_Balance_Quantity=('Balance Quantity', 'sum'),
        Total_Rejection_Events=('Number of Rejection Events', 'sum'),
        Average_Days_for_Completion=('Number of Days for Completion of Order', 'mean')
    ).reset_index()

    st.write("### Firm Performance")
    st.dataframe(firm_performance.head())

    # Normalize
    scaler = MinMaxScaler()
    firm_performance[['Normalized_Balance_Quantity', 'Normalized_Rejection_Events', 'Normalized_Days_for_Completion']] = scaler.fit_transform(
        firm_performance[['Total_Balance_Quantity', 'Total_Rejection_Events', 'Average_Days_for_Completion']]
    )

    # Ranking Score
    firm_performance['Ranking_Score'] = (1 - firm_performance['Normalized_Balance_Quantity']) + \
                                        (1 - firm_performance['Normalized_Rejection_Events']) + \
                                        (1 - firm_performance['Normalized_Days_for_Completion'])

    # Final Ranking
    firm_ranking = firm_performance.sort_values(by='Ranking_Score', ascending=False).reset_index(drop=True)
    firm_ranking.index = firm_ranking.index + 1
    firm_ranking = firm_ranking.rename_axis('Rank')

    st.write("### Top Ranked Firms")
    st.dataframe(firm_ranking[['Contractor/ Firm', 'Ranking_Score']].head())

    st.write("### Top 3 Firms - Detailed")
    st.dataframe(firm_ranking[['Contractor/ Firm', 'Total_Balance_Quantity', 'Total_Rejection_Events', 'Average_Days_for_Completion', 'Ranking_Score']].head(3))

    # --- Visualization ---
    df['Delivery Percentage'] = (df['Quantity Delivered'] / df['Quantity Demanded']) * 100
    firm_summary_viz = df.groupby('Contractor/ Firm').agg(
        Total_PO_Amount=('PO Amount (PKR)', 'sum'),
        Average_Delivery_Percentage=('Delivery Percentage', 'mean')
    ).reset_index()

    fig, ax1 = plt.subplots(figsize=(14, 7))
    sns.barplot(x='Contractor/ Firm', y='Total_PO_Amount', data=firm_summary_viz, ax=ax1, color='skyblue')
    ax1.set_ylabel('Total PO Amount (PKR)', color='skyblue')
    ax1.tick_params(axis='y', labelcolor='skyblue')
    ax1.set_xticklabels(firm_summary_viz['Contractor/ Firm'], rotation=90)

    formatter = mticker.FuncFormatter(lambda x, _: '{:.1f}M'.format(x/1e6))
    ax1.yaxis.set_major_formatter(formatter)

    ax2 = ax1.twinx()
    sns.lineplot(x='Contractor/ Firm', y='Average_Delivery_Percentage', data=firm_summary_viz, ax=ax2, color='red', marker='o')
    ax2.set_ylabel('Average Delivery Percentage', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    ax2.set_ylim(0, 100)

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.title('**SUMMARY - DELIVERY PROGRESS (FY 24/25)**', fontsize=14, fontweight='bold')
    plt.tight_layout()

    st.pyplot(fig)

else:
    st.info("Please upload an Excel file to begin.")
