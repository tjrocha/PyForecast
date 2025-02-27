# Script Name:      USGS_NWIS.py
# Script Author:    Kevin Foley, Civil Engineer
# Description:      A Dataloader for USGS_NWIS data in JSON format.
#                   Uses the REST Protocol

# Function takes the stationDict entry for the station in question
# along with datetime formatted dates and returns a datatable with columns (date, data, flag)

# Import libraries
import pandas as pd
import numpy as np
import requests
from datetime import datetime
INFORMATION = "ABC"


def dataLoaderInfo():

    REQUIREMENTS = ["DatasetExternalID", "DatasetParameterCode"]
    INFORMATION = """This dataset loads data from the USGS' NWIS database.

The dataloader can load any daily-mean (stat code 00003) data for a given Dataset ID and Parameter ID. 

The required metadata parameters are:

Dataset ID: The USGS site code for the site of interest (e.g. 06279940)
Dataset Parameter Code: The USGS parameter code for the site of interest (e.g. 00060 for streamflow)"""

    return REQUIREMENTS, INFORMATION



def dataLoader(stationDict, startDate, endDate):
    """
    This dataloader loads streamflow data from the USGS's NWIS database.The only necessary
    parameter is the USGS streamgage number that should be entered into the "Dataset ID" field.
    DEFAULT OPTIONS
    """

    # Generate a URL
    url = ('https://waterservices.usgs.gov/nwis/dv/?format=json' +
            # Specify the sites to download
            '&sites=' + stationDict['DatasetExternalID'] +
            # Specify the start date
            '&startDT=' + datetime.strftime( startDate, '%Y-%m-%d' ) +
            #Specify the end data
            '&endDT=' + datetime.strftime( endDate, '%Y-%m-%d' ) +
            # Specify that we want streamflow
            '&parameterCd=' + stationDict['DatasetParameterCode'] + 
            # Specify that we want daily means
            '&statCd=00003' +
            # Allow all sites
            '&siteStatus=all' )
    
    # Get the data
    response = requests.get(url)

    # Check the status code
    if response.status_code != 200:
        return 
    else:
        response = response.json()
    
    # Create a dataframe from the data
    df = pd.DataFrame(response['value']['timeSeries'][0]['values'][0]['value'])

    # Set the index to the dateTime index
    df.set_index(pd.DatetimeIndex(pd.to_datetime(df['dateTime'])), inplace = True)
    del df['dateTime'] # Delete the redundant column
    del df['qualifiers']

    # Replace missing data with NaN's
    df['value'].replace(to_replace = '-999999', value = np.nan, inplace = True)

    # Convert to numeric
    df['value'] = pd.to_numeric(df['value'])
    
    # Remove any duplicate data in the dataset
    df = df[~df.index.duplicated(keep='last')] # Remove duplicates from the dataset
    df = df[~df.index.isnull()]

    # Rename the columns
    df.columns = ['USGS | ' + stationDict['DatasetExternalID'] + ' | Streamflow | CFS']
    # Return the data frame
    return df.sort_index()