import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import random
from datetime import datetime
from firmware_data import FIRMWARE_HEX

class UpdateTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RT-880 V1.06 Upgrade Tool 250417")
        self.root.geometry("584x248")
        self.root.resizable(False, False)
        
        # Serial port variables
        self.serial_port = None
        self.port_name = tk.StringVar()
        
        # Update state variables
        self.write_step = 0
        self.rep = 0
        self.step = 0
        self.recv_cnt = 0
        self.send_cnt = 0
        self.g_write_bytes = 0
        
        # Buffers
        self.send_buf = bytearray(2052)
        self.recv_buf = bytearray(29)
        self.hex_data = bytearray(251904)
        
        # Flags
        self.flg_connect = False
        
        # Command bytes
        self.send_connect = bytes([57, 51, 5, 16, 211])
        self.send_end = bytes([57, 51, 5, 238, 177])
        self.send_update = bytes([57, 51, 5, 85, 24])
        self.send_buf_right = bytes([6])
        self.send_buf_error = bytes([255])
        
        # UI variables
        self.all_code = FIRMWARE_HEX
        self.cnt_code = 0
        
        self.setup_ui()
        self.initialize_data()
        
    def setup_ui(self):
        # Create toolbar
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Update button
        self.btn_update = ttk.Button(self.toolbar, text="Update", command=self.btn_update_click)
        self.btn_update.pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Port label
        ttk.Label(self.toolbar, text="Comm:").pack(side=tk.LEFT, padx=5)
        
        # Port combobox
        self.comb_port = ttk.Combobox(self.toolbar, textvariable=self.port_name, state="readonly")
        self.comb_port.pack(side=tk.LEFT, padx=5)
        
        # Reset button
        self.btn_reset = ttk.Button(self.toolbar, text="Reset", command=self.btn_reset_click)
        self.btn_reset.pack(side=tk.LEFT, padx=5)
        
        # Unlock button
        self.btn_unlock = ttk.Button(self.toolbar, text="Unlock", command=self.btn_unlock_click)
        self.btn_unlock.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.txt_state = ttk.Label(self.status_frame, text="000/246")
        self.txt_state.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(self.status_frame, length=290, maximum=246)
        self.progress.pack(side=tk.LEFT, padx=5)
        
        # Instructions label
        self.label1 = ttk.Label(self.root, text="1、Connect the data cable and select the port\n"
                                               "2、Press and hold the PTT key, then turn on the radio\n"
                                               "3、Click the upgrade button",
                               font=("Microsoft Sans Serif", 12, "bold"))
        self.label1.pack(pady=20)
        
    def initialize_data(self):
        # Initialize hex data array
        for i in range(251904):
            self.hex_data[i] = 0
            
        self.g_write_bytes = 0
        self.write_step = 0
        
        # Populate port list
        self.update_port_list()
        
    def update_port_list(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        ports.sort()
        self.comb_port['values'] = ports
        if ports:
            self.comb_port.set(ports[0])
            
    def generate_check_code(self, code_count):
        text = ""
        num = datetime.now().timestamp() + self.rep
        self.rep += 1
        random.seed(int(num) & 0xFFFFFFFF | int(num) >> self.rep)
        
        for i in range(code_count):
            num2 = random.randint(0, 2147483647)
            if num2 % 2 != 0:
                text += chr(65 + (num2 % 26))
            else:
                text += chr(48 + (num2 % 10))
        return text
        
    def checksum(self, array, length):
        b = 0
        for i in range(length - 1):
            b += array[i]
        return (b + 82) & 0xFF
        
    def char_to_int(self, word):
        num = ord(word)
        if 47 < num < 58:
            return num - 48
        if 64 < num < 71:
            return num - 55
        if 96 < num < 103:
            return num - 87
        messagebox.showerror("Error", "Invalid character found")
        return 0
        
    def string_operation(self):
        i = 0
        try:
            while self.all_code[self.cnt_code + i] != ':' or i == 0:
                i += 1
                
            text = self.all_code[self.cnt_code:self.cnt_code + i]
            self.cnt_code += i
            
            num = self.char_to_int(text[7])
            num <<= 4
            
            switch_value = num + self.char_to_int(text[8])
            
            if switch_value == 0:
                num2 = self.char_to_int(text[1])
                num2 <<= 4
                num2 += self.char_to_int(text[2])
                
                num3 = self.char_to_int(text[3])
                num3 <<= 4
                num3 += self.char_to_int(text[4])
                num3 <<= 4
                num3 += self.char_to_int(text[5])
                num3 <<= 4
                num3 += self.char_to_int(text[6])
                
                for j in range(num2):
                    num = self.char_to_int(text[9 + j * 2])
                    num <<= 4
                    num += self.char_to_int(text[10 + j * 2])
                    self.hex_data[num3 + j - 10240 + (self.write_step - 1) * 65536] = num
                return True
                
            elif switch_value == 1:
                return False
                
            elif switch_value == 4:
                self.write_step += 1
                return True
                
            else:
                return True
                
        except Exception:
            return False
            
    def clear_recv_buf(self):
        for i in range(len(self.recv_buf)):
            self.recv_buf[i] = 255
        self.recv_cnt = 0
        
    def data_sum(self, array):
        b = 0
        for i in range(array[2] - 1):
            b += array[i]
        return b
        
    def rev_date_operation(self):
        if self.recv_cnt != 1:
            return
            
        if self.recv_buf[0] == 50:
            pass
        elif self.recv_buf[0] == 0:
            self.recv_cnt = 0
        elif self.recv_buf[0] == 255:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.step = 0
            messagebox.showerror("Error", "Communication Error!")
            self.clear_recv_buf()
        elif self.recv_buf[0] == 6:
            self.recv_cnt = 0
            if self.step < 3:
                self.step += 1
                self.recv_cnt = 0
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.write(self.send_connect)
                    time.sleep(0.05)
            elif self.step == 3:
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.write(self.send_update)
                    time.sleep(0.05)
                self.step = 4
            elif self.step == 4:
                self.root.after(0, self.update_progress)
                if self.serial_port and self.serial_port.is_open:
                    self.send_buf[1] = (self.send_cnt >> 8) & 0xFF
                    self.send_buf[2] = self.send_cnt & 0xFF
                    
                    for i in range(1024):
                        self.send_buf[3 + i] = self.hex_data[self.send_cnt + i]
                        
                    self.send_buf[1027] = self.checksum(self.send_buf, 1028)
                    self.serial_port.write(self.send_buf[:1028])
                    time.sleep(0.05)
                    
                    self.send_cnt += 1024
                    
                    if self.send_cnt == 251904:
                        self.step = 5
                        self.root.after(0, self.complete_update)
                        if self.serial_port and self.serial_port.is_open:
                            self.serial_port.close()
        else:
            self.recv_cnt = 0
            
    def update_progress(self):
        self.progress['value'] += 1
        self.g_write_bytes += 1
        self.txt_state['text'] = f"{self.g_write_bytes:03d}/246"
        
    def complete_update(self):
        self.txt_state['text'] = "Completed!"
        self.progress['value'] = self.progress['maximum']
        self.progress.pack_forget()
        self.progress['value'] = 0
        
    def comm_data_received(self):
        try:
            if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting > 0:
                self.recv_buf[self.recv_cnt] = self.serial_port.read(1)[0]
                self.recv_cnt += 1
                
                if self.recv_buf[0] == 0:
                    self.send_cnt = 0
                    self.flg_connect = True
                    time.sleep(0.2)
                else:
                    self.flg_connect = False
                    time.sleep(0.001)
                    self.rev_date_operation()
                    
        except Exception:
            self.recv_cnt = 0
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                
    def btn_update_click(self):
        if not self.port_name.get():
            messagebox.showwarning("Notice", "Please Select Comm Port!")
            return
            
        self.g_write_bytes = 0
        self.progress['value'] = 0
        self.txt_state['foreground'] = 'green'
        self.progress.pack(side=tk.LEFT, padx=5)
        
        try:
            if not self.serial_port or not self.serial_port.is_open:
                self.serial_port = serial.Serial(
                    port=self.port_name.get(),
                    baudrate=115200,
                    timeout=1
                )
                
            self.step = 1
            self.btn_update['state'] = 'disabled'
            self.send_cnt = 0
            self.flg_connect = True
            
            self.serial_port.write(self.send_connect)
            time.sleep(0.2)
            
            for _ in range(3):
                if self.flg_connect:
                    self.send_cnt = 0
                    self.serial_port.reset_output_buffer()
                    self.serial_port.reset_input_buffer()
                    self.serial_port.write(self.send_connect)
                    time.sleep(0.2)
                    
            if self.flg_connect:
                messagebox.showerror("Error", "Communication Error!")
                self.btn_update['state'] = 'normal'
                if self.serial_port and self.serial_port.is_open:
                    self.serial_port.close()
                    
        except Exception:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.txt_state['text'] = "Error"
            self.txt_state['foreground'] = 'red'
            messagebox.showerror("Error", "Communication Error!")
            
    def btn_reset_click(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.progress['value'] = 0
            
        self.update_port_list()
        
    def btn_unlock_click(self):
        self.btn_update['state'] = 'normal'
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = UpdateTool()
    app.run() 