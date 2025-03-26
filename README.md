# **Repository Overview**  

The repository features a collection of modules to assist with managing and processing financial data.  

## **1. Bank Utilities**  

The `bank` module provides essential functions for handling bank account statements, including:  

- Merging bank statements from multiple individuals and accounts into a single, unified pandas DataFrame for easier analysis and reporting.  

- **Supported Banks**:  
  - Bank of Maharashtra  
  - Canara Bank  
  - ICICI Bank  
  - State Bank of India  

## **2. Securities Utilities**  

The `securities` module provides utilities for retrieving and processing financial market data, including:  

- **Fetching Historical Data**: Retrieves historical stock price data from Yahoo Finance using its internal API.  
  - Supports various **frequencies** (`1d`, `5d`, `1wk`, `1mo`, `3mo`).  
  - Allows selection of different **quote types** (`open`, `close`, `high`, `low`, `adjclose`).  

- **Fetching Corporate Events**: Retrieves corporate events (bonuses, dividends and stock splits) from BSE India using its internal API.  
  - Supports filtering by **event type** (`bonus`, `dividend`, `split`) or fetching all events.  
  - Allows specifying a **date range** (`start_date`, `end_date`).  

- **Fetching BSE Script Code**: Retrieves BSE Script Code from BSE India using its internal API.  
  - Supports filtering by **segment** (`Equity T+1`, `Equity T+0`, `Derivatives`, `Exchange Traded Funds`, `Debt or Others`, `Currency Derivatives`, `Commodity`, `Electronic Gold Receipts`, `Hybrid Security`, `Municipal Bonds`, `Preference Shares`, `Debentures and Bonds`, `Equity - Institutional Series`, `Commercial Papers`, `Social Stock Exchange`).
  - Supports filtering by **status** (`Active`, `Suspended`, `Delisted`) or fetching all.