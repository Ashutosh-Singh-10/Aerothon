from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status 


from .models import *
from django.contrib.auth.models import User

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework_simplejwt.authentication import JWTAuthentication 
from rest_framework_simplejwt.tokens import Token

from rest_framework.views import APIView
from rest_framework.response import Response
from userLogin.serializers import *
from django.http import HttpResponse




import numpy as np
import matplotlib.pyplot as plt
import random

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
        self.cost = 0.0

def distance(node1, node2):
    return np.sqrt((node1.x - node2.x)**2 + (node1.y - node2.y)**2)

def get_nearest_node(node_list, random_node):
    nearest_node = node_list[0]
    min_dist = distance(nearest_node, random_node)
    for node in node_list:
        dist = distance(node, random_node)
        if dist < min_dist:
            nearest_node = node
            min_dist = dist
    return nearest_node

def steer(from_node, to_node, max_extend_length=float("inf")):
    new_node = Node(from_node.x, from_node.y)
    dist = distance(from_node, to_node)
    if dist > max_extend_length:
        theta = np.arctan2(to_node.y - from_node.y, to_node.x - from_node.x)
        new_node.x += max_extend_length * np.cos(theta)
        new_node.y += max_extend_length * np.sin(theta)
    else:
        new_node.x = to_node.x
        new_node.y = to_node.y
    new_node.cost = from_node.cost + distance(from_node, new_node)
    new_node.parent = from_node
    return new_node

def is_collision_free(node, obstacle_list, obstacle_radius):
    for (ox, oy) in obstacle_list:
        if distance(node, Node(ox, oy)) <= obstacle_radius:
            return False
    return True

def get_path(goal_node):
    path = [(goal_node.x, goal_node.y)]
    node = goal_node
    while node.parent is not None:
        node = node.parent
        path.append((node.x, node.y))
    return path[::-1]

def RRT_star(start, goal, obstacle_list, obstacle_radius, search_area, max_iter=500, max_extend_length=1.0, goal_sample_rate=0.2):
    start_node = Node(start[0], start[1])
    goal_node = Node(goal[0], goal[1])
    node_list = [start_node]
    for _ in range(max_iter):
        if random.random() > goal_sample_rate:
            rand_node = Node(random.uniform(search_area[0], search_area[1]),
                             random.uniform(search_area[2], search_area[3]))
        else:
            rand_node = Node(goal[0], goal[1])

        nearest_node = get_nearest_node(node_list, rand_node)
        new_node = steer(nearest_node, rand_node, max_extend_length)

        if is_collision_free(new_node, obstacle_list, obstacle_radius):
            near_nodes = [node for node in node_list if distance(node, new_node) <= max_extend_length]

            if near_nodes:
                best_node = min(near_nodes, key=lambda node: node.cost + distance(node, new_node))
                new_node = steer(best_node, new_node, max_extend_length)

            node_list.append(new_node)

            for near_node in near_nodes:
                if new_node.cost + distance(new_node, near_node) < near_node.cost:
                    near_node.parent = new_node
                    near_node.cost = new_node.cost + distance(new_node, near_node)

        if distance(new_node, goal_node) <= max_extend_length:
            final_node = steer(new_node, goal_node, max_extend_length)
            if is_collision_free(final_node, obstacle_list, obstacle_radius):
                goal_node.parent = final_node
                goal_node.cost = final_node.cost + distance(final_node, goal_node)
                node_list.append(goal_node)
                break

    path = get_path(goal_node)
    return path, node_list

def draw_graph(node_list, path, start, goal, obstacle_list, obstacle_radius,search_area):
    plt.figure(figsize=(10, 10))
    plt.plot(start[0], start[1], "go")
    plt.plot(goal[0], goal[1], "ro")
    for node in node_list:
        if node.parent:
            plt.plot([node.x, node.parent.x], [node.y, node.parent.y], "-g")
    for (ox, oy) in obstacle_list:
        circle = plt.Circle((ox, oy), obstacle_radius, color='r')
        plt.gca().add_patch(circle)
    if path:
        plt.plot([x for (x, y) in path], [y for (x, y) in path], '-r')
    plt.xlim(search_area[0], search_area[1])
    plt.ylim(search_area[2], search_area[3])
    plt.grid(True)
    plt.show()



class RouteFinding(APIView):
    authentication_classes=[JWTAuthentication]
    def get(self,request):
        if "start" in request.data and "goal" in request.data:
            start=request.data["start"]
            goal=request.data["goal"]
            
            obstacle_list=[]
            if "obstacle_list" in request.data:
                obstacle_list=request.data["obstacle_list"]
            obstacle_radius=0
            if "obstacle_radius" in request.data:
                obstacle_radius=request.data["obstacle_radius"]
            
            search_area=Node.objects.all().values()

            path, node_list = RRT_star(start, goal, obstacle_list, obstacle_radius, search_area)
            return Response({path:path,node_list:node_list})
            # draw_graph(node_list, path, start, goal, obstacle_list, obstacle_radius,search_area)
        
        else :
            return Response(status=status.HTTP_400_BAD_REQUEST)

        
    


