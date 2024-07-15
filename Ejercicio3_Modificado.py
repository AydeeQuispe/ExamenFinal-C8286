# Se realiza las importaciones
import time
import threading
import queue

# Se define la Clase para representar un mensaje enviado entre nodos
class Message:
    def __init__(self, sender, content, timestamp):
        self.sender = sender          # Identificador del nodo emisor
        self.content = content        # Contenido del mensaje
        self.timestamp = timestamp    # Marca de tiempo del mensaje

# Se define la clase que representa un nodo en la red distribuida
class Node:
    def __init__(self, node_id, total_nodes, network):
        self.node_id = node_id                    # Identificador único del nodo
        self.total_nodes = total_nodes            # Número total de nodos en la red
        self.network = network                    # Referencia a la red
        self.clock = 0                            # Reloj lógico inicializado en 0
        self.request_queue = []                   # Cola de solicitudes para el algoritmo de Ricart-Agrawala
        self.pending_replies = 0                  # Contador para el algoritmo de Ricart-Agrawala
        self.terminate_flag = False               # Bandera para indicar la terminación de procesos
        self.parent = None                        # Nodo padre en el algoritmo de Dijkstra-Scholten
        self.active_children = set()              # Hijos activos en el algoritmo de Dijkstra-Scholten
        self.memory = {}                          # Memoria del nodo
        self.garbage_collected = set()            # Conjunto para objetos recolectados por basura

    
    # Se define send_message 
    # Método para enviar un mensaje al nodo especificado
    def send_message(self, receiver_id, content):
        message = Message(self.node_id, content, self.clock)  # Crear el mensaje con el contenido y el reloj local
        self.clock += 1                                       # Incrementar el reloj lógico local
        self.network.send_message(receiver_id, message)       # Enviar el mensaje a través de la red

    # Método para manejar un mensaje recibido
    def handle_message(self, message):
        print(f"Nodo {self.node_id} recibió mensaje de Nodo {message.sender}: {message.content}")

    # Método para solicitar la sección crítica
    def request_cs(self):
        self.clock += 1  # Incrementar el reloj lógico local
        request_message = Message(self.node_id, "request", self.clock)  # Crear mensaje de solicitud
        self.request_queue.append(request_message)  # Agregar el mensaje de solicitud a la cola
        # Enviar mensajes de solicitud a todos los otros nodos
        for node_id in range(self.total_nodes):
            if node_id != self.node_id:
                self.send_message(node_id, request_message.content)
                self.pending_replies += 1  # Incrementar el contador de respuestas pendientes

        # Esperar a que lleguen todas las respuestas
        start_time = time.time()
        while self.pending_replies > 0:
            if time.time() - start_time > 5:  # Esperar un máximo de 5 segundos para recibir respuestas
                print(f"Nodo {self.node_id} tiempo de espera excedido para respuestas.")
                break
            time.sleep(0.1)  # Espera para asegurar que todas las respuestas lleguen

        # Sección crítica
        print(f"Nodo {self.node_id} entró en la sección crítica.")
        time.sleep(1)  # Simular tiempo en la sección crítica
        print(f"Nodo {self.node_id} salió de la sección crítica.")

        # Enviar respuestas a los nodos que lo solicitaron
        reply_message = Message(self.node_id, "reply", self.clock)
        for request in self.request_queue:
            if request.sender != self.node_id:
                self.send_message(request.sender, reply_message.content)
        self.request_queue = []  # Limpiar la cola de solicitudes al salir de la sección crítica

    # Método para manejar una solicitud de sección crítica recibida
    def handle_request(self, message):
        if self.terminate_flag:
            return

        self.clock = max(self.clock, message.timestamp) + 1  # Actualizar el reloj lógico local
        self.request_queue.append(message)  # Agregar a la cola de solicitudes
        if self.request_cs_allowed(message):
            reply_message = Message(self.node_id, "reply", self.clock)
            self.send_message(message.sender, reply_message.content)  # Enviar respuesta de aceptación

    # Método para manejar una respuesta de sección crítica recibida
    def handle_reply(self, message):
        if self.terminate_flag:
            return

        self.clock = max(self.clock, message.timestamp) + 1  # Actualizar el reloj lógico local
        self.pending_replies -= 1  # Decrementar contador de respuestas pendientes

    # Método para verificar si se permite la solicitud de sección crítica
    def request_cs_allowed(self, request_message):
        if self.request_queue and (self.request_queue[0].sender < request_message.sender or
                                   (self.request_queue[0].sender == request_message.sender and self.node_id < request_message.sender)):
            return False
        return True

    # Método para marcar el proceso como terminado
    def terminate_process(self):
        self.terminate_flag = True

    # Método para iniciar el algoritmo de Dijkstra-Scholten para detección de terminación
    def start_dijkstra_scholten(self):
        terminate_message = Message(self.node_id, "terminate", self.clock)
        for node_id in range(self.total_nodes):
            if node_id != self.node_id:
                self.send_message(node_id, terminate_message.content)
        self.terminate_process()
        print(f"Nodo {self.node_id} ha marcado su proceso como terminado.")

    # Método para manejar un mensaje de terminación recibido
    def handle_terminate(self, message):
        if not self.terminate_flag:
            self.terminate_flag = True
            print(f"Nodo {self.node_id} ha detectado la terminación del proceso de Nodo {message.sender}.")
            self.start_dijkstra_scholten()

    # Método para sincronizar el reloj del nodo con el reloj global
    def synchronize_clocks(self):
        self.clock = self.network.get_global_time()
        print(f"Nodo {self.node_id} sincronizó su reloj a {self.clock}.")

    # Método para realizar la recolección de basura
    def garbage_collect(self):
        print(f"Nodo {self.node_id} está realizando la recolección de basura.")

        # Marcar y mover objetos vivos a una nueva área de memoria
        self.mark_and_sweep()

        print(f"Nodo {self.node_id} completó la recolección de basura.")

    # Algoritmo de recolección de basura (Cheney)
    def mark_and_sweep(self):
        # Paso 1: Marcar objetos vivos alcanzables desde los roots
        roots = list(self.memory.values())  # Consideramos todos los objetos almacenados en la memoria como roots
        marked = set()  # Conjunto para objetos marcados como vivos

        def dfs(obj):
            if obj in marked:
                return
            marked.add(obj)
            for reference in obj.references():
                dfs(reference)

        for root in roots:
            dfs(root)

        # Paso 2: Mover objetos vivos a una nueva área de memoria
        new_memory = {}
        for obj in marked:
            new_memory[id(obj)] = obj

        # Actualizar la memoria del nodo con la nueva área de memoria
        self.memory = new_memory

    # Método para manejar la adición de un objeto a la memoria
    def add_to_memory(self, obj):
        self.memory[id(obj)] = obj

