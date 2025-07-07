import pandas as pd
from typing import Dict, Optional, List
import logging

class HCPCSLookup:
    #HCPCS code to description lookup system.
    
    def __init__(self):
        self.code_map = {}
        self.logger = logging.getLogger(__name__)
        
    def load_from_csv(self, file_path: str) -> None:
        #only keeps HCPCS and DESCRIPTION columns.
        
        try:
            #find the actual header row by reading multiple rows
            df_raw = pd.read_csv(file_path, low_memory=False, header=None)
            
            # we wanna look for the row that contains 'HCPCS' and 'DESCRIPTION'
            header_row = None
            for i in range(min(10, len(df_raw))):  # check first 10 rows (Its in the 10th row, this just reads past irrelevant rows )
                row_values = df_raw.iloc[i].astype(str).str.upper()
                if any('HCPCS' in str(val) for val in row_values) and any('DESCRIPTION' in str(val) for val in row_values):
                    header_row = i
                    break
            
            
            # read CSV with the correct header row
            df = pd.read_csv(file_path, low_memory=False, header=header_row)
            
            
            df.columns = df.columns.str.strip() #clean column names 
            
            # find HCPCS and DESCRIPTION columns (case insensitive)
            hcpcs_col = None
            desc_col = None
            
            for col in df.columns:
                col_upper = str(col).upper()
                if 'HCPCS' in col_upper:
                    hcpcs_col = col
                if 'DESCRIPTION' in col_upper:
                    desc_col = col
                    

            print(f"Found columns - HCPCS: '{hcpcs_col}', DESCRIPTION: '{desc_col}'")
            
            # we only need these columns, extract them. 
            df_clean = df[[hcpcs_col, desc_col]].copy()
            
            # clean data 
            df_clean = df_clean.dropna()  # rm rows with missing values
            df_clean[hcpcs_col] = df_clean[hcpcs_col].astype(str).str.strip() #convert to string 
            df_clean[desc_col] = df_clean[desc_col].astype(str).str.strip()
            
            # remove any possible empty strings and invalid entries
            df_clean = df_clean[(df_clean[hcpcs_col] != '') & (df_clean[desc_col] != '')]
            df_clean = df_clean[(df_clean[hcpcs_col] != 'nan') & (df_clean[desc_col] != 'nan')]
            
            # create lookup dictionary
            self.code_map = dict(zip(df_clean[hcpcs_col], df_clean[desc_col]))
            
            self.logger.info(f"Loaded {len(self.code_map)} HCPCS codes")
            
        except Exception as e:
            self.logger.error(f"Error loading CSV: {e}")
            raise
    


        
    def lookup(self, code: str) -> Optional[str]:
        """
        Look up description for a given HCPCS code.
        Returns None if code not found.
        """
        code = str(code).strip().upper()
        return self.code_map.get(code, "Description Not Found")
    
    def lookup_multiple(self, codes: List[str]) -> Dict[str, Optional[str]]:
        """
        Look up multiple codes at once.
        Returns dict with code -> description mapping.
        """
        results = {}
        for code in codes:
            results[code] = self.lookup(code)
        return results
    