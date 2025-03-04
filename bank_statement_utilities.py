"""
The module offer tools to present bank statements from various accounts and individuals in a unified format, displaying
transactions in chronological order to facilitate analytical data processing.

1. The files of bank account statement must be named using one of the naming conventions:

    1.1. <initials_of_account_holder>_<initials_of_bank>_<financial_year>.<extention>
    1.2. <initials_of_account_holder>_<initials_of_bank>_<financial_year_start><financial_year_end>.<extention>

        Examples:
            1.1.  TS_BB_2024.xls
                    TS = Tony Stark
                    BB = Bank of Baroda
                    2024 = 2024-2025

            1.2.  CJP_HDFC_2020.csv
                    CJP = Captain Jack Sparrow
                    HDFC = Housing Development Finance Corporation Bank
                    2020 = 2020-2021

            1.3. JM_IDFC_2011_2013.htm
                    JM = Jerry Maguire
                    IDFC = Infrastructure Development Finance Company Bank
                    2011_2013 = 2011-2012, 2012-2013, 2013-2014


2. List of banks supported by the utility:

    BOM: Bank of Maharashtra
    CB: Canara Bank
    ICICI: ICICI Bank
    SBI: State Bank of India

3. Schema of consolidated account statement

    Column Name	        Data Type

    date    	        datetime
    description 	    varchar
    credit	            float
    debit	            float
    balance             float
    bank    	        varchar
    account_holder     	varchar
"""

import os
import re

from bs4 import BeautifulSoup
from decimal import Decimal, getcontext
from pandas import concat, DataFrame, read_csv, read_excel, Series, to_datetime, Timestamp
from typing import Dict, List, Optional, Tuple, Union

getcontext().prec = 12

def are_files_continuous(file_names: List[str]) -> bool:

    """
    Processes a list of file names, extracts account holder information, bank name and financial year from each file and
    checks whether the files span a continuous range of financial years for each bank account.

    If any years are missing from the range, a `ValueError` is raised, detailing which files are missing.

    args:
        file_names (List[str]): A list of account statement file names.

    returns:
        bool: True if all files for each bank account cover a continuous range of financial years.

    raises:
        ValueError: If any files are missing for the continuous range of financial years.
    """

    bank_accounts: Dict[Tuple[str, str], List[int]] = {}
    for file_name in file_names:
        account_holder, bank_name, financial_year, extension = get_file_info(file_name)
        bank_account = (bank_name, account_holder)
        if bank_account not in bank_accounts:
            bank_accounts[bank_account] = []
        bank_accounts[bank_account].append(int(financial_year))
    
    def is_continuous(years: List[int]) -> bool:
        return len(years) == (max(years) - min(years) + 1)
    
    if all(is_continuous(years) for years in bank_accounts.values()):
        return True
    else:
        missing_files = []
        for bank_account, years in bank_accounts.items():
            years = sorted(years)
            min_year, max_year = years[0], years[-1]
            all_years = set(range(min_year, max_year + 1))
            existing_years = set(years)
            missing_years = list(all_years - existing_years)
            if missing_years:
                missing_files.extend(f"{bank_account[0]}{year}_{bank_account[1]}" 
                                     for year in missing_years)
        raise ValueError(f"Files are missing:\n" + "\n".join(missing_files))

def consolidate_statements(bank_statements: Dict[str, DataFrame]) -> DataFrame:

    """
    Consolidates multiple bank statement DataFrames into a single DataFrame, recalculating the cumulative running
    balance across all transactions.

    args:
        bank_statements (Dict[str, DataFrame]): A dictionary where the keys are bank identifiers and the values 
                                                are DataFrames containing bank transactions with columns 
                                                `date`, `description`, `credit`, `debit` and `balance`.

    returns:
        DataFrame: A consolidated DataFrame with recalculated balances and sorted by date and credit in ascending and
        descending order respectively.

    raises:
        None
    """

    return (concat(bank_statements.values(), ignore_index=True)
            .sort_values(by=["date", "credit"], ascending=[True, False])
            .assign(balance=lambda x: (x['credit'].apply(Decimal) + x['debit'].apply(Decimal)).cumsum())
            .reindex(columns=["date", "description", "credit", "debit", "balance", "bank", "account_holder"]))


