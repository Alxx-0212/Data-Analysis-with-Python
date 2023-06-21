import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import streamlit as st
from babel.numbers import format_currency
import os

grouped_ordered_products = pd.read_csv("dashboard/grouped_ordered_products.csv")
rfm_orders_df = pd.read_csv("dashboard/rfm_orders_df.csv")


def grouped_sales_by_year(df):
    sales_df = df[df["order_status"] == "delivered"]
    sales_df["year"] = sales_df["order_purchase_timestamp"].dt.year
    grouped_sales_by_year = sales_df.groupby(sales_df["year"]).count().reset_index()

    return grouped_sales_by_year


def grouped_sales_by_month(df, year):
    df = df[df["order_status"] == "delivered"]
    sales_df_year = df[df["year"] == year]
    grouped_orders_by_month_year = (
        sales_df_year.groupby(sales_df_year["month"]).count().reset_index()
    )
    return grouped_orders_by_month_year


def most_ordered_products(df, n):
    top_ordered_products = (
        df.groupby(df["product_category_name_english"])
        .agg({"order_id": "sum"})
        .reset_index()
    )
    top_ordered_products = top_ordered_products.sort_values(
        by="order_id", ascending=False
    )
    return top_ordered_products.head(n)


def rfm_analysis_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg(
        {
            "order_purchase_timestamp": "max",
            "order_id": "nunique",
            "payment_value": "sum",
        }
    )
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    # menghitung kapan terakhir pelanggan melakukan transaksi (hari)
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(
        lambda x: (recent_date - x).days
    )

    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df


datetime_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
rfm_orders_df.sort_values(by="order_purchase_timestamp", inplace=True)
rfm_orders_df.reset_index(inplace=True)

for column in datetime_columns:
    rfm_orders_df[column] = pd.to_datetime(rfm_orders_df[column])

# Filter data
min_date = rfm_orders_df["order_purchase_timestamp"].min()
max_date = rfm_orders_df["order_purchase_timestamp"].max()

with st.sidebar:
    # Mengambil start_date & end_date dari date_input
    st.subheader("E-commerce Data Timeline")
    start_date, end_date = st.date_input(
        label="",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date],
    )

main_df = rfm_orders_df[
    (rfm_orders_df["order_purchase_timestamp"] >= str(start_date))
    & (rfm_orders_df["order_purchase_timestamp"] <= str(end_date))
]

st.header("E-commerce Dashboard")
st.subheader("Yearly Sales")
# plot grafik sales berdasarkan tahun
grouped_sales_by_year_df = grouped_sales_by_year(main_df)
fig = plt.figure(figsize=(8, 6))
plt.plot(
    grouped_sales_by_year_df["year"],
    grouped_sales_by_year_df["order_purchase_timestamp"],
    marker="o",
)
plt.xticks(grouped_sales_by_year_df["year"])
plt.yticks(grouped_sales_by_year_df["order_purchase_timestamp"])
plt.ylabel("orders delivered")
st.pyplot(fig)

st.subheader("Monthly Sales")
# plot grafik berdasarkan bulan pada tahun tertentu
years_df = main_df.groupby(main_df["year"]).count().reset_index()
years = years_df["year"].sort_values()
months = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]
tabs = []
n = 0
for i in years:
    tabs.append(str(i))

month_tabs = st.tabs(tabs)
for i in month_tabs:
    if n < len(tabs):
        grouped_sales_by_month_df = grouped_sales_by_month(main_df, years[n])
    with i:
        fig = plt.figure(figsize=(8, 6))
        month = []
        for i in grouped_sales_by_month_df["month"]:
            month.append(months[i - 1])
        plt.title("Orders Delivered by Month in {}".format(years[n]))
        plt.plot(
            month, grouped_sales_by_month_df["order_purchase_timestamp"], marker="o"
        )
        plt.xticks(month)
        plt.ylabel("orders delivered")
        st.pyplot(fig)
    n += 1

st.subheader("Most Ordered Products")
# plot grafik berdasarkan produk yang paling banyak diorder
m = 10
m = st.slider("Select the number of most ordered products :", min_value=5, max_value=50)
top10_products = most_ordered_products(grouped_ordered_products, m)
colors = ["#00ffaa"] + (["#D3D3D3"] * (m - 1))
fig = plt.figure(figsize=(12, 12))
plt.barh(top10_products["product_category_name_english"], top10_products["order_id"])
plt.title("Top {} most ordered products".format(m))

sns.barplot(
    x="order_id", y="product_category_name_english", data=top10_products, palette=colors
)
plt.ylabel(None)
plt.xlabel(None)
plt.tick_params(axis="y", labelsize=12)
st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")
# plot grafik RFM
rfm_df = rfm_analysis_df(rfm_orders_df)

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = round(rfm_df.monetary.mean(), 3)
    st.metric("Average Monetary", value=avg_frequency)

colors = ["#00ffaa"] * 5
fig = plt.figure(figsize=(20, 8))
sns.barplot(
    y="recency",
    x="customer_id",
    data=rfm_df.sort_values(by="recency", ascending=True).head(5),
    palette=colors,
)
plt.title("By Recency (days)", loc="center", fontsize=18)
st.pyplot(fig)

fig = plt.figure(figsize=(20, 8))
sns.barplot(
    y="frequency",
    x="customer_id",
    data=rfm_df.sort_values(by="frequency", ascending=False).head(5),
    palette=colors,
)
plt.title("By Frequency", loc="center", fontsize=18)
st.pyplot(fig)

fig = plt.figure(figsize=(20, 8))
sns.barplot(
    y="monetary",
    x="customer_id",
    data=rfm_df.sort_values(by="monetary", ascending=False).head(5),
    palette=colors,
)
plt.title("By Monetary", loc="center", fontsize=18)
st.pyplot(fig)
