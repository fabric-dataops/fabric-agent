import json
import os
from datetime import date, timedelta

# import pandas as pd

from app import App
from config import BaseConfig
from services.aadservice import AadService
from services.powerbi.getactivityevents import GetActivityEventsService

# Initialize App configuration for standalone execution
App.setup(BaseConfig)

# Get today's date in YYYY-MM-DD format
current_date = date.today().strftime("%Y_%m_%d")

# Create a response counter
response_counter = 0

# Folder path
path = "./data/activity_events/"

# Initialize app object and load config
app = App.setup(BaseConfig)


def save_output(path, data, event_date, event_type, suffix):

    # Format date
    prefix = event_date.strftime("%Y-%m-%d")

    # Create folder
    current_folder_path = f"{path}json/{prefix}"
    if not os.path.exists(current_folder_path):
        os.makedirs(current_folder_path)

    # Write data to a file
    with open(
        f"{current_folder_path}/{prefix}_activity_events_{event_type}_{suffix}.json",
        "w",
        encoding="utf-8",
    ) as outfile:
        # Write the JSON data to the file
        json.dump(data, outfile)


def main(event_date):

    # Construct variables
    access_token = AadService.get_access_token()
    start_date_time = f"'{event_date}T00:00:00.000Z'"
    end_date_time = f"'{event_date}T23:59:59.999Z'"
    event_type = "all"
    global response_counter
    global path

    # Specify empty dataframe with all columns
    # schema = {
    #     "Id": str(),
    #     "RecordType": str(),
    #     "CreationTime": str(),
    #     "Operation": str(),
    #     "OrganizationId": str(),
    #     "UserType": int(),
    #     "UserKey": str(),
    #     "Workload": str(),
    #     "UserId": str(),
    #     "ClientIP": str(),
    #     "UserAgent": str(),
    #     "Activity": str(),
    #     "ItemName": str(),
    #     "WorkSpaceName": str(),
    #     "DatasetName": str(),
    #     "ReportName": str(),
    #     "CapacityId": str(),
    #     "CapacityName": str(),
    #     "WorkspaceId": str(),
    #     "ObjectId": str(),
    #     "DatasetId": str(),
    #     "ReportId": str(),
    #     "ArtifactId": str(),
    #     "ArtifactName": str(),
    #     "IsSuccess": str(),
    #     "ReportType": int(),
    #     "RequestId": str(),
    #     "ActivityId": str(),
    #     "DistributionMethod": str(),
    #     "ConsumptionMethod": str(),
    #     "ArtifactKind": str(),
    #     "RefreshEnforcementPolicy": str(),
    #     "ExportEventStartDateTimeParameter": str(),
    #     "ExportEventEndDateTimeParameter": str(),
    #     "ModelsSnapshots": str(),
    #     "DataConnectivityMode": str(),
    #     "RefreshType": str(),
    #     "LastRefreshTime": str(),
    #     "DatasourceId": str(),
    #     "GatewayClusterId": str(),
    #     "IsTenantAdminApi": str(),
    #     "GatewayClustersObjectIds": str(),
    # }
    # df = pd.DataFrame(schema, index=[0])

    activity_event_service = GetActivityEventsService()
    activity_api_response = activity_event_service.get_activity_event(
        access_token, start_date_time, end_date_time, event_type
    )

    if not activity_api_response.ok:
        print(activity_api_response.content)
        if not activity_api_response.reason == "Not Found":
            return (
                json.dumps(
                    {
                        "errorMsg": str(
                            f'Error {activity_api_response.status_code} {activity_api_response.reason}\nRequest Id:\t{activity_api_response.headers.get("RequestId")}'
                        )
                    }
                ),
                activity_api_response.status_code,
            )

    else:
        api_response = activity_api_response.json()

        # Reset the counter
        response_counter = 0

        # Set continuation URL
        cont_url = api_response["continuationUri"]

        # Set last result set flag
        last_result = api_response["lastResultSet"]

        # Extract activity event data
        activity_events = api_response["activityEventEntities"]

        # Save response as JSON
        save_output(path, activity_events, event_date, event_type, response_counter)

        # Append data to the dataframe
        # df2 = pd.DataFrame(activity_events)
        # df = df.dropna(subset=["Id"], inplace=True)
        # df = pd.concat([df, df2])

        # Increment the counter
        response_counter += 1

        # Repeat the api call to get all the data
        while not last_result:

            # Call the api again using the cont url

            activity_api_response_cont = activity_event_service.get_activity_event_cont(
                access_token, cont_url
            )

            if not activity_api_response_cont.ok:
                if not activity_api_response.reason == "Not Found":
                    return (
                        json.dumps(
                            {
                                "errorMsg": str(
                                    f'Error {activity_api_response.status_code} {activity_api_response.reason}\nRequest Id:\t{activity_api_response.headers.get("RequestId")}'
                                )
                            }
                        ),
                        activity_api_response.status_code,
                    )
            else:

                api_response_cont = activity_api_response_cont.json()

                # Set continuation URL
                cont_url = api_response_cont["continuationUri"]

                # Set last result set flag
                last_result = api_response_cont["lastResultSet"]

                # Extract activity event data
                activity_events = api_response_cont["activityEventEntities"]

                # print(json.dumps(api_response_cont, indent = 2))

                # Save response as JSON
                save_output(
                    path, activity_events, event_date, event_type, response_counter
                )

                # df2 = pd.json_normalize(activity_events)

                # df2 = pd.DataFrame(activity_events)
                # df = pd.concat([df, df2])

                # Increment the counter
                response_counter += 1

        # Set ID as Index of df
        # df = df.set_index("Id")

        # path = "./Data/ActivityEvents/"

        # Save df as CSV
        # df.to_csv(path + f"{event_date:%Y-%m-%d}" + f"_{event_type}" + ".csv")

        # Save df as parquet
        # df.to_parquet(
        #     path=f"{path}parquet/{event_date}_{event_type}_activity_events.parquet",
        #     index=True,
        # )


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(days=n)


start_date = date(2025, 9, 28)
end_date = date(2025, 10, 1)

for curr_date in daterange(start_date, end_date):
    main(curr_date)
