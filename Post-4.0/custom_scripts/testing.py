class NewSiteScript(Script):
    
    class Meta:
        name = "New Site"
        description = "Provision a new site"
    
    site_name = StringVar(
        description = "Name of new site"
    )
    
    site_status = ChoiceVar(
        description = "Status for the new site",
        choices = SiteStatusChoices
    )
    
    def run(self, data, commit):
        site = Site(
            name = data['site_name'],
            slug = slugify(data['site_name']),
            status = data['site_status']
        )
        site.save()
        self.log_success(f"Created new site: { site }")
        
        output = [ 'name,slug,status' ]
        
        for site in Site.objects.all():
            attrs = [ site.name,site.slug,site.status ]
            output.append(','.join(attrs))
        
        return '\n'.join(output)