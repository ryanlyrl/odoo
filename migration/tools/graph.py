'''
A simple directed graph implementation for tracking dependencies in the Postgres database
'''


class Graph:

    def __init__(self):
        self.vertices = []
        self.edges = {}

    def add_edge(self, from_vertex, to_vertex):
        if from_vertex not in self.vertices:
            self.vertices.append(from_vertex)

        if to_vertex not in self.vertices:
            self.vertices.append(to_vertex)

        if from_vertex not in self.edges:
            self.edges[from_vertex] = [to_vertex]
        elif to_vertex not in self.edges[from_vertex]:
            self.edges[from_vertex].append(to_vertex)

    def has_edge(self, from_vertex, to_vertex):
        return from_vertex in self.vertices and to_vertex in self.vertices[from_vertex]

    def has_vertex(self, vertex):
        return vertex in self.vertices

    def stringify(self):
        output = []
        for source_vertex in self.edges:
            for dest_vertex in self.edges[source_vertex]:
                output.append('"{}" -> "{}"'.format(source_vertex, dest_vertex))
        return '\n'.join(output)