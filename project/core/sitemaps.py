from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticSitemap(Sitemap):
    def items(self):
        return ['home','about','how-it-works','plan_list','blog','faqs']
    def location(self,item):
        return reverse(item)    