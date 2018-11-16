
import pandas as pd
import numpy as np
from sodapy import Socrata
import geopandas
from shapely.geometry import Point

# Unauthenticated client only works with public data sets. Note 'None'
# in place of application token, and no username or password:
client = Socrata("data.detroitmi.gov",
                 '3qr06d02IsmTLGpO4lGgOruJS')

# Example authenticated client (needed for non-public datasets):
# client = Socrata(data.detroitmi.gov,
#                  MyAppToken,
#                  userame="user@example.com",
#                  password="AFakePassword")
print('Downloading Data...')
results = client.get("but4-ky7y", limit=100000)
# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)
results_df['Lng'] = results_df.site_location.apply(
    lambda x: x['coordinates'][0] if type(x) != float else -1)
results_df['Lat'] = results_df.site_location.apply(
    lambda x: x['coordinates'][1] if type(x) != float else -1)
results_df['Type'] = results_df.site_location.apply(
    lambda x: x['type'] if type(x) != float else 'None')
for time_field in ['permit_issued', 'permit_expire']:
    results_df[time_field] = results_df[time_field].astype('datetime64')
    results_df[time_field] = results_df[time_field].fillna(
        np.datetime64('1970-01-01'))
results_df['YearIssued'] = results_df['permit_issued'].apply(lambda x: x.year)
results_df['MonthYearIssued'] = results_df['permit_issued'].apply(
    lambda x: str(x.month)+'-'+str(x.year))
results_df['MonthIssued'] = results_df['permit_issued'].apply(
    lambda x: x.month)
results_df.to_csv('working/BuildingPermit.csv', index=None)

results_df['Coordinates'] = list(zip(results_df['Lng'], results_df['Lat']))
results_df['Coordinates'] = results_df['Coordinates'].apply(Point)
gdf = geopandas.GeoDataFrame(results_df, geometry='Coordinates')
BIZ_b = geopandas.read_file('BIZ_Boundary.geojson')
BIZ_b = BIZ_b.append([BIZ_b]*(gdf.shape[0]-1), ignore_index=True)
gdf['BIZ'] = gdf.within(BIZ_b)
gdf['BIZ'] = gdf['BIZ'].apply(lambda x: 'Yes' if x == True else 'No')
schema = geopandas.io.file.infer_schema(gdf)

schema['properties']['permit_expire'] = 'datetime'
schema['properties']['permit_issued'] = 'datetime'
print('Exporting shapefile...')
gdf.to_file('working/building_permit.shp',
            driver='ESRI Shapefile', schema=schema)
print('Finished, please check out working/building_permit.shp.')
