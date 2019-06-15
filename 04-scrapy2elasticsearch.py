from datetime import datetime

from elasticsearch_dsl import Text, Date, Keyword, Integer, DocType
from elasticsearch_dsl.connections import connections

connections.create_connection(hosts=["localhost"])   # 在此处指定需要连接的服务器，可以有多台

"""
在scrapy中，将爬取到的数据保存在elasticsearch里
注意:在安装elasticsearch_dsl的时候，版本要和elasticsearch对应，比如elasticsearch5.x.x对应elasticsearch_dsl5.x.x
具体操作：
1.新建一个文件夹models.py, 写一个类ArticleIndex
2.在scrapy的项目pipeline.py文件夹下面，新建一个类ElasticsearchPipeline
3.将ElasticsearchPipeline配置到setting里面
"""

class ArticleIndex(DocType):
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

        article.save()
        return item

if __name__ == '__main__':
    ArticleIndex.init()