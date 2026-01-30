from azure.identity import InteractiveBrowserCredential
from microsoft_fabric_api import FabricClient

# Create credential and client
credential = InteractiveBrowserCredential()
fabric_client = FabricClient(credential)

# Get the list of workspaces using the client
workspaces = list(fabric_client.core.workspaces.list_workspaces())
print(f"Number of workspaces: {len(workspaces)}")
for workspace in workspaces:
    print(f"Workspace: {workspace.display_name}, Capacity ID: {workspace.capacity_id}")