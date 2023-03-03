from az.cli import az
import json
# This script is to help identify Azure NSG's that do not have dianostic data saved to a regional storage account
# And list them to allow the subscription owner to impliment the changes

# Login and get critical information
az("login")

SubScription = input("Enter Subscription Name: ")
StoragePrefix= input("Enter Storage Account naming Prefix: ")
DiagnosticSetting = "FiremonDataCollectorNSGRuleCounter"

az("account set --subscription "+SubScription)



rule2 = {
    "category": "NetworkSecurityGroupRuleCounter",
    "categoryGroup": "null",
    "enabled": "true",
    "retentionPolicy": {
        "days": 7,
        "enabled": "true"
    }
}

Out = "Script for Subscription: "+ SubScription
Out2 = "Resources"
# Go through all Azure locations
locations = (az("account list-locations --query \"[].{Name:name}\""))
for Datacenter in locations[1]:
    location = Datacenter['Name']
  
    # Set Storage Account for location
    Storage = StoragePrefix + location
    # Get list of NSG containing Resource Groups
    resourceGroups = (az("resource list --resource-type Microsoft.Network/networkSecurityGroups --location "+location)[1])
    for resource in resourceGroups:
        # Set Resource ID
        RID = resource['id']
        # See if Rule Exists
        HasSetting=(az("monitor diagnostic-settings show --name "+DiagnosticSetting+" --resource "+ RID)[0])
        
        if HasSetting == 3:
            # Diagnostics to Firemon are not Set
            CLICommand = "az monitor diagnostic-settings create --resource "+ RID +" -n "+DiagnosticSetting+" --storage-account "+ Storage +" --logs "+ json.dumps(rule2)
            Out = Out + "\n" + CLICommand
            
            # If we want to Force the setting
            # Uncomment the next lines
            #response = az("monitor diagnostic-settings create --resource "+ RID +" -n NSGRuleCounter --storage-account "+ Storage +" --logs "+ json.dumps(rule2))
            #print(response)
            
        # Write Recommendations to file
f = open("Recommendations.txt","w")
f.write(Out)
f.close
