import grpc
import chat_pb2
import chat_pb2_grpc
import threading

def receive_messages(response_iterator):
    try:
        for response in response_iterator:
            print(f"\n[{response.user}]: {response.message}")
            print("Mensagem: ", end="", flush=True)  # 👈 imprime o prompt de novo
    except grpc.RpcError as e:
        print(f"Erro ao receber mensagens: {e.details()}")
    except Exception as e:
        print(f"Erro geral na recepção: {e}")

def main():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = chat_pb2_grpc.ChatServiceStub(channel)
        username = input("Digite seu nome: ").strip()

        print("Digite mensagens para enviar ao chat. Digite /sair para encerrar.")

        # Cria gerador de mensagens
        def message_generator():
            while True:
                try:
                    msg = input("Mensagem: ")  # ✅ prompt adicionado aqui
                    if msg.strip().lower() == "/sair":
                        print("Encerrando conexão...")
                        break
                    yield chat_pb2.Message(user=username, message=msg)
                except Exception as e:
                    print("Erro ao enviar:", e)
                    break

        # Inicia chamada gRPC com stream bidirecional
        response_iterator = stub.Chat(message_generator())

        # Thread para escutar mensagens recebidas
        receive_thread = threading.Thread(target=receive_messages, args=(response_iterator,))
        receive_thread.daemon = True
        receive_thread.start()

        # Aguarda o término da thread receptora
        receive_thread.join()

if __name__ == '__main__':
    main()