# Clase que representa la red de nodos distribuidos
class Network:
    def __init__(self, total_nodes):
        self.total_nodes = total_nodes                      # Número total de nodos en la red
        self.nodes = [Node(node_id, total_nodes, self) for node_id in range(total_nodes)]  # Crear nodos en la red
        self.messages = queue.Queue()                      # Cola de mensajes entre nodos
        self.global_time = 0                               # Reloj global para sincronización de relojes
        self.lock = threading.Lock()                       # Bloqueo para sincronizar el acceso a la cola de mensajes

    # Método para enviar un mensaje a un nodo específico
    def send_message(self, receiver_id, message):
        with self.lock:
            self.messages.put((receiver_id, message))

    # Método para obtener el próximo mensaje de la cola de mensajes
    def get_message(self):
        with self.lock:
            return self.messages.get()

    # Método para iniciar la red de nodos
    def start(self):
        threads = []
        for node in self.nodes:
            thread = threading.Thread(target=self.run_node, args=(node,))
            threads.append(thread)
            thread.start()

        # Solicitar la sección crítica para cada nodo después de iniciarlo
        for node in self.nodes:
            threading.Thread(target=node.request_cs).start()

        for thread in threads:
            thread.join()

    # Método para ejecutar un nodo específico
    def run_node(self, node):
        while True:
            receiver_id, message = self.get_message()   # Obtener el siguiente mensaje de la cola
            if message.content == "terminate":
                node.handle_terminate(message)          # Manejar mensaje de terminación
                break
            node.handle_message(message)                # Manejar el mensaje recibido
            if message.content == "request":
                node.handle_request(message)            # Manejar solicitud de sección crítica
            elif message.content == "reply":
                node.handle_reply(message)              # Manejar respuesta de sección crítica

    # Método para sincronizar los relojes de todos los nodos en la red
    def synchronize_clocks(self):
        self.global_time = time.time()  # Usar el tiempo actual como simulación de tiempo global
        for node in self.nodes:
            node.synchronize_clocks()

    # Método para obtener el tiempo global
    def get_global_time(self):
        return self.global_time

    # Método para realizar la recolección de basura en todos los nodos de la red
    def garbage_collect(self):
        for node in self.nodes:
            node.garbage_collect()  # Llamar al método de recolección de basura del nodo

# Ejecutar la simulación
def main():
    total_nodes = 5  # Número total de nodos en la red
    network = Network(total_nodes)

    # Simular añadiendo objetos a la memoria de los nodos
    for node in network.nodes:
        obj = object()  # Objeto de prueba
        node.add_to_memory(obj)

    # Iniciar la red
    network.start()

    # Sincronizar los relojes de los nodos
    network.synchronize_clocks()

    # Realizar la recolección de basura en los nodos
    network.garbage_collect()

if __name__ == "__main__":
    main()




