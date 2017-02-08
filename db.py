from pyArango.connection import *

conn = Connection(username="root@odyssey", password="classics123")
db = conn["odyssey"]

def fetch_entity(name):
    aql = '''
    FOR e in Entities
        FILTER LOWER(e.name) == LOWER(@name)
        RETURN e
    '''
    res = db.AQLQuery(aql, rawResults = False, batchSize = 10, bindVars = { 'name': name })

    if len(res) == 1:
        return res[0]

    raise ValueError("Could not find entity or not specific enough")

def create_entity(name="", typee="", metadata=""):
    if name == "" or type(name) != str:
        raise ValueError("Need a string for name")

    if type(metadata) != str:
        raise ValueError("Need a string for metadata")

    if type(typee) != str:
        raise ValueError("Need a string for typee")

    collection = db["Entities"]
    doc = collection.createDocument()
    doc["name"] = name.capitalize().strip()
    doc["type"] = typee.strip()
    doc["metadata"] = metadata.strip()
    doc.save()
    return doc

def create_interaction(typee=None, fromm=None, to=None, sel={}, book=None):
    if typee == None or fromm == None or to == None or book == None:
        raise ValueError("Need typee, fromm, to, book")

    from_doc = fetch_entity(fromm.strip())
    to_doc = fetch_entity(to.strip())

    edge_collection  = db["Interactions"]
    collection = db["Entities"]
    edge = edge_collection.createEdge()
    edge.links(from_doc, to_doc)
    edge["type"] = typee.strip()
    edge["selection"] = sel
    edge["book"] = book
    edge.save()
    return edge

def fetch_interactions(book=None):
    collection = db["Interactions"]

    if book == None:
        return collection.fetchAll(rawResults=True)

    aql = '''
    FOR i in Interactions 
        FILTER i.book == @book
        RETURN i 
    '''
    res = db.AQLQuery(aql, rawResults = True, batchSize = 10, bindVars = { 'book': book })

    return res

def fetch_adjacent(entity):
    aql = '''
    FOR vertex IN
        1
        ANY
        @e_id
        GRAPH 'testGraph'
            RETURN vertex
    '''
    res = db.AQLQuery(aql, rawResults = True, batchSize = 10, bindVars = { 'e_id': entity['_id'] })
    return res

class BridgeFinder:
    def __init__(self, verticies):
        self.V = verticies
        self.bridges = []

    def find_bridges(self):
        print(len(self.V))
        self.count = 0
        self.low = [-1] * len(self.V)
        self.pre = [-1] * len(self.V)

        for i, v in enumerate(self.V):
            if self.pre[i] == -1:
                self.examine_vertex(i, i)
        
    def examine_vertex(self, u, v):
        self.pre[v] = self.count
        self.low[v] = self.pre[v]
        self.count += 1

        adjacent = fetch_adjacent(self.V[v])

        for wv in adjacent:
            w = [i for i,x in enumerate(self.V) if x['_id'] == wv['_id']][0]
            if self.pre[w] == -1:
                self.examine_vertex(v, w)
                self.low[v] = min(self.low[v], self.low[w])

                if self.low[w] == self.pre[w]:
                    self.bridges.append({'from': self.V[v]['_id'], 'to': self.V[w]['_id']})
                    
            elif w != u:
                self.low[v] = min(self.low[v], self.pre[w])

def fetch_bridges():
    verticies = [x for x in db["Entities"].fetchAll(rawResults = True)]
    bridgeFinder = BridgeFinder(verticies)
    bridgeFinder.find_bridges()
    return bridgeFinder.bridges
