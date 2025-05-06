"""System provider for Contextuals."""

import os
import sys
import platform
import socket
import getpass
import json
import datetime
import subprocess
from typing import Dict, Any, Optional

from contextuals.core.cache import Cache, cached
from contextuals.core.config import Config


class SystemProvider:
    """Provides system-related contextual information.
    
    Features:
    - Retrieves operating system information
    - Gets hostname and username data
    - Provides hardware information
    - Caches results to minimize expensive operations
    """
    
    def __init__(self, config: Config, cache: Cache, context_manager=None):
        """Initialize the system provider.
        
        Args:
            config: Configuration instance.
            cache: Cache instance.
            context_manager: Optional context manager instance.
        """
        self.config = config
        self.cache = cache
        self.context_manager = context_manager
    
    def _get_current_date(self) -> str:
        """Get the current date in ISO format.
        
        This is used to indicate when the data was retrieved.
        
        Returns:
            Current date as string in ISO format.
        """
        if self.context_manager:
            return self.context_manager.get_current_datetime_iso()
        return datetime.datetime.now(datetime.timezone.utc).isoformat()
        
    def _run_command(self, command, shell=False):
        """Run a command and return its output.
        
        Args:
            command: The command to run as a list of strings.
            shell: Whether to run the command in a shell.
            
        Returns:
            The command output as a string or None if the command failed.
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=2  # Timeout after 2 seconds to prevent hanging
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return None
    
    @cached(ttl=3600)  # Cache for 1 hour
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information.
        
        This information is always available since it's local to the machine.
        
        Returns:
            Dictionary with system information.
        """
        response_time = self._get_current_date()
        
        # Collect system information
        system_data = {
            "os": {
                "name": os.name,
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture()[0],
                "python_version": platform.python_version(),
            },
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "user": {
                "username": getpass.getuser(),
                "home_directory": os.path.expanduser("~"),
                "shell": os.environ.get("SHELL", ""),
            },
            "environment": {
                "path": os.environ.get("PATH", ""),
                "lang": os.environ.get("LANG", ""),
                "term": os.environ.get("TERM", ""),
                "terminal": os.environ.get("TERM_PROGRAM", ""),
            },
        }
        
        # Try to get more detailed OS information based on platform
        if platform.system() == "Linux":
            try:
                with open("/etc/os-release", "r") as f:
                    os_release = {}
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            os_release[key] = value.strip('"')
                    
                    system_data["os"]["distribution"] = os_release.get("NAME", "")
                    system_data["os"]["distribution_version"] = os_release.get("VERSION", "")
                    system_data["os"]["distribution_id"] = os_release.get("ID", "")
            except:
                pass
        
        elif platform.system() == "Darwin":
            # Add macOS-specific information
            try:
                import subprocess
                macos_version = subprocess.check_output(["sw_vers", "-productVersion"]).decode().strip()
                system_data["os"]["macos_version"] = macos_version
            except:
                pass
        
        elif platform.system() == "Windows":
            # Add Windows-specific information
            system_data["os"]["edition"] = platform.win32_edition() if hasattr(platform, "win32_edition") else "Unknown"
        
        # Create structured response
        result = {
            "timestamp": response_time,
            "request_time": response_time,
            "type": "system_info",
            "is_cached": False,
            "data": system_data
        }
        
        return result
    
    @cached(ttl=60)  # Cache for 1 minute
    def get_user_info(self) -> Dict[str, Any]:
        """Get user information.
        
        Returns:
            Dictionary with user information.
        """
        response_time = self._get_current_date()
        
        # Collect user information
        user_data = {
            "username": getpass.getuser(),
            "home_directory": os.path.expanduser("~"),
            "shell": os.environ.get("SHELL", ""),
            "language": os.environ.get("LANG", ""),
            "terminal": os.environ.get("TERM_PROGRAM", ""),
        }
        
        # Try to get more detailed user information
        try:
            import pwd
            user_info = pwd.getpwnam(getpass.getuser())
            user_data["uid"] = user_info.pw_uid
            user_data["gid"] = user_info.pw_gid
            user_data["full_name"] = user_info.pw_gecos.split(",")[0] if user_info.pw_gecos else ""
        except (ImportError, KeyError):
            # pwd module is not available on all platforms
            pass
        
        # Create structured response
        result = {
            "timestamp": response_time,
            "request_time": response_time,
            "type": "user_info",
            "is_cached": False,
            "data": user_data
        }
        
        return result
        
    @cached(ttl=60)  # Cache for 1 minute
    def get_machine_info(self) -> Dict[str, Any]:
        """Get detailed information about the local machine.
        
        Returns:
            Dictionary with machine information.
        """
        response_time = self._get_current_date()
        
        # Collect machine information
        machine_data = {
            "hostname": socket.gethostname(),
            "fqdn": socket.getfqdn(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine(),
            "processor": platform.processor(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        }
        
        # Add detailed system information
        uname = platform.uname()
        machine_data["system_info"] = {
            "system": uname.system,
            "node": uname.node,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
            "processor": uname.processor,
            "architecture": platform.architecture()[0]
        }
        
        # Try to get IP address safely
        try:
            machine_data["ip_address"] = socket.gethostbyname(socket.gethostname())
        except:
            try:
                # Alternative method to get IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                machine_data["ip_address"] = s.getsockname()[0]
                s.close()
            except:
                machine_data["ip_address"] = "127.0.0.1"
                
        # Get MAC address (works on all platforms)
        try:
            from uuid import getnode as get_mac
            mac_int = get_mac()
            if mac_int != 0:
                mac_hex = ':'.join(['{:02x}'.format((mac_int >> i) & 0xff) for i in range(0, 48, 8)][::-1])
                machine_data["mac_address"] = mac_hex
        except Exception:
            machine_data["mac_address"] = "Unknown"
            
        # Try to get hardware UUID
        try:
            # For macOS
            if platform.system() == "Darwin":
                system_profiler_output = self._run_command(["system_profiler", "SPHardwareDataType"])
                if system_profiler_output:
                    for line in system_profiler_output.split('\n'):
                        if ':' in line:
                            key, value = [x.strip() for x in line.split(':', 1)]
                            if key == "Hardware UUID":
                                machine_data["hardware_uuid"] = value
            # For Linux
            elif platform.system() == "Linux":
                # Try using dmidecode for hardware UUID (requires root access)
                dmidecode_output = self._run_command(["sudo", "dmidecode", "-s", "system-uuid"])
                if dmidecode_output:
                    machine_data["hardware_uuid"] = dmidecode_output.strip()
                else:
                    # Alternative approach without sudo
                    try:
                        with open("/sys/class/dmi/id/product_uuid", "r") as f:
                            machine_data["hardware_uuid"] = f.read().strip()
                    except:
                        pass
            # For Windows
            elif platform.system() == "Windows":
                wmic_output = self._run_command(["wmic", "csproduct", "get", "UUID"])
                if wmic_output:
                    lines = wmic_output.strip().split('\n')
                    if len(lines) > 1:
                        machine_data["hardware_uuid"] = lines[1].strip()
        except Exception:
            machine_data["hardware_uuid"] = "Unknown"
        
        # Try to get more detailed machine information
        try:
            import subprocess
            
            # Get CPU information
            cpu_info = {}
            
            if platform.system() == "Linux":
                try:
                    # Get CPU count and model
                    with open("/proc/cpuinfo", "r") as f:
                        cpuinfo = f.read()
                    
                    # Count physical processors
                    physical_count = len([line for line in cpuinfo.split("\n") if "physical id" in line])
                    if physical_count == 0:
                        physical_count = 1
                        
                    # Count cores
                    core_count = len([line for line in cpuinfo.split("\n") if "cpu cores" in line])
                    if core_count == 0:
                        core_count = os.cpu_count() or 1
                        
                    # Get model name
                    model_lines = [line for line in cpuinfo.split("\n") if "model name" in line]
                    if model_lines:
                        model = model_lines[0].split(":")[1].strip()
                    else:
                        model = "Unknown"
                        
                    cpu_info = {
                        "physical_processors": physical_count,
                        "cores": core_count,
                        "logical_processors": os.cpu_count() or 1,
                        "model": model
                    }
                except:
                    cpu_info = {"cores": os.cpu_count() or 1}
                    
            elif platform.system() == "Darwin":
                try:
                    # For macOS
                    core_count = int(subprocess.check_output(["sysctl", "-n", "hw.physicalcpu"]).decode().strip())
                    logical_count = int(subprocess.check_output(["sysctl", "-n", "hw.logicalcpu"]).decode().strip())
                    model = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
                    
                    cpu_info = {
                        "physical_processors": 1,  # Usually 1 in Macs
                        "cores": core_count,
                        "logical_processors": logical_count,
                        "model": model
                    }
                except:
                    cpu_info = {"cores": os.cpu_count() or 1}
                    
            elif platform.system() == "Windows":
                try:
                    # For Windows
                    import ctypes
                    
                    # Get logical processor count
                    logical_count = os.cpu_count() or 1
                    
                    # Try to get model info from WMI
                    try:
                        model = subprocess.check_output(["wmic", "cpu", "get", "name"]).decode().strip().split("\n")[1]
                    except:
                        model = "Unknown"
                        
                    cpu_info = {
                        "cores": logical_count,  # Windows doesn't easily expose physical cores
                        "logical_processors": logical_count,
                        "model": model
                    }
                except:
                    cpu_info = {"cores": os.cpu_count() or 1}
            else:
                cpu_info = {"cores": os.cpu_count() or 1}
                
            machine_data["cpu"] = cpu_info
            
            # Get memory information
            memory_info = {}
            
            if platform.system() == "Linux":
                try:
                    with open("/proc/meminfo", "r") as f:
                        meminfo = f.read()
                    
                    total_line = [line for line in meminfo.split("\n") if "MemTotal" in line][0]
                    free_line = [line for line in meminfo.split("\n") if "MemFree" in line][0]
                    
                    total_kb = int(total_line.split()[1])
                    free_kb = int(free_line.split()[1])
                    
                    memory_info = {
                        "total_mb": total_kb // 1024,
                        "free_mb": free_kb // 1024,
                        "used_mb": (total_kb - free_kb) // 1024,
                        "usage_percent": ((total_kb - free_kb) / total_kb) * 100
                    }
                except:
                    pass
                    
            elif platform.system() == "Darwin":
                try:
                    # For macOS
                    total_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip())
                    vm_stat = subprocess.check_output(["vm_stat"]).decode().strip()
                    
                    # Parse vm_stat output
                    page_size = 4096  # Default page size for macOS
                    free_pages = int([line for line in vm_stat.split("\n") if "Pages free" in line][0].split(":")[1].strip().replace(".", ""))
                    free_bytes = free_pages * page_size
                    
                    memory_info = {
                        "total_mb": total_bytes // (1024 * 1024),
                        "free_mb": free_bytes // (1024 * 1024),
                        "used_mb": (total_bytes - free_bytes) // (1024 * 1024),
                        "usage_percent": ((total_bytes - free_bytes) / total_bytes) * 100
                    }
                except:
                    pass
                    
            elif platform.system() == "Windows":
                try:
                    # For Windows
                    import ctypes
                    
                    class MEMORYSTATUSEX(ctypes.Structure):
                        _fields_ = [
                            ("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                        ]

                    memory_status = MEMORYSTATUSEX()
                    memory_status.dwLength = ctypes.sizeof(memory_status)
                    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))
                    
                    memory_info = {
                        "total_mb": memory_status.ullTotalPhys // (1024 * 1024),
                        "free_mb": memory_status.ullAvailPhys // (1024 * 1024),
                        "used_mb": (memory_status.ullTotalPhys - memory_status.ullAvailPhys) // (1024 * 1024),
                        "usage_percent": memory_status.dwMemoryLoad
                    }
                except:
                    pass
                    
            machine_data["memory"] = memory_info
            
            # Get disk information
            if hasattr(os, "statvfs"):
                try:
                    # For Unix-like systems
                    disk_info = {}
                    root_stats = os.statvfs("/")
                    
                    total_blocks = root_stats.f_blocks
                    free_blocks = root_stats.f_bfree
                    block_size = root_stats.f_frsize
                    
                    total_bytes = total_blocks * block_size
                    free_bytes = free_blocks * block_size
                    
                    disk_info = {
                        "total_gb": total_bytes / (1024 * 1024 * 1024),
                        "free_gb": free_bytes / (1024 * 1024 * 1024),
                        "used_gb": (total_bytes - free_bytes) / (1024 * 1024 * 1024),
                        "usage_percent": ((total_bytes - free_bytes) / total_bytes) * 100
                    }
                    
                    machine_data["disk"] = disk_info
                except:
                    pass
                    
            elif platform.system() == "Windows":
                try:
                    # For Windows
                    import ctypes
                    
                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    available_bytes = ctypes.c_ulonglong(0)
                    
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p("C:\\"),
                        ctypes.byref(free_bytes),
                        ctypes.byref(total_bytes),
                        ctypes.byref(available_bytes)
                    )
                    
                    disk_info = {
                        "total_gb": total_bytes.value / (1024 * 1024 * 1024),
                        "free_gb": free_bytes.value / (1024 * 1024 * 1024),
                        "used_gb": (total_bytes.value - free_bytes.value) / (1024 * 1024 * 1024),
                        "usage_percent": ((total_bytes.value - free_bytes.value) / total_bytes.value) * 100
                    }
                    
                    machine_data["disk"] = disk_info
                except:
                    pass
        except:
            # Ignore errors if we can't get additional information
            pass
            
        # Create structured response
        result = {
            "timestamp": response_time,
            "request_time": response_time,
            "type": "machine_info",
            "is_cached": False,
            "data": machine_data
        }
        
        return result
        
    @cached(ttl=60)  # Cache for 1 minute
    def get_logged_users(self) -> Dict[str, Any]:
        """Get information about users logged into the system.
        
        Returns:
            Dictionary with logged users information.
        """
        response_time = self._get_current_date()
        
        # Collect user information
        users_data = {
            "current_user": getpass.getuser(),
            "current_user_info": {},
            "all_logged_users": []
        }
        
        # Get detailed information about current user
        try:
            import pwd
            user_info = pwd.getpwnam(getpass.getuser())
            full_name = user_info.pw_gecos.split(",")[0] if user_info.pw_gecos else ""
            
            users_data["current_user_info"] = {
                "uid": user_info.pw_uid,
                "gid": user_info.pw_gid,
                "full_name": full_name,
                "home_directory": user_info.pw_dir,
                "shell": user_info.pw_shell
            }
            
            # On macOS, try to get more detailed user info
            if platform.system() == "Darwin" and not full_name:
                try:
                    import subprocess
                    # Try using Directory Service command on macOS
                    ds_output = subprocess.check_output(["dscl", ".", "-read", f"/Users/{getpass.getuser()}", "RealName"]).decode().strip()
                    if "RealName:" in ds_output:
                        real_name = ds_output.split("RealName:")[1].strip()
                        if real_name:
                            users_data["current_user_info"]["full_name"] = real_name
                except:
                    pass
        except (ImportError, KeyError):
            # pwd module is not available on all platforms
            users_data["current_user_info"] = {
                "home_directory": os.path.expanduser("~"),
                "shell": os.environ.get("SHELL", "")
            }
            
            # On Windows, try to get user's full name
            if platform.system() == "Windows":
                try:
                    import subprocess
                    import ctypes
                    
                    # Try using Windows Management Instrumentation Command-line (WMIC)
                    try:
                        wmic_output = subprocess.check_output(["wmic", "useraccount", "where", f"name='{getpass.getuser()}'", "get", "fullname"]).decode().strip()
                        lines = wmic_output.split("\n")
                        if len(lines) >= 2:
                            full_name = lines[1].strip()
                            if full_name:
                                users_data["current_user_info"]["full_name"] = full_name
                    except:
                        # Alternative: try using GetUserNameEx function
                        try:
                            GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
                            NameDisplay = 3  # DisplayName
                            
                            size = ctypes.c_ulong(0)
                            GetUserNameEx(NameDisplay, None, ctypes.byref(size))
                            
                            buffer = ctypes.create_unicode_buffer(size.value)
                            GetUserNameEx(NameDisplay, buffer, ctypes.byref(size))
                            
                            if buffer.value:
                                users_data["current_user_info"]["full_name"] = buffer.value
                        except:
                            pass
                except:
                    pass
            
        # Get unique logged-in users (just the count, not all details)
        try:
            unique_users = set()
            
            # On Unix-like systems, try to use 'who' command
            if platform.system() in ["Linux", "Darwin"]:
                import subprocess
                
                who_output = subprocess.check_output(["who"]).decode().strip()
                
                for line in who_output.split("\n"):
                    if not line.strip():
                        continue
                        
                    parts = line.split()
                    if parts:
                        unique_users.add(parts[0])
                
                # Add enhanced user info for each unique user
                for username in unique_users:
                    try:
                        import pwd
                        user_info = pwd.getpwnam(username)
                        full_name = user_info.pw_gecos.split(",")[0] if user_info.pw_gecos else ""
                        
                        # On macOS, try to get more detailed name info if not in GECOS
                        if platform.system() == "Darwin" and not full_name:
                            try:
                                ds_output = subprocess.check_output(["dscl", ".", "-read", f"/Users/{username}", "RealName"]).decode().strip()
                                if "RealName:" in ds_output:
                                    real_name = ds_output.split("RealName:")[1].strip()
                                    if real_name:
                                        full_name = real_name
                            except:
                                pass
                        
                        user_entry = {
                            "username": username,
                            "uid": user_info.pw_uid,
                            "full_name": full_name
                        }
                        
                        # Try to get email address from common locations
                        try:
                            if platform.system() == "Darwin":
                                # macOS contacts lookup
                                contact_cmd = ["contacts", "-m", username]
                                contact_out = subprocess.check_output(contact_cmd, stderr=subprocess.DEVNULL).decode().strip()
                                
                                if "@" in contact_out:
                                    email_lines = [line for line in contact_out.split("\n") if "@" in line]
                                    if email_lines:
                                        email = email_lines[0].strip()
                                        user_entry["email"] = email
                        except:
                            pass
                            
                        users_data["all_logged_users"].append(user_entry)
                    except:
                        users_data["all_logged_users"].append({"username": username})
                        
            # On Windows, get unique logged-in users
            elif platform.system() == "Windows":
                import subprocess
                
                try:
                    # Try query user first
                    output = subprocess.check_output(["query", "user"]).decode().strip()
                    
                    lines = output.split("\n")[1:]  # Skip header
                    for line in lines:
                        parts = [p for p in line.split() if p]
                        if parts:
                            unique_users.add(parts[0])
                except:
                    # If query user fails, try net user
                    try:
                        output = subprocess.check_output(["net", "user"]).decode().strip()
                        lines = output.split("\n")
                        
                        # Extract usernames from the output
                        for line in lines:
                            if "User accounts for" in line or "command completed" in line or "---" in line or not line.strip():
                                continue
                                
                            for username in line.split():
                                if username.strip():
                                    unique_users.add(username.strip())
                    except:
                        pass
                
                # Add enhanced user info for each unique user
                for username in unique_users:
                    try:
                        # Try to get full name
                        wmic_output = subprocess.check_output(["wmic", "useraccount", "where", f"name='{username}'", "get", "fullname"]).decode().strip()
                        lines = wmic_output.split("\n")
                        full_name = ""
                        if len(lines) >= 2:
                            full_name = lines[1].strip()
                            
                        user_entry = {
                            "username": username,
                            "full_name": full_name
                        }
                        
                        users_data["all_logged_users"].append(user_entry)
                    except:
                        users_data["all_logged_users"].append({"username": username})
            
            # Add count of user sessions
            users_data["total_user_count"] = len(unique_users)
        except:
            # If we can't get information about all logged users, just include the current user
            users_data["all_logged_users"].append({
                "username": getpass.getuser()
            })
            users_data["total_user_count"] = 1
            
        # Create structured response
        result = {
            "timestamp": response_time,
            "request_time": response_time,
            "type": "logged_users",
            "is_cached": False,
            "data": users_data
        }
        
        return result