import os

class Node(object):
    '''
    Node containing data, pointers to previous and next node.
    '''
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None


class DoublyLinkedList(object):
    def __init__(self):
        self.head = None
        self.tail = None
        # Number of nodes in list.
        self.count = 0

    def add_node(self, cls, data):
        '''
        Add node instance of class cls.
        '''
        return self.insert_node(cls, data, self.tail, None)

    def insert_node(self, cls, data, prev, next):
        '''
        Insert node instance of class cls.
        '''
        node = cls(data)
        node.prev = prev
        node.next = next
        if prev:
            prev.next = node
        if next:
            next.prev = node
        if not self.head or next is self.head:
            self.head = node
        if not self.tail or prev is self.tail:
            self.tail = node
        self.count += 1
        return node

    def remove_node(self, node):
        if node is self.tail:
            self.tail = node.prev
        else:
            node.next.prev = node.prev
        if node is self.head:
            self.head = node.next
        else:
            node.prev.next = node.next
        self.count -= 1

    def remove_node_by_data(self, data):
        '''
        Remove node which data is equal to data.
        '''
        node = self.head
        while node:
            if node.data == data:
                self.remove_node(node)
                break
            node = node.next

    def get_nodes_data(self):
        '''
        Return list nodes data as a list.
        '''
        data = []
        node = self.head
        while node:
            data.append(node.data)
            node = node.next
        return data


class FreqNode(DoublyLinkedList, Node):
    '''
    Frequency node.
    Frequency node contains a linked list of item nodes with same frequency.
    '''
    def __init__(self, data):
        DoublyLinkedList.__init__(self)
        Node.__init__(self, data)

    def add_item_node(self, data):
        node = self.add_node(ItemNode, data)
        node.parent = self
        return node

    def insert_item_node(self, data, prev, next):
        node = self.insert_node(ItemNode, data, prev, next)
        node.parent = self
        return node

    def remove_item_node(self, node):
        self.remove_node(node)

    def remove_item_node_by_data(self, data):
        self.remove_node_by_data(data)


class ItemNode(Node):
    def __init__(self, data):
        Node.__init__(self, data)
        self.parent = None


class LfuItem(object):
    def __init__(self, data, parent, node):
        self.data = data
        self.parent = parent
        self.node = node


class Cache(DoublyLinkedList):
    def __init__(self, max_size):
        DoublyLinkedList.__init__(self)
        self.items = dict()
        self.avail_size = max_size

    def contains(self, path):
        return path in self.items

    def insert_freq_node(self, data, prev, next):
        return self.insert_node(FreqNode, data, prev, next)

    def remove_freq_node(self, node):
        self.remove_node(node)

    def access(self, key):
        '''
        move the corresponding item into current frequency + 1 freqNode
        '''
        if key in self.items:
            tmp = self.items[key]
        else:
            return

        freq_node = tmp.parent
        next_freq_node = freq_node.next

        if not next_freq_node or next_freq_node.data != freq_node.data + 1:
            next_freq_node = self.insert_freq_node(freq_node.data + 1,
                                                   freq_node, next_freq_node)
        item_node = next_freq_node.add_item_node(key)
        tmp.parent = next_freq_node

        freq_node.remove_item_node(tmp.node)
        if freq_node.count == 0:
            self.remove_freq_node(freq_node)

        tmp.node = item_node
        return tmp.data

    def insert(self, key, value):
        '''
        insert key (path), value (size of file) into cache
        '''
        print '[DEBUG]insert into cache'
        print 'node: key value', key, value
        if key in self.items:
            print "[WARNING]insert fail 1" 
            return            

        # check available size left in local disk
        # delete lfu if used up, and update it
        self.check_avail_size(value)
        
        freq_node = self.head
        if not freq_node or freq_node.data != 1:
            freq_node = self.insert_freq_node(1, None, freq_node)

        item_node = freq_node.add_item_node(key)
        self.items[key] = LfuItem(value, freq_node, item_node)

    def check_avail_size(self, value):
        self.avail_size  -= value
        print '[DEBUG]before delete self:', self
        while self.avail_size < 0:
            lfu, lfu_size = self.get_lfu()
            self.delete_lfu()
            self.avail_size += lfu_size           

    def get_lfu(self):
        if not len(self.items):
            return None, 0
        return self.head.head.data, self.items[self.head.head.data].data

    def delete_lfu(self):
        '''
        Remove the first item node from the first frequency node.
        Remove the LFU item from the dictionary.
        Remove file from local disk
        '''
        if not self.head:
            print "[WARNING]empty cache"
            print self
            exit(1)
            return 

        # remove lfu from cache
        freq_node = self.head
        item_node = freq_node.head
        path = item_node.data
        self.items.pop(item_node.data)
        freq_node.remove_item_node(item_node)
        if freq_node.count == 0:
            self.remove_freq_node(freq_node)

        # remove corresponding file from local disk
        filename = os.getcwd() + path
        try:
            os.remove(filename)
        except OSError:
            print "Filename doesn't exit, can't delete"
            pass

    def __repr__(self):
        """Display access frequency list and items.
        Using the representation:
        freq1: [item, item, ...]
        freq2: [item, item]
        ...
        """
        s = 'total size: %d\n' % self.avail_size
        freq_node = self.head
        while freq_node:
            s += '%s: %s\n' % (freq_node.data, freq_node.get_nodes_data())
            freq_node = freq_node.next
        return s
