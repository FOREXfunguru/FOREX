import pandas as pd
import argparse
import pdb

parser = argparse.ArgumentParser(description='Merge workbooks')

parser.add_argument('--wbs', required=True, help="Comma-separated list of workbooks to merge")
parser.add_argument('--ix', required=True, help="Ix of worksheet in --wbs to be parsed")
parser.add_argument('--out', required=True, help=".xlsx file name of merged workbook")


args = parser.parse_args()

to_merge=args.wbs.split(",")

cols = None
all_df_lst = []
for wb in to_merge:
    df = pd.read_excel(wb, int(args.ix))
    newDF=df.iloc[:, 1:]
    cols = newDF.columns
#    all_df_lst.append(df)
    all_df_lst.append(newDF)

# Merge all the dataframes in all_df_list
# Pandas will automatically append based on similar column names
appended_df = pd.concat(all_df_lst, sort=True, axis=0)
appended_df = appended_df[cols]

# Write the appended dataframe to an excel file
# Add index=False parameter to not include row numbers
appended_df.to_excel(args.out, index=False)