def enrich_bom_statement(statement: DataFrame) -> DataFrame:

    """
    Cleans and enriches a Bank of Maharashtra statement DataFrame by renaming columns, formatting dates and converting debit,
    credit and balance columns to numeric values. It also removes unnecessary columns and fills any missing values with
    0.0.

    args:
        statement (DataFrame): A DataFrame containing raw Bank of Maharashtra statement data.

    returns:
        DataFrame: A cleaned and enriched DataFrame with renamed columns ("date", "description", "debit", "credit", 
                  "balance") and numeric values for debit, credit and balance.

    raises:
        None
    """

    return (statement.iloc[1:-1]
            .rename(columns=lambda x: x.strip())
            .map(lambda x: x.strip())
            .drop(columns=["Cheque No"])
            .rename(columns={"Date": "date", 
                             "Particulars": "description", 
                             "Withdrawals": "debit", 
                             "Deposits": "credit", 
                             "Balance": "balance"})
            .assign(date=lambda x: to_datetime(x["date"], format="%d/%m/%y"),
                    debit=lambda x: x["debit"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    .replace("", 0.0).astype(float),
                    credit=lambda x: x["credit"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    .replace("", 0.0).astype(float), 
                    balance=lambda x: x["balance"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    .replace("", 0.0).astype(float))
            .fillna(0.0))
    
def enrich_cb_statement(statement: DataFrame) -> DataFrame:

    """
    Cleans and enriches a Canara Bank statement DataFrame by renaming columns, formatting dates and converting debit,
    credit and balance columns to numeric values. It also removes unnecessary columns and fills any missing values with
    0.0.

    args:
        statement (DataFrame): A DataFrame containing raw Canara Bank statement data.

    returns:
        DataFrame: A cleaned and enriched DataFrame with renamed columns (`date`, `description`, `debit`, `credit`, 
                  `balance`) and numeric values for debit, credit and balance.

    raises:
        None
    """

    return (statement.drop(columns=["Value Date", "Cheque No.", "Branch Code", "Unnamed: 8"])
            .rename(columns={"Txn Date": "date", 
                             "Description": "description", 
                             "Debit": "debit", 
                             "Credit": "credit", 
                             "Balance": "balance"})
            .assign(date=lambda x: to_datetime(x["date"]
                                               .str.extract(r"(\d{2}-\d{2}-\d{4})")[0], 
                                               format="%d-%m-%Y"),
                    debit=lambda x: x["debit"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    .replace("", 0.0).astype(float),
                    credit=lambda x: x["credit"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    .replace("", 0.0).astype(float), 
                    balance=lambda x: x["balance"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    .replace("", 0.0).astype(float))
            .fillna(0.0))

def enrich_icici_statement(statement: DataFrame) -> DataFrame:

    """
    Processes an ICICI Bank statement DataFrame by renaming columns, formatting dates and converting debit, credit and
    balance columns to numeric values. It removes unnecessary columns and rows, adjusts the index and fills missing
    numeric values with 0.0.

    args:
        statement (DataFrame): A DataFrame containing raw ICICI Bank statement data.

    returns:
        DataFrame: A cleaned and enriched DataFrame with renamed columns (`date`, `description`, `debit`, `credit`, 
                  `balance`) and numeric values for debit, credit and balance.

    raises:
        None
    """

    return (statement.get(list(statement.keys())[0])
            .iloc[12:].reset_index(drop=True)
            .rename(columns={"Unnamed: 2": "date",
                             "Unnamed: 5": "description",
                             "Unnamed: 6": "debit",
                             "Unnamed: 7": "credit",
                             "Unnamed: 8": "balance"})
            .drop(columns=["Unnamed: 0", "Unnamed: 1", "Unnamed: 3", "Unnamed: 4"])
            .assign(date=lambda x: to_datetime(x["date"], format="%d/%m/%Y"),
                    debit=lambda x: x["debit"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    .replace("", 0.0).astype(float), 
                    credit=lambda x: x["credit"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    .replace("", 0.0).astype(float), 
                    balance=lambda x: x["balance"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                    .replace("", 0.0).astype(float))
                    .dropna())

def enrich_merged_statement(bank_statements: Dict[str, DataFrame]) -> Dict[str, DataFrame]:

    """
    Takes a dictionary of bank statements and adds an initial "Balance brought forward" row for each statement, drops
    the balance column and assigns minus sign to debit values.

    args:
        bank_statements (Dict[str, DataFrame]): A dictionary where the keys are bank identifiers and the values
                                                are DataFrames containing bank transactions with columns
                                                `date`, `description`, `credit`, `debit` and `balance`.

    returns:
        Dict[str, DataFrame]: A dictionary with the same keys, but with the enriched DataFrames, with the "balance"
                              column removed and contains an opening balance as debit or credit with appropriate sign
                              convention.

    raises:
        None
    """

    for bank_account in bank_statements.keys():
        statement = bank_statements.get(bank_account)

        opening_transaction: Series = statement.iloc[0].copy()
        opening_transaction["description"] = "Balance brought forward"
        opening_transaction["credit"] = Decimal(opening_transaction["credit"])
        opening_transaction["debit"] = Decimal(opening_transaction["debit"])
        opening_transaction["balance"] = Decimal(opening_transaction["balance"])
        opening_transaction["balance"] += opening_transaction["debit"] - opening_transaction["credit"]
        if opening_transaction["balance"] >= 0:
            opening_transaction["debit"], opening_transaction["credit"] = Decimal(0.0), opening_transaction["balance"]
        else:
            opening_transaction["debit"], opening_transaction["credit"] = opening_transaction["balance"], Decimal(0.0)

        statement = (concat([DataFrame([opening_transaction]), statement], ignore_index=True)
                     .assign(debit=lambda x: (- x["debit"]).apply(Decimal),
                             date=lambda x: to_datetime(x['date'], format='mixed').dt.strftime('%Y-%m-%d'))
                     .drop(columns=["balance"])
                     .rename(columns={"account holder": "account_holder"})
                     .reindex(columns=["date", "description", "credit", "debit", "bank", "account_holder"]))

        bank_statements[bank_account] = statement
    return bank_statements
    
def enrich_sbi_statement(statement: DataFrame) -> DataFrame:

    """
    Processes a State Bank of India bank statement DataFrame by removing unnecessary columns, renaming the remaining
    columns and converting date, debit, credit and balance fields to appropriate formats. It cleans the data by
    replacing missing values with 0.0 and ensures that numeric fields are correctly formatted.

    args:
        statement (DataFrame): A DataFrame containing raw State Bank of India bank statement data.

    returns:
        DataFrame: A cleaned and enriched DataFrame with renamed columns (`date`, `description`, `debit`, `credit`, 
                  `balance`), numeric values for debit, credit and balance and formatted date values.

    raises:
        None
    """

    return (statement.iloc[:-1]
            .drop(columns=["Value Date",
                           "Ref No./Cheque No.",
                           "Unnamed: 7"])
            .replace("", 0.0)
            .rename(columns={"Txn Date": "date",
                             "Description": "description", 
                             "Debit": "debit", 
                             "Credit": "credit", 
                             "Balance": "balance"})
            .assign(date=lambda x: to_datetime(x["date"], format="%d %b %Y"),
                    debit=lambda x: x["debit"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                                                                .replace("", 0.0).astype(float),
                    credit=lambda x: x["credit"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                                                                .replace("", 0.0).astype(float),
                    balance=lambda x: x["balance"].astype(str).str.replace(r"[^0-9.]", "", regex=True)
                                                                .replace("", 0.0).astype(float)))
    
def enrich_statements(statements: Dict[str, DataFrame], 
                      account_holders: Dict[str, str]) -> Dict[str, DataFrame]:

    """
    Processes and enriches a dictionary of bank statement DataFrames by applying specific enrichment functions based on
    the bank name (Bank of Maharashtra, Canara Bank, ICICI Bank, or State Bank of India). It also adds the account holder's name and the bank
    name to each statement.

    args:
        statements (Dict[str, DataFrame]): A dictionary where the keys are file names and the values are DataFrames
                                           representing bank statements for different banks.
        account_holders (Dict[str, str]): A dictionary mapping account holder identifiers to their names to associate
                                          transactions in the consolidated statement to respective account holder.
            Examples:
                1. account_holders = {
                                    "TS": "Tony Stark",
                                    "CJP": "Captain Jack Sparrow"
                                    }

                2. account_holders = {}

    returns:
        Dict[str, DataFrame]: A dictionary with the same keys, but with the enriched DataFrames, including cleaned
                              data, the account holder's name and the bank name for each statement.

    raises:
        None
    """

    for file_name in statements.keys():
        account_holder, bank_name, financial_year, extension = get_file_info(file_name)
        statement = statements.get(file_name)
        
        if bank_name == "BOM":
            statement["bank"] = "Bank of Maharashtra"
        elif bank_name == "CB":
            statement = enrich_cb_statement(statement=statement)
            statement["bank"] = "Canara Bank"
        elif bank_name == "ICICI":
            statement = enrich_icici_statement(statement=statement)
            statement["bank"] = "ICICI Bank"
        elif bank_name == "SBI":
            statement.columns = statement.columns.str.strip()
            statement = enrich_sbi_statement(statement=statement)
            statement["bank"] = "State Bank of India"
            
        statement["account holder"] = account_holders.get(account_holder, None)
        statements[file_name] = statement
    return statements
    
def find_data_start(file_path: str, delimiter: str, min_columns: int) -> int:

    """
    Reads a file line by line to determine where tabular data starts by checking if the line contains at least a minimum
    number of columns, based on the specified delimiter.

    args:
        file_path (str): The path to the file to be analyzed.
        delimiter (str): The character used to separate columns in the file (e.g., ',', '\t').
        min_columns (int): The minimum number of columns that a line must contain to be considered the start of
                           the tabular data.

    returns:
        int: The line number (0-indexed) where the tabular data starts.

    raises:
        ValueError: If no line in the file contains the minimum number of columns, indicating the start of
                    tabular data couldn't be found.
    """

    with open(file_path, "r") as file:
        for start_line, line in enumerate(file):
            if len(line.strip().split(delimiter)) >= min_columns:
                return start_line
    raise ValueError("Unable to determine where tabular data starts in the file.")

def get_file_info(file_name: str) -> Union[Tuple[str, str, str, str], Tuple[str, str, str, str, str]]:

    """
    Extracts account holder information, bank name, financial year(s) and file extension from a file name using a
    predefined pattern.

    args:
        file_name (str): The file name in one of the following formats:
                         1. "account_holder_bank_name_financial_year.extension"
                         2. "account_holder_bank_name_financial_year_start_financial_year_end.extension"

    returns:
        Union[Tuple[str, str, str, str], Tuple[str, str, str, str, str]]: A tuple containing the extracted values:
                                                                          - For format 1: account holder, bank name,
                                                                            financial year and file extension.
                                                                          - For format 2: account holder, bank name,
                                                                            financial year start, financial year end
                                                                            and file extension.

    raises:
        AttributeError: If the file name does not match either of the expected patterns.
    """

    patterns = [
        r"([^_]+)_([^_]+)_([^_]+)\.(\w+)",
        r"([^_]+)_([^_]+)_([^_]+)_([^_]+)\.(\w+)"
    ]

    for pattern in patterns:
        match = re.match(pattern, file_name)
        if match:
            return match.groups()
    
    raise AttributeError("The file name does not match either of the expected patterns.")

def get_financial_year(date: Timestamp) -> str:

    """
    Determines the financial year for a given date.

    args:
        date (Timestamp): The date for which to determine the financial year.

    returns:
        str: The financial year in the format "YYYY-YYYY".
    """

    start_year = date.year if date.month >= 4 else date.year - 1
    end_year = start_year + 1
    return f"{start_year}-{end_year}"

def get_consolidated_statement(directory: str, account_holders: Dict[str, str]) -> DataFrame:

    """
    Retrieves and consolidates bank account statements from the specified directory. The function loads all statement
    files from the directory, enriches the statements and adds account holder information, merges them and consolidates
    the data into a unified pandas DataFrame.

    args:
        directory (str): The path to the directory containing the bank account statement files.
        account_holders (Dict[str, str]): A dictionary mapping account numbers to account holder names for enrichment.

    returns:
        DataFrame: A consolidated pandas DataFrame containing all the bank account statements.

    raises:
        None
    """

    return consolidate_statements(enrich_merged_statement(merge_statements(enrich_statements(load_all_files(directory),
                                                                                             account_holders))))

def load_all_files(directory: str) -> Dict[str, Optional[Union[Dict[str, DataFrame], DataFrame]]]:

    """
    Generates a consolidated DataFrame by loading, enriching and merging all bank statements from a given directory.
    It applies the necessary transformations to the statements and consolidates them into a single DataFrame with
    recalculated balances.

    args:
        directory (str): The path to the directory containing the bank statement files.
        account_holders (Dict[str, str]): A dictionary mapping account holder identifiers to their names.

    returns:
        DataFrame: A consolidated DataFrame containing all enriched and merged bank statement data with recalculated 
                  balances.

    raises:
        None
    """

    file_names: List[str] = [file_name 
                             for file_name in os.listdir(directory) 
                             if os.path.isfile(os.path.join(directory, file_name)) 
                             and 
                             re.match(r"([A-Z]+)_([A-Z]+)_(\d{4})_(\d{4})\.(\w+)", file_name)]
    
    if file_names:
        for file_name in file_names:
           print(f"Processing file: {file_name}")
           file_path = os.path.join(directory, file_name)
           (initials_of_account_holder, initials_of_bank, 
            financial_year_start, financial_year_end, extension) = get_file_info(file_name)
           
           if initials_of_bank == "BOM":
               save_segregated_statements(statements=segregate_statement
                                          (enrich_bom_statement(read_as_html_file(file_path=file_path, min_columns=5))),
                                          initials_of_account_holder=initials_of_account_holder,
                                          initials_of_bank=initials_of_bank,
                                          directory=directory)

    statements: Dict[str, Optional[Union[Dict[str, DataFrame], DataFrame]]] = {}
    
    file_names: List[str] = [file_name 
                             for file_name in os.listdir(directory) 
                             if os.path.isfile(os.path.join(directory, file_name)) 
                             and 
                             re.match(r"([A-Z]+)_([A-Z]+)_\d{4}\.\w+", file_name)]
    
    if are_files_continuous(file_names=file_names):
        for file_name in file_names:
            print(f"Processing file: {file_name}")
            file_path = os.path.join(directory, file_name)
            data_frame: DataFrame = load_file_to_dataframe(file_path)
            if data_frame is not None:
                statements[file_name] = data_frame

        print(f"Out of {len(file_names)}, loaded {len(statements)} files:")
        for file_name in statements.keys():
            print(file_name)

        return statements

def load_file_to_dataframe(file_path: str) -> Optional[Union[Dict[str, DataFrame], DataFrame]]:

    """
    Attempts to load a file into a DataFrame by first trying to read it as an Excel file. If that fails, it attempts to
    read the file as a text file. If both attempts fail, it returns None.

    args:
        file_path (str): The path to the file to be loaded.

    returns:
        Optional[Union[Dict[str, DataFrame], DataFrame]]: A DataFrame if the file is successfully read,
                                                         or a dictionary of DataFrames if reading as an Excel file,
                                                         or None if the file cannot be read.

    raises:
        None
    """

    try:
        try:
            return read_as_excel_file(file_path)
        except Exception as e:
            print(f"Error reading {file_path} as an Excel file: {e}")
        return read_as_text_file(file_path)
    except Exception as e:
        print(f"Error reading file {file_path} as a text file: {e}")
        return None
    
def merge_statements(statements: Dict[str, DataFrame]) -> Dict[str, DataFrame]:

    """
    Merges multiple bank statement DataFrames into a dictionary of DataFrames, grouped by bank account. Statements for
    the same bank account are concatenated and each resulting DataFrame is sorted by date and credit amount.

    args:
        statements (Dict[str, DataFrame]): A dictionary where the keys are file names and the values are DataFrames
                                           representing individual bank statements.

    returns:
        Dict[str, DataFrame]: A dictionary where the keys are bank account identifiers and the values are merged
                              DataFrames for each bank account, sorted by date and credit amount.

    raises:
        None
    """

    bank_accounts: Dict[str, DataFrame] = {}
    for file_name, statement in statements.items():
        account_holder, bank_name, financial_year, extension = get_file_info(file_name)

        bank_account: str = f"{bank_name}_{account_holder}"
        if bank_account not in bank_accounts.keys():
            bank_accounts[bank_account] = statement
        else:
            bank_accounts[bank_account] = concat([bank_accounts[bank_account], statement])
            
    for merged_statements in bank_accounts.values():
        merged_statements.sort_values(by=["date", "credit"], ascending=[True, False], inplace=True)
        
    return bank_accounts

def read_as_excel_file(file_path: str) -> Union[Dict[str, DataFrame], DataFrame]:

    """
    Attempts to read an Excel file using various engines. It tries to load the file with each engine in a specified
    order and returns the data as a dictionary of DataFrames (one for each sheet) or a single DataFrame if the file
    contains only one sheet. If all attempts fail, it raises a `ValueError`.

    args:
        file_path (str): The path to the Excel file to be read.

    returns:
        Union[Dict[str, DataFrame], DataFrame]: A dictionary of DataFrames if the file has multiple sheets,
                                                or a single DataFrame if there is only one sheet.

    raises:
        ValueError: If the file cannot be read with any of the available engines.
    """

    engines: List[str] = ["openpyxl", "pyxlsb", "xlrd"]
    
    for engine in engines:
        try:
            return read_excel(file_path, sheet_name=None, engine=engine)
        except Exception as e:
            print(f"Failed to load {file_path} with engine {engine}: {e}")    
    raise ValueError(f"Unable to read {file_path} as an Excel file.")

def read_as_html_file(file_path: str, min_columns: int) -> DataFrame:

    """
    Reads an HTML file to determine where tabular data starts by checking if the table contains at least a minimum number
    of columns. Returns the table data as a pandas DataFrame.

    args:
        file_path (str): The path to the HTML file to be analyzed.
        min_columns (int): The minimum number of columns that the table must contain to be considered the start of the 
                            tabular data.

    returns:
        DataFrame: A DataFrame containing the table data.

    raises:
        ValueError: If no table in the file contains the minimum number of columns.
    """

    soup = BeautifulSoup(open(file_path), 'html.parser')

    for table in soup.find_all("table"):
        header_row = table.find("tr")
        header_cells = header_row.find_all(['th', 'td'])

        if len(header_cells) >= min_columns:
            list_header = [cell.get_text() for cell in header_cells]
            data = []
            for row in table.find_all("tr")[1:]:
                sub_data = []
                for cell in row.find_all(['td', 'th']):
                    try:
                        sub_data.append(cell.get_text())
                    except:
                        continue
                data.append(sub_data)

            return DataFrame(data=data, columns=list_header)

    raise ValueError("No table contains the minimum number of columns.")

def read_as_text_file(file_path: str) -> DataFrame:

    """
    Attempts to read a text file as either a TSV (tab-separated values) or CSV (comma-separated values) file. It first
    tries to read the file as a TSV, identifying the start of the tabular data and if that fails, it tries to read it
    as a CSV. If both attempts fail, the function prints an error message.

    args:
        file_path (str): The path to the text file to be read.

    returns:
        DataFrame: A DataFrame with the content of the file.

    raises:
        None
    """

    try:
        start_line: int = find_data_start(file_path, delimiter="\t", min_columns=5)
        return read_csv(file_path, delimiter="\t", engine="python", skiprows=start_line)
    except Exception as e:
        print(f"Failed to read {file_path} as a TSV file: {e}")

    try:
        start_line: int = find_data_start(file_path, delimiter=",", min_columns=5)
        return read_csv(file_path, delimiter=",", engine="python", skiprows=start_line)
    except Exception as e:
        print(f"Failed to read {file_path} as a CSV file: {e}")

def save_segregated_statements(statements: Dict[str, DataFrame], initials_of_account_holder: str, initials_of_bank: str, 
                               directory: str) -> None:
    
    """
    Saves segregated financial statements each associated with a specific financial year and saves them as CSV files.
    The filenames are constructed using the initials of the account holder, the initials of the bank and the financial year.

    args:
        statements (Dict[str, DataFrame]): A dictionary where the keys are strings representing financial years
                                       (e.g., '2022-2023') and the values are pandas DataFrames containing
                                       the financial statements for those years.
        initials_of_account_holder (str): The initials of the account holder to be included in the filename.
        initials_of_bank (str): The initials of the bank to be included in the filename.
        directory (str): The directory path where the CSV files will be saved. If the directory does not exist,
                        it will be created.

    returns:
        None
    """

    os.makedirs(directory, exist_ok=True)

    for financial_years, statement in statements.items():
        financial_year = financial_years.split('-')[0]
        file_name = f"{initials_of_account_holder}_{initials_of_bank}_{financial_year}.csv"
        file_path = os.path.join(directory, file_name)
        statement.drop(columns=['financial_year']).to_csv(file_path, index=False)


def segregate_statement(bank_statement: DataFrame) -> Dict[str, DataFrame]:

    """
    Segregate bank statement DataFrame into multiple DataFrames based on financial years.

    args:
        bank_statement (DataFrame): The input DataFrame containing a `date` column.
    
    returns:
        dict: A dictionary where keys are financial years and values are corresponding DataFrames.
    """

    return {
        year: group
        for year, group in (
            bank_statement
            .assign(date=to_datetime(bank_statement["date"], format="%Y-%m-%d"))
            .assign(financial_year=lambda x: x["date"].apply(get_financial_year))
            .groupby("financial_year")
        )
    }
