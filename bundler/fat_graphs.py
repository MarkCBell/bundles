
from __future__ import print_function
from string import ascii_lowercase
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

# This module is quite a mess. At some point this should
# be tidied up and replaced with a more rigid structure.

def ends(edge):
    return edge[0], edge[2]

def other_end(edge, this_end):
    if edge[0] != this_end:
        return edge[0]
    elif edge[2] != this_end:
        return edge[2]
    else:
        return this_end

def to_left_of(in_dir, out_dir, target):
    if in_dir < out_dir:
        return in_dir < target < out_dir
    else:
        return not (out_dir < target < in_dir)

class FatGraph():
    ''' This class represents a fat graph, that is a graph in which the edges adjacent to
    a vertex occur in a predefined order. This can be used, for example, to represent the
    spine of a surface. '''
    def __init__(self, edge_connections, vertex_orders, dual=None, annuli=[], rectangles=[]):
        self.num_vertices = len(vertex_orders)
        self.num_edges = len(edge_connections)
        self.edge_connections = [tuple(e) for e in edge_connections]
        self.vertex_orders = [tuple(v) for v in vertex_orders]
        self.with_boundary = any(None in v for v in self.vertex_orders)
        
        # Compute a maximal tree and the distances from the basepoints.
        used_edges = [False] * self.num_edges
        used_vertices = [False] * self.num_vertices
        distance = [-1] * self.num_vertices
        directions = [-1] * self.num_vertices
        directions_rev = [-1] * self.num_vertices
        
        Q = Queue()
        distance[0] = 0
        used_vertices[0] = True
        Q.put(0)
        while not Q.empty():
            current = Q.get()
            for index, i in enumerate(self.vertex_orders[current]):
                if i is not None:
                    for end in ends(self.edge_connections[i]):
                        if not used_vertices[end]:
                            distance[end] = distance[current] + 1
                            directions[end] = index
                            directions_rev[end] = min(k for k in range(len(self.vertex_orders[end])) if self.vertex_orders[end][k] == i)
                            used_vertices[end] = True
                            used_edges[i] = True
                            Q.put(end)
        
        self.tree, self.tree_sequence, self.tree_directions, self.tree_directions_rev = used_edges, distance, directions, directions_rev
        
        self.dual = dual if dual is not None else self.get_dual()
        
        self.annuli, self.rectangles = annuli, rectangles
        self.fundamental_group = self.get_fundamental_group()
        
        G = self.fundamental_group[0]
        numbered_generators = [i for i, g in enumerate(G) if g]
        if len(numbered_generators) > 26:
            print('Too much homology for this alphabet.')
            exit(1)
        self.fundamental_group_generators = ascii_lowercase[:len(numbered_generators)]
        self.path_lookup = dict(zip(self.fundamental_group_generators, [self.generator_path(e_num) for e_num in numbered_generators]))
        self.generator_lookup = dict(zip(numbered_generators, self.fundamental_group_generators))
    
    @classmethod
    def from_twister_file(cls, file_contents):
        num_vertices = 0
        for line in file_contents.split('\n'):
            data = line.split('#')[0].split(',')
            if data[0] == 'annulus' or data[0] == 'rectangle':
                largest_num = max(map(lambda x: abs(int(x)) + 1, data[3:]))
                if largest_num > num_vertices:
                    num_vertices = largest_num
        
        if num_vertices == 0: raise ValueError('Cannot load fat graph with no vertices.')
        
        vertex_orders = [[None] * 4 for i in range(num_vertices)]
        edge_connections = []
        annuli, rectangles = [], []
        
        for line in file_contents.split('\n'):
            data = line.split('#')[0].split(',')
            
            if data[0] == 'annulus' or data[0] == 'rectangle':
                name, inverse_name = data[1], data[2]
                pairs = zip(data[3:], data[4:]+data[3 if data[0] == 'annulus' else 4:4])
                for a, b in pairs:
                    x, y = abs(int(a)), abs(int(b))
                    e = (x, 1 if a[0] == '+' else 0, y, 3 if b[0] == '+' else 2)
                    
                    e_num = len(edge_connections)
                    vertex_orders[x][1 if a[0] == '+' else 0] = e_num
                    vertex_orders[y][3 if b[0] == '+' else 2] = e_num
                    edge_connections.append(e)
                
                curve_start = abs(int(data[3]))
                curve = []
                for d in data[3:]:
                    curve.append(1 if d[0] == '+' else 0)
                
                if data[0] == 'rectangle':
                    end_dir = curve[-1]
                    start_dir = 3 if curve[0] == 1 else 2
                    curve = curve[:-1]
                    rectangles.append([name, inverse_name, curve_start, curve, start_dir, end_dir])
                else:
                    annuli.append([name, inverse_name, curve_start, curve])
        
        return cls(edge_connections, vertex_orders, None, annuli, rectangles)
    
    def __str__(self):
        return str(self.edge_connections) + '\n' + str(self.vertex_orders)
    
    def get_reverse_direction(self, v, d):
        e_num = self.vertex_orders[v][d]
        edge = self.edge_connections[e_num]
        v = other_end(edge, v)
        d = min(k for k in range(len(self.vertex_orders[v])) if self.vertex_orders[v][k] == e_num and (k != d or edge[0] != edge[2]))
        return v, d
    
    def get_dual(self):
        edge_connections = [[-1, -1, -1, -1] for i in range(self.num_edges)]
        vertex_orders = []
        
        edge_directions = [[False] * len(v) for v in self.vertex_orders]
        
        for i in range(self.num_vertices):
            for j in range(len(self.vertex_orders[i])):
                if self.vertex_orders[i][j] is None: continue
                if edge_directions[i][j]: continue
                
                current_vertex = len(vertex_orders)
                new_vertex = []
                
                v, d = i, j
                edge_directions[v][d] = True
                moved = False
                while v != i or d != j or not moved:
                    moved = True
                    e_num = self.vertex_orders[v][d]
                    e = self.edge_connections[e_num]
                    
                    if e[0] != e[2]:
                        edge_connections[e_num][0 if e[0] == v else 2] = current_vertex
                        edge_connections[e_num][1 if e[0] == v else 3] = len(new_vertex)
                    else:
                        edge_connections[e_num][0 if e[1] == d else 2] = current_vertex
                        edge_connections[e_num][1 if e[1] == d else 3] = len(new_vertex)
                    
                    new_vertex.append(e_num)
                    v, d = self.get_reverse_direction(v, d)
                    
                    num_connections = len(self.vertex_orders[v])
                    
                    moved = False
                    while self.vertex_orders[v][d] is None or not moved:
                        if moved: new_vertex.append(None)
                        moved = True
                        d = (d+1) % num_connections
                    
                    edge_directions[v][d] = True
                
                vertex_orders.append(new_vertex)
        
        return FatGraph(edge_connections, vertex_orders, self)
    
    def _flow(self, information, deleted_edges):
        Q = Queue()
        for i in range(len(information)):
            if information[i]: Q.put(i)
        
        while not Q.empty():
            current = Q.get()
            for edge in self.vertex_orders[current]:
                if edge is not None:
                    if not deleted_edges[edge]:
                        for endpoint in ends(self.edge_connections[edge]):
                            if not information[endpoint]:
                                information[endpoint] = True
                                Q.put(endpoint)
        
        return information
    
    def connected(self, deleted_edges):
        visited = [False] * self.num_vertices
        visited[0] = True
        
        return all(self._flow(visited, deleted_edges))
    
    def connected_to_none_vertex(self, deleted_edges):
        visited = [None in v for v in self.vertex_orders]
        
        return all(self._flow(visited, deleted_edges))
    
    def get_fundamental_group(self):
        relator = []
        relator_signs = []
        deleted_edges = list(self.tree)
        
        for i in range(self.num_edges):
            if not deleted_edges[i]:
                deleted_edges[i] = True
                if not self.dual.connected(deleted_edges): deleted_edges[i] = False
        
        if self.with_boundary:
            # Work out relator.
            for i in range(self.num_edges):
                if not deleted_edges[i]:
                    deleted_edges[i] = True
                    if not self.dual.connected_to_none_vertex(deleted_edges): deleted_edges[i] = False
        else:
            v, d = 0, 0
            moved = False
            while v != 0 or d != 0 or not moved:
                moved = True
                e_num = self.dual.vertex_orders[v][d]
                edge = self.dual.edge_connections[e_num]
                if deleted_edges[e_num]:
                    relator.append(e_num)
                    relator_signs.append(edge[0] == v and edge[1] == d)
                    d = (d + 1) % len(self.dual.vertex_orders[v])
                else:
                    v = other_end(edge, v)
                    d = min(k for k in range(len(self.dual.vertex_orders[v])) if self.dual.vertex_orders[v][k] == e_num)
                    d = (d + 1) % len(self.dual.vertex_orders[v])
        
        generators = [d and not t for t,d in zip(self.tree, deleted_edges)]
        
        return generators, relator, relator_signs
    
    def generator_path(self, edge_generator):
        e1, e2 = ends(self.edge_connections[edge_generator])
        d0 = min(k for k in range(len(self.vertex_orders[e1])) if self.vertex_orders[e1][k] == edge_generator)
        
        P = []
        while e1 != 0:
            d = self.tree_directions[e1]
            P.append(d)
            e1 = other_end(self.edge_connections[self.vertex_orders[e1][self.tree_directions_rev[e1]]], e1)
        P = P[::-1]
        
        P.append(d0)
        
        while e2 != 0:
            d = self.tree_directions_rev[e2]
            P.append(d)
            e2 = other_end(self.edge_connections[self.vertex_orders[e2][self.tree_directions_rev[e2]]], e2)
        
        return P
    
    def twist_action(self, path_dirs, annulus_start, annulus_dirs, left):
        annulus_vertices = [annulus_start]
        annulus_dirs_rev = []
        for d in annulus_dirs:
            v2, d2 = self.get_reverse_direction(annulus_vertices[-1], d)
            annulus_vertices.append(v2)
            annulus_dirs_rev.append(d2)
        
        annulus_dirs_rev = annulus_dirs_rev[::-1]
        
        annulus_dirs_dict = dict(zip(annulus_vertices, annulus_dirs))
        annulus_dirs_rev_dict = dict(zip(annulus_vertices[1:][::-1], annulus_dirs_rev))
        
        path_vertices = [0]
        path_dirs_rev = []
        for d in path_dirs:
            v2, d2 = self.get_reverse_direction(path_vertices[-1], d)
            path_vertices.append(v2)
            path_dirs_rev.append(d2)
        
        P = []
        on_annulus = path_vertices[0] in annulus_vertices
        entered_left = False
        
        n = len(path_dirs)
        for i in range(n):
            v, d = path_vertices[i], path_dirs[i]
            if on_annulus and d != annulus_dirs_dict[v] and d != annulus_dirs_rev_dict[v]:
                on_annulus = False
                exit_left = to_left_of(annulus_dirs_rev_dict[v], annulus_dirs_dict[v], d)
                if exit_left:
                    if left:
                        split_point = len(annulus_vertices) - 1 - min(k for k in range(len(annulus_vertices)) if annulus_vertices[k] == v)
                        P.extend(annulus_dirs_rev[split_point:] + annulus_dirs_rev[:split_point])
                    else:
                        split_point = min(k for k in range(len(annulus_vertices)) if annulus_vertices[k] == v)
                        P.extend(annulus_dirs[split_point:] + annulus_dirs[:split_point])
            
            P.append(d)
            
            if not on_annulus:
                v2, d2 = path_vertices[(i+1) % n], path_dirs_rev[i]
                if v2 in annulus_vertices:
                    on_annulus = True
                    entered_left = to_left_of(annulus_dirs_rev_dict[v2], annulus_dirs_dict[v2], d2)
                    if entered_left:
                        if left:
                            split_point = min(k for k in range(len(annulus_vertices)) if annulus_vertices[k] == v2)
                            P.extend(annulus_dirs[split_point:] + annulus_dirs[:split_point])
                        else:
                            split_point = len(annulus_vertices) - 1 - min(k for k in range(len(annulus_vertices)) if annulus_vertices[k] == v2)
                            P.extend(annulus_dirs_rev[split_point:] + annulus_dirs_rev[:split_point])
        
        return self.simplify_path(P)
    
    def half_twist_action(self, path_dirs, rectangle_start, rectangle_dirs, starting_None_dir, ending_None_dir, left):
        rectangle_vertices = [rectangle_start]
        rectangle_dirs_rev = []
        for d in rectangle_dirs[:-1]:
            v2, d2 = self.get_reverse_direction(rectangle_vertices[-1], d)
            rectangle_vertices.append(v2)
            rectangle_dirs_rev.append(d2)
        rectangle_dirs_rev = list(rectangle_dirs_rev) + [starting_None_dir]
        rectangle_dirs = list(rectangle_dirs) + [ending_None_dir]
        
        rectangle_dirs_dict = dict(zip(rectangle_vertices, rectangle_dirs))
        rectangle_dirs_rev_dict = dict(zip(rectangle_vertices, rectangle_dirs_rev))
        
        A, A2 = [], []
        moved = False
        v, d = rectangle_vertices[-1], rectangle_dirs[-1]
        dirs = [k for k in range(len(self.vertex_orders[v])) if self.vertex_orders[v][k] is not None]
        d0 = min(dirs) if d >= max(dirs) else min(k for k in dirs if k >= d)
        d = d0
        while v != rectangle_vertices[-1] or d != d0 or not moved:
            moved = True
            A.append(d)
            v, d_back = self.get_reverse_direction(v, d)
            dirs = [k for k in range(len(self.vertex_orders[v])) if self.vertex_orders[v][k] is not None]
            d = min(dirs) if d_back >= max(dirs) else min(k for k in dirs if k > d_back)
            A2.append(d_back)
        A2 = A2[::-1]
        
        B, B2 = [], []
        moved = False
        v, d = rectangle_vertices[0], rectangle_dirs_rev[-1]
        dirs = [k for k in range(len(self.vertex_orders[v])) if self.vertex_orders[v][k] is not None]
        d0 = min(dirs) if d >= max(dirs) else min(k for k in dirs if k >= d)
        d = d0
        while v != rectangle_vertices[-1] or d != d0 or not moved:
            moved = True
            B.append(d)
            v, d_back = self.get_reverse_direction(v, d)
            dirs = [k for k in range(len(self.vertex_orders[v])) if self.vertex_orders[v][k] is not None]
            d = min(dirs) if d_back >= max(dirs) else min(k for k in dirs if k > d_back)
            B2.append(d_back)
        B2 = B2[::-1]
        
        path_vertices = [0]
        path_dirs_rev = []
        for d in path_dirs:
            v2, d2 = self.get_reverse_direction(path_vertices[-1], d)
            path_vertices.append(v2)
            path_dirs_rev.append(d2)
        path_dirs_rev = path_dirs_rev[1:] + path_dirs_rev[:1]
        
        P = []
        on_rectangle = path_vertices[0] in rectangle_vertices
        
        n = len(path_dirs)
        for i in range(n):
            v, d = path_vertices[i], path_dirs[i]
            if on_rectangle and d != rectangle_dirs_dict[v] and d != rectangle_dirs_rev_dict[v]:
                on_rectangle = False
                exit_left = to_left_of(rectangle_dirs_rev_dict[v], rectangle_dirs_dict[v], d)
                if exit_left:
                    if left:
                        split_point = len(rectangle_vertices) - 1 - min(k for k in range(len(rectangle_vertices)) if rectangle_vertices[k] == v)
                        P.extend(rectangle_dirs_rev[split_point:-1])
                        P.extend(B2 if left else B)
                        P.extend(rectangle_dirs[:-1])
                        P.extend(A if left else A2)
                        P.extend(rectangle_dirs_rev[:split_point])
                    else:
                        split_point = min(k for k in range(len(rectangle_vertices)) if rectangle_vertices[k] == v)
                        P.extend(rectangle_dirs[split_point:-1])
                        P.extend(A2 if left else A)
                        P.extend(rectangle_dirs_rev[:-1])
                        P.extend(B if left else B2)
                        P.extend(rectangle_dirs[:split_point])
            
            P.append(d)
            
            if not on_rectangle:
                v2, d2 = path_vertices[(i+1) % n], path_dirs_rev[i]
                if v2 in rectangle_vertices:
                    on_rectangle = True
                    entered_left = to_left_of(rectangle_dirs_rev_dict[v2], rectangle_dirs_dict[v2], d2)
                    if entered_left:
                        if left:
                            split_point = min(k for k in range(len(rectangle_vertices)) if rectangle_vertices[k] == v2)
                            P.extend(rectangle_dirs[split_point:-1])
                            P.extend(A2 if left else A)
                            P.extend(rectangle_dirs_rev[:-1])
                            P.extend(B if left else B2)
                            P.extend(rectangle_dirs[:split_point])
                        else:
                            split_point = len(rectangle_vertices) - 1 - min(k for k in range(len(rectangle_vertices)) if rectangle_vertices[k] == v2)
                            P.extend(rectangle_dirs_rev[split_point:-1])
                            P.extend(B2 if left else B)
                            P.extend(rectangle_dirs[:-1])
                            P.extend(A if left else A2)
                            P.extend(rectangle_dirs_rev[:split_point])
        
        return self.simplify_path(P)
    
    def simplify_path(self, P):
        P2, d_backs = [], []
        v = 0
        for d in P:
            v, d_back = self.get_reverse_direction(v, d)
            if d_back is not None and len(d_backs) > 0 and d == d_backs[-1]:
                P2.pop()
                d_backs.pop()
            else:
                P2.append(d)
                d_backs.append(d_back)
        
        return P2
    
    def actions(self, curves):
        results = dict()
        for curve in self.annuli + self.rectangles:
            if curve[0] in curves:
                results[curve[0]] = dict()
            if curve[1] in curves:
                results[curve[1]] = dict()
        
        for g in self.fundamental_group_generators:
            P = self.path_lookup[g]
            
            for annulus in self.annuli:
                annulus_name, annulus_inverse_name, annulus_start, annulus_dirs = annulus
                if annulus_name in curves:
                    results[annulus_name][g] = self.encode_path_generators(self.twist_action(P, annulus_start, annulus_dirs, True))
                if annulus_inverse_name in curves:
                    results[annulus_inverse_name][g] = self.encode_path_generators(self.twist_action(P, annulus_start, annulus_dirs, False))
            
            for rectangle in self.rectangles:
                rectangle_name, rectangle_inverse_name, rectangle_start, rectangle_dirs, starting_None_dir, ending_None_dir = rectangle
                if rectangle_name in curves:
                    results[rectangle_name][g] = self.encode_path_generators(self.half_twist_action(P, rectangle_start, rectangle_dirs, starting_None_dir, ending_None_dir, True))
                if rectangle_inverse_name in curves:
                    results[rectangle_inverse_name][g] = self.encode_path_generators(self.half_twist_action(P, rectangle_start, rectangle_dirs, starting_None_dir, ending_None_dir, False))
        
        return results
    
    def encode_path_generators(self, P):
        v, s = 0, ''
        
        P2 = []
        for d in P:
            e_num = self.vertex_orders[v][d]
            e = self.edge_connections[e_num]
            if self.fundamental_group[0][e_num]:  # If it is a generator.
                P2.append(d)
            elif self.tree[e_num]:
                P2.append(d)
            else:
                P2.extend(self._encode_edge(v, d))
            
            v, d_back = self.get_reverse_direction(v, d)
        
        P3 = self.simplify_path(P2)
        
        v = 0
        for d in P3:
            e_num = self.vertex_orders[v][d]
            e = self.edge_connections[e_num]
            if self.fundamental_group[0][e_num]:  # If it is a generator.
                s += self.generator_lookup[e_num] if e[0] == v and e[1] == d else self.generator_lookup[e_num].swapcase()
            elif self.tree[e_num]:
                pass
            else:
                print('Error', P, P2, P3, e_num)
            
            v, d_back = self.get_reverse_direction(v, d)
        
        return s
    
    def _encode_edge(self, v_start, d_start):
        v_target, d_target = self.get_reverse_direction(v_start, d_start)
        
        tree_lookup = [i for i in range(self.num_edges) if self.tree[i]]
        valid_direction = [(v, d) for v in range(self.num_vertices) for d in range(4) if self.vertex_orders[v][d] in self.generator_lookup or self.vertex_orders[v][d] in tree_lookup]
        valid_direction.append((v_target, d_target))
        
        def turn(v, d, sign=+1):
            d = (d + sign) % 4
            if self.vertex_orders[v][d] is None: return None
            while (v, d) not in valid_direction:
                d = (d + sign) % 4
                if self.vertex_orders[v][d] is None: return None
            return d
        
        for sign in [+1, -1]:
            v, d = v_start, d_start
            A = []
            bad = False
            moved = False
            d = turn(v, d, sign)
            while v != v_target or d != d_target or not moved:
                A.append(d)
                if d is None:
                    bad = True
                    break
                
                v, d = self.get_reverse_direction(v, d)
                moved = True
                
                d = turn(v, d, sign)
            
            if not bad: return A
    
    def annulus_to_path(self, annulus):
        name, inverse_name, curve_start, curve = annulus
        
        e1 = curve_start
        
        P = []
        while e1 != 0:
            d = self.tree_directions[e1]
            P.append(d)
            e1 = other_end(self.edge_connections[self.vertex_orders[e1][self.tree_directions_rev[e1]]], e1)
        P = P[::-1]
        
        v = curve_start
        
        for d in curve:
            P.append(d)
            v, d_back = self.get_reverse_direction(v, d)
        
        e2 = v
        while e2 != 0:
            d = self.tree_directions_rev[e2]
            P.append(d)
            e2 = other_end(self.edge_connections[self.vertex_orders[e2][self.tree_directions_rev[e2]]], e2)
        
        return self.simplify_path(P)
    
    def rectangle_to_path(self, rectangle):
        name, inverse_name, rectangle_start, rectangle_dirs, starting_None_dir, ending_None_dir = rectangle
        
        rectangle_vertices = [rectangle_start]
        rectangle_dirs_rev = []
        for d in rectangle_dirs[:-1]:
            v2, d2 = self.get_reverse_direction(rectangle_vertices[-1], d)
            rectangle_vertices.append(v2)
            rectangle_dirs_rev.append(d2)
        rectangle_dirs_rev = list(rectangle_dirs_rev) + [starting_None_dir]
        rectangle_dirs = list(rectangle_dirs) + [ending_None_dir]
        
        A, A2 = [], []
        moved = False
        v, d = rectangle_vertices[-1], rectangle_dirs[-1]
        dirs = [k for k in range(len(self.vertex_orders[v])) if self.vertex_orders[v][k] is not None]
        d0 = min(dirs) if d >= max(dirs) else min(k for k in dirs if k >= d)
        d = d0
        while v != rectangle_vertices[-1] or d != d0 or not moved:
            moved = True
            A.append(d)
            v, d_back = self.get_reverse_direction(v, d)
            dirs = [k for k in range(len(self.vertex_orders[v])) if self.vertex_orders[v][k] is not None]
            d = min(dirs) if d_back >= max(dirs) else min(k for k in dirs if k > d_back)
            A2.append(d_back)
        A2 = A2[::-1]
        
        B, B2 = [], []
        moved = False
        v, d = rectangle_vertices[0], rectangle_dirs_rev[-1]
        dirs = [k for k in range(len(self.vertex_orders[v])) if self.vertex_orders[v][k] is not None]
        d0 = min(dirs) if d >= max(dirs) else min(k for k in dirs if k >= d)
        d = d0
        while v != rectangle_vertices[-1] or d != d0 or not moved:
            moved = True
            B.append(d)
            v, d_back = self.get_reverse_direction(v, d)
            dirs = [k for k in range(len(self.vertex_orders[v])) if self.vertex_orders[v][k] is not None]
            d = min(dirs) if d_back >= max(dirs) else min(k for k in dirs if k > d_back)
            B2.append(d_back)
        B2 = B2[::-1]
        
        e1 = rectangle_start
        
        P = []
        while e1 != 0:
            d = self.tree_directions[e1]
            P.append(d)
            e1 = other_end(self.edge_connections[self.vertex_orders[e1][self.tree_directions_rev[e1]]], e1)
        P = P[::-1]
        
        P.extend(rectangle_dirs[:-1])
        P.extend(A2)
        P.extend(rectangle_dirs_rev[:-1])
        P.extend(B2)
        
        e2 = rectangle_start
        while e2 != 0:
            d = self.tree_directions_rev[e2]
            P.append(d)
            e2 = other_end(self.edge_connections[self.vertex_orders[e2][self.tree_directions_rev[e2]]], e2)
        
        return self.simplify_path(P)
    
    def possible_seeds(self):
        return [self.encode_path_generators(self.annulus_to_path(a)) for a in self.annuli] + [self.encode_path_generators(self.rectangle_to_path(r)) for r in self.rectangles]
    
    def pi_1_generators(self):
        return ''.join(g + g.swapcase() for g in self.fundamental_group_generators)

