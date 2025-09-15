import socket
import threading
import json


class VehicleTCPServer:
    """TCP服务器用于发送车辆检测数据"""

    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_sockets = []
        self.running = False
        self.lock = threading.Lock()

    def start(self):
        """启动TCP服务器"""
        self.running = True
        threading.Thread(target=self._server_loop, daemon=True).start()
        print(f"TCP服务器启动，监听 {self.host}:{self.port}")

    def _server_loop(self):
        """服务器主循环"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)

            while self.running:
                client_socket, addr = self.server_socket.accept()
                with self.lock:
                    self.client_sockets.append(client_socket)
                print(f"客户端连接: {addr}")

                # 启动客户端处理线程
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()

        except Exception as e:
            if self.running:  # 非预期错误
                print(f"服务器错误: {e}")

    def _handle_client(self, client_socket, addr):
        """处理客户端连接"""
        try:
            while self.running:
                # 保持连接，等待数据发送
                data = client_socket.recv(1024)
                if not data:
                    break
        except Exception as e:
            print(f"客户端 {addr} 错误: {e}")
        finally:
            with self.lock:
                if client_socket in self.client_sockets:
                    self.client_sockets.remove(client_socket)
            client_socket.close()
            print(f"客户端 {addr} 断开连接")

    def send_data(self, data):
        """发送数据到所有连接的客户端"""
        if not self.client_sockets:
            return

        try:
            # 序列化数据为JSON
            json_data = json.dumps(data) + '\n'
            bytes_data = json_data.encode('utf-8')

            # 发送给所有客户端
            with self.lock:
                for client_socket in self.client_sockets[:]:  # 使用副本避免修改迭代中的列表
                    try:
                        client_socket.sendall(bytes_data)
                    except:
                        # 发送失败，移除客户端
                        self.client_sockets.remove(client_socket)
                        client_socket.close()

        except Exception as e:
            print(f"发送数据错误: {e}")

    def stop(self):
        """停止服务器"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        # 关闭所有客户端连接
        with self.lock:
            for client_socket in self.client_sockets:
                try:
                    client_socket.close()
                except:
                    pass
            self.client_sockets.clear()

        print("TCP服务器已停止")
