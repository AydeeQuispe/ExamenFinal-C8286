import asyncio
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Message:
    def __init__(self, sender, content, timestamp):
        self.sender = sender
        self.content = content
        self.timestamp = timestamp

class Node:
    def __init__(self, node_id, total_nodes, network):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.network = network
        self.clock = 0
        self.requesting = False
        self.replies_needed = 0
        self.resource_queue = asyncio.Queue()
        self.resources = set()
        self.young_generation = set()
        self.old_generation = set()
        self.threshold = 10
        self.parent = None
        self.active_children = set()

    async def send_message(self, recipient, content):
        message = Message(self, content, self.clock)
        await self.network.send_message(self, recipient, message)

    async def receive_message(self, message):
        logger.info(f'Node {self.node_id} received message from Node {message.sender.node_id}: {message.content}')
        self.synchronize_clock(message.timestamp)
        await self.process_message(message)

    def synchronize_clock(self, received_clock):
        self.clock = max(self.clock, received_clock) + 1

    async def process_message(self, message):
        content = message.content
        if content['type'] == 'request':
            await self.handle_request(message)
        elif content['type'] == 'reply':
            await self.handle_reply(message)
        elif content['type'] == 'task':
            await self.handle_task(message)
        elif content['type'] == 'ack':
            await self.handle_ack(message)
        elif content['type'] == 'clock_sync':
            self.synchronize_clock(content['timestamp'])

    async def handle_request(self, message):
        sender = message.sender
        timestamp = message.timestamp
        if not self.requesting or (self.requesting and (self.clock, self.node_id) < (timestamp, sender.node_id)):
            await self.send_message(sender, {'type': 'reply'})
        else:
            await self.resource_queue.put((timestamp, sender))

    async def handle_reply(self, message):
        self.replies_needed -= 1
        if self.replies_needed == 0:
            await self.execute_task(message.content['resource'])

    async def handle_task(self, message):
        sender = message.sender
        if not self.parent:
            self.parent = sender
        self.active_children.add(sender)
        await self.execute_task(message.content['task'])

    async def handle_ack(self, message):
        sender = message.sender
        self.active_children.discard(sender)
        if not self.active_children and self.parent:
            await self.send_message(self.parent, {'type': 'ack'})
            logger.info(f'Node {self.node_id} terminated.')

    async def request_resource(self, resource):
        self.requesting = True
        self.clock += 1
        self.replies_needed = self.total_nodes - 1
        for node in self.network.nodes:
            if node.node_id != self.node_id:
                await self.send_message(node, {'type': 'request', 'resource': resource})

    async def execute_task(self, task):
        logger.info(f'Node {self.node_id} executing task {task}')
        await asyncio.sleep(random.uniform(0.5, 2))
        self.release_resource(task)

    def release_resource(self, resource):
        self.requesting = False
        self.resources.discard(resource)
        while not self.resource_queue.empty():
            timestamp, node = await self.resource_queue.get()
            await self.send_message(node, {'type': 'reply'})

    def allocate(self, obj):
        self.young_generation.add(obj)
        if len(self.young_generation) > self.threshold:
            self.collect_garbage()

    def collect_garbage(self):
        new_young = set()
        for obj in self.young_generation:
            if obj in self.resources:
                new_young.add(obj)
        self.old_generation.update(new_young)
        self.young_generation = new_young
        logger.info(f'Node {self.node_id} collected garbage: {self.old_generation}')

# Clase Network

class Network:
    def __init__(self, node_count):
        self.nodes = [Node(i, node_count, self) for i in range(node_count)]

    async def send_message(self, sender, recipient, message):
        if recipient.node_id in [node.node_id for node in self.nodes]:
            await recipient.receive_message(message)

    async def simulate(self):
        tasks = [node.send_message(node, {'type': 'clock_sync', 'timestamp': node.clock}) for node in self.nodes]
        await asyncio.gather(*tasks)
        for node in self.nodes:
            await node.request_resource('resource')
            await node.allocate('obj1')
            await node.allocate('obj2')


