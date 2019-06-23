"""
step1:创建新项目lcv_search,并且在app的views下面新建函数
    在新建app的models下面将《04-scrapy2elasticsearch.py》下面的代码拷贝到models下面
    完成搜索建议功能
"""
import json
import redis

from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View
from search.models import ArticleType


redis_cli = redis.StrictRedis()

class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s', '')
        re_data = []
        if key_words:
            s = ArticleType.search()
            # es的fuzzy搜索，具体请看02-elasticsearch简单查询
            s = s.suggest('my_suggest', key_words, completion={
                "field":"suggest","fuzzy":{
                    "fuzziness":2
                },
                "size":10   #   返回的个数
            })
            suggestions = s.excute_suggest()
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_data.append(source['title'])

        return HttpResponse(json.dumps(re_data), content_type='application/json')


"""
step2:实现搜索功能
"""
from elasticsearch import Elasticsearch

client = Elasticsearch(hosts=["127.0.0.1"])    # 可以指定多台主机

class SearchView(View):
    def get(self, request):
        key_words = request.GET.get('q', '')

        redis_cli.zincrby('search_keywrods_set', key_words)   # 对关键词搜索进行分数+1的操作

        topn_search = redis_cli.zrevrangebyscore('search_keywords_set', '+inf', '-inf', start=0, num=5)     # 获取热门的搜索'+inf', '-inf'表示取出所有范围内的
        response = client.search(
            index='jobbole',
            body={
                "query":{
                    "multi_match":{
                        "query":key_words,
                        "fields":{"tags", "title", "content"}
                    }
                },
                "from":0,
                "size":10,
                "highlight":{           # 对结果进行标亮处理
                    "pre_tags": ['<span class="keyWord">'],  # 对关键词进行包装，使得前端可以进行处理
                    "post_tags": ['</span>'],
                    "fields":{
                        "title":{},                                    # 需要标亮的区域
                        "content":{}                                   # 需要标亮的区域
                    }
                }
            }
        )

        total = response['hits']['total']                   #   获取到查询到的数量
        hit_list = []
        for hit in response['hits']['hits']:
            hit_dict = {}
            if 'title' in hit['highlight']:
                hit_dict['title'] = ''.join(hit['highlight']['title'])
            else:
                hit_dict['title'] = hit['_source']['title']

            if 'content' in hit['content']:
                hit_dict['content'] = ''.join(hit['highlight']['content'][:500])
            else:
                hit_dict['content'] = hit['_source']['content'][:500]

            hit_dict['create_date'] = hit['_souce']['create_date']
            hit_dict['url'] = hit['_souce']['url']
            hit_dict['score'] = hit['_score']

            hit_list.append(hit_dict)

        return render(request, 'reslut.html', {'all_hits':hit_list, 'key_words':key_words})

