## Chat gRPC em Python — Documentação Completa

Este repositório implementa um chat simples com streaming bidirecional usando gRPC em Python. Abaixo estão as respostas às questões do trabalho e um guia prático para executar localmente e entre máquinas.

### Sumário

- 1. O que é Cliente e Servidor
- 2. O que é gRPC, PROTO, STUB e o que cada comando gera
- 3. Função dos códigos deste projeto
- 4. O que é “localhost”, “IP” e “porta”
- 5. Como rodar e demonstrar a troca de mensagens (local e multi‑máquina)

## 1) O que é Cliente e Servidor (responsável: Carlos)

- **Servidor**: programa que expõe serviços (funções/recursos) e escuta requisições de clientes. No projeto, `server.py` inicia um servidor gRPC que aceita conexões em uma porta e retransmite mensagens para todos os clientes conectados.
- **Cliente**: programa que consome serviços do servidor. Em `client.py`, cada cliente se conecta ao servidor gRPC, envia mensagens e recebe mensagens de outros clientes.

Em termos práticos: vários clientes abrem uma sessão com o servidor; o servidor centraliza a coordenação e distribui as mensagens.

## 2) gRPC, PROTO, STUB e geração de artefatos

- **gRPC**: framework de RPC (chamadas de procedimento remoto) de alta performance, baseado em HTTP/2, que suporta streaming, multiplexação de chamadas e geração de código para múltiplas linguagens.
- **PROTO**: arquivo `.proto` é a Interface Definition Language (IDL) do gRPC/Protocol Buffers. Nele definimos mensagens (estruturas) e serviços (métodos RPC), tipos e contratos entre cliente e servidor.
- **STUB**: código gerado a partir do `.proto` que facilita o consumo/implementação:
  - No cliente, o "client stub" expõe métodos como se fossem locais (ex.: `ChatServiceStub`).
  - No servidor, o "server stub" (classe base `Servicer`) define a interface a ser implementada (ex.: `ChatServiceServicer`).

### Comandos e o que cada um gera (Python)

1. Instalar dependências:

```bash
pip install grpcio grpcio-tools
```

2. Gerar os arquivos Python a partir do `chat.proto` (na raiz do projeto):

```bash
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. chat.proto
```

Isso gera:

- `chat_pb2.py`: classes de mensagens (ex.: `Message`).
- `chat_pb2_grpc.py`: stubs do cliente (`ChatServiceStub`) e base do servidor (`ChatServiceServicer`).

## 3) Função dos códigos do projeto

- `chat.proto`: define o serviço e a mensagem do chat (stream bidirecional).

```3:5:chat.proto
service ChatService {
  rpc Chat(stream Message) returns (stream Message);
}
```

```7:10:chat.proto
message Message {
  string user = 1;
  string message = 2;
}
```

- `server.py`:
  - Implementa `ChatServiceServicer` com o método `Chat`, que cria uma fila por cliente, recebe mensagens do cliente e as retransmite (broadcast) para todos.
  - Inicia o servidor gRPC na porta `50051` e aguarda conexões.

```21:28:server.py
        def send_messages():
            try:
                for message in request_iterator:
                    print(f"[{message.user}]: {message.message}")
                    with self.lock:
                        for q in self.clients:
                            q.put(message)
            except:
                pass
```

```46:52:server.py
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Servidor gRPC rodando em porta 50051...")
```

- `client.py`:
  - Abre canal com o servidor, cria `ChatServiceStub`, envia mensagens digitadas via um gerador e recebe mensagens em uma thread separada.

```17:19:client.py
with grpc.insecure_channel('localhost:50051') as channel:
    stub = chat_pb2_grpc.ChatServiceStub(channel)
    username = input("Digite seu nome: ").strip()
```

```36:42:client.py
        response_iterator = stub.Chat(message_generator())
        receive_thread = threading.Thread(target=receive_messages, args=(response_iterator,))
        receive_thread.daemon = True
        receive_thread.start()
```

## 4) O que é “localhost”, “IP” e “porta” (responsável: Fábio)

