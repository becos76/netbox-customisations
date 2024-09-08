import requests
import json
import csv
from io import StringIO
from os import environ

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
        default = environ.get("KENTIK_EMAIL", "KENTIK_EMAIL not found"),
        description = "Your Login User Email",
        regex =  r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b',
        widget = EmailInput
        )
    
    api_token = StringVar(
        label = "API Token",
        default = environ.get("KENTIK_API_TOKEN", "KENTIK_API_TOKEN not found"),
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
    
    def get_plans(self, url, headers):
        # ToDo: handle errors man
        
        new_plans = []
        # valid plans, order is important as [3:] is a pak plan and max_fps is in metadata key
        valid_plans = ['legacy', 'edge', 'metrics', 'cloudpak', 'flowpak', 'cloud', 'universalpak']

        re = requests.get(url, headers=headers)
        
        #self.log_warning(f"WARNING: { re.json() }")
        
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

    def get_sites(self, url, headers):
        
        new_sites = []
        re = requests.get(url, headers=headers)
        kentik_sites = re.json()['sites']
        
        for site in kentik_sites:
            new_site = {}
            new_site.update(
                    { "id" : site['id'],
                      "name" : site['title'],
                      "lat" : site['lat'],
                      "lon": site['lon']
                    }
                )
            new_sites.append(new_site)
        
        return new_sites, kentik_sites
                

    
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
    
       PLANS_URL = f"https://api.kentik.{ data['cluster'] }/api/v5/plans"
       SITES_URL = f"https://grpc.api.kentik.{ data['cluster'] }/site/v202211/sites"
        
    
       kentik_header = {
           "Content-type": "application/json",
           "X-CH-Auth-Email": f"{ data['user_email']}",
           "X-CH-Auth-API-Token": f"{ data['api_token']}"
       }
       
       
       
       self.log_info(f"INFO: Using api.kentik.{data['cluster']}")
       #self.log_success(f"SUCCESS: Using email of: {data['user_email']}")
       #self.log_warning(f"WARNING: { kentik_header }")
    
       match data['resource']:
           case "plans":
            result, raw_result = self.get_plans(PLANS_URL, kentik_header)
           case "sites":
            result, raw_result = self.get_sites(SITES_URL, kentik_header)
           case "site_markets":
            return "Not there yet!!!"
           case "devices":
            return "Not there yet!!!"
           case "as_groups":
            return "Not there yet!!!"
           case _:
            return "Ooops, shouldn't get to that" 
                   
           
            
       
       
       
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