# Introduction

This project is to store various scripts to automate tasks using the Power BI REST API. It enables secure management of Power BI data sources, credentials, and gateways, supporting both MasterUser and ServicePrincipal authentication modes. The application is designed to simplify integration and automation scenarios for Power BI administrators and developers.

# Getting Started

Follow these steps to set up and run the project on your local system:

1. **Clone the repository**
   ```sh
   git clone <your-repo-url>
   cd powerbi-rest-api
   ```
2. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```
3. **Configure environment variables**: Create a `.env` file in the project root and set the following variables:
   ```env
   CLIENT_ID=<your-client-id>
   CLIENT_SECRET=<your-client-secret>
   TENANT_ID=<your-tenant-id>
   AUTHORITY_URL=https://login.microsoftonline.com/${TENANT_ID}
   RESOURCE_URL=https://analysis.windows.net/powerbi/api
   API_URL=https://api.powerbi.com
   ```
4. **Run the application**
   ```sh
   python app.py
   ```
5. **Access the web interface**: Open your browser and navigate to `http://localhost:5000`.

# Build and Test
TODO: Describe and show how to build your code and run the tests. 

# Contribute
TODO: Explain how other users and developers can contribute to make your code better. 

If you want to learn more about creating good readme files then refer the following [guidelines](https://docs.microsoft.com/en-us/azure/devops/repos/git/create-a-readme?view=azure-devops). You can also seek inspiration from the below readme files:
- [ASP.NET Core](https://github.com/aspnet/Home)
- [Visual Studio Code](https://github.com/Microsoft/vscode)
- [Chakra Core](https://github.com/Microsoft/ChakraCore)