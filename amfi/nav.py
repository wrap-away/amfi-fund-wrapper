"""Parse daily NAV file from AMFI.

Notes
-----
- For all MFs: https://www.amfiindia.com/spages/NAVAll.txt
- For historical data: http://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?tp=1&frmdt=01-Oct-2018&todt=03-Oct-2018 
"""
import io
import re
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple

import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Fund:
    SchemeCode: str
    SchemeName: str
    ISINDivPayoutGrowth: str
    ISINDivReinvestment: str
    NAV: str
    Date: str

LINE_BREAK = '\r\n'

AMFI_NAV_ALL_URL = 'https://www.amfiindia.com/spages/NAVAll.txt'

DATACLASS_AMFI_NAMES_TRANSFORMS = {
    'Scheme Code':'SchemeCode',
    'ISIN Div Payout/ ISIN Growth':'ISINDivPayoutGrowth',
    'ISIN Div Reinvestment':'ISINDivReinvestment',
    'Scheme Name':'SchemeName',
    'Net Asset Value':'NAV',
    'Date':'Date',
}

SCHEME_TYPE_CLASSES = [
    'Close Ended',
    'Open Ended',
    'Interval Fund Schemes'
]

def _load_nav_textfile() -> str:
    """Load NAVAll.txt from a source.
    In this case, AMFI Website. 

    Returns
    -------
    str:
        All lines in NAVAll.txt.
    """
    return requests.get(AMFI_NAV_ALL_URL).text

def _parse_fund_string(schema: List[str], fund_str: str) -> Fund:
    """Parse a mutual fund scheme string delimited by ;
    Returns
    -------
    Fund:
        fund information 
    """
    fund_info_raw = fund_str.split(';')
    fund_dict = {
        DATACLASS_AMFI_NAMES_TRANSFORMS[key]: val
        for key, val in zip(schema, fund_info_raw)
    }

    fund = Fund(**fund_dict)
    return fund

def parse_nav_file_lines(raw_data: str) -> Dict[str, Fund]:
    """Parse lines in the NAV File.

    Format
    0: <Schema Line {Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date}>\r\n
    1: \r\n
    2: <Scheme Type {Open Ended Schemes(Debt Scheme - Banking and PSU Fund)}>\r\n
    3: \r\n
    4: <Fund House {Aditya Birla Sun Life Mutual Fund}>\r\n
    5: \r\n
    6: <Fund>\r\n
    .
    6+n_funds-1: <Funds>\n
    6+n_funds: \n 
    """
    EMPTY_LINE = ' '
    
    curr_index = 0
    nav_lines = raw_data.split(LINE_BREAK)
        
    curr_line = (lambda: nav_lines[curr_index])
    def next_line():
        nonlocal curr_index
        curr_index += 1
        return nav_lines[curr_index]

    parsed_funds = dict()
    schema = curr_line().split(';')

    next_line()
    next_line()

    while curr_index < len(nav_lines):
        if curr_index == len(nav_lines) - 1:
            break
        
        for scheme_class in SCHEME_TYPE_CLASSES:
            if scheme_class in curr_line():
                scheme_type_str = curr_line().split('(')
                scheme_type = scheme_type_str[0]
                scheme_sub_type = scheme_type_str[1][:-1]

                if scheme_type not in parsed_funds:
                    parsed_funds[scheme_type] = dict()

                if scheme_sub_type not in parsed_funds[scheme_type]:
                    parsed_funds[scheme_type][scheme_sub_type] = dict()
                    
                next_line()
                next_line()
                
                while all(scheme_type_class not in curr_line() for scheme_type_class in SCHEME_TYPE_CLASSES):
                    fund_house = curr_line()
                    if fund_house not in parsed_funds[scheme_type][scheme_sub_type]:
                        parsed_funds[scheme_type][scheme_sub_type][fund_house] = list()

                    next_line() 
                    next_line()
                    
                    while curr_line() != EMPTY_LINE:
                        if curr_index == len(nav_lines) - 1:
                            break
                        
                        if curr_line() != '':
                            parsed_funds[scheme_type][scheme_sub_type][fund_house].append(_parse_fund_string(schema, curr_line()))
                        next_line()
                        
                    if curr_index == len(nav_lines) - 1:
                        break
                    
                    next_line()

    return parsed_funds
    
def get_all_mfs() -> Dict:
    """Get all mutual funds from AMFI.

    Returns
    -------
    Dict: Dictionary of all mutual funds.
        {
            <scheme_type: Open/Close/Interval>: {
                <scheme_sub_type: Money Market/Liquid/etc>: {
                    <fund_house_name>: [
                        <Fund>
                        ...
                    ]
                }
            }
        }
    """
    nav_file_data = _load_nav_textfile()
    parsed_funds = parse_nav_file_lines(nav_file_data)

    return parsed_funds

if __name__ == "__main__":
    parsed_funds = get_all_mfs()

    total_funds = 0
    for scheme_type, scheme_sub_type in parsed_funds.items():
        for scheme_sub_type_name, fund_houses in scheme_sub_type.items():
            sub_type_funds = sum([len(funds) for fund_house, funds in fund_houses.items()])
            total_funds += sub_type_funds
            logger.info(f'{scheme_type} {scheme_sub_type_name} {sub_type_funds}')
    
    logger.info(f'Total funds: {total_funds}')