- **localhost**: nome padrão que aponta para a própria máquina (loopback). Normalmente resolve para `127.0.0.1` (IPv4) e `::1` (IPv6). Usar `localhost` significa conectar-se ao serviço rodando no mesmo computador.
- **IP**: endereço numérico que identifica uma máquina na rede (ex.: `192.168.1.10`). Pode ser privado (rede local) ou público (internet). DNS pode traduzir nomes (ex.: `meuservidor.exemplo.com`) para IPs.
- **Porta**: número que identifica um serviço em execução dentro de uma máquina (ex.: `50051` para este servidor gRPC). IP + Porta determinam o destino da conexão.

## 5) Como rodar o código e demonstrar a troca de mensagens

### Pré‑requisitos

- Python 3.10+ (o projeto também funciona em 3.12/3.13).
- `pip` atualizado e internet para instalar dependências.

### Instalação (opcional, mas recomendado com ambiente virtual)

```bash
python -m venv .venv
source .venv/Scripts/activate   # Git Bash no Windows
# PowerShell (alternativa): .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install grpcio grpcio-tools
```

### (Re)gerar stubs a partir do .proto (se necessário)

```bash
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. chat.proto
```

### Execução local (mesma máquina)

1. Terminal 1 — iniciar o servidor:

```bash
python server.py
```

2. Terminal 2 — cliente 1:

```bash
python client.py
```

3. Terminal 3 — cliente 2:

```bash
python client.py
```

4. Digite mensagens em qualquer cliente; elas aparecerão nos demais. Para sair, digite `/sair`.

### Execução em múltiplas máquinas (mesma rede)

1. No servidor (máquina A):
   - Descobrir o IP local (Windows):
     - PowerShell: `ipconfig` e localizar “Endereço IPv4”.
   - Garantir que a porta 50051 esteja liberada no Firewall do Windows (PowerShell como Admin):

```powershell
New-NetFirewallRule -DisplayName "gRPC Chat 50051" -Direction Inbound -Protocol TCP -LocalPort 50051 -Action Allow
```

- Iniciar o servidor:

```bash
python server.py
```

2. Nos clientes (máquinas B, C, ...):
   - Editar `client.py` para apontar para o IP do servidor (troque `localhost` pelo IP real):

```17:18:client.py
with grpc.insecure_channel('IP_DO_SERVIDOR:50051') as channel:
```

- Executar o cliente:

```bash
python client.py
```

3. Demonstração: cada usuário digita mensagens que serão exibidas em todos os clientes conectados.

### Observações importantes

- Se as máquinas não estiverem na mesma rede (ou houver NAT/CGNAT), será necessário configurar redirecionamento de porta no roteador ou usar VPN/túnel. Para internet pública, habilite TLS (o exemplo usa `insecure_channel`, adequado apenas para redes confiáveis/testes).
- Em alguns ambientes, o antivírus/firewall pode bloquear o Python; permita o aplicativo “Python” e a porta 50051.

### Problemas comuns (troubleshooting)

- `UNAVAILABLE: failed to connect` no cliente: verifique IP correto, firewall e se o servidor está rodando/escutando na `50051`.
- Mensagens não chegam a todos: confirme que todos os clientes estão conectados ao mesmo servidor/porta e que não há bloqueio de tráfego.
- Erro ao gerar stubs: confirme instalação de `grpcio-tools` e rode o comando na pasta onde está `chat.proto`.

## Segurança (nota rápida)

Este exemplo usa canais inseguros (sem TLS). Para uso fora de redes de confiança, adicione TLS no servidor/cliente gRPC e autenticação.

## Arquivos principais

- `chat.proto`: contrato do serviço e mensagens.
- `chat_pb2.py`: classes de mensagens (gerado).
- `chat_pb2_grpc.py`: stubs e base do servidor (gerado).
- `server.py`: implementação do serviço e bootstrap do servidor.
- `client.py`: cliente interativo de console.

---

Trabalho acadêmico — Seções 1) Carlos; 4) Fábio. Demais seções: documentação do projeto e guia de execução.
