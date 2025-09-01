import grpc
from concurrent import futures
import chat_pb2
import chat_pb2_grpc
import queue
import threading

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.clients = []
        self.lock = threading.Lock()

    def Chat(self, request_iterator, context):
        # Cada cliente tem sua própria fila
        client_queue = queue.Queue()

        # Adiciona fila do cliente à lista de clientes conectados
        with self.lock:
            self.clients.append(client_queue)

        def send_messages():
            try:
                for message in request_iterator:
                    print(f"[{message.user}]: {message.message}")
                    with self.lock:
                        for q in self.clients:
                            q.put(message)
            except:
                pass
            finally:
                with self.lock:
                    self.clients.remove(client_queue)
                print("Cliente desconectado")

        # Thread para escutar mensagens de entrada do cliente
        threading.Thread(target=send_messages, daemon=True).start()

        # Iterador de respostas — envia mensagens da fila para o cliente
        try:
            while True:
                message = client_queue.get()
                yield message
        except grpc.RpcError as e:
            print(f"Erro no stream de envio: {e.details()}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC rodando em porta 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

