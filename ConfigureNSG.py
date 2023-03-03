from az.cli import az
import os
import json
# This script is to help identify Azure NSG's that do not have dianostic data saved to a regional storage account
# And list them to allow the subscription owner to impliment the changes
# Output Status Bar Graphis
def status(state):
    match state:
        case "Found":                      # Setting Exists
            print("!",end='', flush=True) 
        case "NotFound":                   # Setting Does Not Exist
            print(".",end='', flush=True) 
        case "Locale":                     # Location Change
            print("·",end='', flush=True)
        case "Start":                      # Start of Progress Bar
            print("Start [",end='', flush=True)
        case "End":                        # End of Progress Bar
           print("] Done.") 
        case _:                            # Catch All
            print("_",end='', flush=True)
ERR=""

# Welcome Banner and Initial Settings
os.system('cls')
print("Welcome to the Azure NSG rule counter setting checker! \n\nTo get started, Enter your subscriptiion name\n\nIf you are not loggedin to azure, you will be prompted to do so.")
SubScription = input("Enter Subscription Name: ")
StoragePrefix = input("Storage Account Prefix: ")            
DiagnosticSetting = input("Diagnostic Setting Name: ")

# Data validation
if len(SubScription) == 0:
    ERR = ERR + "No Subscription Name entered\n"
if len(StoragePrefix) == 0:
    ERR = ERR + "No Storage Prefix entered\n"
if len(DiagnosticSetting) == 0:
    ERR = ERR + "No Diagnostic setting name entered\n"
if len(ERR) !=0:
    print(ERR)
    quit()
    
# Login and set subscription
loggedin=az("account show")
if loggedin[1]:
    #Logged In
    L1 = True
else:
    az("login")
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

Out = "" 
# Go through all Azure locations
locations = (az("account list-locations --query \"[].{Name:name}\""))
status("Start")
for Datacenter in locations[1]:
    status("Locale")
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
        Settings=(az("monitor diagnostic-settings list --resource "+ RID)[1])        
        if HasSetting == 0:
            status("Found")
        else:
            status("NotFound")
            # Diagnostics to Firemon are not Set
            CLICommand = "az monitor diagnostic-settings create --resource "+ RID +" -n "+DiagnosticSetting+" --storage-account "+ Storage +" --logs "+ json.dumps(rule2)
            Out = Out + "\n" + CLICommand
            # If we want to Force the setting
            # Uncomment the next lines
            #response = az("monitor diagnostic-settings create --resource "+ RID +" -n NSGRuleCounter --storage-account "+ Storage +" --logs "+ json.dumps(rule2))
            #print(response)
    
status("End")
# Write Recommendations to file
f = open(SubScription+"_Azure_cli_Script.txt","w")
f.write(Out)
f.close