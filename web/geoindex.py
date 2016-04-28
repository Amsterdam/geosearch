"""
A helper class for usage by other services to add their data
to the geo search. This is made to be as easy as possible to integrate
into current services and to easily integrate future services

To minimize impact on the models no external dependencies are used
"""
# Python
import urllib.parse
import urllib.request


class GeoIndex(object):
    _default_mapping = {
        'naam': 'naam',
        'center': 'geometrie',
        'dataset': None,  # This cannot be defaulted
        'type': None,  # Dido
    }
    geosearch_index = 'geosearch'

    def __init__(self, model, mapping, elastic_host='0.0.0.0:9200', batch_size=1000):
        """
        Init the indexer give a model and a mapping.
        """
        self.mapping = _default_mapping.copy()
        self.mapping.update(mapping)
        self.model = model
        self.elastic_url = 'http://{0}/{1}/'.format(elastic_host, self.geosearch_index)
        self.batch_size = batch_size

    def get_queryset(self):
        """Overwrite this for custom query sets"""
        return self.model.objects.order_by('id')

    def batch(self):
        qs = self.get_queryset()
        total = qs.count()

        total_batches = int(total / self.batch_size)
        for i, start in enumerate(range(0, total, self.batch_size)):
            end = min(start + self.batch_size, total)
            yield (i+1, qs[start:end])

    def index(self):
        """Index the model to the geoseach index"""
        for batch_count, qs in self.batch():
            data = []
            for item in qs:
                entry = {}
                for key, value in self.mapping:
                    entry[key] = item.getattr(value)
                # Replacing the / for - in the type
                entry['type'] = entry['type'].replace('/', '-')
                data.append(entry)
            # Posting to elastic
            data = urllib.parse.urlencode(data)
            data = data.encode('utf-8')
            req = urllib.request.Request(url=self.elastic_url, data=data)
            with urllib.request.urlopen(req) as f:
                print(f.status)
                print(f.reason)
