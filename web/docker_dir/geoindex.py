"""
A helper class for usage by other services to add their data
to the geo search. This is made to be as easy as possible to integrate
into current services and to easily integrate future services

To minimize impact on the models no external dependencies are used
"""
# Python
import json
import urllib.parse
import urllib.request
# Packages
import requests

class GeoIndex(object):
    mapping = {
        'naam': 'naam',
        'center': 'geometrie',
    }
    index_meta = {
        'dataset': None,
        'type': None,
    }
    geosearch_index = 'geo'
    model = None
    elastic_url = 'http://0.0.0.0:9200/geo/'
    batch_size = 10

    def map_geofield(self):
        """
        Makes sure that the type's geofield is mapped as such
        Important!
        If no index_metahas been set this cannot execute
        """
        if not self.index_meta['dataset']:
            return None
        # @TODO switch to raw python
        mapping = {
            'properties': {
                'center': {
                    'type': 'geo_point'
                },
            },
        }
        # Setting the mapping for the type creating
        r = requests.put(self.elastic_url + '_mapping/' + self.index_meta['dataset'], data=json.dumps(mapping))
        return r.status_code

    def get_queryset(self):
        """Overwrite this for custom query sets"""
        try:
            return self.model.objects.order_by('id')
        except AttributeError:  # Handling a case in which there is no model set
            return None

    def batch(self):
        qs = self.get_queryset()
        if not qs:
            return []  # Queryset not created returning an empty list
        total = qs.count()

        total_batches = int(total / self.batch_size)
        for i, start in enumerate(range(0, total, self.batch_size)):
            end = min(start + self.batch_size, total)
            yield (i+1, qs[start:end])

    def index(self):
        """Index the model to the geoseach index"""
        print ('indexing')
        for batch_count, qs in self.batch():
            data = []
            for item in qs:
                entry = {}
                for key, value in self.mapping.items():
                    entry[key] = getattr(item, value)
                # Transforming to wgs84 for elastic
                entry['center'].transform('wgs84')
                entry['center'] = entry['center'].coords
                # Adding index meta
                entry.update(self.index_meta)
                # Replacing the / for - in the type
                entry['type'] = entry['type'].replace('/', '-')
                # @TODO switch to bulk insert
                r = requests.post(self.elastic_url + entry['dataset'], data = json.dumps(entry))
                
                data.append(entry)
            # @TODO switch over to raw python
            #r = requests.post(self.elastic_url, data=json.dumps(data))
            #print (r.status_code)
            # Posting to elastic
            #data = urllib.parse.urlencode(data)
            #data = data.encode('utf-8')
            #req = urllib.request.Request(url=self.elastic_url, data=data)
            #with urllib.request.urlopen(req) as f:
            #    print(f.status)
            #    print(f.reason)


class GeoIndexTask(GeoIndex):
    """
    A task friendly subclass
    It allows for giving a queryset
    """
    def get_queryset(self):
        # If no query set is explistily given but a model is create initial query set
        if self.model and not self.queryset:
            self.queryset = self.model.objects
        elif not self.queryset:
            # No query set or mode. Cant produce anything
            return None
        queryset = self.queryset.order_by('id')[:50]
        return queryset


    def execute(self):
        self.update_mapping()
        self.map_geofield()
        return self.index()

