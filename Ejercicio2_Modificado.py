# Importaciones necesarias para threading, logging y queue
import threading
import logging
import queue

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clase Robot que implementa el algoritmo de snapshot
class Robot:
    def __init__(self, id, num_robots):
        self.id = id
        self.state = {}  # Estado del robot
        self.channel_states = {i: [] for i in range(num_robots) if i != id}  # Estados de canales
        self.snapshot_initiator = False  # Indicador de iniciación de snapshot
        self.in_snapshot = False  # Indicador de estar en snapshot
        self.num_robots = num_robots
        self.snapshot = {}  # Snapshot capturado
        self.lock = threading.Lock()  # Lock para sincronización

    def initiate_snapshot(self):
        with self.lock:
            self.snapshot_initiator = True
            self.in_snapshot = True
            self.record_state()  # Registra el estado actual
            for i in range(self.num_robots):
                if i != self.id:
                    self.send_marker(i)  # Envía marcadores a otros robots

    def receive_marker(self, sender_id):
        with self.lock:
            if not self.in_snapshot:
                self.initiate_snapshot()
            self.channel_states[sender_id] = []  # Limpia el estado del canal

    def send_marker(self, recipient_id):
        logger.info(f'Robot {self.id} sends marker to Robot {recipient_id}')
        network.simulate_marker(self.id, recipient_id)  # Simula el envío de marcador en la red

    def record_state(self):
        logger.info(f'Robot {self.id} records its state')
        self.snapshot = self.state.copy()  # Captura el snapshot del estado actual

    def receive_message(self, sender_id, message):
        with self.lock:
            if self.in_snapshot:
                self.channel_states[sender_id].append(message)
            # Aquí se procesarían los mensajes normales en caso de no estar en snapshot

# Clase Network que simula la red entre los robots
class Network:
    def __init__(self, num_robots):
        self.robots = [Robot(i, num_robots) for i in range(num_robots)]

    def simulate_message(self, sender_id, recipient_id, message):
        self.robots[recipient_id].receive_message(sender_id, message)
        logger.info(f'Robot {sender_id} sends message to Robot {recipient_id}: {message}')  # Log del mensaje enviado

    def simulate_marker(self, sender_id, recipient_id):
        self.robots[recipient_id].receive_marker(sender_id)  # Simula el recibimiento de un marcador

# Clase Token para algoritmo de exclusión mutua de Raymond
class Token:
    def __init__(self, owner):
        self.owner = owner

# Clase RobotRaymond que implementa el algoritmo de exclusión mutua de Raymond
class RobotRaymond(Robot):
    def __init__(self, id, num_robots):
        super().__init__(id, num_robots)
        self.token = None  # Token para exclusión mutua
        self.request_queue = queue.Queue()  # Cola de solicitudes
        self.parent = None  # Padre en la jerarquía

    def request_resource(self):
        if self.token:
            self.enter_critical_section()  # Entra a la sección crítica si tiene el token
        else:
            self.request_queue.put(self.id)
            self.send_request_to_parent()  # Envía solicitud al padre

    def send_request_to_parent(self):
        if self.parent is not None:
            network.simulate_message(self.id, self.parent, 'REQUEST')
            logger.info(f'Robot {self.id} sends request to parent {self.parent}')

    def receive_request(self, sender_id):
        if not self.token:
            self.request_queue.put(sender_id)
            self.send_request_to_parent()
        else:
            if self.id == self.token.owner:
                self.token.owner = sender_id
                self.send_token(sender_id)
            else:
                self.request_queue.put(sender_id)

    def send_token(self, recipient_id):
        logger.info(f'Robot {self.id} sends token to Robot {recipient_id}')
        self.token = None
        network.simulate_message(self.id, recipient_id, 'TOKEN')  # Envía token a otro robot

    def receive_token(self):
        self.token = Token(self.id)
        if not self.request_queue.empty():
            next_robot = self.request_queue.get()
            self.send_token(next_robot)

    def enter_critical_section(self):
        logger.info(f'Robot {self.id} enters critical section')

    def exit_critical_section(self):
        if not self.request_queue.empty():
            next_robot = self.request_queue.get()
            self.send_token(next_robot)
        else:
            self.token = Token(self.id)

# Clase VectorClock para relojes vectoriales
class VectorClock:
    def __init__(self, num_robots):
        self.clock = [0] * num_robots  # Inicialización del reloj vectorial

    def update(self, sender_id, sender_clock):
        self.clock = [max(self.clock[i], sender_clock[i]) for i in range(len(self.clock))]
        self.clock[sender_id] += 1  # Actualiza el reloj vectorial al recibir un mensaje

    def increment(self, robot_id):
        self.clock[robot_id] += 1  # Incrementa el reloj vectorial propio

    def __str__(self):
        return str(self.clock)

# Clase RobotVector que implementa el algoritmo de relojes vectoriales
class RobotVector(RobotRaymond):
    def __init__(self, id, num_robots):
        super().__init__(id, num_robots)
        self.vector_clock = VectorClock(num_robots)  # Reloj vectorial asociado

    def send_message(self, recipient_id, message):
        self.vector_clock.increment(self.id)
        network.simulate_message(self.id, recipient_id, (message, self.vector_clock.clock))

    def receive_message(self, sender_id, message):
        message, sender_clock = message
        self.vector_clock.update(sender_id, sender_clock)
        super().receive_message(sender_id, message)  # Llama al método padre para procesar el mensaje
        logger.info(f'Robot {self.id} updated vector clock: {self.vector_clock}')

# Clase GenerationalGarbageCollector para recolección de basura generacional
class GenerationalGarbageCollector:
    def __init__(self):
        self.generations = [[], [], []]  # Inicialización de generaciones

    def allocate(self, obj, generation=0):
        self.generations[generation].append(obj)
        if len(self.generations[generation]) > 10:  # Límite arbitrario para la colección
            self.collect_garbage(generation)

    def collect_garbage(self, generation):
        logger.info(f'Collecting garbage in generation {generation}')
        if generation < len(self.generations) - 1:
            next_generation = generation + 1
            for obj in self.generations[generation]:
                self.generations[next_generation].append(obj)
            self.generations[generation] = []

    def full_collect(self):
        for generation in range(len(self.generations)):
            self.collect_garbage(generation)

# Ejemplo de uso de GenerationalGarbageCollector
gc = GenerationalGarbageCollector()
for i in range(15):
    gc.allocate(f'Object {i}')
gc.full_collect()

# Clase FullRobot que integra todas las funcionalidades y algoritmos anteriores
class FullRobot(RobotVector):
    def __init__(self, id, num_robots, gc):
        super().__init__(id, num_robots)
        self.gc = gc  # Asigna el recolector de basura

    def allocate_resource(self, obj):
        self.gc.allocate(obj)  # Asigna un recurso y gestiona la basura

    def perform_task(self):
        self.request_resource()
        self.allocate_resource(f'Resource used by Robot {self.id}')
        self.enter_critical_section()
        # Simular trabajo en la sección crítica
        self.exit_critical_section()

    def receive_token(self):
        super().receive_token()  # Llama al método padre para recibir el token
        logger.info(f'Robot {self.id} received token and finishes execution')

# Configura la red con FullRobot y simula tareas y mensajes entre robots
network = Network(3)
gc = GenerationalGarbageCollector()
network.robots = [FullRobot(i, 3, gc) for i in range(3)]
for robot in network.robots:
    robot.perform_task()  # Ejecuta una tarea
    network.simulate_message(robot.id, (robot.id + 1) % 3, "Hello")  # Simula un mensaje entre robots
    robot.receive_token()  # Recibe un token
