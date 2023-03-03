from az.cli import az
import os
import json
# This script is to help identify Azure NSG's that do not have dianostic data saved to a regional storage account
# And list them to allow the subscription owner to impliment the changes
def status(state):
    # Output Status Bar Graphis
    match state:
        case "Found":                      # Setting Exists
            print("!",end='', flush=True) 
        case "NotFound":                   # Setting Does Not Exist
            print(".",end='', flush=True) 
        case "Locale":                     # Datacenter Change
            print("·",end='', flush=True)
        case "Start":                      # Start of Progress Bar
            print("Start [",end='', flush=True)
        case "End":                        # End of Progress Bar
           print("] Done.") 
        case _:                            # Catch All
            print("_",end='', flush=True)
def main():
    # Main script
    # Welcome Banner and Initial Settings
    os.system('cls')
    print("Welcome to the Azure NSG rule counter setting checker! \n\nTo get started, Enter your subscriptiion name\n\nIf you are not loggedin to azure, you will be prompted to do so.")
    SubScription = input("Enter Subscription Name: ")
    StoragePrefix = input("Storage Account Prefix: ")            
    DiagnosticSetting = input("Diagnostic Setting Name: ")
    #Process="Auto"     # "Auto" will attempt to add the diagnostic setting without further interaction
    Process="Manual"   # "Maunal" will output the scripts to a text file to allow manual processing.   
    #
    # Data validation
    ERR = ""
    if len(SubScription) == 0:
        ERR = ERR + "No Subscription Name entered\n"
    if len(StoragePrefix) == 0:
        ERR = ERR + "No Storage Prefix entered\n"
    if len(DiagnosticSetting) == 0:
        ERR = ERR + "No Diagnostic setting name entered\n"
    if len(Process) == 0:
        ERR = ERR + "No Process Mode defined\n"
    if Process != "Auto" and Process != "Manual":
        ERR = ERR + "Invalid Process Mode defined\n"
    if len(ERR) !=0:
        print("\u001b[31m"+ERR+"\033[0m")
        quit()
    #
    # Login and set subscription
    loggedin=az("account show")
    if loggedin[1]:
        #Logged In
        L1 = True
    else:
        az("login")
    az("account set --subscription "+SubScription)
    #
    # Retention Rule
    rule2 = {
        "category": "NetworkSecurityGroupRuleCounter",
        "categoryGroup": "null",
        "enabled": "true",
        "retentionPolicy": {
            "days": 7,
            "enabled": "true"
        }
    }
    #
    # Clear Output
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
                # Rule Exists, Do not add to script
                status("Found")
            else:
                # Rule does not exist
                status("NotFound")
                if Process == "Manual":
                    # Generate script to add rule
                    CLICommand = "az monitor diagnostic-settings create --resource "+ RID +" -n "+DiagnosticSetting+" --storage-account "+ Storage +" --logs "+ json.dumps(rule2)
                    # Add to output
                    if len(Out) == 0:
                        Out = CLICommand    
                    else:
                        Out = Out + "\n" + CLICommand
                elif Process== "Auto":
                    response = az("monitor diagnostic-settings create --resource "+ RID +" -n NSGRuleCounter --storage-account "+ Storage +" --logs "+ json.dumps(rule2))
    # Complete and Process Output        
    status("End")
    if Process == "Manual":
        # Write Recommendations to file
        f = open(SubScription+"_Azure_cli_Script.txt","w")
        f.write(Out)
        f.close
# Run Script        
main()