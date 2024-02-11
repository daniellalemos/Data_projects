#customer records
SELECT * FROM customers;

#otal number of transactions
SELECT count(*) FROM sales.transactions; #150283

#total number of customers
SELECT count(*) FROM sales.customers; #38

#analize transactions
SELECT * FROM sales.transactions limit 5;
SELECT * FROM sales.transactions WHERE currency = "USD"; #only 2 transactions that need to be converted to INR

#Market chennai -> Mark001
SELECT * FROM sales.transactions WHERE market_code = "Mark001";
SELECT count(*) FROM sales.transactions WHERE market_code = "Mark001"; #1035
#distinct products sold in chennai
SELECT DISTINCT product_code FROM sales.transactions WHERE market_code = "Mark001";

#transactions joined by date table
SELECT sales.transactions.*, sales.date.* FROM sales.transactions INNER JOIN sales.date ON sales.transactions.order_date = sales.date.date;
#transactions in 2020 joined by date table
SELECT sales.transactions.*, sales.date.* FROM sales.transactions INNER JOIN sales.date ON sales.transactions.order_date = sales.date.date WHERE sales.date.year = 2020;
#total revenue in 2020 or total sales
SELECT SUM(sales.transactions.sales_amount) FROM sales.transactions INNER JOIN sales.date ON sales.transactions.order_date = sales.date.date WHERE sales.date.year = 2020; #142235559

#total revenue in 2020 or total sales in chennai
SELECT SUM(sales.transactions.sales_amount) FROM sales.transactions INNER JOIN sales.date ON sales.transactions.order_date = sales.date.date
WHERE sales.date.year = 2020 AND sales.transactions.market_code = "Mark001"; #2463024