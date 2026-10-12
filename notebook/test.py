class node: 
    def __init__(self, data):
        self.data = data
        self.next = None
class LinkedList:
    def __init__(self, ):
        self.head = None
    def create(self, data):
        new_node = node(data)

        if self.head is None :
            self.head = new_node
        else:
            curr = self.head
            while curr.next:
                curr = curr.next
            curr.next = new_node

def __main__():
    n1 = node(10)
    n2 = node(20)
    print(n1, n2)

    



            