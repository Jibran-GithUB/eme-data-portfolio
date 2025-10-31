
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

st.set_page_config(page_title="Inventory Analysis", layout="wide")
st.title("📦 Inventory Stock Movement Analysis")

uploaded_file = st.file_uploader("Upload the Excel file", type=["xlsx"])

if uploaded_file:
    excel_file = pd.ExcelFile(uploaded_file)
    dfs = {sheet_name: excel_file.parse(sheet_name) for sheet_name in excel_file.sheet_names}

    opening_stock_df = dfs.get("Opening Stock")
    stock_movement_df = dfs.get("Stock Movement")

    if opening_stock_df is not None:
        st.subheader("🔍 Opening Stock Overview")
        st.dataframe(opening_stock_df)

        sorted_stock = opening_stock_df.sort_values('Opening Balance', ascending=False)
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.barplot(x='Item Name', y='Opening Balance', data=sorted_stock, palette='viridis', ax=ax)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
        ax.set_title('Opening Stock', fontweight='bold')
        st.pyplot(fig)

    if stock_movement_df is not None:
        st.subheader("🔁 Stock Movement Overview")
        st.dataframe(stock_movement_df)

        received_df = stock_movement_df[stock_movement_df['Voucher Type'] == 'RV'].groupby('Item Name')['Quantity'].sum().reset_index()
        issued_df = stock_movement_df[stock_movement_df['Voucher Type'] == 'IV'].groupby('Item Name')['Quantity'].sum().reset_index()
        merged_stock = pd.merge(received_df, issued_df, on='Item Name', how='outer', suffixes=('_Received', '_Issued')).fillna(0)

        sorted_movement = merged_stock.sort_values('Quantity_Received', ascending=False)
        fig2, ax2 = plt.subplots(figsize=(15, 7))
        bar_width = 0.35
        index = range(len(sorted_movement))
        ax2.bar(index, sorted_movement['Quantity_Received'], bar_width, label='Received')
        ax2.bar([i + bar_width for i in index], sorted_movement['Quantity_Issued'], bar_width, label='Issued')
        ax2.set_xticks([i + bar_width / 2 for i in index])
        ax2.set_xticklabels(sorted_movement['Item Name'], rotation=90)
        ax2.set_title("Receipt & Issue Activity")
        ax2.legend()
        st.pyplot(fig2)

        matched_items_df = merged_stock[merged_stock['Quantity_Received'] == merged_stock['Quantity_Issued']]
        if not matched_items_df.empty:
            merged_matched_items_with_opening_stock = pd.merge(matched_items_df, opening_stock_df, on='Item Name', how='left')
            st.subheader("🎯 Items with Equal Receipt and Issue Quantities")
            fig3, ax3 = plt.subplots(figsize=(8, 8))
            ax3.pie(merged_matched_items_with_opening_stock['Opening Balance'],
                    labels=merged_matched_items_with_opening_stock['Item Name'],
                    autopct='%1.1f%%', startangle=140)
            ax3.set_title('Opening Stock of Balanced Items')
            st.pyplot(fig3)

        opening_balance = opening_stock_df.set_index('Item Name')['Opening Balance']
        issued_total = merged_stock.set_index('Item Name')['Quantity_Issued']
        stock_and_issue = pd.concat([opening_balance, issued_total], axis=1, keys=['Opening_Balance', 'Current_Issued_Rate']).fillna(0)

        def years_to_cease_receipt(row):
            ob = row['Opening_Balance']
            ci = row['Current_Issued_Rate']
            if ci <= 0:
                return float('inf') if ob > 0 else 0
            years, cumulative = 0, 0
            while cumulative < ob:
                years += 1
                cumulative += ci * (2 ** (years - 1))
                if cumulative >= ob:
                    return years
            return years

        stock_and_issue['Years_Sufficient'] = stock_and_issue.apply(years_to_cease_receipt, axis=1)
        finite_items = stock_and_issue[stock_and_issue['Years_Sufficient'] != float('inf')].sort_values('Years_Sufficient', ascending=True)
        st.subheader("⏳ Years Stock Will Last (Doubling Issue Rate)")
        st.dataframe(finite_items[['Years_Sufficient']])
