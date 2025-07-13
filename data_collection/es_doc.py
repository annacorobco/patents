from elasticsearch_dsl import analyzer, token_filter, Document, Text, Date

ngram_filter = token_filter('edge_ngram_filter', 'edge_ngram', min_gram=2, max_gram=20)

edge_ngram_analyzer = analyzer(
    'edge_ngram',
    tokenizer='standard',
    filter=['lowercase', ngram_filter]
)


class EsDocument(Document):
    def to_dict_repr(self):
        return self.to_dict()


class JustiaPatents(EsDocument):
    abstract = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    application_number = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    assignee = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    assistant_examiner = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    citations = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    claims = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    classifications = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    company = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    company_latest_patents = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    date_of_patent = Date(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    description = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    filed = Date(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    # history = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    inventor = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    patent_number = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    primary_examiner = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    publication_number = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    type = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    title = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')
    url = Text(analyzer=edge_ngram_analyzer, search_analyzer='standard')

    class Index:
        name = 'patents'
        index = 'patents'
