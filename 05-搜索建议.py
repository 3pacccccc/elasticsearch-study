from elasticsearch_dsl import Completion, DocType
from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer



"""
step1.在生成mapping的时候传入Completion字段
"""
class CustomAnalyzer(_CustomAnalyzer):
    def get_analysis_definition(self):
        return {}

ik_analyzer = CustomAnalyzer("ik_max_word", filter=['lowercase'])  # filter=['lowercase']表示对搜索进行大小写转换

class ArticleIndex(DocType):
    suggest = Completion(ik_analyzer)   # 搜索建议，自动补全的字段。本可以直接设置为suggest = Completion(analyzer="ik_max_word"),但目前版本有bug，故需要引入CustomAnalyzer传递ik_max_word


"""
step2:
1.在save_to_es函数下。写入article.suggest = [{'input':[], 'weight':2}]
2.新生成函数gen_suggests
"""