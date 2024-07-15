import asyncio  # Importa el módulo asyncio para soportar programación asíncrona.
import logging  # Importa el módulo logging para registrar eventos y mensajes.
import queue  # Importa el módulo queue para usar PriorityQueue, una cola de prioridad.
import threading  # Importa el módulo threading para manejar bloqueos y concurrencia.
from concurrent.futures import ThreadPoolExecutor  # Importa ThreadPoolExecutor para ejecutar tareas en hilos.
from enum import Enum  # Importa Enum para definir tipos de eventos como enumeraciones.

# Importar nest_asyncio si estás en un entorno de notebook
import nest_asyncio  # Importa nest_asyncio para anular la política asyncio en entornos de notebooks.
nest_asyncio.apply()  # Aplica la anulación de asyncio para entornos de notebooks.

# Configuración de logging
logging.basicConfig(level=logging.INFO)  # Configura el nivel de logging a INFO.
logger = logging.getLogger(__name__)  # Crea un logger con el nombre del módulo actual.

# Definición de tipos de eventos como una enumeración
class EventType(Enum):
    CELL_EXECUTION = 1  # Tipo de evento para la ejecución de una celda.
    USER_INPUT = 2  # Tipo de evento para la entrada de usuario.
    SYSTEM_UPDATE = 3  # Tipo de evento para la actualización del sistema.
    ERROR = 4  # Tipo de evento para manejar errores.

# Clase para representar un evento con tipo, datos y prioridad
class Event:
    def __init__(self, event_type, data=None, priority=1):
        self.event_type = event_type  # Tipo de evento (enum).
        self.data = data  # Datos asociados al evento (opcional).
        self.priority = priority  # Prioridad del evento en la cola (menor es más prioritario).

    def __lt__(self, other):
        return self.priority < other.priority  # Comparación de prioridad para la cola de prioridad.

# Sistema basado en eventos
class EventSystem:
    def __init__(self):
        self.event_queue = queue.PriorityQueue()  # Inicializa una cola de prioridad vacía.
        self.executor = ThreadPoolExecutor()  # Inicializa un executor de hilos para tareas concurrentes.
        self.lock = threading.Lock()  # Inicializa un objeto de bloqueo para sincronización.

    def add_event(self, event):
        with self.lock:  # Adquiere el bloqueo antes de operar sobre la cola de eventos.
            self.event_queue.put(event)  # Añade un evento a la cola de prioridad.
            logger.info(f'Event added: {event.event_type}, Priority: {event.priority}')  # Registra el evento añadido.

    async def process_events(self):
        while True:
            if not self.event_queue.empty():  # Verifica si la cola de eventos no está vacía.
                with self.lock:  # Adquiere el bloqueo antes de obtener un evento de la cola.
                    event = self.event_queue.get()  # Obtiene el próximo evento de la cola de prioridad.
                await self.handle_event(event)  # Maneja el evento obtenido de manera asíncrona.
            await asyncio.sleep(0.1)  # Pequeña pausa para evitar sobrecargar la CPU.

    async def handle_event(self, event):
        if event.event_type == EventType.CELL_EXECUTION:  # Si el evento es de tipo CELL_EXECUTION.
            await self.execute_cell(event.data)  # Ejecuta la celda asociada al evento de manera asíncrona.
        elif event.event_type == EventType.USER_INPUT:  # Si el evento es de tipo USER_INPUT.
            self.process_user_input(event.data)  # Procesa la entrada de usuario asociada al evento.
        elif event.event_type == EventType.SYSTEM_UPDATE:  # Si el evento es de tipo SYSTEM_UPDATE.
            self.system_update(event.data)  # Procesa la actualización del sistema asociada al evento.
        elif event.event_type == EventType.ERROR:  # Si el evento es de tipo ERROR.
            self.handle_error(event.data)  # Maneja el error asociado al evento.

    async def execute_cell(self, cell_code):
        try:
            logger.info(f'Executing cell: {cell_code}')  # Registra la ejecución de la celda.
            loop = asyncio.get_running_loop()  # Obtiene el ciclo de eventos en ejecución.
            await loop.run_in_executor(self.executor, exec, cell_code)  # Ejecuta la celda en el executor de hilos.
            logger.info('Cell execution complete')  # Registra la finalización de la ejecución de la celda.
        except Exception as e:
            logger.error(f'Error executing cell: {e}')  # Registra un error si ocurre al ejecutar la celda.
            self.add_event(Event(EventType.ERROR, data=str(e), priority=0))  # Añade un evento de error a la cola.

    def process_user_input(self, user_input):
        logger.info(f'Processing user input: {user_input}')  # Registra el procesamiento de la entrada de usuario.
        # Aquí se procesaría la entrada del usuario (implementación simulada).

    def system_update(self, update_info):
        logger.info(f'Performing system update: {update_info}')  # Registra la actualización del sistema.
        # Aquí se procesaría la actualización del sistema (implementación simulada).

    def handle_error(self, error_message):
        logger.error(f'Handling error: {error_message}')  # Registra el manejo de un error.
        # Aquí se manejarían los errores (implementación simulada).

# Simulación de un notebook interactivo
class NotebookSimulator:
    def __init__(self):
        self.event_system = EventSystem()  # Inicializa el sistema de eventos.

    async def run(self):
        event_task = asyncio.create_task(self.event_system.process_events())  # Crea una tarea para procesar eventos.
        # Agrega algunos eventos para simular interacciones de usuario.
        self.event_system.add_event(Event(EventType.USER_INPUT, data="User input example", priority=2))
        self.event_system.add_event(Event(EventType.CELL_EXECUTION, data="print('Hello, Jupyter!')", priority=1))
        self.event_system.add_event(Event(EventType.SYSTEM_UPDATE, data="System update info", priority=3))
        await asyncio.sleep(5)  # Simula el tiempo de ejecución del notebook.
        event_task.cancel()  # Cancela la tarea de procesamiento de eventos.
        try:
            await event_task  # Espera a que la tarea de procesamiento de eventos termine.
        except asyncio.CancelledError:
            logger.info("Event processing task cancelled")  # Registra la cancelación de la tarea de eventos.

if __name__ == "__main__":
    simulator = NotebookSimulator()  # Crea una instancia del simulador de notebook.
    asyncio.run(simulator.run())  # Ejecuta el simulador utilizando asyncio para manejar la ejecución asíncrona.

    