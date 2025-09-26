"""
eBPF-based log forwarder for advanced Linux monitoring
Provides kernel-level visibility without requiring root privileges for some operations
"""

import asyncio
import logging
import platform
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_forwarder import BaseLogForwarder
from ...shared.models import LogSource


logger = logging.getLogger(__name__)


class EBPFLogForwarder(BaseLogForwarder):
    """eBPF-based log forwarder for advanced Linux monitoring"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        super().__init__(agent_id, config)
        
        self.ebpf_enabled = config.get('ebpf', {}).get('enabled', False)
        self.ebpf_available = False
        
        # Check if running on Linux
        if platform.system() != "Linux":
            logger.warning("eBPF forwarder can only run on Linux")
            self.ebpf_enabled = False
        
        # Check eBPF availability
        if self.ebpf_enabled:
            self._check_ebpf_availability()
    
    def _check_ebpf_availability(self):
        """Check if eBPF is available on the system"""
        try:
            # Check for BCC (BPF Compiler Collection)
            try:
                from bcc import BPF
                self.ebpf_available = True
                logger.info("eBPF (BCC) available for advanced monitoring")
            except ImportError:
                logger.info("BCC not available. Install with: pip install bcc")
                
                # Check for alternative eBPF libraries
                try:
                    import bpfcc
                    self.ebpf_available = True
                    logger.info("Alternative eBPF library available")
                except ImportError:
                    pass
            
            # Check kernel support
            if self.ebpf_available:
                import os
                if not os.path.exists('/sys/kernel/debug/tracing'):
                    logger.warning("eBPF tracing not available - may need debugfs mount")
                    logger.info("Try: sudo mount -t debugfs none /sys/kernel/debug")
                
        except Exception as e:
            logger.error(f"eBPF availability check failed: {e}")
            self.ebpf_available = False
    
    def _get_log_source(self) -> LogSource:
        """Get log source type"""
        return LogSource.LINUX_SYSTEM
    
    async def _collect_logs(self) -> None:
        """Collect logs using eBPF"""
        if not self.ebpf_available:
            logger.info("eBPF not available, using fallback monitoring")
            await self._fallback_monitoring()
            return
        
        try:
            # Start eBPF monitoring tasks
            tasks = [
                asyncio.create_task(self._monitor_syscalls()),
                asyncio.create_task(self._monitor_network_events()),
                asyncio.create_task(self._monitor_file_events()),
                asyncio.create_task(self._monitor_process_events())
            ]
            
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"eBPF monitoring failed: {e}")
            await self._fallback_monitoring()
    
    async def _monitor_syscalls(self) -> None:
        """Monitor system calls using eBPF"""
        try:
            from bcc import BPF
            
            # eBPF program to monitor suspicious syscalls
            bpf_program = """
            #include <uapi/linux/ptrace.h>
            #include <linux/sched.h>
            
            struct data_t {
                u32 pid;
                u32 uid;
                char comm[TASK_COMM_LEN];
                char syscall[64];
            };
            
            BPF_PERF_OUTPUT(events);
            
            int trace_syscall(struct pt_regs *ctx) {
                struct data_t data = {};
                data.pid = bpf_get_current_pid_tgid() >> 32;
                data.uid = bpf_get_current_uid_gid() & 0xffffffff;
                bpf_get_current_comm(&data.comm, sizeof(data.comm));
                
                events.perf_submit(ctx, &data, sizeof(data));
                return 0;
            }
            """
            
            # Load eBPF program
            b = BPF(text=bpf_program)
            
            # Attach to suspicious syscalls
            suspicious_syscalls = ['execve', 'openat', 'connect', 'sendto']
            
            for syscall in suspicious_syscalls:
                try:
                    b.attach_kprobe(event=f"sys_{syscall}", fn_name="trace_syscall")
                except Exception as e:
                    logger.warning(f"Could not attach to {syscall}: {e}")
            
            # Process events
            def process_event(cpu, data, size):
                try:
                    event = b["events"].event(data)
                    
                    log_data = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'event_type': 'ebpf_syscall',
                        'level': 'info',
                        'message': f"Syscall from {event.comm.decode('utf-8', 'replace')}",
                        'process_id': event.pid,
                        'user_id': event.uid,
                        'process_name': event.comm.decode('utf-8', 'replace'),
                        'source': 'ebpf_syscall_monitor'
                    }
                    
                    asyncio.create_task(self.log_queue.put(log_data))
                    
                except Exception as e:
                    logger.error(f"eBPF event processing failed: {e}")
            
            # Start monitoring
            b["events"].open_perf_buffer(process_event)
            
            logger.info("eBPF syscall monitoring started")
            
            while self.running:
                try:
                    b.perf_buffer_poll(timeout=1000)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"eBPF polling error: {e}")
                    await asyncio.sleep(1)
        
        except ImportError:
            logger.info("BCC not available for eBPF syscall monitoring")
        except Exception as e:
            logger.error(f"eBPF syscall monitoring failed: {e}")
    
    async def _monitor_network_events(self) -> None:
        """Monitor network events using eBPF"""
        try:
            from bcc import BPF
            
            # eBPF program for network monitoring
            network_program = """
            #include <uapi/linux/ptrace.h>
            #include <net/sock.h>
            #include <bcc/proto.h>
            
            struct net_event_t {
                u32 pid;
                u32 saddr;
                u32 daddr;
                u16 sport;
                u16 dport;
                char comm[TASK_COMM_LEN];
            };
            
            BPF_PERF_OUTPUT(net_events);
            
            int trace_connect(struct pt_regs *ctx, struct sock *sk) {
                struct net_event_t data = {};
                data.pid = bpf_get_current_pid_tgid() >> 32;
                bpf_get_current_comm(&data.comm, sizeof(data.comm));
                
                // Extract network info
                data.saddr = sk->__sk_common.skc_rcv_saddr;
                data.daddr = sk->__sk_common.skc_daddr;
                data.sport = sk->__sk_common.skc_num;
                data.dport = sk->__sk_common.skc_dport;
                
                net_events.perf_submit(ctx, &data, sizeof(data));
                return 0;
            }
            """
            
            b = BPF(text=network_program)
            b.attach_kprobe(event="tcp_connect", fn_name="trace_connect")
            
            def process_net_event(cpu, data, size):
                try:
                    event = b["net_events"].event(data)
                    
                    log_data = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'event_type': 'ebpf_network',
                        'level': 'info',
                        'message': f"Network connection from {event.comm.decode('utf-8', 'replace')}",
                        'process_id': event.pid,
                        'process_name': event.comm.decode('utf-8', 'replace'),
                        'source_ip': self._int_to_ip(event.saddr),
                        'dest_ip': self._int_to_ip(event.daddr),
                        'source_port': event.sport,
                        'dest_port': event.dport,
                        'source': 'ebpf_network_monitor'
                    }
                    
                    asyncio.create_task(self.log_queue.put(log_data))
                    
                except Exception as e:
                    logger.error(f"eBPF network event processing failed: {e}")
            
            b["net_events"].open_perf_buffer(process_net_event)
            
            logger.info("eBPF network monitoring started")
            
            while self.running:
                try:
                    b.perf_buffer_poll(timeout=1000)
                except Exception as e:
                    logger.error(f"eBPF network polling error: {e}")
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"eBPF network monitoring failed: {e}")
    
    async def _monitor_file_events(self) -> None:
        """Monitor file access using eBPF"""
        try:
            from bcc import BPF
            
            # eBPF program for file monitoring
            file_program = """
            #include <uapi/linux/ptrace.h>
            #include <linux/fs.h>
            
            struct file_event_t {
                u32 pid;
                char comm[TASK_COMM_LEN];
                char filename[256];
                u32 flags;
            };
            
            BPF_PERF_OUTPUT(file_events);
            
            int trace_openat(struct pt_regs *ctx, int dfd, const char __user *filename, int flags) {
                struct file_event_t data = {};
                data.pid = bpf_get_current_pid_tgid() >> 32;
                data.flags = flags;
                bpf_get_current_comm(&data.comm, sizeof(data.comm));
                bpf_probe_read_user(&data.filename, sizeof(data.filename), (void *)filename);
                
                file_events.perf_submit(ctx, &data, sizeof(data));
                return 0;
            }
            """
            
            b = BPF(text=file_program)
            b.attach_kprobe(event="sys_openat", fn_name="trace_openat")
            
            def process_file_event(cpu, data, size):
                try:
                    event = b["file_events"].event(data)
                    filename = event.filename.decode('utf-8', 'replace')
                    
                    # Filter for interesting files
                    if any(pattern in filename for pattern in ['/etc/', '/tmp/', '/var/', '.sh', '.py', '.exe']):
                        log_data = {
                            'timestamp': datetime.utcnow().isoformat(),
                            'event_type': 'ebpf_file_access',
                            'level': 'info',
                            'message': f"File access: {filename}",
                            'process_id': event.pid,
                            'process_name': event.comm.decode('utf-8', 'replace'),
                            'filename': filename,
                            'access_flags': event.flags,
                            'source': 'ebpf_file_monitor'
                        }
                        
                        asyncio.create_task(self.log_queue.put(log_data))
                    
                except Exception as e:
                    logger.error(f"eBPF file event processing failed: {e}")
            
            b["file_events"].open_perf_buffer(process_file_event)
            
            logger.info("eBPF file monitoring started")
            
            while self.running:
                try:
                    b.perf_buffer_poll(timeout=1000)
                except Exception as e:
                    logger.error(f"eBPF file polling error: {e}")
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"eBPF file monitoring failed: {e}")
    
    async def _monitor_process_events(self) -> None:
        """Monitor process events using eBPF"""
        try:
            from bcc import BPF
            
            # eBPF program for process monitoring
            process_program = """
            #include <uapi/linux/ptrace.h>
            #include <linux/sched.h>
            
            struct proc_event_t {
                u32 pid;
                u32 ppid;
                u32 uid;
                char comm[TASK_COMM_LEN];
                char filename[256];
            };
            
            BPF_PERF_OUTPUT(proc_events);
            
            int trace_exec(struct pt_regs *ctx, const char __user *filename) {
                struct proc_event_t data = {};
                data.pid = bpf_get_current_pid_tgid() >> 32;
                data.ppid = bpf_get_current_pid_tgid() & 0xffffffff;
                data.uid = bpf_get_current_uid_gid() & 0xffffffff;
                bpf_get_current_comm(&data.comm, sizeof(data.comm));
                bpf_probe_read_user(&data.filename, sizeof(data.filename), (void *)filename);
                
                proc_events.perf_submit(ctx, &data, sizeof(data));
                return 0;
            }
            """
            
            b = BPF(text=process_program)
            b.attach_kprobe(event="sys_execve", fn_name="trace_exec")
            
            def process_proc_event(cpu, data, size):
                try:
                    event = b["proc_events"].event(data)
                    
                    log_data = {
                        'timestamp': datetime.utcnow().isoformat(),
                        'event_type': 'ebpf_process_exec',
                        'level': 'info',
                        'message': f"Process executed: {event.comm.decode('utf-8', 'replace')}",
                        'process_id': event.pid,
                        'parent_process_id': event.ppid,
                        'user_id': event.uid,
                        'process_name': event.comm.decode('utf-8', 'replace'),
                        'executable_path': event.filename.decode('utf-8', 'replace'),
                        'source': 'ebpf_process_monitor'
                    }
                    
                    asyncio.create_task(self.log_queue.put(log_data))
                    
                except Exception as e:
                    logger.error(f"eBPF process event processing failed: {e}")
            
            b["proc_events"].open_perf_buffer(process_proc_event)
            
            logger.info("eBPF process monitoring started")
            
            while self.running:
                try:
                    b.perf_buffer_poll(timeout=1000)
                except Exception as e:
                    logger.error(f"eBPF process polling error: {e}")
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"eBPF process monitoring failed: {e}")
    
    async def _fallback_monitoring(self) -> None:
        """Fallback monitoring when eBPF not available"""
        logger.info("Using fallback monitoring (procfs/sysfs)")
        
        while self.running:
            try:
                # Monitor /proc for process information
                await self._monitor_proc_filesystem()
                
                # Monitor network connections
                await self._monitor_network_connections()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Fallback monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _monitor_proc_filesystem(self) -> None:
        """Monitor /proc filesystem for process information"""
        try:
            import os
            import glob
            
            # Get list of processes
            proc_dirs = glob.glob('/proc/[0-9]*')
            
            for proc_dir in proc_dirs[:20]:  # Limit to avoid overwhelming
                try:
                    pid = os.path.basename(proc_dir)
                    
                    # Read process info
                    cmdline_file = os.path.join(proc_dir, 'cmdline')
                    if os.path.exists(cmdline_file):
                        with open(cmdline_file, 'r') as f:
                            cmdline = f.read().replace('\x00', ' ').strip()
                        
                        if cmdline and any(suspicious in cmdline.lower() for suspicious in 
                                         ['bash', 'python', 'curl', 'wget', 'nc']):
                            log_data = {
                                'timestamp': datetime.utcnow().isoformat(),
                                'event_type': 'proc_monitor',
                                'level': 'info',
                                'message': f"Process activity: {cmdline[:100]}",
                                'process_id': pid,
                                'command_line': cmdline,
                                'source': 'proc_filesystem_monitor'
                            }
                            
                            await self.log_queue.put(log_data)
                
                except Exception as e:
                    # Expected for some processes
                    continue
        
        except Exception as e:
            logger.error(f"Proc filesystem monitoring failed: {e}")
    
    async def _monitor_network_connections(self) -> None:
        """Monitor network connections from /proc/net"""
        try:
            # Read network connections
            with open('/proc/net/tcp', 'r') as f:
                lines = f.readlines()[1:]  # Skip header
            
            for line in lines[:10]:  # Limit connections
                try:
                    parts = line.split()
                    if len(parts) >= 4:
                        local_addr = parts[1]
                        remote_addr = parts[2]
                        state = parts[3]
                        
                        # Parse addresses
                        local_ip, local_port = self._parse_address(local_addr)
                        remote_ip, remote_port = self._parse_address(remote_addr)
                        
                        if remote_ip != '0.0.0.0':  # Active connection
                            log_data = {
                                'timestamp': datetime.utcnow().isoformat(),
                                'event_type': 'network_connection',
                                'level': 'info',
                                'message': f"Network connection: {local_ip}:{local_port} -> {remote_ip}:{remote_port}",
                                'local_ip': local_ip,
                                'local_port': local_port,
                                'remote_ip': remote_ip,
                                'remote_port': remote_port,
                                'connection_state': state,
                                'source': 'proc_net_monitor'
                            }
                            
                            await self.log_queue.put(log_data)
                
                except Exception as e:
                    continue
        
        except Exception as e:
            logger.error(f"Network connection monitoring failed: {e}")
    
    def _int_to_ip(self, ip_int: int) -> str:
        """Convert integer IP to string"""
        try:
            import socket
            import struct
            return socket.inet_ntoa(struct.pack("!I", ip_int))
        except:
            return "0.0.0.0"
    
    def _parse_address(self, addr_str: str) -> tuple:
        """Parse address string from /proc/net format"""
        try:
            ip_hex, port_hex = addr_str.split(':')
            
            # Convert hex to IP
            ip_int = int(ip_hex, 16)
            ip = self._int_to_ip(ip_int)
            
            # Convert hex to port
            port = int(port_hex, 16)
            
            return ip, port
        except:
            return "0.0.0.0", 0
    
    async def _parse_structured_data(self, raw_log: Dict[str, Any]) -> Dict[str, Any]:
        """Parse eBPF-specific structured data"""
        structured_data = await super()._parse_structured_data(raw_log)
        
        # Add eBPF-specific fields
        ebpf_fields = ['process_id', 'parent_process_id', 'user_id', 'executable_path',
                      'source_ip', 'dest_ip', 'source_port', 'dest_port', 'connection_state',
                      'access_flags', 'filename']
        
        for field in ebpf_fields:
            if field in raw_log:
                structured_data[field] = raw_log[field]
        
        return structured_data
