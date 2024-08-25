import requests
import json
import csv
from io import StringIO

from extras.scripts import *
from django.forms import PasswordInput, EmailInput

class ListKentikResources(Script):
    
    class Meta:
        name = "Kentik Resources"
        description = "Gets resources from Kentik Portal"
    
    #commit_default = False
    scheduling_enabled = False
        
    env = (
        ('com', 'US'),
        ('eu', 'EU')
    )    
    
    resources = (
        ('plans', 'PLANS'),
        ('sites', 'SITES'),
        ('site_markets', 'SITE MARKETS'),
        ('devices', 'DEVICES'),
        ('as_group', 'AS GROUPS')
    )
    
    
    cluster = ChoiceVar(
        choices = env,
        label = "Portal",
        default = "eu",
        description = "Pick the region of your portal account"
        
    )
    
    user_email = StringVar(
        label = "User Email",
        default = "someuser@some.domain",
        description = "Your Login User Email",
        regex =  r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b',
        widget = EmailInput
        )
    
    api_token = StringVar(
        label = "API Token",
        default = "",
        description = "Your User API Token",
        #widget = PasswordInput,
        min_length = 32,
        max_length = 32
    )
    
    resource = ChoiceVar(
        choices = resources,
        label = "Resource",
        default = "plans",
        description = "Pick a resource type"
    )
    
    output = ChoiceVar(
        choices = ( ('json', 'JSON') , ('raw', 'Raw JSON'), ('csv', 'CSV') ),
        label = "Output in",
        default = "json",
        description = "How to produce the results"
    )
    
    def get_plans(self, headers, env):
        # ToDo: handle errors man
        
        new_plans = []
        # valid plans, order is important as [3:] is a pak plan and max_fps is in metadata key
        valid_plans = ['legacy', 'edge', 'metrics', 'cloudpak', 'flowpak', 'cloud', 'universalpak']

        re = requests.get(f"https://api.kentik.{ env }/api/v5/plans", headers=headers)
        
        kentik_plans = re.json()['plans']
        
        for plan in kentik_plans:
            
            if plan['active'] and plan['metadata'].get('type') in valid_plans:    
                new_plan = {}
                new_plan.update(
                    { "id" : plan['id'],
                      "name" : plan['name'],
                      "type" : plan['metadata']['type'],
                      "devices": len(plan['devices']),
                      "max_devices": plan['max_devices'],
                      "fast_retention": plan['fast_retention'],
                      "full_retention": plan['full_retention']
                    # Apologies for this - wrote it better underneath
                    #**({"max_fps": plan['metadata']['pakFps']} if plan['metadata'].get('type') in valid_plans[3:] else {"max_fps": plan['max_fps']} )
                    }
                )
                if new_plan['type'] in valid_plans[3:]:
                    new_plan.update({ "max_fps": plan['metadata']['pakFps'] })
                else:
                    new_plan.update({ "max_fps": plan['max_fps'] })
                
                new_plans.append(new_plan)

        return new_plans, kentik_plans
    
    def dump_json(self, result):
        return f"{json.dumps(result, indent=4)}\n--Script End--"
    
    def dump_csv(self, result):
        output = StringIO()
        fields = result[0].keys()
        writer = csv.DictWriter(output, fieldnames=fields)

        writer.writeheader()
        for entry in result:
            writer.writerow(entry)

        csv_string = output.getvalue()

        return csv_string
    
    def run(self, data, commit):  
    
       kentik_header = {
           "Content-type": "application/json",
           "X-CH-Auth-Email": f"{ data['user_email']}",
           "X-CH-Auth-API-Token": f"{ data['api_token']}"
       }
       
       
       self.log_info(f"INFO: Using api.kentik.{data['cluster']}")
       #self.log_success(f"SUCCESS: Using email of: {data['user_email']}")
       #self.log_warning(f"WARNING: { kentik_header }")
    
       
       
       result, raw_result = self.get_plans(kentik_header,data['cluster'])
       
       
       
       
       ##self.log_success(f"{ result }")
       
       match data['output']:
           case "json":
               return self.dump_json(result)
           case "raw":
               return self.dump_json(raw_result)
           case "csv":
               return self.dump_csv(result)
           case _:
               return "Ooops, shouldn't get to that"