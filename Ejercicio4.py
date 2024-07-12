# Se realiza importaciones y configuracion
import asyncio
import random
import logging
from collections import defaultdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Se define la clase NetworkPartition
class NetworkPartition:
    def __init__(self):
        self.partitions = defaultdict(set)

    def is_partitioned(self, node1, node2):
        for partition in self.partitions.values():
            if node1 in partition and node2 in partition:
                return True
        return False

    def add_partition(self, nodes):
        partition_id = len(self.partitions)
        self.partitions[partition_id] = set(nodes)
        logger.info(f'Added partition {partition_id} with nodes {nodes}')

    def heal_partition(self, partition_id):
        if partition_id in self.partitions:
            del self.partitions[partition_id]
            logger.info(f'Healed partition {partition_id}')

class NodeStatus(Enum):
    UP = 1
    DOWN = 2

# Se realiza el Paso 2: Nodo Raft con latencia simulada

class RaftNode:
    def __init__(self, id, network, nodes):
        self.id = id
        self.status = NodeStatus.UP
        self.network = network
        self.nodes = nodes
        self.term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.data_version = 0

    async def send_message(self, recipient, message):
        if self.status == NodeStatus.UP and recipient.status == NodeStatus.UP and not self.network.is_partitioned(self.id, recipient.id):
            await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulación de latencia de red
            await recipient.receive_message(self, message)

    async def receive_message(self, sender, message):
        logger.info(f'Node {self.id} received message from Node {sender.id}: {message}')
        self.process_message(sender, message)

    def process_message(self, sender, message):
        msg_type, term, *data = message
        if msg_type == 'request_vote':
            self.handle_vote_request(sender, term)
        elif msg_type == 'append_entries':
            self.handle_append_entries(sender, term, data)

    async def start_election(self):
        self.term += 1
        self.voted_for = self.id
        votes = 1  # Voto por sí mismo
        for node in self.nodes:
            if node.id != self.id:
                await self.send_message(node, ('request_vote', self.term))
        # Esperar respuestas de votación y contar votos
        # Si recibe la mayoría, se convierte en líder
        # Aquí se omite la lógica completa por simplicidad

    async def append_entries(self, entries):
        self.log.extend(entries)
        self.commit_index = len(self.log)
        self.data_version += 1
        for node in self.nodes:
            if node.id != self.id:
                await self.send_message(node, ('append_entries', self.term, entries, self.data_version))

    def handle_vote_request(self, sender, term):
        if term > self.term:
            self.term = term
            self.voted_for = sender.id
            logger.info(f'Node {self.id} voted for Node {sender.id} in term {term}')

    def handle_append_entries(self, sender, term, data):
        entries, version = data
        if term >= self.term:
            self.term = term
            self.log.extend(entries)
            self.commit_index = len(self.log)
            self.data_version = version
            logger.info(f'Node {self.id} appended entries from Node {sender.id}: {entries}, version: {version}')

    def crash(self):
        self.status = NodeStatus.DOWN
        logger.info(f'Node {self.id} has crashed')

    def recover(self):
        self.status = NodeStatus.UP
        logger.info(f'Node {self.id} has recovered')

# Se realiza Paso 3: Simulación de Raft y fallos de nodo
network = NetworkPartition()
nodes = [RaftNode(i, network, []) for i in range(5)]
for node in nodes:
    node.nodes = nodes

async def simulate_raft():
    # Iniciar elecciones en un nodo para simular el proceso de elección de líder
    await nodes[0].start_election()
    await asyncio.sleep(1)
    # Simular la adición de entradas de registro
    await nodes[0].append_entries(['data1', 'data2'])
    await asyncio.sleep(1)

async def simulate_failures():
    while True:
        await asyncio.sleep(random.uniform(2, 5))
        node = random.choice(nodes)
        node.crash()
        await asyncio.sleep(random.uniform(2, 5))
        node.recover()

# Paso 4: Configuración de particiones y curaciones

async def simulate_network_partitions():
    while True:
        await asyncio.sleep(random.uniform(10, 20))
        partition_nodes = random.sample(nodes, k=random.randint(2, len(nodes) - 1))
        network.add_partition(partition_nodes)
        await asyncio.sleep(random.uniform(10, 20))
        network.heal_partition(random.choice(list(network.partitions.keys())))

Por ultimo el Paso 5: Ejecución de la simulación completa

async def main():
    await asyncio.gather(simulate_raft(), simulate_failures(), simulate_network_partitions())

asyncio.run(main())
