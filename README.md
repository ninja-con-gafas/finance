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
  - Includes **debug logging** for debugging API calls.  
