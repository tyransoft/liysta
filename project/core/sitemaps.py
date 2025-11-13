from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticSitemap(Sitemap):
    def item(self):
        return ['home','about','how-it-works','plan_list']
    def location(self,item):
        return reverse(item)    