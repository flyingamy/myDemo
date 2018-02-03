# coding: utf-8

from datetime import datetime

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from leancloud import Object
from leancloud import Query
from leancloud.errors import LeanCloudError
import scrapy
import re
from scrapy.crawler import CrawlerProcess
from scrapy import signals
from scrapy.utils.project import get_project_settings

class YanxuanSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["you.163.com"]
    start_urls = (
#        'http://you.163.com',
    )

    def parse(self, response):
        title = response.xpath('//title/text()').extract_first()
        image_url =  re.findall("primaryPicUrl\":\"(.+?)\"", response.body.decode("utf-8"))[0]
        yield {'Product title': title, 'Image url': image_url}

class MyPipeline(object):
    def process_item(self, item, spider):
        results.append(dict(item))

results = []


def runspider(url):
    # set up settings
    settings = get_project_settings()
    #settings.overrides['ITEM_PIPELINES'] = {'__main__.MyPipeline': 1}
    settings.set('ITEM_PIPELINES', {'views.MyPipeline': 1})

    crawler = CrawlerProcess(settings)
    crawler.crawl(YanxuanSpider, start_urls=[url])
    crawler.start()

    return results


class Todo(Object):
    pass


def index(request):
    return render(request, 'index.html', {})


def current_time(request):
    return HttpResponse(datetime.now())


class ItemToDisplay:

    def __init__(self, title, url):
        self.title = title
        self.url = url

class TodoView(View):
    def get(self, request):
        try:
            todos = Query(Todo).descending('createdAt').find()
        except LeanCloudError as e:
            if e.code == 101:  # 服务端对应的 Class 还没创建
                todos = []
            else:
                raise e

        itemsToDisplay = []
        for x in todos:
            title = x.get('product_title')
            url = x.get('image_url')
            if title or url:
                itemToDisplay = ItemToDisplay(title, url)
                itemsToDisplay.append(itemToDisplay)

        return render(request, 'todos.html', {
#            'titles': [x.get('product_title') for x in todos],
#            'todos': todos
            'items': itemsToDisplay
        })

    def post(self, request):
        url = request.POST.get('url')
        scraped = runspider(url)
        print("========= scraped ============")
        print scraped
        product_title = scraped[0].get('Product title')
        print("======== title ==========")
        print product_title.encode("utf-8")
        image_url = scraped[0].get('Image url')
        print("======== image_url ==========")
        print image_url.encode("utf-8")

        todo = Todo()
        todo.set('product_title', product_title.encode("utf-8"))
        todo.set('image_url', image_url.encode("utf-8"))
        print("===== todo ======")
        print todo
        try:
            todo.save()
            print("===== saved ======")
        except LeanCloudError as e:
            print("===== not saved ======")
            return HttpResponseServerError(e.error)
        return HttpResponseRedirect(reverse('todo_list'))
