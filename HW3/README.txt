a. Documentation
I implement a simple version of the distributed Bellman-Ford algorithm with Poison Reverse. The program can linkup, link down, close node, show routine and build new link(extra function).

Please see usage scenario about how to run the code.

###################################################################################################################################

b. Usage Scenario

(1) open a new terminal window, type in “python bfclient.py 4119 3”

(2) open a new terminal window, type in “python bfclient.py 4030 3 192.168.0.5 4119 5”
A connection between 192.168.0.5:4119 and 192.168.0.5:4030 will be built with distance 5.


(3) open a new terminal window, type in ”python bfclient.py 4035 3 192.168.0.5 4119 2 192.168.0.5 4030 1”
Connections between 192.168.0.5:4035 and 192.168.0.5:4030 and between 192.168.0.5:4035 and 192.168.0.5:4119 will be built, with distance 1 and 2 separately. And the algorithm will update the distance by Bellman-Ford algorithm with Poison Reverse.

(4) open a new terminal window, type in ”python bfclient.py 4544 3 192.168.0.5 4035 2”
A connection between 192.168.0.5:4544 and 192.168.0.5:4035 will be built with distance 2. And the algorithm will update the distance by Bellman-Ford algorithm with Poison Reverse.

(5) In the terminal window founded in step (3), type in “linkdown 192.168.0.5 4119”
The link between 192.168.0.5:4035 and 192.168.0.5:4119 will be linked down, And the algorithm will update the distance by Bellman-Ford algorithm with Poison Reverse.

(6) In the same terminal window as step (5), type in “linkup 192.168.0.5 4119”
The link between 192.168.0.5:4035 and 192.168.0.5:4119 will be recovered. And the algorithm will update the distance by Bellman-Ford algorithm with Poison Reverse.

(7) In the terminal window founded by step(4), type in “build 192.168.0.5 4119 1”
A connection between 192.168.0.5:4544 and 192.168.0.5:4119 will be built with distance 1. And the algorithm will update the distance by Bellman-Ford algorithm with Poison Reverse.

(8) In the same terminal window as step (7), type in “close”
The node 192.168.0.5:4544 will stop working, and after 3 timeouts (9s), the node 192.168.0.5:4119 and 192.168.0.5:4035 will notice the node 192.168.0.5:4544 has dead and update the distance by Bellman-Ford algorithm with Poison Reverse.

After every step, you can type in “showrt” to view the current distance vector.

Note: In the usage scenario, you at least need to change the IP in the example.

################################################################################################################################

c. Program Features:
(1) “python bfclient.py 4030 3 192.168.0.5 4119 5”
This can build a node at 192.168.0.5:4030 with time out 3s, and send message to 192.168.0.5:4119 and try to build a connection.

(2) “showrt”
By typing this sentence, the program will show the current distance vector to user.

(3) “linkdown 192.168.0.5 4119”
This will link down the edge from current node to 192.168.0.5:4119
# The function will raise error message when the input format is not correct or the link down node is not currently a neighbor of current node

(4) “linkup 192.168.0.5 4119”
This will recover the linked down edge form current node to 192.168.0.5:4119
# The function will raise error message when the input format is not correct or the link up node is current linking to current node

(5) “build 192.168.0.5 4111 5”  (extra function)
This sentence has one more character ‘5’ then the sentence in (4). It is used to found a new edge for current existing node.
# The function will raise error message when the input format is not correct

(6) “close”
Make the current node dead, other nodes will detect of current node after 3*time outs.

################################################################################################################################
 d. Protocol Specification
The distance vector is stored in a dictionary called “dictDistTable”
The format of dictDistTable is like:
{u'192.168.0.5:4035': [2.0, u'192.168.0.5:4035'], u'192.168.0.5:4544': [1.0, u'192.168.0.5:4544'], u'192.168.0.5:4030': [3.0, u'192.168.0.5:4035']}
where the key is the destination of the distance vector, the value of the key is a list, the first element is the distance from current node to the destination node, and the second element is the first node we need to get through in this path. For instance, on distance vector is a->b->c->…->z and has distance 5, in node a, this vector will be saved as {‘z’:[5,’b’]}.

When the distance vector is changed in a node, the node will send its dictDistTable (with the first node information removed, like {‘z’:5}) encapsulated in json to all its neighbor nodes. Because I use the poison reverse, when sending the update message, if the message to the node that one distance vector take it as the next node to go to the destination, the distance will be mark as infinity, for instance, when a sending message to b, the vector stored in dictDistTable as {‘z’:[5,’b’]} will be sent as {‘z’:float(inf)}.
The poison reverse can increase the efficiency of updating.

When link down, the node will send the distance as {‘z’:float(‘inf’)} to receive node and then link down.

################################################################################################################################

Extra Function:
1. Poison Reverse: if node ‘a’ go to node ‘z’ through node ‘b’, node ‘a’ will tell node ‘z’ its distance as infinity.

2. Build up a new path: by type in “build 192.168.0.5 4111 5”, you can found a new edge for current existing node.2.