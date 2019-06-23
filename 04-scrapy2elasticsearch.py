from datetime import datetime

from elasticsearch_dsl import Text, Date, Keyword, Integer, DocType, Completion
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer

es = connections.create_connection(ArticleIndex._doc_type.using)   # 在此处指定需要连接的服务器，可以有多台

"""
在scrapy中，将爬取到的数据保存在elasticsearch里
注意:在安装elasticsearch_dsl的时候，版本要和elasticsearch对应，比如elasticsearch5.x.x对应elasticsearch_dsl5.x.x
具体操作：
1.新建一个文件夹models.py, 写一个类ArticleIndex
2.在scrapy的项目pipeline.py文件夹下面，新建一个类ElasticsearchPipeline
3.将ElasticsearchPipeline配置到setting里面
"""

class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}

ik_analyzer = CustomAnalyzer("ik_max_word", filter=['lowercase'])  # filter=['lowercase']表示对搜索进行大小写转换


def gen_suggest(index, info_tuple):
    # 根据字符串生成搜索建议数组
    used_words = set()
    suggests = []
    for text, weight in info_tuple:
        if text:
            # 调用es的analyze接口分析字符串
            words = es.indices.analyze(index=index, analyzer="ik_max_word", params={'filter':['lowercase']}, body=text)
            analyzed_words = [r['token'] for r in words if len(words) > 1]   # 过滤掉返回的单个字
            new_words = analyzed_words - used_words
        else:
            new_words = set()
        if new_words:
            suggests.append({'input':list(new_words), 'weight':weight})
    return suggests


class ArticleIndex(DocType):
    suggest = Completion(ik_analyzer)   # 搜索建议，自动补全的字段。本可以直接设置为suggest = Completion(analyzer="ik_max_word"),但目前版本有bug，故需要引入CustomAnalyzer传递ik_max_word
    title = Text(analyzer="ik_max_word")
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    front_image_url = Keyword()
    front_image_path = Keyword()
    praise_nums = Integer()
    comment_nums = Integer()
    fav_nums = Integer()
    tags = Text(analyzer="ik_max_word")
    content = Text(analyzer="ik_max_word")

    class Meta:
        index = "jobbole"    # 在elasticsearch里面的索引名称
        doc_type = "article"  # 在elasticsearch里面的type名称

class ElasticsearchPipeline(object):
    """
    将爬来的数据保存在es
    """

    def process_item(self, item, spider):
        article = ArticleIndex()
        article.title = item['title']
        article.create_date = item['create_date']
        article.content = item['content']
        article.front_image_path = item['front_image_path']
        article.front_image_url = item['front_image_url']
        article.praise_nums = item['praise_nums']
        article.fav_nums = item['fav_nums']
        article.comment_nums = item['comment_nums']
        article.url = item['url']
        article.tags = item['tags']

        article.suggest = gen_suggest(ArticleIndex._doc_type.index, ((article.title, 10), (article.tags, 7)))

        article.save()
        return item

if __name__ == '__main__':
    ArticleIndex.init()